# ATM/services/asset_manager/router.py
from fastapi import APIRouter, HTTPException
# 在Docker环境中使用绝对导入
try:
    from services.asset_manager.logic.asset_manager_logic import list_accounts, create_account, get_balance, transfer, switch_account
except ImportError:
    # 在本地开发环境中回退使用相对导入
    from .logic.asset_manager_logic import list_accounts, create_account, get_balance, transfer, switch_account

router = APIRouter()

@router.get("/asset/accounts")
def api_list_accounts():
    accounts = list_accounts()
    return {"accounts": accounts}

@router.post("/asset/accounts")
def api_create_account():
    address = create_account()
    return {"address": address}

@router.get("/asset/balance/{address}")
def api_get_balance(address: str, token_address: str = None):
    try:
        balance = get_balance(address, token_address)
        return {"address": address, "balance": balance, "token": token_address or "ETH"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/asset/transfer")
def api_transfer(address: str, to_address: str, amount: float, token_address: str = None):
    try:
        tx_hash = transfer(address, to_address, amount, token_address)
        return {"tx_hash": tx_hash, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/asset/switch/{address}")
def api_switch_account(address: str):
    try:
        switch_account(address)
        return {"status": "success", "active_account": address}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/asset/status")
def get_asset_status():
    """返回服务状态信息"""
    return {"status": "running", "service": "asset_manager"}
