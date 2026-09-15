import os
import re
import sqlite3
import logging
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ============================================================
# SOZLAMALAR
# ============================================================

TOKEN = "8516020901:AAFRavXaeE9ngyFIYJT-qwLe3470RjqVz78"

# Vrach/admin Telegram ID
ADMIN_ID = 8978729281

PHONE = "+998879655050"
INSTAGRAM = "@zarshedjamshedovich_"
TELEGRAM = "@ZARSHEDJAMSHEDOVICH_567"

BASE_DIR = r"C:\Users\user\ZBOT"

COLOR_IMAGE = r"C:\Users\user\Pictures\FOTO PRATAKOL\rang.jpg"
INTRAORAL_IMAGE = r"C:\Users\user\Pictures\FOTO PRATAKOL\introoral.jpg"
PATIENT_PHOTO_IMAGE = (
    r"C:\Users\user\Pictures\FOTO PRATAKOL\patsent foto paratakol.jpg"
)

DB_FILE = os.path.join(BASE_DIR, "zbot.db")

MAX_PHOTOS = 4
MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50 MB


# ============================================================
# LOG
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# BOSQICHLAR
# ============================================================

(
    NAME,
    SURNAME,
    PHONE_STEP,
    GENDER,
    AGE,
    COLOR,
    TOOTH,
    WORK,
    SCANNER,
    SCAN_FILE,
    PHOTOS,
    NOTE,
    CONFIRM,
    EDIT,
) = range(14)


# ============================================================
# DATABASE
# ============================================================

