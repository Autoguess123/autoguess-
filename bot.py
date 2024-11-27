import random
import os
import asyncio
import re
from telethon import events, TelegramClient
from telethon.tl.types import PhotoStrippedSize
import shutil

# Telegram API credentials
api_id = 2282111
api_hash = 'da58a1841a16c352a2a999171bbabcad'
from aiohttp import web
import random
import os
import asyncio
import re
from telethon import events, TelegramClient
from telethon.tl.types import PhotoStrippedSize
import shutil

# Telegram API credentials
api_id = 2282111
api_hash = 'da58a1841a16c352a2a999171bbabcad'

# Account configurations
accounts = [
    {"session_name": "account1", "chat_ids": [-4582339132]},
    {"session_name": "account2", "chat_ids": [-4543779814]},
]

# Cache directory
cache_dir = "cache/"
it_cache_dir = "IT/cache/"
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(it_cache_dir, exist_ok=True)

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

async def send_guess_periodically(client, chat_ids):
    """Send /guess to all specified chats every minute."""
    while True:
        for chat_id in chat_ids:
            try:
                await client.send_message(chat_id, '/guess')
                print(f"Periodic /guess sent to chat {chat_id}.")
            except Exception as e:
                print(f"Error sending /guess to chat {chat_id}: {e}")
        await asyncio.sleep(60)

async def run_account(account):
    """Run a single Telegram account with its associated chats."""
    client = TelegramClient(account["session_name"], api_id, api_hash)
    chat_ids = account["chat_ids"]
    last_guess_times = {chat_id: 0 for chat_id in chat_ids}  # Track the last guess time for each chat

    @client.on(events.NewMessage(from_users=572621020, pattern="Who's that pokemon?", incoming=True))
    async def guesser(event):
        if event.chat_id not in chat_ids:
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
                last_guess_times[event.chat_id] = asyncio.get_event_loop().time()
            else:
                print(f"No cached size found for {size}. Saving for future use.")
                sanitized_name = sanitize_filename(str(size))
                it_cache_path = f"{it_cache_dir}/cache.txt"
                with open(it_cache_path, "wb") as file:
                    file.write(size.encode("utf-8"))
                print(f"Saved Pokémon size for {sanitized_name} as cache.txt in IT/cache/")

            break

    @client.on(events.NewMessage(from_users=572621020, pattern="The pokemon was ", incoming=True))
    async def cache_pokemon(event):
        if event.chat_id not in chat_ids:
            return
        pokemon_name = event.message.text.split("The pokemon was ")[1].split(" ")[0]
        sanitized_name = sanitize_filename(pokemon_name)

        it_cache_path = f"{it_cache_dir}/cache.txt"
        final_cache_path = f"{cache_dir}/{sanitized_name}.txt"

        if os.path.exists(it_cache_path):
            shutil.move(it_cache_path, final_cache_path)
            print(f"Moved cached Pokémon for chat {event.chat_id}: {sanitized_name} to cache.")
            with open(final_cache_path, 'a') as file:
                file.write(f"Pokémon name: {sanitized_name}\n")

            await asyncio.sleep(60)
            await client.send_message(event.chat_id, '/guess')
            print(f"Resuming /guess in chat {event.chat_id}.")
        else:
            print(f"No cached size found for {sanitized_name} in IT/cache/.")

    @client.on(events.NewMessage(from_users=572621020, pattern="⚠ Too many commands are being used", incoming=True))
    async def handle_too_many_commands(event):
        if event.chat_id not in chat_ids:
            return
        print(f"Too many commands in chat {event.chat_id}. Waiting for 20 seconds.")
        await asyncio.sleep(20)
        print(f"Resuming guesses in chat {event.chat_id}.")
        await client.send_message(event.chat_id, '/guess')

    await client.start()
    print(f"Bot started for account: {account['session_name']}")
    asyncio.create_task(send_guess_periodically(client, chat_ids))

    for chat_id in chat_ids:
        await client.send_message(chat_id, '/guess')
        print(f"Sent initial /guess in chat {chat_id}.")

    await client.run_until_disconnected()

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

async def main():
    """Run all accounts and the health server concurrently."""
    tasks = [run_account(account) for account in accounts]
    tasks.append(start_health_server())  # Add the health server task
    await asyncio.gather(*tasks)

asyncio.run(main())

# Account configurations
accounts = [
    {"session_name": "account1", "chat_ids": [-4582339132]},
    {"session_name": "account2", "chat_ids": [-4543779814]},
]

# Cache directory
cache_dir = "cache/"
it_cache_dir = "IT/cache/"
os.makedirs(cache_dir, exist_ok=True)  # Ensure the cache directory exists
os.makedirs(it_cache_dir, exist_ok=True)  # Ensure the IT cache directory exists

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

