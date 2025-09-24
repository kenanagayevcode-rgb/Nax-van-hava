import os
import random
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

# Rayon və şəhərlər + kənd/qəsəbələr
REGIONS = {
    "Naxçıvan şəhəri": {
        "Şəhər": ["Naxçıvan (şəhər)"],
        "Qəsəbələr": ["Əliabad (qəsəbə)"],
        "Kəndlər": ["Başbaşı", "Bulqan", "Haciniyyət", "Qaraxanbəyli", "Qaraçuq", "Tumbul"]
    },
    "Babək rayonu": {
        "Şəhər": ["Babək (şəhər)"],
        "Qəsəbələr": ["Cəhri", "Nehrəm"],
        "Kəndlər": [
            "Alagözməzrə", "Araz", "Aşağı Buzqov", "Aşağı Uzunoba", "Badaşqan",
            "Çeşməbasar", "Didivar", "Gərməçataq", "Göynük", "Gülşənabad",
            "Güznüt", "Hacıvar", "Xalxal", "Xəlilli", "Kərimbəyli", "Kültəpə",
            "Qahab", "Qaraqala", "Məmmədrza Dizə", "Naxışnərgiz", "Nəcəfəlidizə",
            "Nəhəcir", "Nəzərabad", "Payız", "Sirab", "Şəkərabad", "Şıxmahmud",
            "Vayxır", "Yarımca", "Yuxarı Buzqov", "Yuxarı Uzunoba", "Zeynəddin"
        ]
    },
    "Culfa rayonu": {
        "Şəhər": ["Culfa (şəhər)"],
        "Qəsəbələr": [],
        "Kəndlər": [
            "Əbrəqunus", "Əlincə", "Ərəfsə", "Ərəzin", "Bənəniyar", "Boyəhməd",
            "Camaldın", "Dizə", "Gal", "Göydərə", "Göynük", "Gülüstan",
            "Xanəgah", "Xoşkeşin", "Kırna", "Qazançı", "Qızılca", "Ləkətağ",
            "Milax", "Saltax", "Şurud", "Teyvaz", "Yaycı"
        ]
    },
    "Kəngərli rayonu": {
        "Şəhər": [],
        "Qəsəbələr": ["Qıvraq"],
        "Kəndlər": ["Böyükdüz", "Çalxanqala", "Xok", "Xıncab", "Qabıllı", "Qarabağlar", "Şahtaxtı", "Təzəkənd", "Yeni Kərki", "Yurdçu"]
    },
    "Ordubad rayonu": {
        "Şəhər": ["Ordubad (şəhər)"],
        "Qəsəbələr": ["Parağaçay", "Şəhriyar"],
        "Kəndlər": [
            "Ağdərə", "Ağrı", "Anabad", "Anaqut", "Aşağı Əndəmic", "Aşağı Əylis", 
            "Aza", "Azadkənd", "Baş Dizə", "Başkənd", "Behrud", "Biləv", "Bist", 
            "Çənnəb", "Darkənd", "Dəstə", "Dırnıs", "Dizə", "Düylün", "Ələhi", 
            "Gənzə", "Gilançay", "Xanağa", "Xurs", "Kələki", "Kələntər Dizə", 
            "Kilit", "Kotam", "Məzrə", "Nəsirvaz", "Nürgüt", "Nüsnüs", "Parağa", 
            "Pəzməri", "Qoşadizə", "Qoruqlar", "Sabirkənd", "Tivi", "Unus", 
            "Üstüpü", "Vələver", "Vənənd", "Yuxarı Əndəmic", "Yuxarı Əylis"
        ]
    },
    "Sədərək rayonu": {
        "Şəhər": [],
        "Qəsəbələr": ["Heydərabad"],
        "Kəndlər": ["Dəmirçi", "Kərki", "Qaraağac", "Sədərək"]
    },
    "Şahbuz rayonu": {
        "Şəhər": ["Şahbuz (şəhər)"],
        "Qəsəbələr": ["Badamlı"],
        "Kəndlər": ["Ağbulaq", "Aşağı Qışlaq", "Ayrınc", "Biçənək", "Daylaqlı", "Gömür",
                     "Güney Qışlaq", "Keçili", "Kiçikoba", "Kolanı", "Kükü", "Külüs",
                     "Qızıl Qışlaq", "Mahmudoba", "Mərəlik", "Nursu", "Sələsüz", "Şada",
                     "Şahbuzkənd", "Türkeş", "Yuxarı Qışlaq"]
    },
    "Şərur rayonu": {
        "Şəhər": ["Şərur (şəhər)"],
        "Qəsəbələr": [],
        "Kəndlər": [
            "Axaməd", "Axura", "Alışar", "Arbatan", "Arpaçay", "Aşağı Aralıq", "Aşağı Daşarx", 
            "Aşma", "Çərçiboğan", "Çomaxtur", "Dərvişlər", "Dəmirçi", "Dərəkənd", "Dizə", 
            "Gümüşlü", "Günnüt", "Xələc", "Xanlıqlar", "İbadulla", "Kərimbəyli", "Kürkənd", 
            "Mahmudkənd", "Maxta", "Muğanlı", "Oğlanqala", "Püsyan", "Qorçulu", "Sərxanlı", 
            "Siyaqut", "Şəhriyar", "Tənənəm", "Tumaslı", "Vərməziyar", "Yengicə", "Yuxarı Aralıq", 
            "Yuxarı Daşarx", "Zeyvə"
        ]
    }
}

