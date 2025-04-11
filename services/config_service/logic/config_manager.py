# ATM/services/config_service/logic/config_manager.py
import json

class ConfigManager:
    def __init__(self, config_path):
        with open(config_path, "r") as f:
            data = json.load(f)
        self.network_mode = data.get("network_mode", "testnet")
        self.auto_approve = data.get("auto_approve", False)
        network_cfg = data.get(self.network_mode, {})
        self.chain_id = network_cfg.get("chain_id")
        self.rpc_url = network_cfg.get("rpc_url")
        self.router_address = network_cfg.get("router_address")
        self.trade_pair = data.get("trade_pair", [])
