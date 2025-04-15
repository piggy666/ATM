# ATM/services/execution_monitor/logic/monitor_logic.py
import time
import os, json
from web3 import Web3, HTTPProvider

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
with open(CONFIG_PATH, "r") as f:
    config_data = json.load(f)
network_mode = config_data.get("network_mode", "testnet")
network_cfg = config_data.get(network_mode, {})
RPC_URL = network_cfg.get("rpc_url")
w3 = Web3(HTTPProvider(RPC_URL))

def monitor_tx(tx_hash: str):
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        status = "confirmed" if receipt.status == 1 else "failed"
        return {"status": status, "block": receipt.blockNumber, "gas_used": receipt.gasUsed}
    except Exception as e:
        return {"status": "pending", "error": str(e)}
