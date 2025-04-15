# ATM/services/signal_listener/router.py
from fastapi import APIRouter
# 同时支持Docker环境和本地环境的导入
try:
    from services.signal_listener.logic import signal_logic
except ImportError:
    # 本地环境回退使用相对导入
    from .logic import signal_logic

router = APIRouter()

@router.post("/signal")
def receive_signal(signal: dict):
    result = signal_logic.handle_signal(signal)
    return {"result": result}

@router.get("/signal/latest")
def get_latest_signal():
    latest = signal_logic.get_latest_signal()
    return {"latest_signal": latest}
