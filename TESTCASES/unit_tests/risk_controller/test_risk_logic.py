"""
u98ceu63a7u670du52a1u7684u5355u5143u6d4bu8bd5
u6d4bu8bd5u98ceu63a7u89c4u5219u68c0u67e5u548cu4ea4u6613u8bb0u5f55u529fu80fd
"""

import sys
import os
import json
import time
import pytest
from unittest.mock import patch, MagicMock

# u6dfbu52a0u9879u76eeu6839u76eeu5f55u5230Pythonu8defu5f84uff0cu4ee5u4fbfu80fdu591fu5bfcu5165u670du52a1u4ee3u7801
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# u5bfcu5165u5f85u6d4bu8bd5u7684u6a21u5757
from services.risk_controller.logic import risk_logic
from TESTCASES.test_config import TEST_SIGNALS

# u6d4bu8bd5u6570u636e
TOKEN_SIGNAL = TEST_SIGNALS["token_format"]


class TestRiskLogic:
    """u6d4bu8bd5u98ceu63a7u903bu8f91"""
    
    def setup_method(self):
        """u6bcfu4e2au6d4bu8bd5u65b9u6cd5u524du7684u8bbeu7f6e"""
        # u91cdu7f6eu98ceu63a7u76f8u5173u7684u5168u5c40u53d8u91cf
        risk_logic.LAST_TRADE_TIME = 0
        risk_logic.DAILY_VOLUME = 0
        risk_logic.DAILY_RESET = time.time() - 100  # u8bbeu7f6eu4e3a100u79d2u524du7684u503c
        
        # u4fddu5b58u539fu59cb RISK_PARAMS u5e76u8bbeu7f6eu6d4bu8bd5u503c
        self.original_params = risk_logic.RISK_PARAMS.copy()
        risk_logic.RISK_PARAMS = {
            "max_trade_amount": 1000,
            "daily_limit": 5000,
            "cooldown": 60
        }
    
    def teardown_method(self):
        """u6bcfu4e2au6d4bu8bd5u65b9u6cd5u540eu7684u6e05u7406"""
        # u6062u590du539fu59cb RISK_PARAMS
        risk_logic.RISK_PARAMS = self.original_params
    
    def test_check_risk_normal(self):
        """u6d4bu8bd5u6b63u5e38u60c5u51b5u4e0bu7684u98ceu63a7u68c0u67e5"""
        # u6b63u5e38u8303u56f4u5185u7684u4ea4u6613
        signal = {"amount": "500"}  # u5c0fu4e8e max_trade_amount
        result = risk_logic.check_risk(signal)
        assert result["allowed"] is True, "u6b63u5e38u8303u56f4u5185u7684u4ea4u6613u5e94u8be5u88abu5141u8bb8"
    
    def test_check_risk_amount_exceed(self):
        """u6d4bu8bd5u4ea4u6613u91d1u989du8d85u8fc7u4e0au9650u7684u60c5u51b5"""
        # u91d1u989du8d85u8fc7u4e0au9650u7684u4ea4u6613
        signal = {"amount": "1500"}  # u5927u4e8e max_trade_amount (1000)
        result = risk_logic.check_risk(signal)
        assert result["allowed"] is False, "u91d1u989du8d85u8fc7u4e0au9650u7684u4ea4u6613u5e94u8be5u88abu62d2u7edd"
        assert "amount exceeds limit" in result["reason"].lower(), "u5e94u6307u51fau91d1u989du8d85u8fc7u4e0au9650u7684u539fu56e0"
    
    def test_check_risk_daily_limit(self):
        """u6d4bu8bd5u6bcfu65e5u4ea4u6613u9650u989du7684u68c0u67e5"""
        # u9996u5148u8bb0u5f55u4e00u4e9bu4ea4u6613u4ee5u8fbeu5230u65e5u9650u989du7684u4e34u754cu503c
        risk_logic.DAILY_VOLUME = 4600  # u5df2u7ecfu4f7fu7528u4e864600uff0cu8fd8u5269400u7684u7a7au95f4
        
        # u5728u65e5u9650u989du8303u56f4u5185u7684u4ea4u6613
        signal1 = {"amount": "300"}  # u52a0u4e0au5df2u6709u76844600uff0cu603bu8ba14900uff0cu5c0fu4e8e daily_limit (5000)
        result1 = risk_logic.check_risk(signal1)
        assert result1["allowed"] is True, "u5728u65e5u9650u989du8303u56f4u5185u7684u4ea4u6613u5e94u8be5u88abu5141u8bb8"
        
        # u8d85u8fc7u65e5u9650u989du7684u4ea4u6613
        signal2 = {"amount": "500"}  # u52a0u4e0au5df2u6709u76844600uff0cu603bu8ba15100uff0cu5927u4e8e daily_limit (5000)
        result2 = risk_logic.check_risk(signal2)
        assert result2["allowed"] is False, "u8d85u8fc7u65e5u9650u989du7684u4ea4u6613u5e94u8be5u88abu62d2u7edd"
        assert "daily volume limit" in result2["reason"].lower(), "u5e94u6307u51fau8d85u8fc7u65e5u9650u989du7684u539fu56e0"
    
    def test_check_risk_cooldown(self):
        """u6d4bu8bd5u4ea4u6613u51b7u5374u671fu9650u5236"""
        # u5148u8bb0u5f55u4e00u6b21u4ea4u6613u65f6u95f4
        risk_logic.LAST_TRADE_TIME = time.time() - 30  # 30u79d2u524du4ea4u6613uff0cu51b7u5374u671fu4e3a60u79d2
        
        # u5728u51b7u5374u671fu5185u7684u4ea4u6613
        signal = {"amount": "100"}
        result = risk_logic.check_risk(signal)
        assert result["allowed"] is False, "u5728u51b7u5374u671fu5185u7684u4ea4u6613u5e94u8be5u88abu62d2u7edd"
        assert "cooldown period" in result["reason"].lower(), "u5e94u6307u51fau4ea4u6613u5728u51b7u5374u671fu5185u7684u539fu56e0"
        
        # u5bf9u4e8eu8d85u8fc7u51b7u5374u671fu7684u60c5u51b5u8fdbu884cu6d4bu8bd5
        risk_logic.LAST_TRADE_TIME = time.time() - 70  # 70u79d2u524du4ea4u6613uff0cu8d85u8fc7u51b7u5374u671f
        result = risk_logic.check_risk(signal)
        assert result["allowed"] is True, "u8d85u8fc7u51b7u5374u671fu7684u4ea4u6613u5e94u8be5u88abu5141u8bb8"
    
    def test_daily_reset(self):
        """u6d4bu8bd5u6bcfu65e5u91cdu7f6eu529fu80fd"""
        # u6a21u62dfu524du4e00u5929u7684u6570u636e
        risk_logic.DAILY_VOLUME = 3000
        risk_logic.DAILY_RESET = time.time() - 86500  # u8d85u8fc724u5c0fu65f6(86400u79d2)
        
        # u6267u884cu98ceu63a7u68c0u67e5uff0cu5e94u8be5u89e6u53d1u6bcfu65e5u91cdu7f6e
        signal = {"amount": "100"}
        result = risk_logic.check_risk(signal)
        
        # u9a8cu8bc1u662fu5426u91cdu7f6eu4e86u6bcfu65e5u91cf
        assert risk_logic.DAILY_VOLUME == 0, "u8d85u8fc724u5c0fu65f6u540eu5e94u91cdu7f6eu6bcfu65e5u4ea4u6613u91cf"
        assert result["allowed"] is True, "u91cdu7f6eu540eu7684u4ea4u6613u5e94u8be5u88abu5141u8bb8"
    
    def test_record_trade(self):
        """u6d4bu8bd5u4ea4u6613u8bb0u5f55u529fu80fd"""
        # u8bb0u5f55u524du7684u521du59cbu91cf
        initial_volume = risk_logic.DAILY_VOLUME
        
        # u8bb0u5f55u4e00u6b21u4ea4u6613
        trade = {"amount": "200"}
        result = risk_logic.record_trade(trade)
        
        # u9a8cu8bc1u7ed3u679c
        assert result["recorded"] is True, "u4ea4u6613u8bb0u5f55u5e94u8fd4u56deu6210u529f"
        assert risk_logic.DAILY_VOLUME == initial_volume + 200, "u6bcfu65e5u4ea4u6613u91cfu5e94u589eu52a0u4ea4u6613u91d1u989d"
        assert result["current_daily_volume"] == risk_logic.DAILY_VOLUME, "u8fd4u56deu7684u5f53u524du6bcfu65e5u91cfu5e94u4e0eu5185u90e8u8bb0u5f55u4e00u81f4"


if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
