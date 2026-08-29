import os
import json
import logging
from pathlib import Path
import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ========================= НАСТРОЙКИ (заполни своими значениями) =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН")

# Твой Telegram ID (числовой, не username). Узнать: напиши /start боту @userinfobot.
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

IMAGES = {
    "main": "images/main.jpg",
    "games": "images/games.jpg",
}

LINKS = {
    "pubg": "https://t.me/+jqDtn3M099RmNmRi",
    "brawl": "https://link.brawlstars.com/invite/friend/en/?tag=PR8P2VP0U",
    "steam1": "https://steamcommunity.com/id/sodachkaikarys",
    "steam2": "https://steamcommunity.com/id/76561198695464934",
    "roblox": "https://www.roblox.com/share?code=615949c11b97e04db3de925976c0eaae&type=Profile&source=ProfileShare&stamp=1755272642929",
    "spotify": "https://open.spotify.com/playlist/28P9qmooQM1MQ16d6uCjpz?si=Ors4RhKQQTKo7cmHLIhIsg&utm_source=copy-link&pi=xR0LjmeeR_eAl",
    "youtube": "https://youtube.com/@milkiuis",
    "discord": "https://discord.gg/GGCW4NWy",
}

WELCOME_TEXT = "✦･ﾟ: *✧･ﾟ:*  W E L C O M E  *:･ﾟ✧*:･ﾟ✦\n\n"
GAMES_TEXT = "🎮 ° • ˚ ˚ ˖  G A M E S  ˖ ˚ ˚ • ° 🎮\n\nвыбери куда хочешь заглянуть:"

# ===========================================================================================

# --- Хранение ABOUT_TEXT в файле, чтобы менять его командой без правки кода ---
ABOUT_FILE = Path("about.json")
DEFAULT_ABOUT = "WoW, no info\n\n"


def load_about() -> str:
    if ABOUT_FILE.exists():
        try:
            return json.loads(ABOUT_FILE.read_text(encoding="utf-8")).get("text", DEFAULT_ABOUT)
        except Exception:
            pass
    return DEFAULT_ABOUT


def save_about(text: str):
    ABOUT_FILE.write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")


ABOUT_TEXT = load_about()

# --- Хранение связки "пересланное админу сообщение -> кто автор", чтобы отвечать людям ---
RELAY_FILE = Path("relay_map.json")


