import os
import shutil
import telebot
from telebot import types, apihelper
from converter import combine_files_to_single_pdf

# Load .env variables cleanly without depending on external packages
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

load_env_file()

# Telegram Bot Token (loaded securely from environment)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN muhit o'zgaruvchisi topilmadi! Iltimos, .env faylida BOT_TOKEN ni belgilang.")

# Configure outbound proxy for PythonAnywhere free tier if running in that environment
PROXY = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
if not PROXY and "pythonanywhere" in os.getenv("HOSTNAME", "").lower():
    PROXY = "http://proxy.server:3128"

if PROXY:
    os.environ["http_proxy"] = PROXY
    os.environ["https_proxy"] = PROXY
    try:
        apihelper.proxy = {'http': PROXY, 'https': PROXY}
    except Exception:
        pass

# Synchronous bot instance required for WSGI / Webhook processing
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# User files cache directory
BASE_TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_uploads")
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

# User session: {user_id: [file_path1, file_path2, ...]}
user_files = {}

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_convert = types.KeyboardButton("✅ Bo'ldi, PDF-ga aylantir")
    btn_status = types.KeyboardButton("📊 Yuborilgan fayllar")
    btn_clear = types.KeyboardButton("🗑 Tozalash")
    markup.add(btn_convert)
    markup.add(btn_status, btn_clear)
    return markup

def send_safe_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    try:
        return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        # Fallback to plain text if formatting fails
        return bot.send_message(chat_id, text, reply_markup=reply_markup)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    user_files[user_id] = []
    
    welcome_text = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men istalgan faylni sifatli <b>PDF</b> formatiga aylantirib beruvchi botman!\n\n"
        "📌 <b>Imkoniyatlar:</b>\n"
        "• 📸 Rasmlar (JPG, PNG, WEBP)\n"
        "• 📝 Matnli hujjatlar (TXT)\n"
        "• 📄 Word hujjatlar (DOCX)\n"
        "• 📑 Tayyor PDF fayllarni birlashtirish\n"
        "• 🎥 Video fayllar (kadr ko'rinishida)\n\n"
        "🚀 <b>Qanday ishlaydi?</b>\n"
        "1. Menga bir yoki bir nechta fayl yuboring.\n"
        "2. Hammasini yuborib bo'lgach, pastdagi <b>«✅ Bo'ldi, PDF-ga aylantir»</b> tugmasini bosing!\n"
        "3. Men sizga tayyor PDF hujjatni yuboraman."
    )
    send_safe_message(user_id, welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "📊 Yuborilgan fayllar")
def show_status(message):
    user_id = message.chat.id
    files = user_files.get(user_id, [])
    if not files:
        send_safe_message(user_id, "ℹ️ Hozircha hech qanday fayl yuklamadingiz.", reply_markup=get_main_keyboard())
    else:
        text = f"📂 <b>Yuklangan fayllar ro'yxati ({len(files)} ta):</b>\n\n"
        for idx, f in enumerate(files, 1):
            text += f"{idx}. <code>{os.path.basename(f)}</code>\n"
        text += "\nTayyor bo'lsangiz, <b>«✅ Bo'ldi, PDF-ga aylantir»</b> tugmasini bosing."
        send_safe_message(user_id, text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "🗑 Tozalash")
def clear_files(message):
    user_id = message.chat.id
    user_dir = os.path.join(BASE_TEMP_DIR, str(user_id))
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir, ignore_errors=True)
    user_files[user_id] = []
    send_safe_message(user_id, "🗑 Barcha yuklangan fayllar tozalandi. Yangi fayllarni yuborishingiz mumkin.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "✅ Bo'ldi, PDF-ga aylantir")
def process_to_pdf(message):
    user_id = message.chat.id
    files = user_files.get(user_id, [])

    if not files:
        send_safe_message(
            user_id,
            "⚠️ Hali birorta ham fayl yubormadingiz!\nIltimos, avval rasm yoki hujjat yuboring.",
            reply_markup=get_main_keyboard()
        )
        return

    msg_wait = send_safe_message(user_id, "⏳ Fayllar PDF formatiga o'tkazilmoqda, iltimos kuting...")

    try:
        user_dir = os.path.join(BASE_TEMP_DIR, str(user_id))
        output_pdf = os.path.join(user_dir, f"tayyor_hujjat_{user_id}.pdf")

        # Convert and combine
        combine_files_to_single_pdf(files, output_pdf)

        if os.path.exists(output_pdf):
            with open(output_pdf, 'rb') as f:
                bot.send_document(
                    user_id,
                    f,
                    caption=f"🎉 <b>Hujjatingiz tayyor!</b>\nJami {len(files)} ta fayl bitta PDF-ga jamlandi.",
                    parse_mode="HTML"
                )
        else:
            send_safe_message(user_id, "❌ Xatolik yuz berdi: PDF fayl hosil bo'lmadi.")
    except Exception as e:
        send_safe_message(user_id, f"❌ Xatolik yuz berdi: {str(e)}")
    finally:
        user_dir = os.path.join(BASE_TEMP_DIR, str(user_id))
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir, ignore_errors=True)
        user_files[user_id] = []
        try:
            if msg_wait:
                bot.delete_message(user_id, msg_wait.message_id)
        except Exception:
            pass

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    user_dir = os.path.join(BASE_TEMP_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    if user_id not in user_files:
        user_files[user_id] = []

    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    file_name = f"photo_{len(user_files[user_id]) + 1}.jpg"
    save_path = os.path.join(user_dir, file_name)

    with open(save_path, 'wb') as f:
        f.write(downloaded_file)

    user_files[user_id].append(save_path)
    reply_text = (
        f"📸 Rasm qabul qilindi! (Jami: {len(user_files[user_id])} ta)\n\n"
        "Yana yuborishingiz yoki <b>«✅ Bo'ldi, PDF-ga aylantir»</b> tugmasini bosishingiz mumkin."
    )
    send_safe_message(user_id, reply_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.chat.id
    user_dir = os.path.join(BASE_TEMP_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    if user_id not in user_files:
        user_files[user_id] = []

    doc = message.document
    file_name = doc.file_name or f"doc_{len(user_files[user_id]) + 1}"
    file_info = bot.get_file(doc.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    save_path = os.path.join(user_dir, file_name)
    with open(save_path, 'wb') as f:
        f.write(downloaded_file)

    user_files[user_id].append(save_path)
    reply_text = (
        f"📄 Fayl qabul qilindi: <code>{file_name}</code> (Jami: {len(user_files[user_id])} ta)\n\n"
        "Yana yuborishingiz yoki <b>«✅ Bo'ldi, PDF-ga aylantir»</b> tugmasini bosishingiz mumkin."
    )
    send_safe_message(user_id, reply_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.chat.id
    user_dir = os.path.join(BASE_TEMP_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    if user_id not in user_files:
        user_files[user_id] = []

    video = message.video
    file_name = video.file_name or f"video_{len(user_files[user_id]) + 1}.mp4"
    file_info = bot.get_file(video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    save_path = os.path.join(user_dir, file_name)
    with open(save_path, 'wb') as f:
        f.write(downloaded_file)

    user_files[user_id].append(save_path)
    reply_text = (
        f"🎥 Video qabul qilindi! (Jami: {len(user_files[user_id])} ta)\n\n"
        "Yana yuborishingiz yoki <b>«✅ Bo'ldi, PDF-ga aylantir»</b> tugmasini bosishingiz mumkin."
    )
    send_safe_message(user_id, reply_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

if __name__ == '__main__':
    print("Bot polling rejimida ishga tushirilmoqda...")
    bot.infinity_polling(skip_pending=True)
