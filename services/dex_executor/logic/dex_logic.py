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
    Execute token swap operation.
    
    Trade parameters should include:
      - wallet_address: Wallet address (optional, will use default from config if not provided)
      - private_key: Private key (optional, will use default from config if not provided)
      - token_in: Input token address or symbol (e.g., "USDT")
      - token_out: Output token address or symbol (e.g., "WBTC")
      - amount: Amount (in token's base unit, e.g., with 18 decimals)
      - slippage: Slippage tolerance (e.g., 0.01 for 1%)
      - network: Optional, specify network (testnet or mainnet)
    """
    try:
        # Validate required parameters
        wallet_address = trade.get("wallet_address", DEFAULT_WALLET_ADDRESS)
        private_key = trade.get("private_key", DEFAULT_PRIVATE_KEY)
        token_in_raw = trade.get("token_in")
        token_out_raw = trade.get("token_out")
        amount_in = int(float(trade.get("amount", 0)) * (10 ** 18))  # Assuming 18 decimals
        slippage = float(trade.get("slippage", 0.01))
        network = trade.get("network")  # Support dynamic network from signal
        
        # Resolve token symbols to addresses
        try:
            token_in = resolve_token_address(token_in_raw)
            if not token_in:
                return {"error": f"Unable to resolve input token {token_in_raw}, check token address mapping in config"}
        except Exception as e:
            return {"error": f"Error resolving input token: {str(e)}, check if token symbol {token_in_raw} exists in config"}
        
        try:
            token_out = resolve_token_address(token_out_raw)
            if not token_out:
                return {"error": f"Unable to resolve output token {token_out_raw}, check token address mapping in config"}
        except Exception as e:
            return {"error": f"Error resolving output token: {str(e)}, check if token symbol {token_out_raw} exists in config"}
        
        # Validate required parameters
        if not wallet_address:
            return {"error": "Configuration error: No wallet address provided in trade or config"}
        if not private_key:
            return {"error": "Configuration error: No private key provided in trade or config"}
        if not token_in or not token_out:
            return {"error": "Parameter error: Input and output token addresses are required"}
        if amount_in <= 0:
            return {"error": "Parameter error: Trade amount must be greater than 0"}
        
        # Get network configuration
        try:
            net_config = get_network_config(network)
            w3 = net_config["web3"]
            chain_id = net_config["chain_id"]
            router_address = net_config["router_address"]
            
            # Check wallet balance
            try:
                # Check ETH balance for gas
                eth_balance = w3.eth.get_balance(wallet_address)
                if eth_balance < w3.to_wei(0.001, "ether"):  # Check if enough ETH for gas
                    return {"error": f"Insufficient ETH balance: {w3.from_wei(eth_balance, 'ether')} ETH, at least 0.001 ETH needed for gas"}
                
                # If input token is not ETH, check ERC20 token balance
                if token_in.lower() != "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" and \
                   token_in.lower() != "eth":
                    try:
                        # Simple ERC20 balance check ABI
                        balance_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],
                                        "name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],
                                        "type":"function"}]
                        token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_in), abi=balance_abi)
                        token_balance = token_contract.functions.balanceOf(wallet_address).call()
                        if token_balance < amount_in:
                            return {"error": f"Insufficient token balance: Need {amount_in/(10**18)} {token_in_raw}, account only has {token_balance/(10**18)} {token_in_raw}"}
                    except Exception as e:
                        return {"error": f"Failed to check token balance: {str(e)}, token contract address {token_in} may be invalid or not support standard ERC20 interface"}
            except Exception as e:
                return {"error": f"Failed to check wallet balance: {str(e)}"}
            
            # Check if router address is valid
            if not w3.is_address(router_address):
                return {"error": f"Invalid Router address: {router_address}"}
            
            # Check network connection status
            try:
                block_number = w3.eth.block_number
                print(f"Current block height: {block_number}")
            except Exception as e:
                return {"error": f"RPC connection error: {str(e)}, check if RPC URL is correct and accessible"}
            
            # Auto approve: If token_in is not ETH and auto_approve is enabled, check and execute ERC20 approve
            if AUTO_APPROVE and token_in.lower() != "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" and \
               token_in.lower() != "eth":
                try:
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
                            return {"error": "Approval transaction failed: Transaction rejected by blockchain, possibly due to insufficient gas or contract error"}
                except Exception as e:
                    return {"error": f"Token approval failed: {str(e)}"}
            
            # Calculate minimum output amount (simple ratio calculation, should use oracle in production)
            min_amount_out = int(amount_in * (1 - slippage))
            
            # Construct swap transaction (example using swapExactTokensForTokens)
            try:
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
            except Exception as e:
                return {"error": f"Failed to build swap transaction: {str(e)}, Router contract ABI may not match or Router address is invalid on current network"}
            
            # Sign and send transaction
            try:
                signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key=private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_swap.rawTransaction)
                return {"tx_hash": tx_hash.hex()}
            except Exception as e:
                error_msg = str(e)
                if "insufficient funds" in error_msg.lower():
                    return {"error": "Transaction failed: Insufficient ETH balance to pay for gas"}
                elif "nonce too low" in error_msg.lower():
                    return {"error": "Transaction failed: Nonce too low, wallet may have pending transactions"}
                elif "gas price too low" in error_msg.lower():
                    return {"error": "Transaction failed: Gas price too low, increase gasPrice"}
                elif "already known" in error_msg.lower():
                    return {"error": "Transaction failed: Transaction already submitted, waiting for confirmation"}
                else:
                    return {"error": f"Transaction submission failed: {error_msg}"}
                
        except Exception as e:
            return {"error": f"Network configuration error: {str(e)}"}
            
    except Exception as e:
        # Catch all other exceptions
        return {"error": f"DEX execution error: {str(e)}"}