def load_relay_map() -> dict:
    if RELAY_FILE.exists():
        try:
            return json.loads(RELAY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_relay_map(data: dict):
    RELAY_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


relay_map = load_relay_map()  # {"<message_id в чате админа>": <chat_id пользователя>}

# --- Список всех, кто писал боту (для /stats и /broadcast) ---
USERS_FILE = Path("users.json")


def load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_users(data: dict):
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


users = load_users()  # {"<chat_id>": {"name": ..., "username": ...}}


def remember_user(update: Update):
    user = update.effective_user
    chat_id = update.effective_chat.id
    users[str(chat_id)] = {"name": user.full_name, "username": user.username or ""}
    save_users(users)


# --- Заблокированные пользователи (не могут писать тебе через бота) ---
BLOCKED_FILE = Path("blocked.json")


def load_blocked() -> set:
    if BLOCKED_FILE.exists():
        try:
            return set(json.loads(BLOCKED_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def save_blocked(data: set):
    BLOCKED_FILE.write_text(json.dumps(list(data)), encoding="utf-8")


blocked_users = load_blocked()

# --- Свои приватные заметки о пользователях (мини-CRM, видно только тебе) ---
NOTES_FILE = Path("notes.json")


def load_notes() -> dict:
    if NOTES_FILE.exists():
        try:
            return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_notes(data: dict):
    NOTES_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


notes = load_notes()  # {"<user_id>": "текст заметки"}

# --- Журнал последних сообщений от пользователей (для /recent) ---
RECENT_FILE = Path("recent.json")
RECENT_MAX = 20  # сколько храним, показываем последние 5


def load_recent() -> list:
    if RECENT_FILE.exists():
        try:
            return json.loads(RECENT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_recent(data: list):
    RECENT_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


recent_log = load_recent()  # [{"name":..., "id":..., "preview":...}, ...]

# --- Дополнительные кнопки, добавляемые командой /addbutton без правки кода ---
CUSTOM_BUTTONS_FILE = Path("custom_buttons.json")


def load_custom_buttons() -> dict:
    if CUSTOM_BUTTONS_FILE.exists():
        try:
            return json.loads(CUSTOM_BUTTONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_custom_buttons(data: dict):
    CUSTOM_BUTTONS_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


custom_buttons = load_custom_buttons()  # {"key": {"url": ..., "label": ...}}

# ===========================================================================================


def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("about me", callback_data="about")],
        [InlineKeyboardButton("🎮 Games", callback_data="games")],
        [InlineKeyboardButton("🎧 Spotify", url=LINKS["spotify"])],
        [InlineKeyboardButton("📺 YouTube", url=LINKS["youtube"])],
        [InlineKeyboardButton("💬 Discord", url=LINKS["discord"])],
    ]
    for key, btn in custom_buttons.items():
        keyboard.append([InlineKeyboardButton(btn["label"], url=btn["url"])])
    return InlineKeyboardMarkup(keyboard)


def games_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔫 PUBG", url=LINKS["pubg"])],
        [InlineKeyboardButton("⭐ Brawl Stars", url=LINKS["brawl"])],
        [InlineKeyboardButton("🕹 Steam #1", url=LINKS["steam1"])],
        [InlineKeyboardButton("🕹 Steam #2", url=LINKS["steam2"])],
        [InlineKeyboardButton("🟥 Roblox", url=LINKS["roblox"])],
        [InlineKeyboardButton("‹ Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def about_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("‹ Назад", callback_data="back")]])


# --- Погода в Санкт-Петербурге (видно только тебе) ---
WEATHER_CODES = {
    0: "☀️ Ясно", 1: "🌤 Малооблачно", 2: "⛅ Переменная облачность", 3: "☁️ Пасмурно",
    45: "🌫 Туман", 48: "🌫 Изморозь",
    51: "🌦 Лёгкая морось", 53: "🌦 Морось", 55: "🌧 Сильная морось",
    61: "🌦 Небольшой дождь", 63: "🌧 Дождь", 65: "🌧 Сильный дождь",
    71: "🌨 Небольшой снег", 73: "❄️ Снег", 75: "❄️ Сильный снег",
    80: "🌦 Ливень", 81: "🌧 Сильный ливень", 82: "⛈ Очень сильный ливень",
    95: "⛈ Гроза",
}


async def get_weather_spb() -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": 59.9311, "longitude": 30.3609,
                    "current_weather": "true",
                    "daily": "temperature_2m_max,temperature_2m_min",
                    "timezone": "Europe/Moscow",
                },
            )
            data = r.json()
        cw = data["current_weather"]
        desc = WEATHER_CODES.get(cw["weathercode"], "погода неизвестна")
        temp = cw["temperature"]
        wind = cw["windspeed"]
        t_max = data["daily"]["temperature_2m_max"][0]
        t_min = data["daily"]["temperature_2m_min"][0]
        return (
            f"{desc}\n"
            f"Сейчас: {temp}°C, ветер {wind} км/ч\n"
            f"Сегодня: от {t_min}°C до {t_max}°C"
        )
    except Exception:
        return "Не удалось получить погоду — проверь интернет и попробуй ещё раз."


def _image_source(key: str):
    path = IMAGES[key]
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return open(path, "rb")


async def show_screen(chat_id: int, context: ContextTypes.DEFAULT_TYPE, image_key: str, text: str, keyboard: InlineKeyboardMarkup):
    old = context.user_data.get("screen_msgs")
    if old:
        for msg_id in (old.get("photo_id"), old.get("text_id")):
            if msg_id:
                try:
                    await context.bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass

    photo_msg = await context.bot.send_photo(chat_id=chat_id, photo=_image_source(image_key))
    text_msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)

    context.user_data["screen_msgs"] = {
        "photo_id": photo_msg.message_id,
        "text_id": text_msg.message_id,
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remember_user(update)

    if update.effective_user.id == ADMIN_ID:
        weather_kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("☀️ Погода в Питере сейчас", callback_data="weather_spb")]]
        )
        await update.message.reply_text(
            "Привет, Andrew! Хорошего дня! ❤️",
            reply_markup=weather_kb,
        )

    await show_screen(update.effective_chat.id, context, "main", WELCOME_TEXT, main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == "about":
        await show_screen(chat_id, context, "main", ABOUT_TEXT, about_menu())
    elif query.data == "games":
        await show_screen(chat_id, context, "games", GAMES_TEXT, games_menu())
    elif query.data == "back":
        await show_screen(chat_id, context, "main", WELCOME_TEXT, main_menu())
    elif query.data == "weather_spb":
        if update.effective_user.id != ADMIN_ID:
            return
        weather_text = await get_weather_spb()
        await query.message.reply_text(weather_text)


# ========================= АДМИН-КОМАНДЫ (управление функционалом) =========================

async def set_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/setabout текст — меняет ABOUT_TEXT без правки кода. Доступно только тебе (ADMIN_ID)."""
    global ABOUT_TEXT
    if update.effective_user.id != ADMIN_ID:
        return

    new_text = update.message.text.partition(" ")[2].strip()
    if not new_text:
        await update.message.reply_text("Использование: /setabout твой новый текст о себе")
        return

    ABOUT_TEXT = new_text + "\n\n"
    save_about(ABOUT_TEXT)
    await update.message.reply_text("Текст «Обо мне» обновлён ✅")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats — сколько людей писало боту."""
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"Всего пользователей: {len(users)}\nЗаблокировано: {len(blocked_users)}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/broadcast текст — разослать сообщение всем, кто писал боту."""
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Использование: /broadcast текст рассылки")
        return

    sent, failed = 0, 0
    for chat_id_str in list(users.keys()):
        try:
            await context.bot.send_message(int(chat_id_str), text)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"Рассылка завершена ✅\nДоставлено: {sent}\nНе удалось: {failed}")


