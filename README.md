# 🚀 MN Auto Delete Management Bot

A MongoDB-backed Telegram auto-delete bot built with Pyrogram/pyrotgfork. Every group or channel owner/admin can manage their own delete timer, and pending delete jobs are persisted so they continue after a bot restart.

> **Credits:** Developed by **GitHub.com/mntgxo**<br>
> Source repo: https://github.com/MN-BOTS/Mn-Auto-Delete

---

## ✨ Features

- ✅ **Per-group and per-channel settings** managed by each chat owner/admin.
- ✅ **Default safe mode:** the bot does **not delete anything** until `/setdelete` or `/deleteon` is used in that chat.
- ✅ **Custom delete times:** supports seconds, minutes, hours, and days (`10s`, `5m`, `1h`, `1d`).
- ✅ **MongoDB persistence:** chat settings and pending delete jobs survive restarts.
- ✅ **Restart recovery:** the bot resumes all pending delete schedules from MongoDB on startup.
- ✅ **Proper FloodWait handling** for deleting, admin checks, force-sub checks, and broadcasts.
- ✅ **Multiple force-sub chats** with owner commands to add/remove/list requirements.
- ✅ **Rich dynamic UI** with inline buttons for settings, source links, and force-sub verification.
- ✅ **Owner management panel** with stats for users, chats, enabled chats, force-sub chats, and pending delete jobs.
- ✅ **Forward-method broadcast** to bot PM users, groups, and channels.
- ✅ **Blocked/deleted PM cleanup:** blocked users are automatically marked in MongoDB during broadcast.
- ✅ Flask health check for Koyeb/Render-style deployments.

---

## 🧩 Environment Variables

| Variable | Required | Description | Example |
|---|---:|---|---|
| `TOKEN` | ✅ | Bot token from [@BotFather](https://t.me/BotFather) | `123456:ABCDEF...` |
| `API_ID` | ✅ | Telegram API ID from https://my.telegram.org | `123456` |
| `API_HASH` | ✅ | Telegram API hash | `abcdef123456...` |
| `OWNER` | ✅ | Telegram user ID of the bot owner | `123456789` |
| `MONGO_URI` | ✅ | MongoDB connection URI | `mongodb+srv://user:pass@cluster/db` |
| `DATABASE_NAME` | ❌ | MongoDB database name | `mn_auto_delete` |
| `PORT` | ❌ | Flask health-check port | `8000` |
| `BROADCAST_SLEEP` | ❌ | Small delay between broadcast forwards | `0.05` |

---

## 👥 Group/Channel Admin Commands

Use these inside a group or channel where the bot is present:

| Command | Description |
|---|---|
| `/settings` | Open the dynamic settings panel. |
| `/setdelete 30s` | Enable auto-delete and delete new messages after 30 seconds. |
| `/setdelete 5m` | Enable auto-delete with a 5-minute timer. |
| `/setdelete off` | Disable auto-delete. |
| `/deleteon` | Enable auto-delete with saved time, or 60 seconds if no time was saved. |
| `/deleteoff` | Disable auto-delete for new messages. |
| `/help` | Show chat help and repo credits. |

The bot must have permission to delete messages in the group/channel.

---

## 👑 Owner Commands

Use these in the bot PM from the configured `OWNER` account:

| Command | Description |
|---|---|
| `/admin` or `/stats` | Open the owner management panel. |
| `/broadcast` | Reply to any message and broadcast it using Telegram **forward**. |
| `/addfsub <chat_id> [invite_link]` | Add a required force-sub chat. |
| `/delfsub <chat_id>` | Remove a force-sub chat. |
| `/fsubs` | List all configured force-sub chats. |

---

## 🗄️ MongoDB Collections

- `chats` - per-chat settings, status, titles, and metadata.
- `messages` - pending/completed delete jobs with delete timestamps.
- `users` - bot PM users and blocked/deactivated status.
- `fsubs` - multiple force-sub chat requirements.
- `broadcasts` - broadcast history and delivery stats.

---

## 🚀 Deploy

1. Add the bot to your group/channel as admin with delete permissions.
2. Set the required environment variables.
3. Start the bot:

```bash
python bot.py
```

4. In each chat, run:

```text
/setdelete 30s
```

or open:

```text
/settings
```

---

## ⚠️ Notes

- Default mode is disabled for every chat, so newly added chats are safe.
- Telegram limits are respected through FloodWait sleeps.
- Broadcast uses `forward`, not `copy`, as requested.
- This project keeps original credits for **GitHub.com/mntgxo** and the source repository.
