import os
import json
import logging
from pathlib import Path
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

# ===========================================================================================


def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("about me", callback_data="about")],
        [InlineKeyboardButton("🎮 Games", callback_data="games")],
        [InlineKeyboardButton("🎧 Spotify", url=LINKS["spotify"])],
        [InlineKeyboardButton("📺 YouTube", url=LINKS["youtube"])],
        [InlineKeyboardButton("💬 Discord", url=LINKS["discord"])],
    ]
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
    await show_screen(update.effective_chat.id, context, "main", WELCOME_TEXT, main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == "about":
        await show_screen(chat_id, context, "main", ABOUT_TEXT, main_menu())
    elif query.data == "games":
        await show_screen(chat_id, context, "games", GAMES_TEXT, games_menu())
    elif query.data == "back":
        await show_screen(chat_id, context, "main", WELCOME_TEXT, main_menu())


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


# ========================= ЧАТ С ЛЮДЬМИ ЧЕРЕЗ БОТА (relay) =========================

async def relay_from_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любое текстовое сообщение от обычного пользователя (не команда) пересылается тебе."""
    if not ADMIN_ID:
        return  # ADMIN_ID не настроен — пересылка выключена

    msg = update.message
    user = msg.from_user

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
        log.warning("ADMIN_ID не задан — чат с пользователями и /setabout работать не будут.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setabout", set_about))
    app.add_handler(CallbackQueryHandler(button_handler))

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