def init_db():
    os.makedirs(BASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE,
            user_id INTEGER,
            username TEXT,
            name TEXT,
            surname TEXT,
            phone TEXT,
            gender TEXT,
            age TEXT,
            color TEXT,
            tooth TEXT,
            work TEXT,
            scanner TEXT,
            scan_name TEXT,
            photos_count INTEGER,
            note TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_order(data):
    conn = sqlite3.connect(DB_FILE)

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders (
            order_code,
            user_id,
            username,
            name,
            surname,
            phone,
            gender,
            age,
            color,
            tooth,
            work,
            scanner,
            scan_name,
            photos_count,
            note,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TEMP",
        data["user_id"],
        data["username"],
        data["name"],
        data["surname"],
        data["phone"],
        data["gender"],
        data["age"],
        data["color"],
        data["tooth"],
        data["work"],
        data["scanner"],
        data.get("scan_name", ""),
        len(data.get("photos", [])),
        data["note"],
        "Qabul qilindi",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    row_id = cur.lastrowid
    order_code = f"ZB-{row_id:06d}"

    cur.execute(
        "UPDATE orders SET order_code = ? WHERE id = ?",
        (order_code, row_id),
    )

    conn.commit()
    conn.close()

    return order_code


# ============================================================
# YORDAMCHI
# ============================================================

async def send_example_image(update, path, caption):
    if not os.path.isfile(path):
        return False

    try:
        with open(path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
            )
        return True
    except Exception as e:
        logger.error("Rasm yuborishda xato: %s", e)
        return False


def main_keyboard():
    return ReplyKeyboardMarkup(
        [["❌ BEKOR QILISH"]],
        resize_keyboard=True,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ BUYURTMA BEKOR QILINDI.\n\n"
        "Qaytadan boshlash uchun /start ni bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🦷 ZBOT DENTAL LABORATORIYA\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 Assalomu alaykum!\n"
        "Xush kelibsiz!\n\n"
        "📋 Yangi buyurtma berish uchun "
        "ma'lumotlaringizni kiriting.\n\n"
        "👤 ISMINGIZNI KIRITING:",
        reply_markup=main_keyboard(),
    )

    return NAME


# ============================================================
# ISM
# ============================================================

async def name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if len(text) < 2:
        await update.message.reply_text(
            "❗ Iltimos, ismingizni to'g'ri kiriting."
        )
        return NAME

    context.user_data["name"] = text

    await update.message.reply_text(
        "👨‍👩‍👦 FAMILIYANGIZNI KIRITING:",
        reply_markup=main_keyboard(),
    )

    return SURNAME


# ============================================================
# FAMILIYA
# ============================================================

async def surname_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if len(text) < 2:
        await update.message.reply_text(
            "❗ Iltimos, familiyangizni to'g'ri kiriting."
        )
        return SURNAME

    context.user_data["surname"] = text

    keyboard = [
        [
            KeyboardButton(
                "📱 Telefon raqamni yuborish",
                request_contact=True,
            )
        ],
        ["❌ BEKOR QILISH"],
    ]

    await update.message.reply_text(
        "📱 TELEFON RAQAMINGIZNI YUBORING\n\n"
        "Quyidagi tugmani bosing:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )

    return PHONE_STEP


# ============================================================
# TELEFON
# ============================================================

async def phone_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    phone = None

    if update.message.contact:
        phone = update.message.contact.phone_number

    elif update.message.text:
        phone = update.message.text.strip()

    if not phone:
        await update.message.reply_text(
            "❗ Iltimos, telefon raqamingizni yuboring."
        )
        return PHONE_STEP

    context.user_data["phone"] = phone

    keyboard = [
        ["👨 Erkak", "👩 Ayol"],
        ["❌ BEKOR QILISH"],
    ]

    await update.message.reply_text(
        "👤 JINSINGIZNI TANLANG:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        ),
    )

    return GENDER


# ============================================================
# JINS
# ============================================================

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if text not in ["👨 Erkak", "👩 Ayol"]:
        await update.message.reply_text(
            "❗ Iltimos, tugmalardan birini tanlang."
        )
        return GENDER

    context.user_data["gender"] = text

    await update.message.reply_text(
        "🎂 YOSHINGIZNI KIRITING\n\n"
        "Masalan: 25",
        reply_markup=main_keyboard(),
    )

    return AGE


# ============================================================
# YOSH
# ============================================================

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if not text.isdigit():
        await update.message.reply_text(
            "❗ Yoshni faqat raqam bilan kiriting."
        )
        return AGE

    number = int(text)

    if number < 1 or number > 120:
        await update.message.reply_text(
            "❗ Yosh 1 dan 120 gacha bo'lishi kerak."
        )
        return AGE

    context.user_data["age"] = text

    await send_example_image(
        update,
        COLOR_IMAGE,
        "🎨 TISH RANGI NAMUNASI\n\n"
        "Rasmga qarab kerakli rangni tanlang.",
    )

    keyboard = [
        ["A1", "A2", "A3"],
        ["A3.5", "A4", "B1"],
        ["B2", "B3", "B4"],
        ["C1", "C2", "C3"],
        ["C4", "D2", "D3"],
        ["D4"],
        ["❌ BEKOR QILISH"],
    ]

    await update.message.reply_text(
        "🎨 TISH RANGINI TANLANG:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        ),
    )

    return COLOR


# ============================================================
# RANG
# ============================================================

VALID_COLORS = {
    "A1", "A2", "A3", "A3.5", "A4",
    "B1", "B2", "B3", "B4",
    "C1", "C2", "C3", "C4",
    "D2", "D3", "D4",
}


async def color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if text not in VALID_COLORS:
        await update.message.reply_text(
            "❗ Iltimos, rangni faqat tugmalardan tanlang."
        )
        return COLOR

    context.user_data["color"] = text

    await update.message.reply_text(
        "🦷 TISH RAQAMINI KIRITING\n\n"
        "Bitta:\n"
        "11\n\n"
        "Bir nechta:\n"
        "11, 12, 13\n\n"
        "Oraliq:\n"
        "11-13",
        reply_markup=main_keyboard(),
    )

    return TOOTH


# ============================================================
# TISH
# ============================================================

VALID_TEETH = {
    "11", "12", "13", "14", "15", "16", "17", "18",
    "21", "22", "23", "24", "25", "26", "27", "28",
    "31", "32", "33", "34", "35", "36", "37", "38",
    "41", "42", "43", "44", "45", "46", "47", "48",
}


def valid_tooth_input(text):
    cleaned = text.replace(" ", "")

    if "-" in cleaned:
        parts = cleaned.split("-")

        if len(parts) != 2:
            return False

        if parts[0] not in VALID_TEETH or parts[1] not in VALID_TEETH:
            return False

        return True

    if "," in cleaned:
        parts = cleaned.split(",")

        return (
            len(parts) > 0
            and all(part in VALID_TEETH for part in parts)
        )

    return cleaned in VALID_TEETH


async def tooth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if not valid_tooth_input(text):
        await update.message.reply_text(
            "❗ Tish raqami noto'g'ri.\n\n"
            "Masalan:\n"
            "11\n"
            "11, 12, 13\n"
            "11-13"
        )
        return TOOTH

    context.user_data["tooth"] = text

    keyboard = [
        ["🦾 METALOKERAMIK", "✨ VINIR"],
        ["💎 ZIRCON NANISENI", "👑 FULL ZIRCON"],
        ["🦷 PROTEZ", "🦾 SENALITOY"],
        ["🦷 SHITF NANISENI", "🪛 SHITIF"],
        ["🦷🦾 BALKA NA IMPLANTE", "🦷🔩 ABB + SIRCON"],
        ["🦾 ABB + METALOKERAMIK", "✨ PMMA"],
        ["🛠 BOSHQA"],
        ["❌ BEKOR QILISH"],
    ]

    await update.message.reply_text(
        "🛠 QANDAY ISH KERAK?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        ),
    )

    return WORK


# ============================================================
# ISH TURI
# ============================================================

VALID_WORKS = {
    "🦾 METALOKERAMIK",
    "✨ VINIR",
    "💎 ZIRCON NANISENI",
    "👑 FULL ZIRCON",
    "🦷 PROTEZ",
    "🦾 SENALITOY",
    "🦷 SHITF NANISENI",
    "🪛 SHITIF",
    "🦷🦾 BALKA NA IMPLANTE",
    "🦷🔩 ABB + SIRCON",
    "🦾 ABB + METALOKERAMIK",
    "✨ PMMA",
    "🛠 BOSHQA",
}


async def work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if text not in VALID_WORKS:
        await update.message.reply_text(
            "❗ Iltimos, ish turini tugmalardan tanlang."
        )
        return WORK

    context.user_data["work"] = text

    keyboard = [
        ["✅ HA", "❌ YO'Q"],
        ["❌ BEKOR QILISH"],
    ]

    await update.message.reply_text(
        "🖥 INTRAORAL SKANER\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Intraoral skaner bormi?\n\n"
        "✅ HA — ZIP fayl yuborasiz.\n"
        "❌ YO'Q — bemor fotosiga o'tamiz.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        ),
    )

    return SCANNER


# ============================================================
# SCANNER
# ============================================================

async def scanner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if text not in ["✅ HA", "❌ YO'Q"]:
        await update.message.reply_text(
            "❗ Iltimos, ✅ HA yoki ❌ YO'Q ni tanlang."
        )
        return SCANNER

    context.user_data["scanner"] = text

    if text == "❌ YO'Q":
        context.user_data.pop("scan_file", None)
        context.user_data.pop("scan_name", None)

        await send_example_image(
            update,
            PATIENT_PHOTO_IMAGE,
            "📸 BEMOR FOTO NAMUNASI\n\n"
            "1–4 ta rasm yuboring.",
        )

        await update.message.reply_text(
            "📸 BEMOR RASMLARINI YUBORING\n\n"
            "1 dan 4 tagacha rasm yuborishingiz mumkin.",
            reply_markup=main_keyboard(),
        )

        context.user_data["photos"] = []

        return PHOTOS

    await send_example_image(
        update,
        INTRAORAL_IMAGE,
        "🖥 INTRAORAL SKANER NAMUNASI\n\n"
        "ZIP fayl yuboring.",
    )

    await update.message.reply_text(
        "📦 ZIP FAYLNI YUBORING\n\n"
        "Faqat .ZIP fayl qabul qilinadi.",
        reply_markup=main_keyboard(),
    )

    return SCAN_FILE


# ============================================================
# ZIP
# ============================================================

async def scan_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    document = update.message.document

    if not document:
        await update.message.reply_text(
            "❗ Iltimos, ZIP faylni Telegram fayl sifatida yuboring."
        )
        return SCAN_FILE

    filename = document.file_name or ""

    if not filename.lower().endswith(".zip"):
        await update.message.reply_text(
            "❗ Faqat ZIP fayl qabul qilinadi."
        )
        return SCAN_FILE

    if document.file_size and document.file_size > MAX_ZIP_SIZE:
        await update.message.reply_text(
            "❗ ZIP fayl juda katta.\n"
            "Maksimal hajm: 50 MB."
        )
        return SCAN_FILE

    context.user_data["scan_file"] = document.file_id
    context.user_data["scan_name"] = filename

    context.user_data["photos"] = []

    await update.message.reply_text(
        f"✅ ZIP QABUL QILINDI!\n\n"
        f"📦 Fayl: {filename}\n\n"
        "Endi 1–4 ta bemor rasmini yuboring.",
        reply_markup=main_keyboard(),
    )

    await send_example_image(
        update,
        PATIENT_PHOTO_IMAGE,
        "📸 BEMOR FOTO NAMUNASI",
    )

    return PHOTOS


# ============================================================
# FOTO
# ============================================================

async def photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    photo_list = context.user_data.setdefault("photos", [])

    if not update.message.photo:
        await update.message.reply_text(
            "❗ Iltimos, rasm yuboring."
        )
        return PHOTOS

    if len(photo_list) >= MAX_PHOTOS:
        await update.message.reply_text(
            "✅ 4 ta rasm allaqachon qabul qilindi.\n\n"
            "Keyingi bosqichga o'tish uchun "
            "«✅ RASMLARNI TUGATISH» tugmasini bosing."
        )
        return PHOTOS

    file_id = update.message.photo[-1].file_id

    photo_list.append(file_id)

    count = len(photo_list)

    keyboard = [
        ["✅ RASMLARNI TUGATISH"],
        ["❌ BEKOR QILISH"],
    ]

    if count < MAX_PHOTOS:
        await update.message.reply_text(
            f"✅ {count}-rasm qabul qilindi.\n\n"
            f"Yana {MAX_PHOTOS - count} tagacha rasm yuborishingiz mumkin.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            ),
        )
    else:
        await update.message.reply_text(
            "✅ 4 ta rasm qabul qilindi.\n\n"
            "Endi «✅ RASMLARNI TUGATISH» tugmasini bosing.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            ),
        )

    return PHOTOS


async def finish_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    if text != "✅ RASMLARNI TUGATISH":
        await update.message.reply_text(
            "📸 Rasm yuboring yoki "
            "«✅ RASMLARNI TUGATISH» tugmasini bosing."
        )
        return PHOTOS

    photo_list = context.user_data.get("photos", [])

    if len(photo_list) < 1:
        await update.message.reply_text(
            "❗ Kamida 1 ta rasm yuboring."
        )
        return PHOTOS

    await update.message.reply_text(
        "📝 QO'SHIMCHA IZOH\n\n"
        "Qo'shimcha ma'lumot bo'lsa yozing.\n"
        "Izoh bo'lmasa «yo'q» deb yozing.",
        reply_markup=main_keyboard(),
    )

    return NOTE


# ============================================================
# NOTE
# ============================================================

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ BEKOR QILISH":
        return await cancel(update, context)

    context.user_data["note"] = text

    user = update.effective_user

    context.user_data["user_id"] = user.id
    context.user_data["username"] = (
        "@" + user.username
        if user.username
        else "Username yo'q"
    )

    data = context.user_data

    scanner_text = (
        f"✅ HA — {data.get('scan_name', '')}"
        if data.get("scanner") == "✅ HA"
        else "❌ YO'Q"
    )

    summary = (
        "📋 BUYURTMA MA'LUMOTLARI\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "👤 MIJOZ\n"
        f"Ism: {data['name']}\n"
        f"Familiya: {data['surname']}\n"
        f"Telefon: {data['phone']}\n"
        f"Username: {data['username']}\n\n"

        "🦷 BUYURTMA\n"
        f"Jinsi: {data['gender']}\n"
        f"Yoshi: {data['age']}\n"
        f"Tish rangi: {data['color']}\n"
        f"Tish raqami: {data['tooth']}\n"
        f"Ish turi: {data['work']}\n"
        f"Intraoral: {scanner_text}\n"
        f"📸 Rasmlar: {len(data.get('photos', []))} ta\n"
        f"📝 Izoh: {data['note']}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "Ma'lumotlar to'g'rimi?"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ TASDIQLASH",
                callback_data="confirm",
            ),
            InlineKeyboardButton(
                "❌ BEKOR",
                callback_data="cancel_order",
            ),
        ]
    ]

    await update.message.reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )

    return CONFIRM


