# ATM/services/config_service/router.py
from fastapi import APIRouter
from logic.config_manager import ConfigManager

router = APIRouter()
# 注意：相对路径请根据实际部署情况调整
cfg = ConfigManager("../../../config.json")

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
    value = getattr(cfg, key, None)
    if value is None:
        return {"error": "Key not found"}
    return {key: value}
