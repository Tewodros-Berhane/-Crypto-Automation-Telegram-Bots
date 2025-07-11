import asyncio
from telethon import TelegramClient
from telethon.errors import RPCError
import requests
from collections import defaultdict


rpc_url = "https://floral-thrilling-feather.solana-mainnet.quiknode.pro/77eb4d2c2dbe0007175d8e238ce79aaca1a9cfde"
api_id = ''
api_hash = ''
telegram_user_id = ''


original_wallets = [
    "DQ5JWbJyWdJeyBxZuuyu36sUBud6L6wo3aN1QC1bRmsR",
    "HyGpRUHowWMn3iEJ1uSUAYXMJm276pi5Cmjj1QHPcYC4",
    "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t",
    "AaZkwhkiDStDcgrU37XAj9fpNLrD8Erz5PNkdm4k5hjy",
]


checked_transactions = defaultdict(set)  
destination_wallets = set()  


client = TelegramClient('session_name', api_id, api_hash)


def get_recent_transactions(wallet_address, limit=10):
    print(f"Fetching recent transactions for wallet: {wallet_address}")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [wallet_address, {"limit": limit}]
    }
    try:
        response = requests.post(rpc_url, json=payload)
        response.raise_for_status()
        transactions = response.json().get("result", [])
        print(f"Found {len(transactions)} transactions for wallet: {wallet_address}")
        return transactions
    except Exception as e:
        print(f"Error fetching transactions for {wallet_address}: {e}")
        return []


def get_transaction_details(tx_signature):
    print(f"Fetching details for transaction: {tx_signature}")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [tx_signature, {"encoding": "jsonParsed"}]
    }
    try:
        response = requests.post(rpc_url, json=payload)
        response.raise_for_status()
        
        details = response.json().get("result")
        if details:
            print(f"Transaction details fetched successfully for: {tx_signature}")
        return details
    except Exception as e:
        print(f"Error fetching transaction details for {tx_signature}: {e}")
        return None


def has_previous_transactions(wallet_address):
    print(f"Checking if wallet {wallet_address} has previous transactions...")
    transactions = get_recent_transactions(wallet_address, limit=1)
    has_transactions = len(transactions) > 0
    print(f"Wallet {wallet_address} {'has' if has_transactions else 'does not have'} previous transactions.")
    return has_transactions


async def send_telegram_message(token_address):
    print(f"Sending token address {token_address} to Telegram...")
    try:
        await client.send_message(telegram_user_id, f"Token address detected: {token_address}")
        print(f"Token address {token_address} sent to Telegram successfully.")
    except RPCError as e:
        print(f"Error sending message to Telegram: {e}")


async def monitor_token_purchases():
    while True:
        print("Checking for token purchases...")
        token_purchase_candidates = []

        for wallet in list(destination_wallets):
            print(f"Checking wallet {wallet} for outgoing transactions or token purchases...")
            transactions = get_recent_transactions(wallet, limit=10)
            for tx in transactions:
                if tx["signature"] not in checked_transactions[wallet]:
                    details = get_transaction_details(tx["signature"])
                    if details:
                        instructions = details.get("transaction", {}).get("message", {}).get("instructions", [])
                        for instruction in instructions:
                            program_id = instruction.get("programId")
                            if program_id == "11111111111111111111111111111111":  
                                source = instruction.get("parsed", {}).get("info", {}).get("source")
                                if source == wallet:
                                    print(f"Wallet {wallet} performed an outgoing transaction. Stopping token monitoring.")
                                    destination_wallets.remove(wallet)
                                    break

            
            
            token_purchase_candidates.append("FakeTokenAddress")  

        if len(token_purchase_candidates) > 1:
            print(f"Detected token purchase by at least 2 wallets. Sending token address to Telegram...")
            await send_telegram_message(token_purchase_candidates[0])

        await asyncio.sleep(10)


async def monitor_wallet(wallet):
    while True:
        print(f"Monitoring original wallet: {wallet}")
        transactions = get_recent_transactions(wallet, limit=10)
        for tx in transactions:
            if tx["signature"] not in checked_transactions[wallet]:
                checked_transactions[wallet].add(tx["signature"])
                details = get_transaction_details(tx["signature"])
                if details:
                    instructions = details.get("transaction", {}).get("message", {}).get("instructions", [])
                    for instruction in instructions:
                        program_id = instruction.get("programId")
                        if program_id == "11111111111111111111111111111111":  
                            source = instruction.get("parsed", {}).get("info", {}).get("source")
                            destination = instruction.get("parsed", {}).get("info", {}).get("destination")
                            amount = int(instruction.get("parsed", {}).get("info", {}).get("lamports", 0)) / 1_000_000_000

                            if source == wallet and not has_previous_transactions(destination) and amount >= 5:
                                print(f"Valid destination wallet detected: {destination}")
                                destination_wallets.add(destination)

        await asyncio.sleep(5)


async def main():
    print("Starting monitoring...")
    await client.start()
    tasks = [monitor_wallet(wallet) for wallet in original_wallets]
    tasks.append(monitor_token_purchases())
    await asyncio.gather(*tasks)

with client:
    client.loop.run_until_complete(main())