# ============================================================
# TASDIQLASH
# ============================================================

async def confirm_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    if query.data == "cancel_order":
        context.user_data.clear()

        await query.edit_message_text(
            "❌ BUYURTMA BEKOR QILINDI.\n\n"
            "Qaytadan boshlash uchun /start ni bosing."
        )

        return ConversationHandler.END

    if query.data != "confirm":
        return CONFIRM

    if ADMIN_ID == 0:
        await query.message.reply_text(
            "⚠️ ADMIN_ID sozlanmagan."
        )
        return CONFIRM

    data = context.user_data

    try:
        order_code = create_order(data)

        admin_text = (
            "🚨 YANGI BUYURTMA!\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"🧾 BUYURTMA: {order_code}\n"
            f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

            "👤 MIJOZ\n"
            f"Ism: {data['name']}\n"
            f"Familiya: {data['surname']}\n"
            f"Telefon: {data['phone']}\n"
            f"Username: {data['username']}\n"
            f"Telegram ID: {data['user_id']}\n\n"

            "🦷 BUYURTMA\n"
            f"Jinsi: {data['gender']}\n"
            f"Yoshi: {data['age']}\n"
            f"Tish rangi: {data['color']}\n"
            f"Tish raqami: {data['tooth']}\n"
            f"Ish turi: {data['work']}\n"
            f"Intraoral: {data['scanner']}\n"
            f"📸 Rasmlar: {len(data.get('photos', []))} ta\n"
            f"📝 Izoh: {data['note']}\n"
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
        )

        # FOTO YUBORISH
        for index, photo_id in enumerate(
            data.get("photos", []),
            start=1,
        ):
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=f"📸 {order_code} — {index}-rasm",
            )

        # ZIP YUBORISH
        if data.get("scanner") == "✅ HA" and data.get("scan_file"):
            try:
                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=data["scan_file"],
                    caption=(
                        f"📦 {order_code} — INTRAORAL SKANER\n"
                        f"Fayl: {data['scan_name']}"
                    ),
                )
            except Exception as e:
                logger.error("ZIP yuborishda xato: %s", e)

                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"⚠️ {order_code} ZIP yuborilmadi.\n"
                        f"Fayl: {data.get('scan_name', '')}\n"
                        f"Xato: {e}"
                    ),
                )

        # ADMIN STATUS TUGMALARI
        status_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🟡 QABUL QILINDI",
                    callback_data=f"status|{order_code}|Qabul qilindi",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔵 ISHLANMOQDA",
                    callback_data=f"status|{order_code}|Ishlanmoqda",
                )
            ],
            [
                InlineKeyboardButton(
                    "🟢 TAYYOR",
                    callback_data=f"status|{order_code}|Tayyor",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔴 BEKOR",
                    callback_data=f"status|{order_code}|Bekor qilindi",
                )
            ],
        ])

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚙️ {order_code} STATUSINI TANLANG:",
            reply_markup=status_keyboard,
        )

        # MIJOZGA JAVOB
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📲 Instagram",
                    url="https://instagram.com/zarshedjamshedovich_",
                )
            ],
            [
                InlineKeyboardButton(
                    "💬 Telegram",
                    url="https://t.me/ZARSHEDJAMSHEDOVICH_567",
                )
            ],
        ])

        await query.edit_message_text(
            f"🎉 BUYURTMANGIZ QABUL QILINDI!\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🧾 Buyurtma raqami: {order_code}\n\n"
            "✅ Barcha ma'lumotlaringiz qabul qilindi.\n\n"
            "❤️ Tez orada siz bilan bog'lanamiz.\n\n"
            f"📞 Telefon: {PHONE}\n"
            f"📲 Instagram: {INSTAGRAM}\n"
            f"💬 Telegram: {TELEGRAM}",
            reply_markup=buttons,
        )

        context.user_data.clear()

        return ConversationHandler.END

    except Exception as e:
        logger.exception("Buyurtmani yuborishda xato")

        await query.message.reply_text(
            "⚠️ Buyurtmani yuborishda texnik xatolik yuz berdi.\n\n"
            "Ma'lumotlaringiz o'chirilmadi. Iltimos, "
            "birozdan keyin qayta urinib ko'ring."
        )

        return CONFIRM


