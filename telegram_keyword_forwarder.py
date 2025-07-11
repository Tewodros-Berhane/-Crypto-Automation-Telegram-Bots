import re
import asyncio
from telethon import TelegramClient, events


api_id = ''  
api_hash = ''  
client = TelegramClient('textforwardUser', api_id, api_hash)


DESTINATION_GROUP = ''  
KEYWORD = ''  

@client.on(events.NewMessage(chats=['@DRBTSolanaPF'], incoming=True))
async def forward_messages(event):
    try:
        message_text = event.message.message  
        
        
        urls = re.findall(r'https?://[^\s]+', message_text)

        
        if KEYWORD in message_text or any(KEYWORD in url for url in urls):
            
            await client.forward_messages(DESTINATION_GROUP, event.message)
            print(f"Forwarded message containing the keyword '{KEYWORD}' to {DESTINATION_GROUP}")
        else:
            print("No keywords found in the message.")

    except Exception as e:
        print(f"Error while forwarding message: {e}")


async def main():
    await client.start()
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    print("Starting the bot...")
    asyncio.run(main())
