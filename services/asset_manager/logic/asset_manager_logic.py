# ATM/services/asset_manager/logic/asset_manager_logic.py
import os, secrets, json
from eth_account import Account
from web3 import Web3, HTTPProvider

def get_service_rpcurl(service_name: str) -> str:
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)
    network_mode = cfg.get("network_mode","testnet")
    if network_mode == "mainnet":
        return cfg.get("mainnet", {}).get("rpc_url")
    else:
        return cfg.get("testnet", {}).get("rpc_url")

# 连接区块链节点（请修改为正确的RPC地址）
RPC_URL = get_service_rpcurl("asset_manager")
w3 = Web3(HTTPProvider(RPC_URL))

# 内存中存储钱包信息（生产环境请使用安全存储方案）
accounts = {}
active_account = None

def list_accounts():
    return list(accounts.keys())

def create_account():
    acct = Account.create(secrets.token_hex(32))
    address = acct.address
    private_key = acct.key.hex()
    accounts[address] = private_key
    global active_account
    if active_account is None:
        active_account = address
    return address

def get_balance(address, token_address=None):
    if address not in accounts:
        return None
    if token_address:
        erc20_abi = [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
             "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
        ]
        try:
            token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
            balance = token.functions.balanceOf(Web3.to_checksum_address(address)).call()
            return balance
        except Exception as e:
            return None
    else:
        try:
            balance = w3.eth.get_balance(Web3.to_checksum_address(address))
            return w3.from_wei(balance, 'ether')
        except Exception as e:
            return None

def transfer(from_address, to_address, amount, token_address=None):
    if from_address not in accounts:
        return None
    private_key = accounts[from_address]
    try:
        if token_address:
            erc20_abi = [
                {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                 "name": "transfer", "outputs": [{"name": "success", "type": "bool"}], "type": "function"}
            ]
            token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
            tx = token.functions.transfer(Web3.to_checksum_address(to_address), int(amount)).build_transaction({
                'from': Web3.to_checksum_address(from_address),
                'nonce': w3.eth.get_transaction_count(Web3.to_checksum_address(from_address)),
                'chainId': w3.eth.chain_id,
                'gas': 100000,
                'gasPrice': w3.to_wei('5', 'gwei')
            })
        else:
            tx = {
                'to': Web3.to_checksum_address(to_address),
                'value': w3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': w3.to_wei('5', 'gwei'),
                'nonce': w3.eth.get_transaction_count(Web3.to_checksum_address(from_address)),
                'chainId': w3.eth.chain_id
            }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        return None

def switch_account(address):
    global active_account
    if address in accounts:
        active_account = address
        return True
    return False

def get_active_account():
    return active_account
