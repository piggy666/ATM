# ATM/services/risk_controller/router.py
from fastapi import APIRouter
# 同时支持Docker环境和本地环境的导入
try:
    from services.risk_controller.logic import risk_logic
except ImportError:
    # 本地环境回退使用相对导入
    from .logic import risk_logic

router = APIRouter()

@router.post("/risk/check")
def check_risk(signal: dict):
    return risk_logic.check_risk(signal)

@router.post("/risk/record")
def record_trade(trade: dict):
    return risk_logic.record_trade(trade)

@router.get("/risk/status")
def get_risk_status():
    # 返回服务状态信息
    return {"status": "running", "service": "risk_controller"}
