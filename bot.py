import logging
from io import BytesIO
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "7174293758:AAG96TMs5toDwFICxYCOJ_ECY3njvYa6mzI"

# Load logo images
logo_left = Image.open("logo_left.png").convert("RGBA")
logo_right = Image.open("logo_right.png").convert("RGBA")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for user photos
user_photos = {}

def add_logos(img: Image.Image, resize_to_square: bool = False) -> Image.Image:
    if resize_to_square:
        img = img.copy()
        min_side = min(img.size)
        img = img.crop(((img.width - min_side) // 2,
                        (img.height - min_side) // 2,
                        (img.width + min_side) // 2,
                        (img.height + min_side) // 2))
        img = img.resize((1500, 1500))

    # Ensure it's RGBA for transparency
    img = img.convert("RGBA")

    # Paste logos
    img.paste(logo_left, (20, 20), logo_left)
    img.paste(logo_right, (img.width - logo_right.width - 20, 20), logo_right)

    return img

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gửi ảnh cho tôi để xử lý!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    user_photos[update.message.chat_id] = photo_bytes

    keyboard = [
        [
            InlineKeyboardButton("📏 Giữ nguyên kích thước", callback_data="original"),
            InlineKeyboardButton("🔲 Ảnh vuông 1500x1500", callback_data="square"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bạn muốn xử lý ảnh theo cách nào?", reply_markup=reply_markup)

async def handle_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    if chat_id not in user_photos:
        await query.edit_message_text("Không tìm thấy ảnh để xử lý.")
        return

    option = query.data
    image = Image.open(BytesIO(user_photos[chat_id]))

    if option == "original":
        result = add_logos(image, resize_to_square=False)
    else:
        result = add_logos(image, resize_to_square=True)

    bio = BytesIO()
    bio.name = "result.png"
    result.save(bio, format="PNG")
    bio.seek(0)

    await context.bot.send_photo(chat_id=chat_id, photo=bio)
    await query.edit_message_text("Ảnh đã được xử lý xong!")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_option))
    app.run_polling()

if __name__ == "__main__":
    main()
