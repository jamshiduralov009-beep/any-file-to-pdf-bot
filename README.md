# Any2PDF Telegram Bot

Foydalanuvchi yuborgan turli formatdagi fayllarni (rasm, matn, docx va h.k.) qabul qilib, ularni bitta tartibli PDF hujjatiga birlashtirib beruvchi Telegram bot.

Muallif: **Jamshidbek Uralov**

## Imkoniyatlar
- Rasmlar (JPG, PNG, WEBP) formatlarini PDF sahifalariga aylantirish
- Matnli fayllar (TXT) va Word hujjatlarini (DOCX) PDF formatiga o'tkazish
- Bir nechta fayllarni bitta PDF hujjatiga birlashtirish
- PythonAnywhere serverida Webhook orqali 24/7 ishlash imkoniyati

## O'rnatish va ishga tushirish

1. Repozitoriyani yuklab oling va kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

2. `.env.example` faylidan nusxa olib, `.env` faylini yarating va bot tokeningizni kiriting:
```bash
BOT_TOKEN=sizning_bot_tokeningiz
```

3. Botni mahalliy muhitda ishga tushirish:
```bash
python bot.py
```

4. Serverda (PythonAnywhere) ishga tushirish uchun `flask_app.py` va `wsgi.py` fayllari Webhook rejimida ulanadi.
