from aiohttp import web
import random
import os
import asyncio
import re
from datetime import datetime, timedelta
from telethon import events, TelegramClient
from telethon.errors.rpcerrorlist import PeerIdInvalidError
from telethon.tl.types import PhotoStrippedSize

api_id = 2282111
api_hash = 'da58a1841a16c352a2a999171bbabcad'

accounts = [
    {"session_name": "account1", "chat_ids": [-1002237065471]},
    {"session_name": "account2", "chat_ids": [-1002472727498]},
    {"session_name": "kashish1", "chat_ids": [-1002382167273]},
]

cache_dir = "cache/"
it_cache_dir = "IT/cache/"
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(it_cache_dir, exist_ok=True)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def seconds_until_next_day_6am():
    now = datetime.now()
    next_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        next_6am += timedelta(days=1)
    return (next_6am - now).seconds

async def send_guess_periodically(client, chat_ids, paused_chats):
    while True:
        for chat_id in chat_ids:
            if chat_id in paused_chats:
                continue
            try:
                entity = await client.get_input_entity(chat_id)
                await client.send_message(entity, '/guess')
            except PeerIdInvalidError:
                pass
            except Exception as e:
                pass
        await asyncio.sleep(60)

async def run_account(account):
    client = TelegramClient(account["session_name"], api_id, api_hash)
    chat_ids = account["chat_ids"]
    paused_chats = set()

    @client.on(events.NewMessage(from_users=572621020, incoming=True))
    async def handle_bot_message(event):
        if event.chat_id not in chat_ids:
            return
        if "Who's that pokemon?" in event.message.text:
            if event.chat_id in paused_chats:
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
                    await asyncio.sleep(5)
                    await client.send_message(event.chat_id, '/guess')
                else:
                    sanitized_name = sanitize_filename(str(size))
                    it_cache_path = f"{it_cache_dir}/cache.txt"
                    with open(it_cache_path, "wb") as file:
                        file.write(size.encode("utf-8"))
                break
        elif "The pokemon was " in event.message.text:
            if "guessed" in event.message.text and "+5 💵" in event.message.text:
                if event.chat_id in paused_chats:
                    paused_chats.remove(event.chat_id)
            else:
                paused_chats.add(event.chat_id)
                await asyncio.sleep(seconds_until_next_day_6am())
                paused_chats.remove(event.chat_id)

    @client.on(events.NewMessage(pattern="/stop", incoming=True))
    async def handle_stop_command(event):
        if event.chat_id in chat_ids:
            paused_chats.add(event.chat_id)
            print(f"/stop received. Pausing guesses in chat {event.chat_id} until 6 AM IST.")
            await event.reply("Bot paused in this chat until 6 AM IST.")

    await client.start()
    asyncio.create_task(send_guess_periodically(client, chat_ids, paused_chats))

    for chat_id in chat_ids:
        try:
            entity = await client.get_input_entity(chat_id)
            await client.send_message(entity, '/guess')
        except PeerIdInvalidError:
            pass
        except Exception as e:
            pass

    await client.run_until_disconnected()

async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_health_server():
    app = web.Application()
    app.add_routes([web.get("/", health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

async def main():
    tasks = [run_account(account) for account in accounts]
    tasks.append(start_health_server())
    await asyncio.gather(*tasks)

asyncio.run(main())
