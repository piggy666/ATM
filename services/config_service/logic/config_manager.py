# ATM/services/config_service/logic/config_manager.py
import json

class ConfigManager:
    def __init__(self, config_path=None):
        # 默认配置
        default_config = {
            "network_mode": "testnet",
            "auto_approve": False,
            "testnet": {
                "chain_id": 11155111,  # Sepolia
                "rpc_url": "https://rpc.sepolia.org",
                "router_address": "0x0000000000000000000000000000000000000000"
            },
            "ports": {
                "config_service": 52100,
                "signal_listener": 52110,
                "risk_controller": 52120,
                "dex_executor": 52130,
                "execution_monitor": 52140,
                "asset_manager": 52150
            },
            "trade_pair": []
        }
        
        data = default_config
        
        # 如果提供了配置文件路径，尝试读取
        if config_path:
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                print(f"Loaded configuration from {config_path}")
            except Exception as e:
                print(f"Error loading config file {config_path}: {str(e)}")
                print("Using default configuration")
        else:
            print("No config file specified. Using default configuration.")
            
        # 从配置中读取设置
        self.network_mode = data.get("network_mode", "testnet")
        self.auto_approve = data.get("auto_approve", False)
        
        # 读取网络特定配置
        network_cfg = data.get(self.network_mode, {})
        self.chain_id = network_cfg.get("chain_id")
        self.rpc_url = network_cfg.get("rpc_url")
        self.router_address = network_cfg.get("router_address")
        
        # 读取其他设置
        self.trade_pair = data.get("trade_pair", [])
