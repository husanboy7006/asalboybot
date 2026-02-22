# main.py — ASALBOY (aiogram v3 + WebApp) — info_full support (single "Asal haqida" button)
import os
import json
import logging
import asyncio
import sqlite3
from pathlib import Path
from contextlib import closing
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)

# ============ ENV ============
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
logging.basicConfig(level=logging.INFO)

BOT_TOKEN      = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID  = int(os.getenv("ADMIN_CHAT_ID") or 0)
ADMIN_USER_ID  = int(os.getenv("ADMIN_USER_ID") or 0)
LANG_DEFAULT   = os.getenv("LANG_DEFAULT", "uz")

APP_HOST       = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT       = int(os.getenv("PORT", os.getenv("APP_PORT", "8080")))
APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", os.getenv("WEBAPP_URL", "https://example.com/app"))

logging.info(f"ADMIN_CHAT_ID={ADMIN_CHAT_ID}")
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp  = Dispatcher(storage=MemoryStorage())


def is_admin(uid: int) -> bool:
    return bool(ADMIN_USER_ID and uid == ADMIN_USER_ID)

import hmac
import hashlib
from urllib.parse import parse_qsl

def validate_init_data(init_data: str, token: str) -> bool:
    """
    Validates the data received from the Telegram Web App.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return False

    if "hash" not in parsed_data:
        return False

    hash_from_telegram = parsed_data.pop("hash")
    
    # Sort the dictionary keys to ensure correct data-check-string creation
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )
    
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == hash_from_telegram


# ============ TRANSLATIONS ============
TR = {
    "uz": {
        "welcome": "Assalomu alaykum! <b>Asalboy</b>ga xush kelibsiz.\nKatalog uchun <b>“Katalog”</b> yoki <b>“🛒 Interaktiv menyu”</b> tugmasini bosing.",
        "menu": ["Katalog", "Savatcha", "Kontakt"],
        "contact": "<b>Kontakt</b>\n📞 +998953442020\n📲 Instagram: @asalboy_att",
        "choose_lang": "Bot tilini tanlang:",
        "uzbek": "🇺🇿 O‘zbekcha",
        "russian": "🇷🇺 Русский",
        "price_kg_only": "Narx (1 kg): <b>{price}</b> so'm",
        "no_products": "Hozircha mahsulotlar yo‘q.",
        "cart_empty": "Savatcha bo'sh.",
        "cart_total": "<b>Jami:</b> {total} so'm",
        "name_ask": "Ismingizni kiriting:",
        "name_short": "Ism juda qisqa. To‘liqroq kiriting.",
        "phone_ask": "Telefon (masalan +998901234567):",
        "phone_bad": "Telefon formati xato. Masalan: +998901234567",
        "addr_ask": "Yetkazib berish manzili:",
        "addr_short": "Manzil juda qisqa.",
        "order_ok": "✅ Buyurtmangiz qabul qilindi! Tez orada bog‘lanamiz.",
        "added": "{name} — {qty} ta (1 kg) savatchaga qo‘shildi. {price} so‘m",
        "select": "Tanlash",
        "qty": "Miqdor",
        "add_to_cart": "➕ Savatchaga",
        "back": "⬅️ Orqaga",
        "checkout": "Checkout",
        "clear_cart": "Clear cart",
        "webapp": "🛒 Interaktiv menyu",
        "phone_share": "📱 Telefon raqamingizni yuboring (tugma orqali yoki yozib):",
        "loc_ask": "📍 Iltimos, lokatsiyangizni yuboring (tugma orqali):",
        "loc_bad": "Lokatsiya olinmadi. 'Lokatsiyani yuborish' tugmasini bosing.",
        "thanks": "✅ Rahmat! Buyurtmangiz qabul qilindi.",
        "info_btn": "Asal haqida",
        # New keys for WebApp keys
        "ord_new": "🆕 WebApp buyurtma #{id}",
        "ord_from": "👤 Kimdan: {name}",
        "ord_user": "🧑‍💻 User: {user}",
        "ord_phone": "📞 Telefon: {phone}",
        "ord_addr": "🏠 Manzil: {addr}",
        "ord_items": "🛒 Mahsulotlar:",
        "ord_total": "<b>Jami:</b> {total} so'm",
        "ord_map": "\n📍 <a href='{link}'>Google Xarita</a>",
        "ord_received": "✅ WebApp orqali buyurtma qabul qilindi. Rahmat!",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в <b>Asalboy</b>.",
        "menu": ["Каталог", "Корзина", "Контакт"],
        "contact": "<b>Контакты</b>\n📞 +998953442020\n📲 Instagram: @asalboy_att",
        "choose_lang": "Выберите язык:",
        "uzbek": "🇺🇿 Узбекский",
        "russian": "🇷🇺 Русский",
        "price_kg_only": "Цена (1 кг): <b>{price}</b> сум",
        "no_products": "Пока нет товаров.",
        "cart_empty": "Корзина пустая.",
        "cart_total": "<b>Итого:</b> {total} сум",
        "name_ask": "Введите имя:",
        "name_short": "Имя слишком короткое.",
        "phone_ask": "Введите телефон (например +998901234567):",
        "phone_bad": "Неверный формат телефона.",
        "addr_ask": "Адрес доставки:",
        "addr_short": "Адрес слишком короткий.",
        "order_ok": "✅ Заказ принят! Мы скоро свяжемся.",
        "added": "{name} — {qty} шт (1 кг) добавлен. {price} сум",
        "select": "Выбрать",
        "qty": "Кол-во",
        "add_to_cart": "➕ В корзину",
        "back": "⬅️ Назад",
        "checkout": "Оформить",
        "clear_cart": "Очистить",
        "webapp": "🛒 Интерактивное меню",
        "phone_share": "📱 Отправьте номер телефона (кнопкой или текстом):",
        "loc_ask": "📍 Отправьте вашу геолокацию (кнопкой):",
        "loc_bad": "Геолокация не получена.",
        "thanks": "✅ Спасибо! Заказ принят.",
        "info_btn": "О мёде",
        # New keys for WebApp keys
        "ord_new": "🆕 Заказ WebApp #{id}",
        "ord_from": "👤 От: {name}",
        "ord_user": "🧑‍💻 User: {user}",
        "ord_phone": "📞 Телефон: {phone}",
        "ord_addr": "🏠 Адрес: {addr}",
        "ord_items": "🛒 Товары:",
        "ord_total": "<b>Итого:</b> {total} сум",
        "ord_map": "\n📍 <a href='{link}'>Google Maps</a>",
        "ord_received": "✅ Заказ через WebApp принят. Спасибо!",
    }
}


def t(lang, key, **kw):
    lang = lang if lang in TR else "uz"
    s = TR[lang].get(key, "")
    return s.format(**kw) if kw else s


# ============ DB ============
DB_PATH = "data/orders.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, user_name TEXT, phone TEXT, address TEXT,
            cart_json TEXT, total INTEGER, created_at TEXT,
            lat REAL, lon REAL
        )"""
        )
        con.commit()