async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/block id — запретить конкретному человеку писать тебе через бота."""
    if update.effective_user.id != ADMIN_ID:
        return
    parts = update.message.text.split()
    if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
        await update.message.reply_text("Использование: /block id_пользователя")
        return
    blocked_users.add(int(parts[1]))
    save_blocked(blocked_users)
    await update.message.reply_text(f"Пользователь {parts[1]} заблокирован ✅")


async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/unblock id — снять блокировку."""
    if update.effective_user.id != ADMIN_ID:
        return
    parts = update.message.text.split()
    if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
        await update.message.reply_text("Использование: /unblock id_пользователя")
        return
    blocked_users.discard(int(parts[1]))
    save_blocked(blocked_users)
    await update.message.reply_text(f"Пользователь {parts[1]} разблокирован ✅")


async def add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/addbutton key url label — добавляет новую кнопку в главное меню на лету."""
    if update.effective_user.id != ADMIN_ID:
        return

    parts = update.message.text.split(maxsplit=3)
    if len(parts) < 4:
        await update.message.reply_text(
            "Использование: /addbutton key url label\n"
            "Пример: /addbutton tiktok https://tiktok.com/@me 🎵 TikTok"
        )
        return

    _, key, url, label = parts
    custom_buttons[key] = {"url": url, "label": label}
    save_custom_buttons(custom_buttons)
    await update.message.reply_text(f"Кнопка «{label}» добавлена в меню ✅")


async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/removebutton key — убирает добавленную ранее кнопку."""
    if update.effective_user.id != ADMIN_ID:
        return

    parts = update.message.text.split()
    if len(parts) != 2:
        keys = ", ".join(custom_buttons.keys()) or "(пока пусто)"
        await update.message.reply_text(f"Использование: /removebutton key\nТекущие ключи: {keys}")
        return

    key = parts[1]
    if key not in custom_buttons:
        await update.message.reply_text(f"Нет такой кнопки: {key}")
        return

    del custom_buttons[key]
    save_custom_buttons(custom_buttons)
    await update.message.reply_text(f"Кнопка «{key}» удалена ✅")


async def note_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/note id текст — приватная заметка о пользователе. /note id без текста — показать заметку."""
    if update.effective_user.id != ADMIN_ID:
        return

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await update.message.reply_text("Использование: /note id_пользователя текст заметки")
        return

    user_id = parts[1]
    if len(parts) == 2:
        existing = notes.get(user_id)
        await update.message.reply_text(f"Заметка: {existing}" if existing else "Заметок нет.")
        return

    notes[user_id] = parts[2].strip()
    save_notes(notes)
    await update.message.reply_text("Заметка сохранена ✅")


async def recent_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/recent — последние 5 человек, которые писали боту, с превью сообщения."""
    if update.effective_user.id != ADMIN_ID:
        return
    if not recent_log:
        await update.message.reply_text("Пока никто не писал.")
        return

    lines = []
    for entry in recent_log[-5:][::-1]:
        note = notes.get(str(entry["id"]))
        note_part = f" 📌{note}" if note else ""
        lines.append(f"• {entry['name']} (id {entry['id']}){note_part}\n   „{entry['preview']}“")
    await update.message.reply_text("Последние обращения:\n\n" + "\n\n".join(lines))


