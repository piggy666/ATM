# ATM/services/risk_controller/logic/risk_logic.py
import time

# 模拟风控参数（后续可改为动态从 Config Service 获取）
RISK_PARAMS = {
    "max_trade_amount": 1000,
    "daily_limit": 5000,
    "cooldown": 60
}

LAST_TRADE_TIME = 0
DAILY_VOLUME = 0
DAILY_RESET = time.time()

def check_risk(signal: dict):
    global LAST_TRADE_TIME, DAILY_VOLUME, DAILY_RESET
    now = time.time()
    amount = float(signal.get("amount", 0))
    # 重置每日累计数（超过24小时则重置）
    if now - DAILY_RESET > 86400:
        DAILY_VOLUME = 0
        DAILY_RESET = now
    if amount > RISK_PARAMS["max_trade_amount"]:
        return {"allowed": False, "reason": "Trade amount exceeds limit"}
    if DAILY_VOLUME + amount > RISK_PARAMS["daily_limit"]:
        return {"allowed": False, "reason": "Daily volume limit exceeded"}
    if now - LAST_TRADE_TIME < RISK_PARAMS["cooldown"]:
        return {"allowed": False, "reason": "Cooldown period not elapsed"}
    LAST_TRADE_TIME = now
    return {"allowed": True}

def record_trade(trade: dict):
    global DAILY_VOLUME
    amount = float(trade.get("amount", 0))
    DAILY_VOLUME += amount
    return {"recorded": True, "current_daily_volume": DAILY_VOLUME}
