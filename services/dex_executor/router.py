# ATM/services/dex_executor/router.py
from fastapi import APIRouter
from logic import dex_logic

router = APIRouter()

@router.post("/dex/execute")
def execute_trade(trade: dict):
    try:
        tx_hash = dex_logic.execute_swap(trade)
        return {"status": "submitted", "tx_hash": tx_hash}
    except Exception as e:
        return {"error": str(e)}
