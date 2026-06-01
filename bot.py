import asyncio
import logging
import threading
from datetime import timedelta
from flask import Flask
from pyrogram import Client
from pyrogram import utils as pyroutils
from config import BOT, API, OWNER, WEB
import database
from utils import safe_delete

# ✅ Peer ID Fix (for large channel/group IDs)
pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -10099999999999

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    return "MN Auto Delete Bot is running! Credits: GitHub.com/mntgxo"

def run_flask():
    app.run(host='0.0.0.0', port=WEB.PORT)

class MN_Bot(Client):
    def __init__(self):
        super().__init__(
            "MN-Bot",
            api_id=API.ID,
            api_hash=API.HASH,
            bot_token=BOT.TOKEN,
            plugins=dict(root="plugins"),
            workers=32,
        )
        self.delete_tasks = {}

    async def start(self):
        database.init_db()
        await super().start()
        me = await self.get_me()
        BOT.USERNAME = f"@{me.username}"
        self.mention = me.mention
        self.username = me.username
        await self.resume_pending_deletes()
        text = (
            f"{me.first_name} ✅ BOT started successfully\n"
            "Persistent auto-delete scheduler resumed from MongoDB.\n"
            "Credits: GitHub.com/mntgxo"
        )
        if OWNER.ID:
            await self.send_message(chat_id=OWNER.ID, text=text)
        logging.info("✅ %s BOT started successfully", me.first_name)

    async def stop(self, *args):
        for task in self.delete_tasks.values():
            task.cancel()
        await super().stop()
        logging.info("Bot Stopped 🙄")

    def schedule_delete(self, chat_id, message_id, delete_at):
        key = f"{chat_id}:{message_id}"
        old_task = self.delete_tasks.pop(key, None)
        if old_task:
            old_task.cancel()
        self.delete_tasks[key] = asyncio.create_task(self._delete_later(key, chat_id, message_id, delete_at))

    async def _delete_later(self, key, chat_id, message_id, delete_at):
        try:
            delete_at = database.normalize_dt(delete_at)
            delay = max(0, (delete_at - database.now_utc()).total_seconds())
            if delay:
                await asyncio.sleep(delay)
            await safe_delete(self, chat_id, message_id)
        finally:
            self.delete_tasks.pop(key, None)

    async def resume_pending_deletes(self):
        count = 0
        for item in database.pending_messages(limit=5000):
            self.schedule_delete(item["chat_id"], item["message_id"], item["delete_at"])
            count += 1
        logging.info("Resumed %s pending delete jobs from MongoDB", count)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    MN_Bot().run()