# ============================================================
# ADMIN STATUS
# ============================================================

async def status_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "⛔ Siz admin emassiz.",
            show_alert=True,
        )
        return

    parts = query.data.split("|", 2)

    if len(parts) != 3:
        return

    _, order_code, status = parts

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM orders WHERE order_code = ?",
        (order_code,),
    )

    row = cur.fetchone()

    cur.execute(
        "UPDATE orders SET status = ? WHERE order_code = ?",
        (status, order_code),
    )

    conn.commit()
    conn.close()

    if not row:
        await query.message.reply_text(
            f"❗ {order_code} topilmadi."
        )
        return

    user_id = row[0]

    status_text = {
        "Qabul qilindi": "🟡 Buyurtmangiz qabul qilindi.",
        "Ishlanmoqda": "🔵 Buyurtmangiz hozir ishlab chiqilmoqda.",
        "Tayyor": "🟢 Buyurtmangiz tayyor!",
        "Bekor qilindi": "🔴 Buyurtmangiz bekor qilindi.",
    }.get(
        status,
        f"📌 Buyurtma holati: {status}",
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"🧾 BUYURTMA: {order_code}\n\n"
                f"{status_text}"
            ),
        )

        await query.message.reply_text(
            f"✅ {order_code} statusi o'zgartirildi:\n"
            f"{status}"
        )

    except Exception as e:
        logger.error("Status yuborishda xato: %s", e)

        await query.message.reply_text(
            f"⚠️ Status bazada o'zgartirildi, "
            f"lekin mijozga xabar yuborilmadi.\n\n"
            f"Sabab: {e}"
        )


