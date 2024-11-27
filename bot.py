from aiohttp import web
import random
import os
import asyncio
import re
from datetime import datetime, timedelta
from telethon import events, TelegramClient
from telethon.tl.types import PhotoStrippedSize
import shutil

# Telegram API credentials
api_id = 2282111
api_hash = 'da58a1841a16c352a2a999171bbabcad'

# Account configurations
accounts = [
    {"session_name": "account1", "chat_ids": [-4582339132], "link": "https://t.me/c/2237065471/3"},
    {"session_name": "account2", "chat_ids": [-4543779814], "link": "https://t.me/c/2472727498/3"},
    {"session_name": "kashish1", "chat_ids": [-1002382167273], "link": "https://t.me/c/2382167273/16"},
]

# Cache directory
cache_dir = "cache/"
it_cache_dir = "IT/cache/"
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(it_cache_dir, exist_ok=True)

# Dictionary to keep track of paused chats across all accounts
paused_chats = {}

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

async def send_guess_periodically(client, chat_ids):
    """Send /guess to all specified chats every minute if not paused."""
    while True:
        for chat_id in chat_ids:
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
    try:
        client = TelegramClient(account["session_name"], api_id, api_hash)
        chat_ids = account["chat_ids"]
        account_link = account["link"]  # Get the link for the account

        @client.on(events.NewMessage(from_users=572621020, incoming=True))
        async def handle_bot_message(event):
            """Handle bot messages to guess Pokémon and check rewards."""
            if event.chat_id not in chat_ids:
                return

            # Handle "Who's that Pokémon?" prompt
            if "Who's that pokemon?" in event.message.text:
                if event.chat_id in paused_chats:
                    print(f"Chat {event.chat_id} is paused. Ignoring Pokémon guess.")
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
                    await client.send_message(event.chat_id, correct_name)
                    print(f"Guessed Pokémon in chat {event.chat_id}: {correct_name}")
                    await asyncio.sleep(5)
                    await client.send_message(event.chat_id, '/guess')
                    print(f"Sent /guess command in chat {event.chat_id}.")
                else:
                    print(f"No cached size found for {size}. Saving for future use.")
                    sanitized_name = sanitize_filename(str(size))
                    it_cache_path = f"{it_cache_dir}/cache.txt"
                    with open(it_cache_path, "wb") as file:
                        file.write(size.encode("utf-8"))
                    print(f"Saved Pokémon size for {sanitized_name} as cache.txt in IT/cache/")
                return  # Exit the function here, no need for break

            # Handle reward confirmation and pause if no reward after guess
            elif "guessed" in event.message.text and "The pokemon was " in event.message.text:
                # Check if the reward was NOT given (i.e., "+5 💵" not in the message)
                if "+5 💵" not in event.message.text:
                    print(f"No reward after guessing. Pausing until 6 AM IST and tagging pinned message.")
                    paused_chats[event.chat_id] = {"link": account_link, "paused": True}
                    await reply_to_pinned_message(client, event.chat_id, account_link)
                    await asyncio.sleep(seconds_until_next_day_6am())
                    print(f"Resuming guesses in chat {event.chat_id}.")
                    paused_chats.pop(event.chat_id)

                else:
                    print(f"Reward received after guessing. Continuing guesses.")
                    if event.chat_id in paused_chats:
                        paused_chats.pop(event.chat_id)

        await client.start()
        print(f"Bot started for account: {account['session_name']}")
        asyncio.create_task(send_guess_periodically(client, chat_ids))

        for chat_id in chat_ids:
            await client.send_message(chat_id, '/guess')
            print(f"Sent initial /guess in chat {chat_id}.")

        await client.run_until_disconnected()

    except Exception as e:
        print(f"Error running account {account['session_name']}: {e}")

async def reply_to_pinned_message(client, chat_id, account_link):
    """Reply to the pinned message in a chat with '/give 3200'."""
    try:
        # Simulate reply to pinned message using link
        print(f"Using link: {account_link}")
        await client.send_message(chat_id, "/give 3200")
        print(f"Replied to chat {chat_id} with '/give 3200'.")
    except Exception as e:
        print(f"Error replying to pinned message in chat {chat_id}: {e}")

    @client.on(events.NewMessage(from_users=572621020, pattern="⚠ Too many commands are being used", incoming=True))
    async def handle_too_many_commands(event):
        """Handle 'Too many commands' message."""
        if event.chat_id not in chat_ids:
            return
        print(f"Too many commands in chat {event.chat_id}. Waiting for 20 seconds.")
        await asyncio.sleep(20)
        print(f"Resuming guesses in chat {event.chat_id}.")
        await client.send_message(event.chat_id, '/guess')

async def health_check(request):
    """Health check endpoint."""
    return web.Response(text="OK", status=200)

async def start_health_server():
    """Starts the health check server."""
    app = web.Application()
    app.add_routes([web.get("/", health_check)])  # Respond to GET requests on '/'
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)  # Listen on port 8000
    await site.start()
    print("Health check server running on port 8000")

async def keep_alive():
    """A keep-alive task to ensure the event loop runs forever."""
    while True:
        await asyncio.sleep(60)  # Sleep forever

async def main():
    """Run all accounts and the health server concurrently."""
    tasks = [run_account(account) for account in accounts]
    tasks.append(start_health_server())  # Add the health server task
    tasks.append(keep_alive())  # Keep the event loop alive
    await asyncio.gather(*tasks)

asyncio.run(main())
