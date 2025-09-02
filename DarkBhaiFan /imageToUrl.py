import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import requests
import os
from datetime import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your Telegram bot token and ImgBB API key
TELEGRAM_TOKEN = "8119013845:AAHjsNvMV3HVOxx2E_vSyIEyW3JVLL0P1JM"
IMGBB_API_KEY = "37a8908c36ddf77c1964cbc21b22bd9c"

# Function to upload image to ImgBB and get various link types
def upload_to_imgbb(image_path: str, file_name: str) -> dict:
    try:
        with open(image_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": IMGBB_API_KEY,
                "name": file_name  # Custom filename for the URL
            }
            files = {"image": file}
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
            data = response.json()
            if data["success"]:
                img_data = data["data"]
                # Prepare various link types
                links = {
                    "direct": img_data["url"],
                    "viewer": img_data["url_viewer"],
                    "thumbnail": img_data["thumb"]["url"],
                    "html": f'<img src="{img_data["url"]}" alt="{img_data["title"]}" title="{img_data["title"]}">',
                    "bbcode": f'[img]{img_data["url"]}[/img]',
                    "markdown": f'![{img_data["title"]}]({img_data["url"]})',
                    "full_html": f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{img_data["title"]}</title>
</head>
<body>
    <img src="{img_data["url"]}" alt="{img_data["title"]}" style="max-width:100%; height:auto;">
</body>
</html>
""".strip(),
                    "embed": f'<iframe src="{img_data["url_viewer"]}" width="800" height="600" frameborder="0"></iframe>'
                }
                return links
            else:
                return {"error": "Failed to upload image to ImgBB."}
    except Exception as e:
        logger.error(f"Error uploading to ImgBB: {e}")
        return {"error": f"Error uploading image: {str(e)}"}

# Handler for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Send me an image, and I'll upload it to ImgBB and provide various link types "
        "(direct URL, HTML, BBCode, Markdown, full HTML page, embed, etc.)."
    )

# Handler for image messages
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send an image!")
        return

    # Get user ID to store links
    user_id = update.effective_user.id

    # Get the largest photo size
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    # Generate a filename similar to the example (IMG-YYYYMMDD-HHMMSS-<random>)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_name = f"IMG-{timestamp}-{photo.file_unique_id[:3]}.jpg"
    
    # Download the image
    file_path = f"temp_{file_name}"
    await file.download_to_drive(file_path)
    
    # Upload to ImgBB
    links = upload_to_imgbb(file_path, file_name)
    
    if "error" in links:
        await update.message.reply_text(links["error"])
    else:
        # Store links in user_data with user_id
        if "links" not in context.user_data:
            context.user_data["links"] = {}
        context.user_data["links"][user_id] = links
        
        # Create inline keyboard for selecting link types
        keyboard = [
            [InlineKeyboardButton("Direct URL", callback_data="direct")],
            [InlineKeyboardButton("Viewer Page", callback_data="viewer")],
            [InlineKeyboardButton("Thumbnail URL", callback_data="thumbnail")],
            [InlineKeyboardButton("HTML Image Tag", callback_data="html")],
            [InlineKeyboardButton("BBCode", callback_data="bbcode")],
            [InlineKeyboardButton("Markdown", callback_data="markdown")],
            [InlineKeyboardButton("Full HTML Page", callback_data="full_html")],
            [InlineKeyboardButton("Embed Code", callback_data="embed")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Image uploaded! Choose a link type:", reply_markup=reply_markup)
    
    # Clean up the downloaded file
    try:
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Error deleting temp file: {e}")

# Handler for button clicks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    # Get user ID
    user_id = query.from_user.id
    
    # Retrieve links from user_data
    user_data = context.user_data.get("links", {})
    links = user_data.get(user_id)
    
    if not links:
        await query.message.reply_text("Session expired or no image uploaded. Please upload an image again.")
        return
    
    link_type = query.data
    if link_type in links:
        # For long responses like full_html, truncate or handle appropriately
        response = links[link_type]
        if len(response) > 4096:  # Telegram's message length limit
            # Send as a file if too long
            with open(f"temp_{link_type}.txt", "w") as f:
                f.write(response)
            with open(f"temp_{link_type}.txt", "rb") as f:
                await query.message.reply_document(f, filename=f"{link_type}.txt")
            os.remove(f"temp_{link_type}.txt")
        else:
            await query.message.reply_text(f"{link_type.replace('_', ' ').capitalize()}:\n{response}")
    else:
        await query.message.reply_text("Invalid selection.")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update.message:
        await update.message.reply_text("An error occurred. Please try again later.")

def main():
    # Initialize the bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(error_handler)

    # Start the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()