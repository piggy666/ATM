from eth_account import Account
Account.enable_unaudited_hdwallet_features()
acct, mnemonic = Account.create_with_mnemonic()

wallet_address = acct.address
private_key = acct.key.hex()
print(f"钱包地址: {wallet_address}")
print(f"私钥: {private_key}")
print(f"助记词: {mnemonic}")