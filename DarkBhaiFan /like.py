import telebot
import requests
import time
import threading
import json
import os
from datetime import datetime
from collections import defaultdict

# --- Configuration ---
BOT_TOKEN = "7784175709:AAE0Eyg7Oo0C2pQu9KScsUPFfMSfgJ6NcOQ"
DATA_FILE = "like_limits.json"
API_KEY = "7yearskeysforujjaiwal"

VIP_USERS = {7470004765}  # Set of VIP user IDs

bot = telebot.TeleBot(BOT_TOKEN)

# --- Load tracker from file ---
def load_limits():
    if not os.path.exists(DATA_FILE):
        return defaultdict(lambda: {"count": 0, "last_reset": datetime.utcnow().date().isoformat()})
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        tracker = defaultdict(lambda: {"count": 0, "last_reset": datetime.utcnow().date().isoformat()})
        for user_id, info in data.items():
            tracker[int(user_id)] = info
        return tracker

# --- Save tracker to file ---
def save_limits():
    data = {str(user_id): info for user_id, info in like_request_tracker.items()}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- Reset limit if 24 hours passed ---
def reset_limit_if_needed(user_id):
    today = datetime.utcnow().date()
    last_reset_str = like_request_tracker[user_id]["last_reset"]
    last_reset_date = datetime.fromisoformat(last_reset_str).date()
    if last_reset_date < today:
        like_request_tracker[user_id] = {"count": 0, "last_reset": today.isoformat()}
        save_limits()

# --- Retry-based API Call Function ---
def call_api(region, uid):
    url = f"https://garenafreefireteamujjaiwalresources.vercel.app/like?uid={uid}&region={region}&key={API_KEY}"
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200 or not response.text.strip():
                time.sleep(2)
                continue
            return response.json()
        except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError):
            time.sleep(2)
    return "API_ERROR"

# --- Process Like Logic ---
def process_like(message, region, uid):
    chat_id = message.chat.id
    user_id = message.from_user.id

    bot.send_chat_action(chat_id=chat_id, action='typing')

    if user_id not in VIP_USERS:
        reset_limit_if_needed(user_id)
        if like_request_tracker[user_id]["count"] >= 2:
            bot.reply_to(message, "⚠️ You have reached your daily limit of 2 likes! Please try again after 24 hours.")
            return

    processing_msg = bot.reply_to(message, " Got your request, please wait...")

    response = call_api(region, uid)

    if response == "API_ERROR":
        bot.edit_message_text(
            "❌ API is not responding right now due to heavy traffic or server issue.\n\nPlease try again after some time or contact @Ujjaiwal for help.",
            chat_id,
            processing_msg.message_id
        )
        return

    if response.get("status") == 1:
        likes_given = int(response.get("LikesGivenByAPI", 0))
        if likes_given >= 2:
            if user_id not in VIP_USERS:
                like_request_tracker[user_id]["count"] += 1
                save_limits()

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=(
                    f" **Player Nickname:** `{response.get('PlayerNickname', 'N/A')}`\n"
                    f" **Likes at Start of Day:** `{response.get('LikesbeforeCommand', 'N/A')}`\n"
                    f" **Likes Before Command:** `{response.get('LikesbeforeCommand', 'N/A')}`\n"
                    f" **Likes After Command:** `{response.get('LikesafterCommand', 'N/A')}`\n"
                    f" **Likes Given by Bot:** `{response.get('LikesGivenByAPI', 'N/A')}`\n\n"
                    "**Join Our Channels for Next Updates:**\n"
                    "🔗 [Join Group](https://t.me/+BqmiqI4WCbNkZmI1)\n"
                    " [JOIN CHANNEL](https://t.me/IndTeamApis)"
                ),
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text="⚠️ The Daily Like Limit is Over for this UID.\nPlease wait for reset or contact @Ujjaiwal to upgrade your package."
            )
    else:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_msg.message_id,
            text=f"❗ UID `{uid}` has already received max likes for today. Try a different UID.",
            parse_mode="Markdown"
        )

# --- Command Handler ---
@bot.message_handler(commands=['like'])
def handle_like(message):
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❌ Incorrect format! Use:\n`/like {region} {uid}`\n📌 Example: `/like ind 8385763215`", parse_mode="Markdown")
        return

    region, uid = args[1], args[2]

    if not region.isalpha() or not uid.isdigit():
        bot.reply_to(message, "⚠️ Invalid input! Region should be text and UID should be numbers.\n📌 Example: `/like ind 8385763215`")
        return

    threading.Thread(target=process_like, args=(message, region, uid)).start()

# --- Load limits on startup ---
like_request_tracker = load_limits()

# --- Start bot polling ---
bot.polling(none_stop=True)