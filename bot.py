import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ========================= НАСТРОЙКИ (заполни своими ссылками) =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8966646842:AAE8deXGmAhJkyNI_rXUnGAbgXEAH1cJ7k8")

# Картинки. Можно указать либо путь к локальному файлу (положи картинки в папку images/
# рядом с bot.py), либо прямую ссылку на картинку (https://...jpg).
IMAGES = {
    "main": "images/main.jpg",    # картинка для главного меню и "Обо мне"
    "games": "images/games.jpg",  # картинка для раздела Games
}

ABOUT_TEXT = (
    "WoW, no info\n\n"
)
LINKS = {
    "pubg": "https://t.me/+jqDtn3M099RmNmRi",
    "brawl": "https://link.brawlstars.com/invite/friend/en/?tag=PR8P2VP0U",
    "steam1": "https://steamcommunity.com/id/sodachkaikarys",
    "steam2": "https://steamcommunity.com/id/76561198695464934",
    "roblox": "https://www.roblox.com/share?code=615949c11b97e04db3de925976c0eaae&type=Profile&source=ProfileShare&stamp=1755272642929",
    "spotify": "https://open.spotify.com/playlist/28P9qmooQM1MQ16d6uCjpz?si=Ors4RhKQQTKo7cmHLIhIsg&utm_source=copy-link&pi=xR0LjmeeR_eAl",
    "youtube": "https://https://youtube.com/@milkiuis",
    "discord": "https://discord.gg/GGCW4NWy",
}

# ========================================================================================

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


WELCOME_TEXT = (
    "✦･ﾟ: *✧･ﾟ:*  W E L C O M E  *:･ﾟ✧*:･ﾟ✦\n\n"
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
    if not BOT_TOKEN or BOT_TOKEN == "8966646842:AAE8deXGmAhJkyNI_rXUnGAbgXEAH1cJ7k8":
        raise SystemExit("Не задан BOT_TOKEN. Укажи его в переменных окружения (см. README).")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    log.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
