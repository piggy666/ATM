# ATM/services/risk_controller/router.py
from fastapi import APIRouter
from logic import risk_logic

router = APIRouter()

@router.post("/risk/check")
def check_risk(signal: dict):
    return risk_logic.check_risk(signal)

@router.post("/risk/record")
def record_trade(trade: dict):
    return risk_logic.record_trade(trade)
