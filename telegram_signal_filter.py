from telethon import TelegramClient, events
import asyncio
import re


api_id = ''
api_hash = ''


source_channel = ''  
target_group = ''  


client = TelegramClient('forward_bot', api_id, api_hash)


def check_conditions(message_text):
    try:
        
        # supply_match = re.search(r"Supply:\s*([\d,]+)", message_text)
        # deci_match = re.search(r"Deci:\s*(\d+)", message_text)
        from_match = re.search(r"From:\s*(\w+)", message_text)
        balance_match = re.search(r"Balance:\s*([\d.]+)", message_text)

        
        # supply = int(supply_match.group(1).replace(',', '')) if supply_match else None
        # deci = int(deci_match.group(1)) if deci_match else None
        source = from_match.group(1) if from_match else None
        balance = float(balance_match.group(1)) if balance_match else None

        
        return (
            
            
            source == 'KuCoin' and
            balance >= 65.99
        )
    except Exception as e:
        print(f"Error parsing message: {e}")
        return False


@client.on(events.NewMessage(chats=source_channel))
async def handler(event):
    message_text = event.message.text
    if check_conditions(message_text):
        
        await client.forward_messages(target_group, event.message)
        print("Message forwarded successfully!")


async def run_client():
    while True:
        try:
            print("Bot is starting...")
            await client.start()
            print("Bot is running...")
            await client.run_until_disconnected()
        except (ConnectionError, asyncio.TimeoutError) as e:
            print(f"Connection lost: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)  
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)  


if __name__ == "__main__":
    asyncio.run(run_client())
