# ATM/services/config_service/router.py
from fastapi import APIRouter, HTTPException
import os, json

# u5728Dockeru73afu5883u4e2du4f7fu7528u7eddu5bf9u5bfcu5165
try:
    from services.config_service.logic.config_manager import ConfigManager
except ImportError:
    # u5728u672cu5730u5f00u53d1u73afu5883u4e2du56deu9000u5230u76f8u5bf9u5bfcu5165
    from .logic.config_manager import ConfigManager

router = APIRouter()

# u9996u5148u5c1du8bd5Dockeru73afu5883u4e2du7684u914du7f6eu6587u4ef6u8defu5f84
config_path = "/app/config.json"

# u786eu4fddu914du7f6eu6587u4ef6u662fu771fu5b9eu6587u4ef6u800cu4e0du662fu76eeu5f55
if not os.path.isfile(config_path):
    # u5982u679cu5728Dockeru4e2du662fu76eeu5f55uff0cu5c1du8bd5u4f7fu7528u9ed8u8ba4u914du7f6eu521bu5efau4e34u65f6u6587u4ef6
    if os.path.isdir(config_path):
        # u5220u9664u76eeu5f55u5e76u521bu5efau4e34u65f6u914du7f6eu6587u4ef6
        try:
            os.rmdir(config_path)
            # u521bu5efau4e34u65f6u914du7f6eu6587u4ef6u5e76u5199u5165u9ed8u8ba4u914du7f6e
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
                }
            }
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            print(f"Error creating temporary config file: {e}")
    
    # u5982u679cu4ecdu7136u5931u8d25uff0cu56deu9000u5230u672cu5730u73afu5883u8defu5f84
    if not os.path.isfile(config_path):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

# u4f7fu7528u786eu8ba4u6709u6548u7684u914du7f6eu6587u4ef6u8defu5f84u521du59cbu5316ConfigManager
if os.path.isfile(config_path):
    cfg = ConfigManager(config_path)
else:
    # u5982u679cu4ecdu7136u65e0u6cd5u627eu5230u914du7f6eu6587u4ef6uff0cu4f7fu7528u9ed8u8ba4u914du7f6e
    print("WARNING: Could not find config file. Using default configuration.")
    cfg = ConfigManager(None)  # u9700u8981u4feeu6539ConfigManageru4ee5u652fu6301u65e0u6587u4ef6u65f6u4f7fu7528u9ed8u8ba4u503c

@router.get("/config")
def get_full_config():
    return {
        "network_mode": cfg.network_mode,
        "auto_approve": cfg.auto_approve,
        "chain_id": cfg.chain_id,
        "router_address": cfg.router_address,
        "rpc_url": cfg.rpc_url,
        "trade_pair": cfg.trade_pair
    }

@router.get("/config/{key}")
def get_config_key(key: str):
    if key == "network":
        return {"network_mode": cfg.network_mode}
    elif key == "chain_id":
        return {"chain_id": cfg.chain_id}
    elif key == "router_address":
        return {"router_address": cfg.router_address}
    else:
        return {"error": f"Unknown config key: {key}"}