# Hər yerin koordinatları (tam siyahını doldur)
COORDS = {
    "Naxçıvan (şəhər)": (39.2090, 45.4120),
    "Əliabad (qəsəbə)": (39.2167, 45.3833),
    "Başbaşı": (39.2000, 45.4000),
    "Bulqan": (39.1950, 45.4100),
    "Haciniyyət": (39.1980, 45.4200),
    "Qaraxanbəyli": (39.1900, 45.4300),
    "Qaraçuq": (39.1833, 45.4000),
    "Tumbul": (39.2100, 45.3900),
    "Babək (şəhər)": (39.1500, 45.4500),
    "Cəhri": (39.1167, 45.4833),
    "Nehrəm": (39.0833, 45.5000),
    # Digər koordinatlar da eyni formatda davam etdirilməlidir...
}

# Hava şərhlərinə görə emoji
WEATHER_ICONS = {
    "clear": "☀️", "clouds": "☁️", "few clouds": "🌤", 
    "scattered clouds": "🌤", "broken clouds": "☁️", 
    "rain": "🌧", "shower rain": "🌧", "thunderstorm": "⛈",
    "snow": "❄️", "mist": "🌫"
}

# Hava vəziyyətinə uyğun iltifat və zarafat
WEATHER_QUOTES = {
    "hot": [
        "🔥 İsti günlər üçün günəş gözəldir, amma suyu unutma! 😎",
        "☀️ Günəşlə oynama zamanı! Qoruyucu krem və gülüş unutulmasın! 😁",
        "🥵 Bu gün isti olacaq, amma sənin enerjin hələ də üstündür! 💪",
        "🌞 Günəşdən zövq al, amma kölgədə də istirahət et! 🍹",
        "🔥 İsti hava – buzlu şirniyyat və yaxşı musiqi üçün mükəmməl! 🎶"
    ],
    "warm": [
        "☀️ Bu hava səni açıq havada macəraya dəvət edir! 🌿",
        "🌼 Günəşli hava – çiçəklərlə rəqs etmək üçün idealdır! 💃",
        "🌞 İsti, amma rahat – sənin gülümsəməyin üçün əla gün! 😄",
        "🍀 Açıq havada gəzintiyə çıx, təbiət səni salamlayacaq! 🌳",
        "🥰 Sərin bir külək və günəşin istiliyi – ruhunu qaldıracaq! ✨"
    ],
    "mild": [
        "🌤 Gəzintiyə çıxmaq üçün ideal hava! 🥰",
        "🍃 Rahat və yumşaq hava – kitab oxumaq və çay içmək üçün mükəmməl! 📚",
        "😊 Havanın yumşaqlığı sənin üzünü güldürsün! 🌺",
        "☁️ Buludlar sənə kölgə versin, amma günəş hələ də salamlayır! 🌞",
        "🌸 Bu gün sakit və xoş – ürəyini açıq saxla! 💖"
    ],
    "cool": [
        "🧥 Bir az soyuyub, amma ürəyin isti olsun! 😉",
        "🌬 Soyuq, amma isti bir gülüş qış gününü isidir! 😄",
        "🍂 Qalın geyin, amma ruhun həmişə isti qalsın! ❤️",
        "☕ İsti çay və sərin hava – mükəmməl kombinasiyadır! 🍵",
        "🧣 Şal və gülüşünü unutma, soyuq da olsa gün gözəl olacaq! 😎"
    ],
    "cold": [
        "❄️ Soyuqdur, isti çay və isti ürək lazımdır! ❤️",
        "☃️ Havanın soyuğu ruhunu daha da istiləndirsin! 🔥",
        "🧤 Əllərini isti saxla, amma gülüşünü paylaş! 😁",
        "🍫 Şokolad və isti yumşaq yorğan – mükəmməl gün! 🛌",
        "🧣 Soyuq hava – dostlarla isti söhbət üçün əla fürsətdir! 💕"
    ]
}

