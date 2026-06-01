from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserNotParticipant
import database
from utils import start_keyboard, sleep_flood

CREDITS = "GitHub.com/mntgxo"
REPO = "https://github.com/MN-BOTS/Mn-Auto-Delete"

async def missing_fsubs(client, user_id):
    missing = []
    for sub in database.list_fsubs():
        try:
            await client.get_chat_member(sub["_id"], user_id)
        except FloodWait as fw:
            await sleep_flood(fw.value)
            try:
                await client.get_chat_member(sub["_id"], user_id)
            except UserNotParticipant:
                missing.append(sub)
            except Exception:
                missing.append(sub)
        except UserNotParticipant:
            missing.append(sub)
        except Exception:
            missing.append(sub)
    return missing

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    database.upsert_user(message.from_user)
    missing = await missing_fsubs(client, message.from_user.id)
    if missing:
        await message.reply_text(
            "**🔐 Force Subscribe Required**\n\n"
            "Please join every required channel/group, then tap **I Joined**.",
            reply_markup=start_keyboard(missing),
            disable_web_page_preview=True,
        )
        return

    await message.reply_text(
        "**👋 Welcome to MN Auto Delete Bot**\n\n"
        "• Group/channel admins can set their own delete timer.\n"
        "• Settings are saved in MongoDB and survive restarts.\n"
        "• Default mode deletes nothing until enabled.\n\n"
        "**Commands:**\n"
        "`/settings` - open chat settings\n"
        "`/setdelete 30s` - set custom delete time\n"
        "`/deleteon` / `/deleteoff` - toggle auto-delete\n\n"
        f"**Credits:** {CREDITS}\n"
        f"**Repo:** {REPO}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⭐ Source Code", url=REPO)], [InlineKeyboardButton("Developer", url="https://github.com/mntgxo")]]
        ),
        disable_web_page_preview=True,
    )

@Client.on_callback_query(filters.regex("^check_fsub$"))
async def check_fsub(client, query):
    database.upsert_user(query.from_user)
    missing = await missing_fsubs(client, query.from_user.id)
    if missing:
        await query.answer("Please join all required chats first.", show_alert=True)
        await query.message.edit_reply_markup(reply_markup=start_keyboard(missing))
        return
    await query.answer("Verified ✅", show_alert=True)
    await query.message.edit_text(
        "**✅ Subscription verified!**\n\nSend /start again to open the management panel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Repo", url=REPO)]]),
        disable_web_page_preview=True,
    )
