import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER, BROADCAST
import database
from utils import forward_with_flood


def owner_only(_, __, message):
    return bool(message.from_user and message.from_user.id == OWNER.ID)

owner_filter = filters.create(owner_only)

@Client.on_message(filters.private & owner_filter & filters.command("admin"))
async def admin_panel(client, message):
    total_users = database.users.count_documents({})
    blocked_users = database.users.count_documents({"blocked": True})
    total_chats = database.chats.count_documents({})
    enabled_chats = database.chats.count_documents({"enabled": True})
    pending = database.messages.count_documents({"status": "pending"})
    fsubs = database.fsubs.count_documents({})
    await message.reply_text(
        "**👑 Owner Management Panel**\n\n"
        f"Users: `{total_users}`\n"
        f"Blocked/Deleted PM users: `{blocked_users}`\n"
        f"Known groups/channels: `{total_chats}`\n"
        f"Auto-delete enabled chats: `{enabled_chats}`\n"
        f"Pending delete jobs: `{pending}`\n"
        f"Force-sub chats: `{fsubs}`\n\n"
        "**Owner commands**\n"
        "`/broadcast` - reply to a post and forward it everywhere\n"
        "`/addfsub <chat_id> [invite_link]`\n"
        "`/delfsub <chat_id>`\n"
        "`/fsubs`\n"
        "`/stats`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Repo", url="https://github.com/MN-BOTS/Mn-Auto-Delete")]]),
        disable_web_page_preview=True,
    )

@Client.on_message(filters.private & owner_filter & filters.command("stats"))
async def stats_cmd(client, message):
    await admin_panel(client, message)

@Client.on_message(filters.private & owner_filter & filters.command("addfsub"))
async def add_fsub_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/addfsub -1001234567890 https://t.me/example`")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("Chat ID must be numeric.")
    invite_link = message.command[2] if len(message.command) > 2 else None
    title = None
    username = None
    try:
        chat = await client.get_chat(chat_id)
        title = chat.title
        username = chat.username
        invite_link = invite_link or chat.invite_link
    except Exception:
        pass
    database.add_fsub(chat_id, title=title, username=username, invite_link=invite_link)
    await message.reply_text(f"Force-sub chat added ✅\nID: `{chat_id}`")

@Client.on_message(filters.private & owner_filter & filters.command("delfsub"))
async def del_fsub_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/delfsub -1001234567890`")
    database.remove_fsub(int(message.command[1]))
    await message.reply_text("Force-sub chat removed ✅")

@Client.on_message(filters.private & owner_filter & filters.command("fsubs"))
async def list_fsub_cmd(client, message):
    subs = database.list_fsubs()
    if not subs:
        return await message.reply_text("No force-sub chats configured.")
    lines = ["**Configured Force-Sub Chats**"]
    for sub in subs:
        lines.append(f"• `{sub['_id']}` - {sub.get('title') or sub.get('username') or 'Unknown'}")
    await message.reply_text("\n".join(lines))

@Client.on_message(filters.private & owner_filter & filters.command("broadcast"))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to the message you want to broadcast. The bot will use Telegram forward, not copy.")

    targets = set()
    targets.update(user["_id"] for user in database.users.find({"blocked": {"$ne": True}}, {"_id": 1}))
    targets.update(chat["_id"] for chat in database.chats.find({}, {"_id": 1}))

    if not targets:
        return await message.reply_text("No broadcast targets found yet.")

    status_message = await message.reply_text(f"Broadcast started to `{len(targets)}` targets using forward method...")
    stats = {"sent": 0, "blocked": 0, "forbidden": 0, "failed": 0}
    for target in targets:
        result = await forward_with_flood(message.reply_to_message, target)
        stats[result] = stats.get(result, 0) + 1
        await asyncio.sleep(BROADCAST.SLEEP)

    database.broadcasts.insert_one(
        {
            "from_user": message.from_user.id,
            "message_id": message.reply_to_message.id,
            "targets": len(targets),
            "stats": stats,
            "created_at": database.now_utc(),
        }
    )
    await status_message.edit_text(
        "**Broadcast completed ✅**\n\n"
        f"Sent: `{stats['sent']}`\n"
        f"Blocked/deleted PM users auto-marked: `{stats['blocked']}`\n"
        f"Forbidden chats: `{stats['forbidden']}`\n"
        f"Failed: `{stats['failed']}`"
    )