def weather_alert(temp):
    if temp >= 35: quotes = WEATHER_QUOTES["hot"]
    elif temp >= 25: quotes = WEATHER_QUOTES["warm"]
    elif temp >= 15: quotes = WEATHER_QUOTES["mild"]
    elif temp >= 5: quotes = WEATHER_QUOTES["cool"]
    else: quotes = WEATHER_QUOTES["cold"]
    return random.choice(quotes)

def build_regions_keyboard():
    keyboard = []
    for region, places in REGIONS.items():
        for city in places["Şəhər"]:
            keyboard.append([InlineKeyboardButton(city, callback_data=f"city|{city}")])
    return InlineKeyboardMarkup(keyboard)

def build_places_keyboard(region):
    places = REGIONS[region]
    all_places = places["Qəsəbələr"] + places["Kəndlər"]
    keyboard = []
    row = []
    for i, p in enumerate(all_places, start=1):
        row.append(InlineKeyboardButton(p, callback_data=f"place|{p}"))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    if user_id not in welcome_last_shown or now - welcome_last_shown[user_id] >= timedelta(hours=1):
        welcome_text = (
            "✨ Salam! **Naxçıvan Hava Botuna** xoş gəlmisiniz!\n\n"
            "📍 Əvvəlcə şəhəri seçin, sonra həmin şəhərə aid kənd/qəsəbələr görünəcək.\n"
            "💡 Hava məlumatını əldə edin və gününüzü planlayın!"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        welcome_last_shown[user_id] = now
    await update.message.reply_text("🏙 Şəhəri seçin:", reply_markup=build_regions_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("city|"):
        city = data.split("|",1)[1]
        await send_weather(update, city)
        region = next(r for r,p in REGIONS.items() if city in p["Şəhər"])
        await query.message.reply_text(f"📌 {city}-ə aid kənd və qəsəbələr:", reply_markup=build_places_keyboard(region))
    elif data.startswith("place|"):
        place = data.split("|",1)[1]
        await send_weather(update, place)

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
            icon = next((emoji for key, emoji in WEATHER_ICONS.items() if key in desc), "🌡")
            alert_text = weather_alert(temp)
            text = (
                f"{place} üçün hava {icon}:\n"
                f"🌡 Temperatur: {temp}°C\n"
                f"🌤 Şərh: {desc}\n"
                f"💧 Rütubət: {humidity}%\n"
                f"🌬 Külək: {wind} m/s\n\n"
                f"✨ {alert_text}"
            )
        except Exception:
            text = "⚠️ Hava məlumatını gətirmək mümkün olmadı."
    if update.callback_query:
        await update.callback_query.message.reply_text(text)
    elif update.message:
        await update.message.reply_text(text)

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    matched = next((p for p in COORDS if p.lower() == text), None)
    if matched:
        await send_weather(update, matched)
    else:
        await update.message.reply_text("❌ Bu kənd/qəsəbəni tanımıram. Şəhəri seçin:", reply_markup=build_regions_keyboard())

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
