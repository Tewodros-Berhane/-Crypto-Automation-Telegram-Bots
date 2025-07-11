from telethon import TelegramClient
from telethon.errors import RPCError
import requests
import time
import os
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, HTTPError
from urllib3.util.retry import Retry


rpc_url = "https://floral-thrilling-feather.solana-mainnet.quiknode.pro/77eb4d2c2dbe0007175d8e238ce79aaca1a9cfde"
wallet_address = ""

api_id = ''  
api_hash = ''  
telegram_user_id = ''  


client = TelegramClient('session_name', api_id, api_hash)


checked_transactions = set()


session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))


async def send_telegram_message(wallet_address):
    try:
        await client.send_message(telegram_user_id, wallet_address)
        print(f"Sent wallet address {wallet_address} to Telegram user.")
    except RPCError as e:
        print(f"Error sending message to Telegram: {e}")

def get_transaction_details(tx_signature):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            tx_signature,
            {"encoding": "jsonParsed"}
        ]
    }
    try:
        response = session.post(rpc_url, json=payload)
        response.raise_for_status()
        return response.json().get("result")
    except (ConnectionError, HTTPError) as e:
        print(f"Error fetching transaction details: {e}")
        return None

def get_recent_transactions(wallet_address):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            wallet_address,
            {"limit": 10}
        ]
    }
    try:
        response = session.post(rpc_url, json=payload)
        response.raise_for_status()
        return response.json().get("result", [])
    except (ConnectionError, HTTPError) as e:
        print(f"Error fetching recent transactions: {e}")
        return []

def get_balance(wallet):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet]
    }
    try:
        response = session.post(rpc_url, json=payload)
        response.raise_for_status()
        balance_lamports = response.json().get("result", {}).get("value", 0)
        return balance_lamports / 1_000_000_000  
    except (ConnectionError, HTTPError) as e:
        print(f"Error fetching balance for {wallet}: {e}")
        return None


def has_previous_transactions(wallet, current_tx_signature):
    """
    Check if the wallet has any previous transactions excluding the current one.
    """
    transactions = get_recent_transactions(wallet)
    for tx in transactions:
        if tx["signature"] != current_tx_signature:
            return True  
    return False  




async def process_transaction(transaction_details):
    instructions = transaction_details.get("transaction", {}).get("message", {}).get("instructions", [])
    current_tx_signature = transaction_details.get("transaction", {}).get("signatures", [])[0]
    print(f"Processing {len(instructions)} instructions for transaction {current_tx_signature}.")

    for i, instruction in enumerate(instructions):
        program_id = instruction.get("programId")
        print(f"Instruction {i+1}: Detected program ID {program_id}")

        
        if program_id in ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "11111111111111111111111111111111"]:
            source_wallet = instruction.get("parsed", {}).get("info", {}).get("source")
            destination_wallet = instruction.get("parsed", {}).get("info", {}).get("destination")
            amount_sent_lamports = instruction.get("parsed", {}).get("info", {}).get("amount", 0)
            amount_sent_sol = int(amount_sent_lamports) / 1_000_000_000  

            
            if source_wallet == wallet_address:
                print(f"Instruction {i+1}: Outgoing transaction detected.")

                
                if not has_previous_transactions(destination_wallet, current_tx_signature) and amount_sent_sol >= 4:
                    print(f"Instruction {i+1}: Destination wallet {destination_wallet} has no previous transactions.")
                    print(destination_wallet)
                    await send_telegram_message(destination_wallet)

                    
                    destination_balance = get_balance(destination_wallet)
                    
                    if destination_balance is not None:
                        if destination_balance <= amount_sent_sol:
                            print(destination_wallet)
                            await send_telegram_message(destination_wallet)
                        else:
                            print(f"Instruction {i+1}: Transaction checked but balance condition not met.")
                    else:
                        print(f"Instruction {i+1}: Error retrieving balance for destination wallet {destination_wallet}.")
                else:
                    print(f"Instruction {i+1}: Destination wallet {destination_wallet} has previous transactions. Skipping.")
            else:
                print(f"Instruction {i+1}: Not an outgoing transaction from {wallet_address}. Skipping.")
        else:
            print(f"Instruction {i+1}: Program ID {program_id} does not match Token or System Program. Skipping.")



async def check_transaction_history():
    try:
        transactions = get_recent_transactions(wallet_address)
        if not transactions:
            print("No recent transactions found.")
        for tx in transactions:
            tx_signature = tx['signature']
            if tx_signature in checked_transactions:
                continue  

            checked_transactions.add(tx_signature)

            transaction_details = get_transaction_details(tx_signature)
            if transaction_details:
                await process_transaction(transaction_details)
    except Exception as e:
        print(f"General error: {e}")


async def main():
    await client.start()
    while True:
        print("Checking transaction history...")
        await check_transaction_history()
        time.sleep(5)  

with client:
    client.loop.run_until_complete(main())
