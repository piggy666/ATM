# ATM/services/execution_monitor/router.py
from fastapi import APIRouter
# 同时支持Docker环境和本地环境的导入
try:
    from services.execution_monitor.logic import monitor_logic
except ImportError:
    # 本地环境回退使用相对导入
    from .logic import monitor_logic

router = APIRouter()

@router.post("/monitor")
def monitor_transaction(tx_hash: str):
    status = monitor_logic.monitor_tx(tx_hash)
    return {"tx_hash": tx_hash, "status": status}

@router.get("/monitor/status")
def get_monitor_status():
    # 返回服务状态信息
    return {"status": "running", "service": "execution_monitor"}
