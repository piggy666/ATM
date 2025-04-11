"""信号监听服务的单元测试"""

import sys
import os
import json
import pytest
import requests
import requests_mock
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径，以便能够导入服务代码
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 导入待测试的模块
from services.signal_listener.logic import signal_logic
from TESTCASES.test_config import TEST_SIGNALS

# 设置测试信号
SYMBOL_SIGNAL = TEST_SIGNALS["symbol_format"]
TOKEN_SIGNAL = TEST_SIGNALS["token_format"]
ADDRESS_SIGNAL = TEST_SIGNALS["address_format"]


@pytest.fixture
def mock_requests():
    """使用requests_mock模拟HTTP请求"""
    with requests_mock.Mocker() as m:
        yield m


class TestSignalLogic:
    """信号处理逻辑测试"""

    def test_process_trade_symbols(self):
        """测试交易符号处理功能"""
        # 测试买入信号处理
        buy_signal = SYMBOL_SIGNAL.copy()
        buy_signal["side"] = "buy"
        signal_logic.process_trade_symbols(buy_signal)
        
        # 对于BTC/USDT买入 - token_in应该是USDT，token_out应该是WBTC
        assert buy_signal.get("token_in") == "USDT"
        assert buy_signal.get("token_out") == "WBTC"

        # 测试卖出信号处理
        sell_signal = SYMBOL_SIGNAL.copy()
        sell_signal["side"] = "sell"
        signal_logic.process_trade_symbols(sell_signal)
        
        # 对于BTC/USDT卖出 - token_in应该是WBTC，token_out应该是USDT
        assert sell_signal.get("token_in") == "WBTC"
        assert sell_signal.get("token_out") == "USDT"

    def test_validate_signal_format(self):
        """测试信号格式验证"""
        # 有效信号
        valid_signal = {
            "token_in": "USDT",
            "token_out": "WBTC",
            "amount": "10"
        }
        assert signal_logic.validate_signal_format(valid_signal) is True

        # 缺少token_in
        invalid_signal1 = {
            "token_out": "WBTC",
            "amount": "10"
        }
        assert signal_logic.validate_signal_format(invalid_signal1) is False

        # 缺少token_out
        invalid_signal2 = {
            "token_in": "USDT",
            "amount": "10"
        }
        assert signal_logic.validate_signal_format(invalid_signal2) is False

        # 缺少amount
        invalid_signal3 = {
            "token_in": "USDT",
            "token_out": "WBTC"
        }
        assert signal_logic.validate_signal_format(invalid_signal3) is False

    def test_handle_signal_with_mocks(self, mock_requests):
        """使用mock测试完整的信号处理流程"""
        # 模拟风控校验请求和响应
        mock_requests.post(
            "http://risk_controller:52120/risk/check",
            json={"allowed": True}
        )
        
        # 模拟DEX执行请求和响应
        mock_requests.post(
            "http://dex_executor:52130/dex/execute",
            json={"status": "submitted", "tx_hash": "0x1234567890abcdef"}
        )
        
        # 模拟交易监控请求和响应
        mock_requests.post(
            "http://execution_monitor:52140/monitor/tx",
            json={
                "status": "confirmed",
                "timestamp": 1681234567,
                "confirmation_blocks": 12
            }
        )
        
        # 模拟风控记录请求和响应
        mock_requests.post(
            "http://risk_controller:52120/risk/record",
            json={"recorded": True}
        )
        
        # 执行测试 - 使用代币符号格式
        result = signal_logic.handle_signal(TOKEN_SIGNAL.copy())
        
        # 验证结果
        assert result.get("status") == "success"
        assert "tx_hash" in result
        assert result.get("token_in") == TOKEN_SIGNAL.get("token_in")
        assert result.get("token_out") == TOKEN_SIGNAL.get("token_out")

    def test_handle_signal_risk_rejected(self, mock_requests):
        """测试风控拒绝的情况"""
        # 模拟风控拒绝
        mock_requests.post(
            "http://risk_controller:52120/risk/check",
            json={"allowed": False, "reason": "Risk limit exceeded"}
        )
        
        # 执行测试
        result = signal_logic.handle_signal(TOKEN_SIGNAL.copy())
        
        # 验证结果
        assert result.get("status") == "rejected"
        assert "Risk limit exceeded" in result.get("reason", "")

    def test_handle_signal_dex_failed(self, mock_requests):
        """测试DEX执行失败的情况"""
        # 模拟风控通过
        mock_requests.post(
            "http://risk_controller:52120/risk/check",
            json={"allowed": True}
        )
        
        # 模拟DEX执行失败
        mock_requests.post(
            "http://dex_executor:52130/dex/execute",
            json={"status": "failed", "error": "Execution error"}
        )
        
        # 执行测试
        result = signal_logic.handle_signal(TOKEN_SIGNAL.copy())
        
        # 验证结果
        assert result.get("status") == "failed"
        assert "DEX execution failed" in result.get("reason", "")

    def test_handle_invalid_signal(self):
        """测试无效信号"""
        # 缺少必要字段的信号
        invalid_signal = {"token_in": "USDT"}
        result = signal_logic.handle_signal(invalid_signal)
        
        # 验证结果
        assert "error" in result
        assert "Invalid signal format" in result.get("error", "")


if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
