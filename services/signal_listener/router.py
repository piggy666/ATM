# ATM/services/signal_listener/router.py
from fastapi import APIRouter
from logic import signal_logic

router = APIRouter()

@router.post("/signal")
def receive_signal(signal: dict):
    result = signal_logic.handle_signal(signal)
    return {"result": result}

@router.get("/signal/latest")
def get_latest_signal():
    latest = signal_logic.get_latest_signal()
    return {"latest_signal": latest}