init_db()

# ============ PRODUCTS ============
PRODUCTS_FILE = "products.json"


def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Ensure info fields exist (fallback to empty strings)
    for p in data:
        if "info_short" not in p:
            p["info_short"] = ""
        if "info_full" not in p:
            p["info_full"] = ""
    return data


products = load_products()

# PRODUCT_INFO mapping (for quick access)
PRODUCT_INFO: Dict[str, Dict[str, str]] = {}
for p in products:
    pid = str(p.get("id"))
    PRODUCT_INFO[pid] = {
        "short": p.get("info_short", "") or "",
        "full": p.get("info_full", "") or "",
        "name_uz": p.get("name_uz") or "",
        "name_ru": p.get("name_ru") or "",
    }

logging.info("Loaded products: %d", len(products))


def find_product(pid) -> Optional[Dict[str, Any]]:
    pid = str(pid)
    for p in products:
        if str(p.get("id")) == pid:
            return p
    return None


def unit_price_1kg(p: Dict[str, Any]) -> int:
    if p.get("price_per_kg") is not None:
        return int(float(p["price_per_kg"]))
    if p.get("price_1") is not None:
        return int(float(p["price_1"]))
    return 0


# ============ STATES ============
class AdminAddProduct(StatesGroup):
    waiting_photo = State()
    waiting_name_uz = State()
    waiting_desc_uz = State()
    waiting_price = State()


class ClassicCheckout(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()


class QuickCheckout(StatesGroup):
    waiting_phone = State()
    waiting_location = State()


# ============ KEYBOARDS ============
def main_kb(lang="uz") -> ReplyKeyboardMarkup:
    labels = TR[lang]["menu"] if lang in TR else TR["uz"]["menu"]
    # App URL with language query param
    web_url = f"{APP_PUBLIC_URL}?lang={lang}"
    
    kb_rows = [
        # [KeyboardButton(text=labels[0])],  <-- Removed Katalog
        [KeyboardButton(text=labels[1])],
        [KeyboardButton(text=labels[2])],
        [KeyboardButton(text=t(lang, "webapp"), web_app=WebAppInfo(url=web_url))],
    ]
    return ReplyKeyboardMarkup(keyboard=kb_rows, resize_keyboard=True)


def lang_select_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=TR["uz"]["uzbek"], callback_data="lang:uz")],
            [InlineKeyboardButton(text=TR["ru"]["russian"], callback_data="lang:ru")],
        ]
    )


