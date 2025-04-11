# ATM/services/execution_monitor/router.py
from fastapi import APIRouter
from logic import monitor_logic

router = APIRouter()

@router.post("/monitor")
def monitor_transaction(tx_hash: str):
    status = monitor_logic.monitor_tx(tx_hash)
    return {"tx_hash": tx_hash, "status": status}
