import asyncio
from datetime import timedelta
from pyrogram.errors import (
    FloodWait,
    UserIsBlocked,
    InputUserDeactivated,
    PeerIdInvalid,
    ChatWriteForbidden,
    ChannelPrivate,
    ChatAdminRequired,
    MessageDeleteForbidden,
    MessageIdInvalid,
)
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import database

OWNER_STATUSES = {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR}
BLOCK_ERRORS = (UserIsBlocked, InputUserDeactivated, PeerIdInvalid)
CHAT_ERRORS = (ChatWriteForbidden, ChannelPrivate, ChatAdminRequired)
DELETE_IGNORED_ERRORS = (MessageDeleteForbidden, MessageIdInvalid)


def human_time(seconds):
    seconds = int(seconds)
    if seconds <= 0:
        return "Off"
    units = ((86400, "d"), (3600, "h"), (60, "m"), (1, "s"))
    parts = []
    for size, suffix in units:
        value, seconds = divmod(seconds, size)
        if value:
            parts.append(f"{value}{suffix}")
    return " ".join(parts) or "0s"


def parse_time(value):
    if not value:
        raise ValueError("missing time")
    raw = value.strip().lower()
    if raw in {"off", "disable", "disabled", "0"}:
        return 0
    suffix = raw[-1]
    number = raw[:-1] if suffix.isalpha() else raw
    if not number.isdigit():
        raise ValueError("invalid time")
    amount = int(number)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if suffix.isalpha() and suffix not in multipliers:
        raise ValueError("supported units are s, m, h, and d")
    multiplier = multipliers.get(suffix, 1)
    seconds = amount * multiplier
    if seconds < 0 or seconds > 30 * 86400:
        raise ValueError("time must be between 0 seconds and 30 days")
    return seconds


async def sleep_flood(seconds):
    await asyncio.sleep(int(seconds) + 1)


async def safe_delete(client, chat_id, message_id):
    while True:
        try:
            await client.delete_messages(chat_id, message_id)
            database.finish_scheduled_message(chat_id, message_id, "deleted")
            return True
        except FloodWait as fw:
            await sleep_flood(fw.value)
        except DELETE_IGNORED_ERRORS as err:
            database.finish_scheduled_message(chat_id, message_id, "skipped", str(err))
            return False
        except Exception as err:
            database.finish_scheduled_message(chat_id, message_id, "failed", str(err))
            return False


async def forward_with_flood(message, chat_id):
    while True:
        try:
            await message.forward(chat_id)
            return "sent"
        except FloodWait as fw:
            await sleep_flood(fw.value)
        except BLOCK_ERRORS:
            database.mark_blocked(chat_id)
            return "blocked"
        except CHAT_ERRORS:
            return "forbidden"
        except Exception:
            return "failed"


async def is_chat_admin(client, chat_id, user_id):
    if not user_id:
        return False
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in OWNER_STATUSES
    except FloodWait as fw:
        await sleep_flood(fw.value)
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in OWNER_STATUSES
    except Exception:
        return False


def settings_keyboard(chat_id, enabled):
    toggle = "Disable 📴" if enabled else "Enable ✅"
    action = "off" if enabled else "on"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(toggle, callback_data=f"set:{chat_id}:{action}")],
            [
                InlineKeyboardButton("30s", callback_data=f"delay:{chat_id}:30"),
                InlineKeyboardButton("5m", callback_data=f"delay:{chat_id}:300"),
                InlineKeyboardButton("1h", callback_data=f"delay:{chat_id}:3600"),
            ],
            [InlineKeyboardButton("Refresh 🔄", callback_data=f"settings:{chat_id}")],
        ]
    )


def start_keyboard(fsubs=None):
    rows = []
    for sub in fsubs or []:
        label = sub.get("title") or sub.get("username") or str(sub["_id"])
        link = sub.get("invite_link") or (f"https://t.me/{sub['username']}" if sub.get("username") else None)
        if link:
            rows.append([InlineKeyboardButton(f"Join {label}", url=link)])
    rows.append([InlineKeyboardButton("✅ I Joined", callback_data="check_fsub")])
    rows.append([InlineKeyboardButton("Repo ⭐", url="https://github.com/MN-BOTS/Mn-Auto-Delete")])
    return InlineKeyboardMarkup(rows)


def settings_text(chat, settings):
    state = "Enabled ✅" if settings.get("enabled") else "Disabled 📴"
    delay = human_time(settings.get("delete_delay", 0))
    return (
        f"**🛠 Auto Delete Settings**\n\n"
        f"**Chat:** {chat.title or chat.id}\n"
        f"**ID:** `{chat.id}`\n"
        f"**Status:** {state}\n"
        f"**Delete Time:** `{delay}`\n\n"
        "Use `/setdelete 30s`, `/setdelete 5m`, `/setdelete 1h`, or `/setdelete off`.\n"
        "Default is disabled, so the bot deletes nothing until an admin enables it."
    )
