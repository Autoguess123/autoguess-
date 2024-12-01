from aiohttp import web
import os
import asyncio
import re
from datetime import datetime, timedelta
from telethon import events, TelegramClient
from telethon.tl.types import PhotoStrippedSize
import logging

# Telegram API credentials
api_id = 2282111
api_hash = 'da58a1841a16c352a2a999171bbabcad'

# Updated accounts with both chat_id and message_id
accounts = [
    {"session_name": "account1", "chats": [{"chat_id": -1002237065471, "message_id": 70}]},
    {"session_name": "kashish1", "chats": [{"chat_id": -1002382167273, "message_id": 72}]},
    {"session_name": "kashish2", "chats": [{"chat_id": -1002285133643, "message_id": 70}]},
    {"session_name": "nitish1", "chats": [{"chat_id": -1002445220543, "message_id": 70}]},
    {"session_name": "yash2", "chats": [{"chat_id": -1002472727498, "message_id": 16}]}
]

cache_dir = "cache/"
it_cache_dir = "IT/cache/"
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(it_cache_dir, exist_ok=True)

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def seconds_until_next_day_6am():
    """Calculate the number of seconds until the next 6 AM IST."""
    now = datetime.now()
    next_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        next_6am += timedelta(days=1)
    return (next_6am - now).seconds

async def send_guess_periodically(client, chats, paused_chats):
    """Send /guess to all specified chats every minute if not paused."""
    while True:
        for chat in chats:
            chat_id = chat['chat_id']
            if chat_id in paused_chats:
                print(f"Chat {chat_id} is paused. Skipping /guess.")
                continue
            try:
                await client.send_message(chat_id, '/guess')
                print(f"Periodic /guess sent to chat {chat_id}.")
            except Exception as e:
                print(f"Error sending /guess to chat {chat_id}: {e}")
        await asyncio.sleep(60)

async def run_account(account):
    """Run a single Telegram account with its associated chats."""
    client = TelegramClient(account["session_name"], api_id, api_hash)
    chats = account["chats"]
    paused_chats = set()  # Track chats that are paused

    @client.on(events.NewMessage(from_users=572621020, incoming=True))
    async def handle_bot_message(event):
        """Handle bot messages to guess Pokémon and check rewards."""
        chat_id = event.chat_id
        message_id = event.message.id

        # Check if the message is from a relevant chat
        relevant_chat = next((chat for chat in chats if chat['chat_id'] == chat_id), None)
        if not relevant_chat:
            return

        # Handle "Who's that Pokémon?" prompt
        if "Who's that pokemon?" in event.message.text:
            if chat_id in paused_chats:
                print(f"Chat {chat_id} is paused. Ignoring Pokémon guess.")
                return

            await asyncio.sleep(2)
            correct_name = None
            for size in event.message.photo.sizes:
                if isinstance(size, PhotoStrippedSize):
                    size = str(size)

                for file in os.listdir(cache_dir):
                    with open(f"{cache_dir}/{file}", "rb") as f:
                        file_content = f.read()
                        if file_content == size.encode("utf-8"):
                            correct_name = file.split(".txt")[0]
                            break

                if correct_name:
                    await client.send_message(chat_id, correct_name, reply_to=message_id)
                    print(f"Guessed Pokémon in chat {chat_id}: {correct_name}")
                    await asyncio.sleep(5)
                    await client.send_message(chat_id, '/guess', reply_to=message_id)
                    print(f"Sent /guess command in chat {chat_id}.")
                else:
                    print(f"No cached size found for {size}. Saving for future use.")
                    sanitized_name = sanitize_filename(str(size))
                    it_cache_path = f"{it_cache_dir}/cache.txt"
                    with open(it_cache_path, "wb") as file:
                        file.write(size.encode("utf-8"))
                    print(f"Saved Pokémon size for {sanitized_name} as cache.txt in IT/cache/")

                break

        elif "guessed" in event.message.text and "+5" not in event.message.text:
            if "Nobody" in event.message.text:
                print(f"'Nobody guessed' detected in chat {chat_id}. Continuing without pausing.")
            else:
                print(f"'Guessed' is present but no reward in chat {chat_id}. Pausing until 6 AM IST.")
                
                # Add chat to paused chats set
                paused_chats.add(chat_id)

                # Sleep until 6 AM IST
                await asyncio.sleep(seconds_until_next_day_6am())  # Wait until 6 AM IST

                # Confirm that we woke up from sleep
                print(f"Resuming chat {chat_id} after pause.")
                paused_chats.remove(chat_id)
                print(f"Resumed guessing in chat {chat_id}.")

    @client.on(events.NewMessage(from_users=6535828301, incoming=True))
    async def reply_to_user(event):
        chat_id = event.chat_id
        await client.send_message(chat_id, "/give 3200", reply_to=event.message.id)
        logger.info(f"Replied with /give 3200 to message from 6535828301 in chat {chat_id}.")
            

    @client.on(events.NewMessage(from_users=572621020, pattern="⚠ Too many commands are being used", incoming=True))
    async def handle_too_many_commands(event):
        """Handle 'Too many commands' message."""
        chat_id = event.chat_id
        relevant_chat = next((chat for chat in chats if chat['chat_id'] == chat_id), None)
        if not relevant_chat:
            return
        message_id = event.message.id
        print(f"Too many commands in chat {chat_id}. Waiting for 20 seconds.")
        await asyncio.sleep(20)
        print(f"Resuming guesses in chat {chat_id}.")
        await client.send_message(chat_id, '/guess', reply_to=message_id)

    await client.start()
    print(f"Bot started for account: {account['session_name']}")
    asyncio.create_task(send_guess_periodically(client, chats, paused_chats))

    for chat in chats:
        chat_id = chat["chat_id"]
        message_id = chat["message_id"]

        # Send the initial /guess command
        await client.send_message(chat_id, '/guess', reply_to=message_id)
        print(f"Sent initial /guess in chat {chat_id}.")

    await client.run_until_disconnected()

async def health_check(request):
    """Health check endpoint."""
    return web.Response(text="OK", status=200)

async def start_health_server():
    """Starts the health check server."""
    app = web.Application()
    app.add_routes([web.get("/", health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    print("Health check server running on port 8000")

async def main():
    """Run all accounts and the health server concurrently."""
    tasks = [run_account(account) for account in accounts]
    tasks.append(start_health_server())
    await asyncio.gather(*tasks)

asyncio.run(main())
