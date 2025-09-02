import logging
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Bot token
BOT_TOKEN = "7817283574:AAHRNKv9KwUrlqsMNarCguAA7qD_1pwugMU"
ALLOWED_GROUPS_ID = [-1002333835562, -1002284467099]  # Change this to your group IDs

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API call
def get_player_info(uid, region):
    url = f"https://garenafreefireteams.onrender.com/player-info?uid={uid}&region={region}&key=2explainationskeysforujjaiwal"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return None

# Timestamp convert
def format_time(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y, %H:%M:%S")
    except:
        return "Not Found"

# Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_GROUPS_ID:
        await update.message.reply_text("Unauthorized group!")
        return

    text = update.message.text.strip()
    if not text.startswith("Get"):
        return

    parts = text.split()
    if len(parts) != 3:
        await update.message.reply_text("Use: Get <Region> <UID>")
        return

    region, uid = parts[1], parts[2]
    msg = await update.message.reply_text("Fetching info...")

    data = get_player_info(uid, region)
    if not data:
        await msg.edit_text("Failed to fetch info.")
        return

    acc = data.get("basicInfo", {})
    soc = data.get("socialInfo", {})
    pet = data.get("petInfo", {})
    guild = data.get("clanBasicInfo", {})
    leader = data.get("captainBasicInfo", {})
    credit = data.get("creditScoreInfo", {})
    profile = data.get("profileInfo", {})
    craftland = data.get("craftlandMapText", "Not Found")

    message = f"""<b>ACCOUNT INFO:</b>
┌ 👤 <b>ACCOUNT BASIC INFO</b>
├─ Name: {acc.get('nickname', 'Not Found')}
├─ UID: {uid}
├─ Level: {acc.get('level', 'Not Found')} (Exp: {acc.get('exp', 'Not Found')})
├─ Region: {acc.get('region', 'Not Found')}
├─ Likes: {acc.get('liked', 'Not Found')}
├─ Honor Score: {credit.get('creditScore', 'Not Found')}
├─ Celebrity Status: {"True" if acc.get('isCelebrity', False) else "False"}
├─ Evo Access Badge : {"Active" if acc.get('isEvoEnabled', False) else "Inactive"}
├─ Title: {acc.get('title', 'Not Found')}
└─ Signature: {soc.get('signature', 'Not Found')}

┌ 🎮 <b>ACCOUNT ACTIVITY</b>
├─ Most Recent OB: {acc.get('releaseVersion', 'Not Found')}
├─ Fire Pass: {"Elite" if acc.get('hasElitePass', False) else "Basic"}
├─ Current BP Badges: {acc.get('badgeCnt', '0')}
├─ BR Rank: {acc.get('maxRank', 'Not Found')}
├─ CS Rank: {acc.get('csRank', 'Not Found')} (Points: {acc.get('csRankingPoints', 'Not Found')})
├─ Created At: {format_time(acc.get('createAt', 0))}
└─ Last Login: {format_time(acc.get('lastLoginAt', 0))}

┌ 👕 <b>ACCOUNT OVERVIEW</b>
├─ Avatar ID: {acc.get('headPic', 'default')}
├─ Banner ID: {acc.get('bannerId', 'default')}
├─ Pin ID: {acc.get('badgeId', 'default')}
├─ Equipped Skills: {', '.join(map(str, profile.get('equipedSkills', ['Not Equipped'])))}
├─ Pet ID: {pet.get('id', 'Not Found')}
├─ Equipped Animation ID: Not Found
├─ Transform Animation ID: Not Found
└─ Outfits: {', '.join(map(str, profile.get('clothes', []))) or 'None'}

┌ 🐾 <b>PET DETAILS</b>
├─ Equipped?: {"Yes" if pet.get('isSelected') else "No"}
├─ Pet Name: {pet.get('name', 'Not Found')}
├─ Pet Type: {pet.get('id', 'Not Found')}
├─ Pet Exp: {pet.get('exp', 'Not Found')}
└─ Pet Level: {pet.get('level', 'Not Found')}

┌ 🛡️ <b>GUILD INFO</b>
├─ Guild Name: {guild.get('clanName', 'Not Found')}
├─ Guild ID: {guild.get('clanId', 'Not Found')}
├─ Guild Level: {guild.get('clanLevel', 'Not Found')}
├─ Live Members: {guild.get('memberNum', 'Not Found')}
└─ Leader Info:
    ├─ Leader Name: {leader.get('nickname', 'Not Found')}
    ├─ Leader UID: {leader.get('accountId', 'Not Found')}
    ├─ Leader Level: {leader.get('level', 'Not Found')} (Exp: {leader.get('exp', 'Not Found')})
    ├─ Leader Created At: {format_time(leader.get('createAt', 0))}
    ├─ Leader Last Login: {format_time(leader.get('lastLoginAt', 0))}
    ├─ Leader Title: {leader.get('title', 'Not Found')}
    └─ Leader CS Points: {leader.get('csRankingPoints', 'Not Found')}

┌ 🗺️ <b>PUBLIC CRAFTLAND MAPS</b>
{craftland}

<b>Follow Admins for API & Token Giveaways:</b>
dhruva = https://t.me/Api_Discussion_Group
Rahul = https://t.me/GlobalEarth_Gaming
"""

    await msg.edit_text(message, parse_mode="HTML")

# Main
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()