async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пришли ФОТО с подписью «/setphoto main» или «/setphoto games» — заменит картинку бота."""
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message
    caption = (msg.caption or "").strip()
    parts = caption.split()

    if len(parts) != 2 or parts[1] not in IMAGES:
        await msg.reply_text(
            "Пришли фото с подписью:\n"
            "/setphoto main — для главного экрана и «Обо мне»\n"
            "/setphoto games — для раздела Games"
        )
        return

    key = parts[1]
    photo = msg.photo[-1]  # самое высокое разрешение из присланных вариантов
    file = await context.bot.get_file(photo.file_id)

    path = Path(IMAGES[key])
    path.parent.mkdir(parents=True, exist_ok=True)
    await file.download_to_drive(str(path))

    await msg.reply_text(f"Картинка «{key}» обновлена ✅ Проверь в боте: /start")


# ========================= ЧАТ С ЛЮДЬМИ ЧЕРЕЗ БОТА (relay) =========================

async def relay_from_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любое текстовое сообщение от обычного пользователя (не команда) пересылается тебе."""
    if not ADMIN_ID:
        return  # ADMIN_ID не настроен — пересылка выключена

    msg = update.message
    user = msg.from_user

    if user.id in blocked_users:
        await msg.reply_text("Отправка сообщений недоступна.")
        return

    remember_user(update)

    preview = (msg.text or "")[:80]
    recent_log.append({"name": user.full_name, "id": user.id, "preview": preview})
    save_recent(recent_log[-RECENT_MAX:])

    info = f"✉️ Сообщение от {user.full_name} (@{user.username or '—'}, id {user.id}):"
    await context.bot.send_message(ADMIN_ID, info)
    copied = await context.bot.copy_message(
        chat_id=ADMIN_ID, from_chat_id=msg.chat.id, message_id=msg.message_id
    )

    relay_map[str(copied.message_id)] = msg.chat.id
    save_relay_map(relay_map)

    await msg.reply_text("Сообщение отправлено ✅ Скоро отвечу.")


async def relay_from_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ты отвечаешь свайпом (reply) на пересланное сообщение — бот доставит ответ автору."""
    msg = update.message
    if msg.from_user.id != ADMIN_ID or not msg.reply_to_message:
        return

    replied_id = str(msg.reply_to_message.message_id)
    user_chat_id = relay_map.get(replied_id)
    if not user_chat_id:
        return  # это не пересланное ботом сообщение — игнорируем

    await context.bot.copy_message(chat_id=user_chat_id, from_chat_id=ADMIN_ID, message_id=msg.message_id)


def main():
    if not BOT_TOKEN or BOT_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
        raise SystemExit("Не задан BOT_TOKEN. Укажи его через переменную окружения BOT_TOKEN.")
    if not ADMIN_ID:
        log.warning("ADMIN_ID не задан — чат с пользователями и админ-команды работать не будут.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setabout", set_about))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(CommandHandler("addbutton", add_button))
    app.add_handler(CommandHandler("removebutton", remove_button))
    app.add_handler(CommandHandler("note", note_user))
    app.add_handler(CommandHandler("recent", recent_contacts))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Фото с подписью /setphoto main|games от тебя — меняет картинку бота
    app.add_handler(MessageHandler(
        filters.PHOTO & filters.CaptionRegex(r"(?i)^/setphoto") & filters.User(user_id=ADMIN_ID),
        set_photo,
    ))

    # Свайп-ответ админа на пересланное сообщение — должен идти РАНЬШЕ общего relay_from_user
    app.add_handler(MessageHandler(
        filters.TEXT & filters.User(user_id=ADMIN_ID) & filters.REPLY, relay_from_admin
    ))
    # Любой текст от обычных пользователей (не команда) — пересылка админу
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.User(user_id=ADMIN_ID), relay_from_user
    ))

    log.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
