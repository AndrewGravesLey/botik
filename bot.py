import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ========================= НАСТРОЙКИ (заполни своими ссылками) =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН")

# Картинки. Можно указать либо путь к локальному файлу (положи картинки в папку images/
# рядом с bot.py), либо прямую ссылку на картинку (https://...jpg).
IMAGES = {
    "main": "images/main.jpg",    # картинка для главного меню и "Обо мне"
    "games": "images/games.jpg",  # картинка для раздела Games
}

ABOUT_TEXT = (
    "☆°•*⁀➷ * ~ О М Н Е ~ * ⁀➷•°☆\n\n"
    "✧ Имя: ...\n"
    "✧ Возраст: ...\n"
    "✧ Немного о себе: ...\n\n"
    "𝙩𝙝𝙖𝙣𝙠𝙨 𝙛𝙤𝙧 𝙫𝙞𝙨𝙞𝙩𝙞𝙣𝙜 ♡"
)

LINKS = {
    "pubg": "https://example.com/pubg",
    "brawl": "https://example.com/brawlstars",
    "steam1": "https://steamcommunity.com/id/твой_первый_профиль",
    "steam2": "https://steamcommunity.com/id/твой_второй_профиль",
    "roblox": "https://www.roblox.com/users/твой_id/profile",
    "spotify": "https://open.spotify.com/user/твой_профиль",
    "youtube": "https://www.youtube.com/@твой_канал",
    "discord": "https://discord.gg/твой_инвайт",
}

# ========================================================================================

def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("☆ Обо мне ☆", callback_data="about")],
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


WELCOME_TEXT = (
    "✦･ﾟ: *✧･ﾟ:*  W E L C O M E  *:･ﾟ✧*:･ﾟ✦\n\n"
    "тут инфа обо мне и всё самое интересное ↓"
)

GAMES_TEXT = "🎮 ° • ˚ ˚ ˖  G A M E S  ˖ ˚ ˚ • ° 🎮\n\nвыбери куда хочешь заглянуть:"


def _image_source(key: str):
    """Локальный файл открываем в бинарном режиме, ссылку передаём как есть."""
    path = IMAGES[key]
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return open(path, "rb")


async def show_screen(chat_id: int, context: ContextTypes.DEFAULT_TYPE, image_key: str, text: str, keyboard: InlineKeyboardMarkup):
    """Удаляет предыдущую пару (картинка + текст) и шлёт новую: картинка сверху, текст с кнопками снизу отдельным сообщением."""
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


def main():
    if not BOT_TOKEN or BOT_TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
        raise SystemExit("Не задан BOT_TOKEN. Укажи его в переменных окружения (см. README).")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    log.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
