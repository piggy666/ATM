# ATM/services/dex_executor/logic/dex_logic.py
import os
import time
import json
from web3 import Web3, HTTPProvider

# 从上层配置文件加载网络参数
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
with open(CONFIG_PATH, "r", encoding='utf-8') as f:
    config_data = json.load(f)

network_mode = config_data.get("network_mode", "testnet")
network_cfg = config_data.get(network_mode, {})
CHAIN_ID = network_cfg.get("chain_id")
RPC_URL = network_cfg.get("rpc_url")
ROUTER_ADDRESS = network_cfg.get("router_address")
AUTO_APPROVE = config_data.get("auto_approve", False)

# 从配置文件加载默认钱包信息（仅用于测试）
DEFAULT_WALLET_ADDRESS = config_data.get("wallet", {}).get("address", "")
DEFAULT_PRIVATE_KEY = config_data.get("wallet", {}).get("private_key", "")

# 从配置文件加载可选的代币地址映射表
TOKEN_ADDRESSES = config_data.get("token_addresses", {})

# 预先初始化Web3对象
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

# Uniswap V3 Router ABI示例
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

# 动态加载网络配置
def get_network_config(network=None):
    """根据指定的网络返回相应的配置参数"""
    global config_data, w3, CHAIN_ID, RPC_URL, ROUTER_ADDRESS
    
    # 如果没有指定网络，使用配置文件中的默认设置
    if not network:
        network = config_data.get("network_mode", "testnet")
    
    # 确保网络类型有效
    if network not in ["testnet", "mainnet"]:
        network = "testnet"  # 默认回退到测试网
    
    network_cfg = config_data.get(network, {})
    chain_id = network_cfg.get("chain_id")
    rpc_url = network_cfg.get("rpc_url")
    router_address = network_cfg.get("router_address")
    
    # 如果网络配置与当前不同，重新初始化 Web3
    if rpc_url != RPC_URL:
        w3 = Web3(HTTPProvider(rpc_url))
        CHAIN_ID = chain_id
        RPC_URL = rpc_url
        ROUTER_ADDRESS = router_address
    
    return {
        "chain_id": chain_id,
        "rpc_url": rpc_url,
        "router_address": router_address,
        "web3": w3
    }

# 解析代币地址，支持符号（如"BTC"）或直接使用合约地址
def resolve_token_address(token):
    """将代币符号解析为合约地址，如果输入已经是地址则直接返回"""
    # 如果输入已经看起来像是地址，则直接返回
    if token and token.startswith("0x") and len(token) >= 40:
        return token
    
    # 否则，尝试从TOKEN_ADDRESSES映射中查找
    token_upper = token.upper() if token else ""
    if token_upper in TOKEN_ADDRESSES:
        return TOKEN_ADDRESSES[token_upper]
    
    # 如果找不到映射，返回原始输入
    return token

def execute_swap(trade: dict):
    """
    执行代币交换操作。
    
    trade 参数应包含:
      - wallet_address: 钱包地址（可选，如不提供则使用配置中的默认值）
      - private_key: 对应私钥（可选，如不提供则使用配置中的默认值）
      - token_in: 输入代币地址或符号（如"USDT"）
      - token_out: 输出代币地址或符号（如"WBTC"）
      - amount: 数量（单位为代币的基本单位，例如以 18 位为例）
      - slippage: 滑点容忍（如 0.01 表示 1%）
      - network: 可选，指定交易网络 (testnet 或 mainnet)
    """
    # 验证必要参数
    wallet_address = trade.get("wallet_address", DEFAULT_WALLET_ADDRESS)
    private_key = trade.get("private_key", DEFAULT_PRIVATE_KEY)
    token_in_raw = trade.get("token_in")
    token_out_raw = trade.get("token_out")
    amount_in = int(float(trade.get("amount", 0)) * (10 ** 18))  # 假设使用 18 位精度
    slippage = float(trade.get("slippage", 0.01))
    network = trade.get("network")  # 支持从信号动态指定网络
    
    # 解析代币符号为地址
    token_in = resolve_token_address(token_in_raw)
    token_out = resolve_token_address(token_out_raw)
    
    # 验证必要参数
    if not wallet_address:
        raise Exception("No wallet address provided in trade or config")
    if not private_key:
        raise Exception("No private key provided in trade or config")
    if not token_in or not token_out or amount_in <= 0:
        raise Exception("Invalid trade parameters: token addresses and amount are required")
    
    # 获取网络配置
    net_config = get_network_config(network)
    w3 = net_config["web3"]
    chain_id = net_config["chain_id"]
    router_address = net_config["router_address"]
    
    # 自动授权：若 token_in 非 ETH 且开启 auto_approve，则检查并执行 ERC20 approve
    if AUTO_APPROVE and token_in.lower() != "eth":
        token_in_contract = w3.eth.contract(address=Web3.to_checksum_address(token_in), abi=erc20_abi)
        current_allowance = token_in_contract.functions.allowance(wallet_address, Web3.to_checksum_address(router_address)).call()
        if current_allowance < amount_in:
            approve_tx = token_in_contract.functions.approve(
                Web3.to_checksum_address(router_address),
                amount_in
            ).build_transaction({
                'from': wallet_address,
                'nonce': w3.eth.get_transaction_count(wallet_address),
                'chainId': chain_id,
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
    router = w3.eth.contract(address=Web3.to_checksum_address(router_address), abi=router_abi)
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
        'chainId': chain_id,
        'gas': 250000,
        'gasPrice': w3.to_wei('5', 'gwei')
    })
    
    signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_swap.rawTransaction)
    return tx_hash.hex()
