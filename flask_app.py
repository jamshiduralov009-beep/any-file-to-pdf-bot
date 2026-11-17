import sys
import telebot
from flask import Flask, request
from bot import bot, BOT_TOKEN

app = Flask(__name__)

WEBHOOK_URL_PATH = f"/{BOT_TOKEN}"

@app.route('/', methods=['GET'])
def index():
    return "🤖 <b>Fayllarni PDF-ga aylantiruvchi bot</b> PythonAnywhere-da faol ishlamoqda!", 200

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        if json_string:
            update = telebot.types.Update.de_json(json_string)
            if update:
                bot.process_new_updates([update])
    except Exception as e:
        print(f"Webhook processing error: {e}", file=sys.stderr)
    return 'OK', 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    host = request.host_url.rstrip('/')
    webhook_url = f"{host}{WEBHOOK_URL_PATH}"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    if success:
        return f"<h3>✅ Webhook muvaffaqiyatli o'rnatildi!</h3><p>Telegram bot manzili: {webhook_url}</p>", 200
    else:
        return "<h3>❌ Webhook o'rnatilmadi. Tokenni tekshiring!</h3>", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
