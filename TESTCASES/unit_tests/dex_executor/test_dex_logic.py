"""
DEXu6267u884cu5668u7684u5355u5143u6d4bu8bd5
u6d4bu8bd5u4ea4u6613u5bf9u89e3u6790u3001u7f51u7edcu914du7f6eu52a0u8f7du53cau4ea4u6613u6267u884cu529fu80fd
"""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

# u6dfbu52a0u9879u76eeu6839u76eeu5f55u5230Pythonu8defu5f84uff0cu4ee5u4fbfu80fdu591fu5bfcu5165u670du52a1u4ee3u7801
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# u5bfcu5165u5f85u6d4bu8bd5u7684u6a21u5757
from services.dex_executor.logic import dex_logic
from TESTCASES.test_config import TEST_SIGNALS, TEST_CONFIG

# u6d4bu8bd5u6570u636e
TOKEN_SIGNAL = TEST_SIGNALS["token_format"]
ADDRESS_SIGNAL = TEST_SIGNALS["address_format"]
WITH_WALLET_SIGNAL = TEST_SIGNALS["with_wallet"]
TEST_WALLET = TEST_CONFIG["wallet"]

class TestDexLogic:
    """u6d4bu8bd5DEXu6267u884cu5668u903bu8f91"""
    
    def test_resolve_token_address(self):
        """u6d4bu8bd5u4ee3u5e01u7b26u53f7u89e3u6790u529fu80fd"""
        # u6d4bu8bd5u70b9uff1au89e3u6790u5df2u7ecfu662fu5730u5740u683cu5f0fu7684u8f93u5165
        address = "0x1234567890abcdef1234567890abcdef12345678"
        result = dex_logic.resolve_token_address(address)
        assert result == address, "u5df2u7ecfu662fu5730u5740u683cu5f0fu7684u8f93u5165u5e94u539fu6837u8fd4u56de"
        
        # u6d4bu8bd5u70b9uff1au89e3u6790u7b26u53f7u683cu5f0fu7684u8f93u5165
        result = dex_logic.resolve_token_address("USDT")
        assert result == TEST_CONFIG["token_addresses"]["USDT"] or \
               result in [v for k, v in dex_logic.TOKEN_ADDRESSES.items() if k == "USDT"], \
               "USDTu7b26u53f7u5e94u8be5u88abu89e3u6790u4e3au76f8u5e94u5730u5740"
        
        # u6d4bu8bd5u70b9uff1au5904u7406u4e0du5b58u5728u7684u7b26u53f7
        nonexistent = "NONEXISTENT_TOKEN"
        result = dex_logic.resolve_token_address(nonexistent)
        assert result == nonexistent, "u4e0du5b58u5728u7684u7b26u53f7u5e94u539fu6837u8fd4u56de"
    
    def test_get_network_config(self):
        """u6d4bu8bd5u7f51u7edcu914du7f6eu52a0u8f7du529fu80fd"""
        # u6d4bu8bd5u70b9uff1au52a0u8f7du9ed8u8ba4u7f51u7edcu914du7f6e
        config = dex_logic.get_network_config()
        assert "chain_id" in config, "u7f51u7edcu914du7f6eu5e94u5305u542b chain_id"
        assert "rpc_url" in config, "u7f51u7edcu914du7f6eu5e94u5305u542b rpc_url"
        assert "router_address" in config, "u7f51u7edcu914du7f6eu5e94u5305u542b router_address"
        assert "web3" in config, "u7f51u7edcu914du7f6eu5e94u5305u542b web3 u5b9eu4f8b"
        
        # u6d4bu8bd5u70b9uff1au6307u5b9au7f51u7edcu7c7bu578b
        testnet_config = dex_logic.get_network_config("testnet")
        assert testnet_config["chain_id"] == dex_logic.config_data["testnet"]["chain_id"], "u6d4bu8bd5u7f51u914du7f6eIDu4e0du5339u914d"
        
        # u6d4bu8bd5u70b9uff1au5904u7406u65e0u6548u7f51u7edcu7c7bu578b
        invalid_config = dex_logic.get_network_config("invalid_network")
        assert invalid_config["chain_id"] == dex_logic.config_data["testnet"]["chain_id"], "u65e0u6548u7f51u7edcu5e94u9ed8u8ba4u4f7fu7528u6d4bu8bd5u7f51"
    
    @patch('services.dex_executor.logic.dex_logic.Web3')
    def test_execute_swap_with_wallet_from_config(self, mock_web3):
        """u6d4bu8bd5u4econfigu6587u4ef6u52a0u8f7du94b1u5305"""
        # u6a21u62dfWeb3u76f8u5173u65b9u6cd5
        mock_web3_instance = MagicMock()
        mock_web3.HTTPProvider.return_value = MagicMock()
        mock_web3.to_checksum_address.return_value = "0xChecksumAddress"
        mock_web3.eth.return_value = MagicMock()
        mock_web3.to_wei.return_value = 5000000000
        
        # u6a21u62dfu533au5757u94feu4ea4u4e92
        mock_contract = MagicMock()
        mock_contract.functions.swapExactTokensForTokens.return_value.build_transaction.return_value = {}
        mock_web3.eth.contract.return_value = mock_contract
        
        # u6a21u62dfu4ea4u6613u7b7eu540du548cu63d0u4ea4
        mock_signed_tx = MagicMock()
        mock_signed_tx.rawTransaction = b'raw_tx_data'
        mock_web3.eth.account.sign_transaction.return_value = mock_signed_tx
        mock_web3.eth.send_raw_transaction.return_value = b'tx_hash'
        
        # u51c6u5907u6d4bu8bd5u6570u636e - u4e0du5305u542bu94b1u5305u4fe1u606fuff0cu5e94u4f7fu7528u914du7f6eu4e2du7684u94b1u5305
        test_trade = TOKEN_SIGNAL.copy()
        
        # u4fddu5b58u539fu59cbu51fdu6570u5e76patch
        original_resolve = dex_logic.resolve_token_address
        dex_logic.resolve_token_address = lambda x: x  # u7b80u5316u6d4bu8bd5uff0cu76f4u63a5u8fd4u56deu8f93u5165
        
        try:
            # u6267u884cu6d4bu8bd5
            result = dex_logic.execute_swap(test_trade)
            
            # u68c0u67e5u662fu5426u4f7fu7528u4e86u914du7f6eu4e2du7684u94b1u5305
            mock_web3.eth.account.sign_transaction.assert_called_once()
            call_args = mock_web3.eth.account.sign_transaction.call_args[1]
            assert "private_key" in call_args, "u5e94u4f7fu7528u79c1u94a5u7b7eu540du4ea4u6613"
        finally:
            # u6062u590du539fu59cbu51fdu6570
            dex_logic.resolve_token_address = original_resolve
    
    @patch('services.dex_executor.logic.dex_logic.Web3')
    def test_execute_swap_with_explicit_wallet(self, mock_web3):
        """u6d4bu8bd5u4f7fu7528u663eu5f0fu63d0u4f9bu7684u94b1u5305u4fe1u606f"""
        # u6a21u62dfWeb3u76f8u5173u65b9u6cd5
        mock_web3_instance = MagicMock()
        mock_web3.HTTPProvider.return_value = MagicMock()
        mock_web3.to_checksum_address.return_value = "0xChecksumAddress"
        mock_web3.eth.return_value = MagicMock()
        mock_web3.to_wei.return_value = 5000000000
        
        # u6a21u62dfu533au5757u94feu4ea4u4e92
        mock_contract = MagicMock()
        mock_contract.functions.swapExactTokensForTokens.return_value.build_transaction.return_value = {}
        mock_web3.eth.contract.return_value = mock_contract
        
        # u6a21u62dfu4ea4u6613u7b7eu540du548cu63d0u4ea4
        mock_signed_tx = MagicMock()
        mock_signed_tx.rawTransaction = b'raw_tx_data'
        mock_web3.eth.account.sign_transaction.return_value = mock_signed_tx
        mock_web3.eth.send_raw_transaction.return_value = b'tx_hash'
        
        # u51c6u5907u6d4bu8bd5u6570u636e - u5305u542bu663eu5f0fu7684u94b1u5305u4fe1u606f
        test_trade = WITH_WALLET_SIGNAL.copy()
        
        # u4fddu5b58u539fu59cbu51fdu6570u5e76patch
        original_resolve = dex_logic.resolve_token_address
        dex_logic.resolve_token_address = lambda x: x  # u7b80u5316u6d4bu8bd5uff0cu76f4u63a5u8fd4u56deu8f93u5165
        
        try:
            # u6267u884cu6d4bu8bd5
            result = dex_logic.execute_swap(test_trade)
            
            # u68c0u67e5u662fu5426u4f7fu7528u4e86u663eu5f0fu63d0u4f9bu7684u94b1u5305
            mock_web3.eth.account.sign_transaction.assert_called_once()
            call_args = mock_web3.eth.account.sign_transaction.call_args[1]
            assert call_args["private_key"] == test_trade["private_key"], "u5e94u4f7fu7528u663eu5f0fu63d0u4f9bu7684u79c1u94a5"
        finally:
            # u6062u590du539fu59cbu51fdu6570
            dex_logic.resolve_token_address = original_resolve
    
    def test_execute_swap_missing_params(self):
        """u6d4bu8bd5u7f3au5c11u5fc5u8981u53c2u6570u7684u60c5u51b5"""
        # u51c6u5907u6d4bu8bd5u6570u636e - u7f3au5c11token_in
        invalid_trade1 = {
            "token_out": "WBTC",
            "amount": "10"
        }
        
        # u6d4bu8bd5u7f3au5c11token_in
        with pytest.raises(Exception) as excinfo:
            dex_logic.execute_swap(invalid_trade1)
        assert "token addresses" in str(excinfo.value).lower(), "u5e94u629bu51fau5173u4e8eu7f3au5c11u4ee3u5e01u5730u5740u7684u5f02u5e38"
        
        # u51c6u5907u6d4bu8bd5u6570u636e - u7f3au5c11amount
        invalid_trade2 = {
            "token_in": "USDT",
            "token_out": "WBTC"
        }
        
        # u6d4bu8bd5u7f3au5c11amount
        with pytest.raises(Exception) as excinfo:
            dex_logic.execute_swap(invalid_trade2)
        assert "amount" in str(excinfo.value).lower(), "u5e94u629bu51fau5173u4e8eu7f3au5c11u91d1u989du7684u5f02u5e38"


if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
