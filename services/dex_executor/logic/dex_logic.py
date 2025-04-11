# ATM/services/dex_executor/logic/dex_logic.py
import os
import time
import json
from web3 import Web3, HTTPProvider

# 从上层配置文件加载网络参数
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
with open(CONFIG_PATH, "r") as f:
    config_data = json.load(f)

network_mode = config_data.get("network_mode", "testnet")
network_cfg = config_data.get(network_mode, {})
CHAIN_ID = network_cfg.get("chain_id")
RPC_URL = network_cfg.get("rpc_url")
ROUTER_ADDRESS = network_cfg.get("router_address")
AUTO_APPROVE = config_data.get("auto_approve", False)

w3 = Web3(HTTPProvider(RPC_URL))

# 简单 ERC20 ABI，只包含 allowance 和 approve 方法
erc20_abi = [
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function"
    }
]

# Dummy Router ABI 示例（实际应使用 Uniswap V3 的ABI）
router_abi = [
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}]
    }
]

def execute_swap(trade: dict):
    """
    trade 参数应包含:
      - wallet_address: 钱包地址
      - private_key: 对应私钥（注：实际生产环境请使用安全存储方案）
      - token_in: 输入代币地址（若为 "ETH" 则表示本币）
      - token_out: 输出代币地址
      - amount: 数量（单位为代币的基本单位，例如以 18 位为例）
      - slippage: 滑点容忍（如 0.01 表示 1%）
    """
    wallet_address = trade.get("wallet_address")
    private_key = trade.get("private_key")
    token_in = trade.get("token_in")
    token_out = trade.get("token_out")
    amount_in = int(float(trade.get("amount", 0)) * (10 ** 18))
    slippage = float(trade.get("slippage", 0.01))
    
    if not wallet_address or not private_key or not token_in or not token_out or amount_in <= 0:
        raise Exception("Invalid trade parameters")
    
    # 自动授权：若 token_in 非 ETH 且开启 auto_approve，则检查并执行 ERC20 approve
    if AUTO_APPROVE and token_in.lower() != "eth":
        token_in_contract = w3.eth.contract(address=Web3.to_checksum_address(token_in), abi=erc20_abi)
        current_allowance = token_in_contract.functions.allowance(wallet_address, Web3.to_checksum_address(ROUTER_ADDRESS)).call()
        if current_allowance < amount_in:
            approve_tx = token_in_contract.functions.approve(
                Web3.to_checksum_address(ROUTER_ADDRESS),
                amount_in
            ).build_transaction({
                'from': wallet_address,
                'nonce': w3.eth.get_transaction_count(wallet_address),
                'chainId': CHAIN_ID,
                'gas': 60000,
                'gasPrice': w3.to_wei('5', 'gwei')
            })
            signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key=private_key)
            approve_tx_hash = w3.eth.send_raw_transaction(signed_approve.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(approve_tx_hash, timeout=120)
            if receipt.status != 1:
                raise Exception("Approval transaction failed")
    
    # 计算最小输出数量（简单比例计算，实际应调用预言机查询）
    min_amount_out = int(amount_in * (1 - slippage))
    
    # 构造 swap 交易（示例使用 swapExactTokensForTokens）
    router = w3.eth.contract(address=Web3.to_checksum_address(ROUTER_ADDRESS), abi=router_abi)
    deadline = int(time.time()) + 300
    swap_tx = router.functions.swapExactTokensForTokens(
        amount_in,
        min_amount_out,
        [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)],
        wallet_address,
        deadline
    ).build_transaction({
        'from': wallet_address,
        'nonce': w3.eth.get_transaction_count(wallet_address),
        'chainId': CHAIN_ID,
        'gas': 250000,
        'gasPrice': w3.to_wei('5', 'gwei')
    })
    
    signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_swap.rawTransaction)
    return tx_hash.hex()
