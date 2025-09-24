import os
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)

from dotenv import load_dotenv

# .env faylını oxu
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWM_API_KEY = os.environ.get("OWM_API_KEY")

# İstifadəçilərin xoş gəldin mesajlarını yadda saxla
welcome_last_shown = {}

# Rayon, kənd və qəsəbələr (qısaldılmış nümunə, sən tam siyahını qoyacaqsan)
REGIONS = {
    "Naxçıvan şəhəri": [
        "Naxçıvan (şəhər)", "Əliabad (qəsəbə)", "Qaraçuq (kənd)", 
        "Qaraxanbəyli (kənd)", "Bulqan (kənd)", "Haciniyyət (kənd)", "Tumbul (kənd)"
    ],
    "Babək Rayonu": [
        "Babək (şəhər)", "Nehrəm (qəsəbə)", "Araz (kənd)", "Cəhri (kənd)", "Sirab (kənd)"
    ],
    "Culfa Rayonu": [
        "Culfa (şəhər)", "Əbrəqunus (kənd)", "Əlincə (kənd)", "Yaycı (kənd)"
    ]
    # burda sənin verdiyin tam siyahını yerləşdirəcəyik
}

# Hər kənd/qəsəbənin koordinatları (demo üçün bir neçəsi, sən tam dolduracaqsan)
COORDS = {
    "Naxçıvan (şəhər)": (39.2090, 45.4120),
    "Əliabad (qəsəbə)": (39.2167, 45.3833),
    "Qaraçuq (kənd)": (39.1833, 45.4000),
    "Babək (şəhər)": (39.1500, 45.4500),
    "Nehrəm (qəsəbə)": (39.0833, 45.5000),
    "Cəhri (kənd)": (39.1167, 45.4833),
    "Culfa (şəhər)": (38.9550, 45.6290),
    "Əlincə (kənd)": (38.9833, 45.6667),
    "Yaycı (kənd)": (38.9667, 45.6000),
}

# Hava şərhlərinə görə emoji
WEATHER_ICONS = {
    "clear": "☀️", "clouds": "☁️", "few clouds": "🌤", 
    "scattered clouds": "🌤", "broken clouds": "☁️", 
    "rain": "🌧", "shower rain": "🌧", "thunderstorm": "⛈",
    "snow": "❄️", "mist": "🌫"
}

# Temperatur xəbərdarlıqları
def weather_alert(temp):
    if temp >= 35:
        return "🔥 Çox isti! Günəşdən qorun və su iç!"
    elif temp >= 25:
        return "☀️ İsti hava, açıq havada əyləncə üçün əla!"
    elif temp >= 15:
        return "🌤 Hava yaxşıdır, gəzintiyə çıxmaq üçün ideal!"
    elif temp >= 5:
        return "🧥 Soyuqdur, isti geyin, lakin günəş var!"
    else:
        return "❄️ Çox soyuq! Ehtiyatlı olun, isti qalın!"

# Rayon seçimi üçün düymələr
def build_regions_keyboard():
    keyboard = []
    for region in REGIONS.keys():
        keyboard.append([InlineKeyboardButton(region, callback_data=f"region|{region}")])
    return InlineKeyboardMarkup(keyboard)

# Kəndlər üçün 3 sütunlu düymələr
def build_villages_keyboard(region):
    villages = REGIONS[region]
    keyboard = []
    row = []
    for i, v in enumerate(villages, start=1):
        row.append(InlineKeyboardButton(v, callback_data=f"village|{v}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# /start komandası
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()

    if user_id not in welcome_last_shown or now - welcome_last_shown[user_id] >= timedelta(hours=1):
        welcome_text = (
            "✨ Salam! Xoş gəlmisiniz **Naxçıvan Hava Botuna**!\n\n"
            "🌟 Buradan rayon və kəndlər üzrə hava məlumatını öyrənə bilərsiniz.\n"
            "📌 Əvvəlcə rayon seçin, sonra kənd/qəsəbəyə klikləyin.\n"
            "💡 Planlarınızı havaya görə qurun və hər gün məlumatlı olun!"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        welcome_last_shown[user_id] = now

    await update.message.reply_text("📍 Rayon seçin:", reply_markup=build_regions_keyboard())

# Callback işləyici
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("region|"):
        region = data.split("|", 1)[1]
        await query.message.reply_text(
            f"📍 {region} üçün kənd/qəsəbə seçin:",
            reply_markup=build_villages_keyboard(region)
        )
    elif data.startswith("village|"):
        village = data.split("|", 1)[1]
        await send_weather(update, village)

# Hava məlumatı
async def send_weather(update, place):
    if place not in COORDS:
        text = f"❌ Təəssüf ki, {place} üçün koordinatlar tapılmadı."
    else:
        lat, lon = COORDS[place]
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=az"
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"].lower()
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            icon = "🌡"
            for key, emoji in WEATHER_ICONS.items():
                if key in desc:
                    icon = emoji
                    break

            alert_text = weather_alert(temp)

            text = (
                f"{place} üçün hava {icon}:\n"
                f"🌡 Temperatur: {temp}°C\n"
                f"🌤 Şərh: {desc}\n"
                f"💧 Rütubət: {humidity}%\n"
                f"🌬 Külək sürəti: {wind} m/s\n\n"
                f"⚠️ {alert_text}"
            )
        except Exception:
            text = "⚠️ Hava məlumatını gətirmək mümkün olmadı."

    if update.callback_query:
        await update.callback_query.message.reply_text(text)
    elif update.message:
        await update.message.reply_text(text)

# Mətnlə axtarış
async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in COORDS:
        await send_weather(update, text)
    else:
        await update.message.reply_text("❌ Bu kənd/qəsəbəni tanımıram. Rayon seçin:", reply_markup=build_regions_keyboard())

# Botu işə sal
def main():
    if not BOT_TOKEN or not OWM_API_KEY:
        print("Xəta: BOT_TOKEN və ya OWM_API_KEY .env-də tapılmadı.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    print("✅ Bot işləyir...")
    app.run_polling()

if __name__ == "__main__":
    main()
