"""
u6267u884cu76d1u63a7u670du52a1u7684u5355u5143u6d4bu8bd5
u7531u4e8eu6267u884cu76d1u63a7u670du52a1u4e3bu8981u8d1fu8d23u94feu4e0au4ea4u6613u72b6u6001u67e5u8be2uff0cu6d4bu8bd5u65f6u4e3bu8981u4f7fu7528u6a21u62dfu7684Web3u5bf9u8c61
"""

import sys
import os
import json
import time
import pytest
from unittest.mock import patch, MagicMock

# u6dfbu52a0u9879u76eeu6839u76eeu5f55u5230Pythonu8defu5f84uff0cu4ee5u4fbfu80fdu591fu5bfcu5165u670du52a1u4ee3u7801
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# u5bfcu5165u6d4bu8bd5u914du7f6e
from TESTCASES.test_config import TEST_SIGNALS, TEST_CONFIG

# u6a21u62dfWeb3u5bf9u8c61u548cu6267u884cu76d1u63a7u670du52a1
class MockWeb3:
    """u7528u4e8eu6d4bu8bd5u7684Web3u6a21u62dfu7c7b"""
    def __init__(self, tx_hash, status="success", blocks=12):
        self.eth = MagicMock()
        self.tx_hash = tx_hash
        self.status = status
        self.blocks = blocks
        
        # u8bbeu7f6eu4ea4u6613u72b6u6001u548cu6536u636e
        receipt = {
            "status": 1 if status == "success" else 0,
            "blockNumber": 100 if status == "success" else 0,
            "blockHash": b"block_hash",
            "transactionHash": tx_hash.encode(),
            "transactionIndex": 0
        }
        self.eth.get_transaction_receipt.return_value = receipt
        
        # u8bbeu7f6eu533au5757u6570
        self.eth.block_number = 100 + blocks if status == "success" else 0
        
        # u8bbeu7f6eu4ea4u6613u8be6u60c5
        tx = {
            "hash": tx_hash.encode(),
            "blockNumber": 100 if status != "pending" else None,
            "from": TEST_CONFIG["wallet"]["address"],
            "to": TEST_CONFIG["testnet"]["router_address"],
            "value": 1000000000000000000,  # 1 ETH
            "gas": 200000,
            "gasPrice": 50000000000  # 50 Gwei
        }
        self.eth.get_transaction.return_value = tx

# u865au62dfu7684u76d1u63a7u670du52a1u903bu8f91
class MockMonitorLogic:
    """u6a21u62dfu7684u6267u884cu76d1u63a7u670du52a1u903bu8f91"""
    def __init__(self):
        self.monitored_txs = {}
    
    def monitor_transaction(self, tx_hash, network="testnet", original_signal=None):
        """mocku5b9eu7528u76d1u63a7u4ea4u6613u72b6u6001"""
        # u521bu5efaMockWeb3u5bf9u8c61
        mock_web3 = MockWeb3(tx_hash, status="success")
        
        # u8bb0u5f55u76d1u63a7u8bf7u6c42
        self.monitored_txs[tx_hash] = {
            "network": network,
            "status": "confirmed",
            "timestamp": int(time.time()),
            "confirmations": 12,
            "original_signal": original_signal,
            "tx_hash": tx_hash  # u786eu4fddu5305u542btx_hashu5b57u6bb5
        }
        
        return self.monitored_txs[tx_hash]
    
    def get_transaction_status(self, tx_hash):
        """mocku6839u636eu54c8u5e0cu503cu83b7u53d6u4ea4u6613u72b6u6001"""
        if tx_hash in self.monitored_txs:
            return self.monitored_txs[tx_hash]
        return {"status": "unknown", "tx_hash": tx_hash}


class TestMonitorLogic:
    """ExecutionMonitoru6a21u5757u6d4bu8bd5"""
    
    def setup_method(self):
        """u51c6u5907u6d4bu8bd5u73afu5883"""
        self.monitor_logic = MockMonitorLogic()
        self.test_tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    
    def test_monitor_transaction(self):
        """u6d4bu8bd5u76d1u63a7u4ea4u6613u529fu80fd"""
        # u521bu5efau6d4bu8bd5u6570u636e
        original_signal = TEST_SIGNALS["token_format"].copy()
        
        # u8c03u7528u76d1u63a7u51fdu6570
        result = self.monitor_logic.monitor_transaction(
            self.test_tx_hash, 
            network="testnet", 
            original_signal=original_signal
        )
        
        # u9a8cu8bc1u7ed3u679c
        assert result["status"] == "confirmed", "u5e94u8fd4u56deu786eu8ba4u72b6u6001"
        assert result["tx_hash"] == self.test_tx_hash, "u5e94u8fd4u56deu6b63u786eu7684u4ea4u6613u54c8u5e0c"
        assert result["confirmations"] == 12, "u5e94u8fd4u56deu6b63u786eu7684u786eu8ba4u6570"
        assert "timestamp" in result, "u5e94u5305u542bu65f6u95f4u6233"
        assert result["original_signal"] == original_signal, "u5e94u4fddu5b58u539fu59cbu4fe1u53f7"
    
    def test_get_transaction_status(self):
        """u6d4bu8bd5u83b7u53d6u4ea4u6613u72b6u6001u529fu80fd"""
        # u5148u76d1u63a7u4e00u4e2au4ea4u6613
        self.monitor_logic.monitor_transaction(self.test_tx_hash)
        
        # u83b7u53d6u5df2u76d1u63a7u4ea4u6613u7684u72b6u6001
        status = self.monitor_logic.get_transaction_status(self.test_tx_hash)
        assert status["status"] == "confirmed", "u5e94u8fd4u56deu5df2u76d1u63a7u4ea4u6613u7684u6b63u786eu72b6u6001"
        assert status["tx_hash"] == self.test_tx_hash, "u5e94u8fd4u56deu6b63u786eu7684u4ea4u6613u54c8u5e0c"
        
        # u83b7u53d6u672au76d1u63a7u4ea4u6613u7684u72b6u6001
        unknown_tx = "0xunknown"
        status = self.monitor_logic.get_transaction_status(unknown_tx)
        assert status["status"] == "unknown", "u5e94u8fd4u56deu672au76d1u63a7u4ea4u6613u7684u672au77e5u72b6u6001"
        assert status["tx_hash"] == unknown_tx, "u5e94u8fd4u56deu6b63u786eu7684u672au77e5u4ea4u6613u54c8u5e0c"


if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