async def send_guess_periodically(client, chat_ids):
    """Send /guess to all specified chats every minute."""
    while True:
        for chat_id in chat_ids:
            try:
                await client.send_message(chat_id, '/guess')
                print(f"Periodic /guess sent to chat {chat_id}.")
            except Exception as e:
                print(f"Error sending /guess to chat {chat_id}: {e}")
        await asyncio.sleep(60)  # Wait for 1 minute before sending again

async def run_account(account):
    """Run a single Telegram account with its associated chats."""
    client = TelegramClient(account["session_name"], api_id, api_hash)
    chat_ids = account["chat_ids"]
    last_guess_times = {chat_id: 0 for chat_id in chat_ids}  # Track the last guess time for each chat
    photo_cache = {}  # Store sizes temporarily for unsaved Pokémon

    @client.on(events.NewMessage(from_users=572621020, pattern="Who's that pokemon?", incoming=True))
    async def guesser(event):
        if event.chat_id not in chat_ids:
            return  # Ignore messages from chats not assigned to this account

        # Sleep for 2 seconds before starting the guessing process
        await asyncio.sleep(2)

        correct_name = None
        for size in event.message.photo.sizes:
            if isinstance(size, PhotoStrippedSize):
                size = str(size)  # Ensure it's converted to string

            # Search for the Pokémon in the cache
            for file in os.listdir(cache_dir):
                with open(f"{cache_dir}/{file}", "rb") as f:
                    file_content = f.read()
                    if file_content == size.encode("utf-8"):
                        correct_name = file.split(".txt")[0]
                        break

            if correct_name:
                # Send the correct Pokémon name
                await client.send_message(event.chat_id, correct_name)
                print(f"Guessed Pokémon in chat {event.chat_id}: {correct_name}")

                # Wait 2 seconds before sending the /guess command
                await asyncio.sleep(5)
                await client.send_message(event.chat_id, '/guess')
                print(f"Sent /guess command in chat {event.chat_id}.")

                # Update last_guess_time after sending /guess
                last_guess_times[event.chat_id] = asyncio.get_event_loop().time()
            else:
                print(f"No cached size found for {size}. Saving for future use.")
                sanitized_name = sanitize_filename(str(size))
                # Save the size as a new file in the IT cache directory
                it_cache_path = f"{it_cache_dir}/cache.txt"
                with open(it_cache_path, "wb") as file:
                    file.write(size.encode("utf-8"))
                print(f"Saved Pokémon size for {sanitized_name} as cache.txt in IT/cache/")

            break  # Exit the loop after handling the first photo

    @client.on(events.NewMessage(from_users=572621020, pattern="The pokemon was ", incoming=True))
    async def cache_pokemon(event):
        if event.chat_id not in chat_ids:
            return  # Ignore messages from chats not assigned to this account

        # Wait for the Pokémon name to appear in the message
        pokemon_name = event.message.text.split("The pokemon was ")[1].split(" ")[0]
        sanitized_name = sanitize_filename(pokemon_name)

        # Move the cache.txt file to the final cache directory with the Pokémon name
        it_cache_path = f"{it_cache_dir}/cache.txt"
        final_cache_path = f"{cache_dir}/{sanitized_name}.txt"

        if os.path.exists(it_cache_path):
            # Move the file from IT/cache/ to the final cache location
            shutil.move(it_cache_path, final_cache_path)
            print(f"Moved cached Pokémon for chat {event.chat_id}: {sanitized_name} to cache.")

            # Optionally write Pokémon info to a log or perform other operations here
            with open(final_cache_path, 'a') as file:
                file.write(f"Pokémon name: {sanitized_name}\n")

            # Wait 60 seconds before sending /guess again
            await asyncio.sleep(60)
            await client.send_message(event.chat_id, '/guess')
            print(f"Resuming /guess in chat {event.chat_id}.")
        else:
            print(f"No cached size found for {sanitized_name} in IT/cache/.")

    @client.on(events.NewMessage(from_users=572621020, pattern="⚠ Too many commands are being used", incoming=True))
    async def handle_too_many_commands(event):
        """Handle 'Too many commands' message."""
        if event.chat_id not in chat_ids:
            return  # Ignore messages from chats not assigned to this account

        print(f"Too many commands in chat {event.chat_id}. Waiting for 20 seconds.")
        await asyncio.sleep(20)  # Wait for 20 seconds before resuming
        print(f"Resuming guesses in chat {event.chat_id}.")
        await client.send_message(event.chat_id, '/guess')

    # Start the client
    await client.start()
    print(f"Bot started for account: {account['session_name']}")

    # Start the periodic /guess task
    asyncio.create_task(send_guess_periodically(client, chat_ids))

    # Send /guess when the bot starts
    for chat_id in chat_ids:
        await client.send_message(chat_id, '/guess')
        print(f"Sent initial /guess in chat {chat_id}.")

    await client.run_until_disconnected()

async def main():
    """Run all accounts concurrently."""
    tasks = [run_account(account) for account in accounts]
    await asyncio.gather(*tasks)

asyncio.run(main())
