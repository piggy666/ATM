# ATM/services/signal_listener/logic/signal_logic.py
import requests
import json
import os

LAST_SIGNAL = None

def handle_signal(signal: dict):
    global LAST_SIGNAL
    LAST_SIGNAL = signal
    
    # 处理交易的符号信息，支持使用交易符号（如 BTC/USDT）
    process_trade_symbols(signal)
    
    # 校验信号格式 - 确保包含必要的交易对信息
    if not validate_signal_format(signal):
        return {"error": "Invalid signal format. Must contain token_in and token_out parameters."}
    
    # Step 1: 将信号转发给 Risk Controller 进行风控校验
    try:
        response = requests.post("http://risk_controller:52120/risk/check", json=signal, timeout=5)
        risk_result = response.json()
        if not risk_result.get("allowed", False):
            return {"status": "rejected", "reason": risk_result.get("reason", "Risk check failed")}
    except Exception as e:
        return {"error": f"Risk check failed: {str(e)}"}
    
    # Step 2: 风控通过后，调用 DEX Executor 执行交易
    try:
        dex_response = requests.post("http://dex_executor:52130/dex/execute", json=signal, timeout=10)
        dex_result = dex_response.json()
        if "tx_hash" not in dex_result:
            return {"status": "failed", "reason": "DEX execution failed", "details": dex_result}
        tx_hash = dex_result["tx_hash"]
    except Exception as e:
        return {"error": f"DEX execution failed: {str(e)}"}
    
    # Step 3: 调用 Execution Monitor 监控交易状态
    try:
        monitor_data = {
            "tx_hash": tx_hash,
            "network": signal.get("network", get_default_network()),
            "original_signal": signal
        }
        monitor_response = requests.post("http://execution_monitor:52140/monitor/tx", json=monitor_data, timeout=5)
        monitor_result = monitor_response.json()
    except Exception as e:
        # 交易已发出，但监控设置失败
        return {
            "status": "pending", 
            "tx_hash": tx_hash,
            "warning": f"Transaction submitted but monitoring failed: {str(e)}"
        }
    
    # Step 4: 交易成功记录到风控系统
    try:
        record_data = {
            "amount": signal.get("amount", 0),
            "token_in": signal.get("token_in"),
            "token_out": signal.get("token_out"),
            "tx_hash": tx_hash,
            "timestamp": monitor_result.get("timestamp", 0)
        }
        requests.post("http://risk_controller:52120/risk/record", json=record_data, timeout=5)
    except Exception as e:
        # 记录失败但不影响交易结果
        print(f"Warning: Failed to record trade: {str(e)}")
    
    return {
        "status": "success",
        "tx_hash": tx_hash,
        "monitor_status": monitor_result.get("status", "unknown"),
        "token_in": signal.get("token_in"),
        "token_out": signal.get("token_out"),
        "amount": signal.get("amount")
    }

def process_trade_symbols(signal):
    """处理交易符号信息，支持使用交易符号（如 BTC/USDT），解析为 token_in 和 token_out"""
    # 如果输入了symbol参数（如"BTC/USDT"），且没有指定token_in和token_out，则解析symbol为 token_in 和 token_out
    trading_symbol = signal.get("symbol")
    if trading_symbol and "/" in trading_symbol and not (signal.get("token_in") and signal.get("token_out")):
        parts = trading_symbol.split("/")
        if len(parts) == 2:
            # 分解BTC/USDT符号为 token_in 和 token_out
            base_symbol, quote_symbol = parts  # 基础符号和报价符号
            
            # 判断交易方向
            if signal.get("side", "").lower() == "sell":
                # 卖出时，基础符号为 token_in，报价符号为 token_out - 例如卖出BTC换USDT
                signal["token_in"] = base_symbol  # 卖出基础符号（如BTC）
                signal["token_out"] = quote_symbol  # 购买报价符号（如USDT）
            else:  # 默认为买入
                # 买入时，报价符号为 token_in，基础符号为 token_out - 例如用USDT买BTC
                signal["token_in"] = quote_symbol  # 买入报价符号（如USDT）
                signal["token_out"] = base_symbol  # 购买基础符号（如BTC）

def validate_signal_format(signal: dict) -> bool:
    """验证信号格式是否包含必要的交易对信息"""
    # 必须包含 token_in、token_out 和 amount
    essential_fields = ["token_in", "token_out", "amount"]
    return all(field in signal for field in essential_fields)

def get_default_network() -> str:
    """从配置文件获取默认网络模式"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
            return config.get("network_mode", "testnet")
    except Exception:
        return "testnet"  # 默认回退到测试网

def get_latest_signal():
    return LAST_SIGNAL
