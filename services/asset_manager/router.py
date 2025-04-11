# ATM/services/asset_manager/router.py
from fastapi import APIRouter, HTTPException
from logic.asset_manager_logic import list_accounts, create_account, get_balance, transfer, switch_account

router = APIRouter()

@router.get("/accounts")
def api_list_accounts():
    return {"accounts": list_accounts()}

@router.post("/accounts")
def api_create_account():
    address = create_account()
    return {"address": address}

@router.get("/accounts/{address}/balance")
def api_get_balance(address: str, token_address: str = None):
    balance = get_balance(address, token_address)
    if balance is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"address": address, "balance": str(balance), "token": token_address or "native"}

@router.post("/accounts/{address}/transfer")
def api_transfer(address: str, to_address: str, amount: float, token_address: str = None):
    tx_hash = transfer(address, to_address, amount, token_address)
    if tx_hash is None:
        raise HTTPException(status_code=400, detail="Transfer failed")
    return {"from": address, "to": to_address, "amount": amount, "token": token_address or "native", "tx_hash": tx_hash}

@router.post("/accounts/{address}/switch")
def api_switch_account(address: str):
    if switch_account(address):
        return {"active_account": address}
    raise HTTPException(status_code=404, detail="Account not found")