# ============================================================
# ADMIN
# ============================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Sizda admin huquqi yo'q."
        )
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM orders")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'Qabul qilindi'"
    )
    accepted = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'Ishlanmoqda'"
    )
    working = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'Tayyor'"
    )
    ready = cur.fetchone()[0]

    conn.close()

    await update.message.reply_text(
        "👨‍⚕️ ZBOT ADMIN PANEL\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Jami buyurtmalar: {total}\n"
        f"🟡 Qabul qilindi: {accepted}\n"
        f"🔵 Ishlanmoqda: {working}\n"
        f"🟢 Tayyor: {ready}\n\n"
        "💰 Narx ma'lumotlari bemorga yuborilmaydi."
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update, context):
    logger.exception(
        "Telegram update xatosi:",
        exc_info=context.error,
    )


# ============================================================
# MAIN
# ============================================================

def main():
    init_db()

    if ADMIN_ID == 0:
        logger.warning(
            "ADMIN_ID hali sozlanmagan."
        )

    app = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],

        states={

            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    name_step,
                )
            ],

            SURNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    surname_step,
                )
            ],

            PHONE_STEP: [
                MessageHandler(
                    filters.CONTACT,
                    phone_step,
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    phone_step,
                ),
            ],

            GENDER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    gender,
                )
            ],

            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    age,
                )
            ],

            COLOR: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    color,
                )
            ],

            TOOTH: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    tooth,
                )
            ],

            WORK: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    work,
                )
            ],

            SCANNER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    scanner,
                )
            ],

            SCAN_FILE: [
                MessageHandler(
                    filters.Document.ALL,
                    scan_file,
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    scan_file,
                ),
            ],

            PHOTOS: [
                MessageHandler(
                    filters.PHOTO,
                    photos,
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    finish_photos,
                ),
            ],

            NOTE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    note,
                )
            ],

            CONFIRM: [
                CallbackQueryHandler(
                    confirm_callback,
                    pattern=r"^(confirm|cancel_order)$",
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
    )

    app.add_handler(conversation)

    app.add_handler(
        CallbackQueryHandler(
            status_callback,
            pattern=r"^status\|",
        )
    )

    app.add_handler(
        CommandHandler("admin", admin)
    )

    app.add_error_handler(error_handler)

    print("========================================")
    print("🦷 ZBOT DENTAL LABORATORIYA")
    print("✅ BOT ISHGA TUSHDI")
    print("📸 1–4 FOTO")
    print("📦 ZIP")
    print("💾 SQLITE")
    print("👨‍⚕️ ADMIN STATUS")
    print("========================================")

    app.run_polling()


if __name__ == "__main__":
    main()

