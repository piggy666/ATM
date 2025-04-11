"""测试配置和通用辅助函数"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径，以便能够导入服务代码
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# 测试配置
TEST_CONFIG = {
    "network_mode": "testnet",
    "wallet": {
        "address": "0x8456562E8f91C9f791335f60388E2F777AE077eB",
        "private_key": "62a030db1bf7e52c98f89a20f554a581c427f884d65fe39c5a9de0a495162e0f"
    },
    "token_addresses": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6",  # Goerli 测试网
        "USDT": "0x509Ee0d083DdF8AC028f2a56731412edD63223B9",  # Goerli 测试网
        "USDC": "0x07865c6E87B9F70255377e024ace6630C1Eaa37F",  # Goerli 测试网
        "WBTC": "0xC04B0d3107736C32e19F1c62b2aF67BE61d63a05",  # Goerli 测试网
    },
    "testnet": {
        "chain_id": 5,
        "rpc_url": "https://goerli.infura.io/v3/b9a1744a0b9e497da46190ecc10e0cdf",
        "router_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    }
}

# 测试交易信号样例
TEST_SIGNALS = {
    "symbol_format": {
        "symbol": "WBTC/USDT",
        "side": "buy",
        "amount": "0.001",
        "slippage": 0.01
    },
    "token_format": {
        "token_in": "USDT",
        "token_out": "WBTC",
        "amount": "10",
        "slippage": 0.01
    },
    "address_format": {
        "token_in": "0x509Ee0d083DdF8AC028f2a56731412edD63223B9",  # USDT on Goerli
        "token_out": "0xC04B0d3107736C32e19F1c62b2aF67BE61d63a05",  # WBTC on Goerli
        "amount": "10",
        "slippage": 0.01
    },
    "with_wallet": {
        "token_in": "USDT",
        "token_out": "WBTC",
        "amount": "10",
        "wallet_address": TEST_CONFIG["wallet"]["address"],
        "private_key": TEST_CONFIG["wallet"]["private_key"]
    }
}

# 辅助函数
def get_project_path(relative_path=""):
    """获取项目中文件的绝对路径"""
    return os.path.join(ROOT_DIR, relative_path)

def load_service_config():
    """加载实际服务配置"""
    config_path = get_project_path("services/config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"无法加载配置文件: {e}")
        return {}