def product_inline_kb(pid: str, lang: str) -> InlineKeyboardMarkup:
    """
    Inline keyboard for product: Select + Asal haqida
    - second button callback will be "info:{pid}" and handler will send full info
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "select"), callback_data=f"sel:{pid}"),
                InlineKeyboardButton(text=t(lang, "info_btn"), callback_data=f"info:{pid}")
            ]
        ]
    )


def selection_menu_kb(pid: str, qty: int, lang: str) -> InlineKeyboardMarkup:
    qbtn = InlineKeyboardButton(text=f"{t(lang,'qty')}: {qty}", callback_data="noop")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="−", callback_data=f"qdec:{pid}:{qty}"),
                qbtn,
                InlineKeyboardButton(text="+", callback_data=f"qinc:{pid}:{qty}"),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "add_to_cart"),
                    callback_data=f"addsel:{pid}:{qty}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"back:{pid}")],
        ]
    )


def cart_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "checkout"), callback_data="checkout")],
            [
                InlineKeyboardButton(
                    text=t(lang, "clear_cart"), callback_data="clear_cart"
                )
            ],
        ]
    )


def share_phone_kb(lang: str) -> ReplyKeyboardMarkup:
    label = "📱 Telefonni yuborish" if lang == "uz" else "📱 Отправить телефон"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label, request_contact=True)]],
        resize_keyboard=True,
    )


def share_location_kb(lang: str) -> ReplyKeyboardMarkup:
    label = (
        "📍 Lokatsiyani yuborish"
        if lang == "uz"
        else "📍 Отправить локацию"
    )
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label, request_location=True)]],
        resize_keyboard=True,
    )


# ============ HELPERS ============
PHONE_RE =  r"^\+?\d{9,15}$"
import re as _re
PHONE_RE = _re.compile(PHONE_RE)


def get_lang(sd: dict) -> str:
    return sd.get("lang") or LANG_DEFAULT or "uz"


def save_order_to_db(
    user_id,
    name,
    phone,
    address,
    cart,
    total,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> int:
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO orders (user_id,user_name,phone,address,cart_json,total,created_at,lat,lon) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                user_id,
                name,
                phone,
                address,
                json.dumps(cart, ensure_ascii=False),
                total,
                datetime.utcnow().isoformat(),
                lat,
                lon,
            ),
        )
        con.commit()
        return cur.lastrowid


# ============ COMMON UTILS ============
@dp.message(Command("whoami"))
async def whoami(message: Message):
    await message.answer(
        f"🆔 user_id: <code>{message.from_user.id}</code>\n"
        f"👥 chat_id: <code>{message.chat.id}</code>\n"
        f"⚙️ ADMIN_CHAT_ID: <code>{ADMIN_CHAT_ID}</code>"
    )


@dp.message(Command("testadmin"))
async def testadmin(message: Message):
    try:
        await bot.send_message(ADMIN_CHAT_ID, "✅ Admin chat sinovi")
        await message.answer("Yuborildi.")
    except Exception as e:
        await message.answer(f"❌ Yuborilmadi: {e}")


# ============ HANDLERS ============
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(t("uz", "choose_lang"), reply_markup=lang_select_kb())


@dp.callback_query(F.data.startswith("lang:"))
async def set_lang(callback: types.CallbackQuery, state: FSMContext):
    _, lang = callback.data.split(":")
    await state.update_data(lang=lang)
    await callback.answer("OK")
    await callback.message.answer(t(lang, "welcome"), reply_markup=main_kb(lang))


@dp.message(F.text.lower().in_(["kontakt", "контакт"]))
async def contact_info(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    await message.answer(t(lang, "contact"))


@dp.message(F.text.lower().in_(["katalog", "каталог"]))
async def show_catalog(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    if not products:
        await message.answer(t(lang, "no_products"))
        return
    for p in products:
        if p.get("available") is False:
            continue
        name = (
            p.get("name_uz", "Nomsiz")
            if lang == "uz"
            else p.get("name_ru", "Без названия")
        )
        desc = p.get("desc_uz") if lang == "uz" else p.get("desc_ru")
        desc = desc or ""
        price_text = t(lang, "price_kg_only", price=unit_price_1kg(p))
        caption = f"<b>{html.quote(name)}</b>\n{html.quote(desc)}\n\n{price_text}"
        photo = (
            p.get("photo_file_id")
            or p.get("photo")
            or p.get("photo_url")
            or "https://via.placeholder.com/600x400?text=Asal"
        )
        kb = product_inline_kb(str(p.get("id")), lang)
        try:
            # if photo looks like a file_id (telegram file id), use answer_photo with file_id
            await message.answer_photo(photo, caption=caption, reply_markup=kb)
        except Exception:
            # fallback to plain text
            await message.answer(caption, reply_markup=kb)
        await asyncio.sleep(0.03)


# ====== INFO CALLBACK: single-step (Asal haqida => full info) ======
@dp.callback_query(F.data.startswith("info:"))
async def show_info_full(callback: types.CallbackQuery, state: FSMContext):
    """
    When user presses "Asal haqida", send full info (info_full).
    Fallback: try info_short, desc_uz/desc_ru, or default message.
    """
    s = await state.get_data()
    lang = get_lang(s)
    _, pid = callback.data.split(":")
    await callback.answer()
    info = PRODUCT_INFO.get(pid, {})
    full = info.get("full") or ""
    if not full:
        # fallback to product fields
        p = find_product(pid)
        if p:
            # prefer info_short if full not available
            full = (p.get("info_full") or p.get("info_short") or p.get("desc_uz") or p.get("desc_ru")) or ""
    if not full:
        full = "Ma'lumot mavjud emas."
    # Send full info as a message (may be long)
    await callback.message.answer(full)


# ====== EXISTING CALLBACKS (selection, qty, add to cart, back) ======
@dp.callback_query(F.data.startswith("sel:"))
async def select_qty(callback: types.CallbackQuery, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    _, pid = callback.data.split(":")
    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=selection_menu_kb(pid, 1, lang)
    )


def clamp(q: int) -> int:
    return max(1, min(99, q))


@dp.callback_query(F.data.startswith("qinc:"))
async def qty_inc(callback: types.CallbackQuery, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    _, pid, raw = callback.data.split(":")
    qty = clamp(int(raw) + 1)
    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=selection_menu_kb(pid, qty, lang)
    )


@dp.callback_query(F.data.startswith("qdec:"))
async def qty_dec(callback: types.CallbackQuery, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    _, pid, raw = callback.data.split(":")
    qty = clamp(int(raw) - 1)
    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=selection_menu_kb(pid, qty, lang)
    )


@dp.callback_query(F.data.startswith("addsel:"))
async def add_selected(callback: types.CallbackQuery, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    _, pid, raw = callback.data.split(":")
    qty = clamp(int(raw))
    p = find_product(pid)
    if not p:
        await callback.answer("Not found")
        return
    one = unit_price_1kg(p)
    total = one * qty
    cart = s.get("cart", [])
    cart.append(
        {
            "product_id": str(p.get("id")),
            "name": p.get("name_uz") if lang == "uz" else p.get("name_ru"),
            "kg": 1.0,
            "qty": qty,
            "unit_price": one,
            "price": total,
        }
    )
    await state.update_data(cart=cart)
    await callback.answer("OK")
    await callback.message.answer(
        t(
            lang,
            "added",
            name=p.get("name_uz") if lang == "uz" else p.get("name_ru"),
            qty=qty,
            price=total,
        )
    )
    # Tezkor checkoutni boshlash: telefon so'raymiz
    await callback.message.answer(
        t(lang, "phone_share"), reply_markup=share_phone_kb(lang)
    )
    await state.set_state(QuickCheckout.waiting_phone)


@dp.callback_query(F.data.startswith("back:"))
async def back_to_card(callback: types.CallbackQuery, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    _, pid = callback.data.split(":")
    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=product_inline_kb(pid, lang)
    )


@dp.message(F.text.lower().in_(["savatcha", "корзина"]))
async def show_cart(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    cart = s.get("cart", [])
    if not cart:
        await message.answer(t(lang, "cart_empty"))
        return
    total = sum(i["price"] for i in cart)
    rows = []
    for i, it in enumerate(cart, 1):
        rows.append(
            f"{i}. {it['name']} — 1 kg x{it.get('qty',1)} — {it['price']} so'm"
        )
    text = "\n".join(rows) + f"\n\n{t(lang,'cart_total', total=total)}"
    await message.answer(text, reply_markup=cart_kb(lang))


@dp.callback_query(F.data == "clear_cart")
async def clear_cart_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart=[])
    await callback.message.answer("OK")


# ====== KLASSIK CHECKOUT (optional) ======
@dp.callback_query(F.data == "checkout")
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    cart = s.get("cart", [])
    if not cart:
        await callback.message.answer(t(lang, "cart_empty"))
        return
    await callback.message.answer(t(lang, "name_ask"))
    await state.set_state(ClassicCheckout.waiting_name)


@dp.message(StateFilter(ClassicCheckout.waiting_name))
async def cs_name(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(t(lang, "name_short"))
        return
    await state.update_data(checkout_name=name)
    await message.answer(t(lang, "phone_ask"))
    await state.set_state(ClassicCheckout.waiting_phone)


@dp.message(StateFilter(ClassicCheckout.waiting_phone))
async def cs_phone(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    phone = (message.text or "").strip()
    if not PHONE_RE.match(phone):
        await message.answer(t(lang, "phone_bad"))
        return
    await state.update_data(checkout_phone=phone)
    await message.answer(t(lang, "addr_ask"))
    await state.set_state(ClassicCheckout.waiting_address)


@dp.message(StateFilter(ClassicCheckout.waiting_address))
async def cs_addr(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer(t(lang, "addr_short"))
        return
    data = await state.get_data()
    name = data.get("checkout_name")
    phone = data.get("checkout_phone")
    cart = data.get("cart", [])
    total = sum(i["price"] for i in cart)
    order_id = save_order_to_db(
        message.from_user.id, name, phone, address, cart, total
    )

    txt = (
        f"🆕 Buyurtma #{order_id}\n"
        f"👤 From: {name}\n"
        f"🧑‍💻 User: @{message.from_user.username or 'N/A'} ({message.from_user.id})\n"
        f"📞 Phone: {phone}\n"
        f"🏠 Address: {address}\n\n🛒 Items:\n"
    )
    for it in cart:
        txt += (
            f"• {it['name']} — 1 kg x{it.get('qty',1)} — {it['price']} so'm\n"
        )
    txt += f"\n<b>Jami:</b> {total} so'm"
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID, txt)
        except Exception:
            logging.exception("Adminga yuborilmadi (klassik)")
    await message.answer(t(lang, "order_ok"))
    await state.update_data(cart=[])
    await state.clear()


# ====== TEZKOR CHECKOUT: Telefon → Geo ======
@dp.message(StateFilter(QuickCheckout.waiting_phone))
async def qc_phone(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    if message.contact:
        phone = (message.contact.phone_number or "").strip()
        name = (
            (message.contact.first_name or "")
            + (" " + (message.contact.last_name or "")).rstrip()
        )
        name = name.strip() or (message.from_user.full_name or "")
    else:
        raw = (message.text or "").strip()
        if not PHONE_RE.match(raw):
            await message.answer(t(lang, "phone_bad"))
            return
        phone = raw
        name = message.from_user.full_name or ""
    await state.update_data(qc_phone=phone, qc_name=name)
    await message.answer(
        t(lang, "loc_ask"), reply_markup=share_location_kb(lang)
    )
    await state.set_state(QuickCheckout.waiting_location)


@dp.message(StateFilter(QuickCheckout.waiting_location))
async def qc_location(message: Message, state: FSMContext):
    s = await state.get_data()
    lang = get_lang(s)
    if not message.location:
        await message.answer(
            t(lang, "loc_bad"), reply_markup=share_location_kb(lang)
        )
        return
    lat, lon = message.location.latitude, message.location.longitude
    cart = s.get("cart", [])
    if not cart:
        await message.answer(t(lang, "cart_empty"))
        await state.clear()
        return
    total = sum(i["price"] for i in cart)
    name = s.get("qc_name") or (message.from_user.full_name or "")
    phone = s.get("qc_phone") or ""
    address = f"geo:{lat},{lon}"
    order_id = save_order_to_db(
        message.from_user.id, name, phone, address, cart, total, lat, lon
    )

    link = f"https://maps.google.com/?q={lat},{lon}"
    txt = (
        f"🆕 Quick buyurtma #{order_id}\n"
        f"👤 From: {name}\n"
        f"🧑‍💻 User: @{message.from_user.username or 'N/A'} ({message.from_user.id})\n"
        f"📞 Phone: {phone}\n"
        f"📍 Geo: {lat:.6f}, {lon:.6f}\n{link}\n\n🛒 Items:\n"
    )
    for it in cart:
        txt += (
            f"• {it['name']} — 1 kg x{it['qty']} — {it['price']} so'm\n"
        )
    txt += f"\n<b>Jami:</b> {total} so'm"

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                ADMIN_CHAT_ID, txt, disable_web_page_preview=True
            )
            await bot.send_location(
                ADMIN_CHAT_ID, latitude=lat, longitude=lon
            )  # jonli pin
        except Exception:
            logging.exception("Adminga yuborilmadi (quick)")

    await message.answer(t(lang, "thanks"), reply_markup=main_kb(lang))
    await state.update_data(cart=[])
    await state.clear()


# ====== ADMIN: addproduct ======
@dp.message(Command("addproduct"))
async def addproduct(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.reply("Siz admin emassiz.")
    await message.reply("🖼 Rasm yuboring (photo yoki URL):")
    await state.set_state(AdminAddProduct.waiting_photo)


@dp.message(StateFilter(AdminAddProduct.waiting_photo))
async def ap1(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(photo=message.photo[-1].file_id)
    else:
        await state.update_data(photo=(message.text or "").strip())
    await message.answer("📝 Nomi (o‘zbekcha):")
    await state.set_state(AdminAddProduct.waiting_name_uz)


@dp.message(StateFilter(AdminAddProduct.waiting_name_uz))
async def ap2(message: Message, state: FSMContext):
    await state.update_data(name_uz=(message.text or "").strip())
    await message.answer("✍️ Ta’rif (o‘zbekcha), ixtiyoriy:")
    await state.set_state(AdminAddProduct.waiting_desc_uz)


@dp.message(StateFilter(AdminAddProduct.waiting_desc_uz))
async def ap3(message: Message, state: FSMContext):
    await state.update_data(desc_uz=(message.text or "").strip())
    await message.answer(
        "💰 Narx (1 kg, so‘m) — faqat son, masalan 350000"
    )
    await state.set_state(AdminAddProduct.waiting_price)


@dp.message(StateFilter(AdminAddProduct.waiting_price))
async def ap4(message: Message, state: FSMContext):
    try:
        price = int((message.text or "").strip())
    except Exception:
        return await message.answer(
            "Faqat son kiriting (masalan 350000)."
        )
    d = await state.get_data()
    ids = [str(p.get("id")) for p in products]
    N = 1
    while f"p{N}" in ids:
        N += 1
    new_id = f"p{N}"
    prod = {
        "id": new_id,
        "name_uz": d.get("name_uz") or "Nomsiz",
        "name_ru": d.get("name_uz") or "Без названия",
        "desc_uz": d.get("desc_uz") or "",
        "desc_ru": d.get("desc_uz") or "",
        "price_1": price,
        "photo": d.get("photo"),
        "available": True,
        "info_short": d.get("desc_uz") or "",
        "info_full": d.get("desc_uz") or "",
    }
    products.append(prod)
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    # update PRODUCT_INFO map
    PRODUCT_INFO[new_id] = {
        "short": prod["info_short"],
        "full": prod["info_full"],
        "name_uz": prod.get("name_uz",""),
        "name_ru": prod.get("name_ru",""),
    }
    await message.answer(
        f"✅ Qo‘shildi: <b>{html.quote(prod['name_uz'])}</b> (1 kg: {price} so‘m)\nID: {new_id}"
    )
    await state.clear()


@dp.message(Command("listorders"))
async def listorders(message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("Siz admin emassiz.")
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.cursor()
        cur.execute(
            "SELECT id,user_name,phone,total,created_at,lat,lon "
            "FROM orders ORDER BY id DESC LIMIT 20"
        )
        rows = cur.fetchall()
    if not rows:
        return await message.answer("Buyurtma yo‘q.")

    def line(r):
        _id, uname, phone, total, ts, lat, lon = r
        geo = (
            f" ({lat:.5f},{lon:.5f})"
            if (lat is not None and lon is not None)
            else ""
        )
        return f"#{_id} — {uname} — {phone} — {total} — {ts}{geo}"

    await message.answer(
        "🧾 So‘nggi buyurtmalar:\n" + "\n".join([line(r) for r in rows])
    )


@dp.message(F.photo)
async def on_photo_upload_debug(message: Message):
    # Bu vaqtincha barcha rasmlarni ushlaydi va IDni ko'rsatadi
    if message.caption and message.caption.startswith("p"):
        product_id = message.caption.strip()
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        
        # Admin tekshiruvini vaqtincha olib tashlaymiz (yoki log qilamiz)
        logging.info(f"Rasm keldi: {message.from_user.id} -> {product_id}")
        
        save_path = os.path.join("webapp", "img", f"{product_id}.jpg")
        await bot.download_file(file_info.file_path, save_path)
        await message.answer(f"✅ Rasm saqlandi: <b>{product_id}.jpg</b> (Admin check skipped)")
    else:
         await message.answer(f"⚠️ Iltimos, rasm izohiga mahsulot ID sini yozing (masalan: p1).\nSizning ID: {message.from_user.id}")


# ====== WEBAPP (AIOHTTP) ======
webapp = web.Application()


async def api_products(request: web.Request):
    return web.json_response({"items": products})


async def api_order(request: web.Request):
    """
    Handles order checkout directly from the WebApp via fetch().
    Expects JSON payload with initData and order details.
    """
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)

    init_data = payload.get("initData")
    if not init_data or not validate_init_data(init_data, BOT_TOKEN):
        return web.json_response({"success": False, "error": "Invalid initData"}, status=401)

    # Decode initData to find user
    from urllib.parse import parse_qsl
    parsed_data = dict(parse_qsl(init_data))
    user_str = parsed_data.get("user")
    
    user_info = {}
    if user_str:
        user_info = json.loads(user_str)
    
    user_id = user_info.get("id", 0)
    username = user_info.get("username", "")
    lang = user_info.get("language_code", "uz")
    
    cart = []
    total = 0
    for it in payload.get("items", []):
        p = find_product(it.get("id"))
        if not p:
            continue
        qty = int(it.get("qty", 1))
        one = unit_price_1kg(p)
        price = one * qty
        p_name = p.get("name_uz") if lang == "uz" else p.get("name_ru")
        p_name = p_name or p.get("name_uz") or "Nomsiz"

        cart.append({
            "product_id": str(p["id"]),
            "name": p_name,
            "kg": 1.0,
            "qty": qty,
            "unit_price": one,
            "price": price,
        })
        total += price
        
    name = payload.get("name", "")
    phone = payload.get("phone", "")
    address = payload.get("address", "")
    lat = payload.get("lat")
    lon = payload.get("lon")
    
    order_id = save_order_to_db(user_id, name, phone, address, cart, total, lat=lat, lon=lon)
    
    maps_link = ""
    if lat and lon:
        link_url = f"https://www.google.com/maps?q={lat},{lon}"
        maps_link = f"\n📍 <a href='{link_url}'>Google Xarita</a>"

    user_handle = f"@{username}" if username else "N/A"
    
    txt = (
        f"🆕 WebApp buyurtma #{order_id}\n"
        f"👤 Kimdan: {html.quote(name)}\n"
        f"🧑‍💻 User: {user_handle} ({user_id})\n"
        f"📞 Telefon: {html.quote(phone)}\n"
        f"🏠 Manzil: {html.quote(address)}{maps_link}\n\n"
        f"🛒 Mahsulotlar:\n"
    )
    for it in cart:
        txt += f"• {it['name']} — 1 kg x{it['qty']} — {it['price']} \n"
    txt += f"\nJami: {total} so'm"
    
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID, txt, disable_web_page_preview=True)
            if lat and lon:
                await bot.send_location(ADMIN_CHAT_ID, latitude=lat, longitude=lon)
        except Exception:
            logging.exception("Adminga yuborilmadi (webapp fetch)")
            
    # Send confirmation to user
    try:
        await bot.send_message(user_id, f"✅ Buyurtmangiz qabul qilindi! ID: #{order_id}\nTez orada bog'lanamiz.")
    except Exception:
        pass # User hasn't started the bot or blocked it
        
    return web.json_response({"success": True, "order_id": order_id})


async def app_index(request: web.Request):
    print(f"📥 REQUEST: {request.path}")
    return web.FileResponse(path=os.path.join("webapp", "index.html"))


async def style_css(request: web.Request):
    return web.FileResponse(os.path.join("webapp", "style.css"))


async def script_js(request: web.Request):
    return web.FileResponse(os.path.join("webapp", "script.js"))


async def get_telegram_image(request: web.Request):
    file_id = request.match_info.get("file_id")
    if not file_id:
        return web.Response(status=404)

    try:
        # 1. Get file_path from Telegram API
        f_info = await bot.get_file(file_id)
        if not f_info or not f_info.file_path:
            logging.error(f"❌ FILE NOT FOUND: {file_id}")
            return web.Response(status=404)
            
        file_path = f_info.file_path
        
        # 2. Download content from Telegram file server
        url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return web.Response(body=data, content_type="image/jpeg")
                else:
                    logging.error(f"❌ DOWNLOAD FAILED {resp.status}: {url}")
                    return web.Response(status=resp.status)
    except Exception as e:
        logging.exception(f"❌ PROXY EXCEPTION for {file_id}: {e}")
        return web.Response(status=500)


webapp.router.add_get("/api/products", api_products)
webapp.router.add_post("/api/order", api_order)
webapp.router.add_get("/app", app_index)
webapp.router.add_get("/style.css", style_css)
webapp.router.add_get("/script.js", script_js)
# Dynamic image proxy route
webapp.router.add_get("/images/{file_id}", get_telegram_image)
webapp.router.add_static("/webapp/", path="webapp", name="static")


async def start_servers():
    runner = web.AppRunner(webapp)
    await runner.setup()
    site = web.TCPSite(runner, APP_HOST, APP_PORT)
    await site.start()
    logging.info(f"WebApp started on http://{APP_HOST}:{APP_PORT}")


# ====== WEBAPP callback: Telegram.WebApp.sendData(JSON) ======
@dp.message(F.web_app_data)
async def on_webapp_data(message: Message, state: FSMContext):
    try:
        payload = json.loads(message.web_app_data.data)
    except Exception:
        return await message.answer("Error parsing data.")
    
    # Get user language
    s = await state.get_data()
    lang = get_lang(s)

    cart = []
    total = 0
    for it in payload.get("items", []):
        p = find_product(it.get("id"))
        if not p:
            continue
        qty = int(it.get("qty", 1))
        one = unit_price_1kg(p)
        price = one * qty
        # Choose name based on language
        p_name = p.get("name_uz") if lang == "uz" else p.get("name_ru")
        p_name = p_name or p.get("name_uz") or "Nomsiz"

        cart.append(
            {
                "product_id": str(p["id"]),
                "name": p_name,
                "kg": 1.0,
                "qty": qty,
                "unit_price": one,
                "price": price,
            }
        )
        total += price
    name = payload.get("name", "")
    phone = payload.get("phone", "")
    address = payload.get("address", "")
    lat = payload.get("lat")
    lon = payload.get("lon")
    
    order_id = save_order_to_db(
        message.from_user.id, name, phone, address, cart, total, lat=lat, lon=lon
    )
    
    maps_link = ""
    if lat and lon:
        link_url = f"https://www.google.com/maps?q={lat},{lon}"
        maps_link = t(lang, "ord_map", link=link_url)

    # Build msg using translations
    user_handle = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    
    txt = (
        f"{t(lang, 'ord_new', id=order_id)}\n"
        f"{t(lang, 'ord_from', name=html.quote(name))}\n"
        f"{t(lang, 'ord_user', user=f'{user_handle} ({message.from_user.id})')}\n"
        f"{t(lang, 'ord_phone', phone=html.quote(phone))}\n"
        f"{t(lang, 'ord_addr', addr=html.quote(address))}{maps_link}\n\n"
        f"{t(lang, 'ord_items')}\n"
    )
    for it in cart:
        txt += (
            f"• {it['name']} — 1 kg x{it['qty']} — {it['price']} \n"
        )
    # Total
    # Note: t() returns string. We can just append.
    # We used 'so\'m' in translation, but here let's stick to formatted string if needed or translation
    # The translation key "ord_total" already has {total} placeholder
    txt += f"\n{t(lang, 'ord_total', total=total)}"
    
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID, txt, disable_web_page_preview=True)
            if lat and lon:
                await bot.send_location(ADMIN_CHAT_ID, latitude=lat, longitude=lon)
        except Exception:
            logging.exception("Adminga yuborilmadi (webapp)")
    
    await message.answer(t(lang, "ord_received"))


# ====== RUN ======
if __name__ == "__main__":
    import sys

    try:
        if sys.platform != "win32":
            import uvloop
            uvloop.install()
    except Exception as e:
        logging.warning("uvloop o‘rnatilmadi: %s", e)
    async def handle_webhook(request):
        url = str(request.url)
        # Check secret token if needed, or just process
        try:
            update_data = await request.json()
            update = types.Update(**update_data)
            await dp.feed_update(bot, update)
            return web.Response(text="OK")
        except Exception as e:
            logging.error(f"Webhook error: {e}")
            return web.Response(status=500)

    async def main():
        # Setup Environment
        WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
        # Clean URL construction
        base_url = APP_PUBLIC_URL.rstrip("/app").rstrip("/")
        if not base_url.startswith("http"):
             base_url = "https://" + base_url # fallback
        WEBHOOK_URL = base_url + WEBHOOK_PATH

        # 1. Start Server manually
        app = webapp
        app.router.add_post(WEBHOOK_PATH, handle_webhook)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, APP_HOST, APP_PORT)
        await site.start()
        logging.info(f"✅ Server started on http://{APP_HOST}:{APP_PORT}")

        # 2. Set Webhook securely
        try:
            # Delete old webhook first
            await bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(1)
            # Set new webhook
            await bot.set_webhook(WEBHOOK_URL)
            logging.info(f"✅ Webhook set: {WEBHOOK_URL}")
        except Exception as e:
            logging.error(f"❌ Webhook setting failed: {e}")

        # 3. Notify Admin
        if ADMIN_CHAT_ID:
            try:
                await bot.send_message(ADMIN_CHAT_ID, f"🚀 Bot (Manual Webhook) ishga tushdi!\n{APP_PUBLIC_URL}")
            except Exception:
                pass

        # 4. Keep alive
        await asyncio.Event().wait()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
