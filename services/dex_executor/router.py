# ATM/services/dex_executor/router.py
from fastapi import APIRouter
# 同时支持Docker环境和本地环境的导入
try:
    from services.dex_executor.logic import dex_logic
except ImportError:
    # 本地环境回退使用相对导入
    from .logic import dex_logic

router = APIRouter()

@router.post("/dex/execute")
def execute_trade(trade: dict):
    try:
        tx_hash = dex_logic.execute_swap(trade)
        return {"status": "submitted", "tx_hash": tx_hash}
    except Exception as e:
        return {"error": str(e)}

@router.get("/dex/status")
def get_dex_status():
    # 返回服务状态信息
    return {"status": "running", "service": "dex_executor"}
