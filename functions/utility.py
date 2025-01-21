from aiogram.types import Message, ReplyKeyboardRemove
from keyboards.default.menu_keyboard import *
from utils.db_api.postgresql import owner_phone
import openpyxl
import psycopg2
from data.config import DB_CONFIG
# from utils.db_api.postgresql import add_user


# menu_handler funksiyasi
async def menu_handler(message: Message):
    if message.text == "Накладные":
        await message.answer("Выберите месяц:", reply_markup=delivery_notes)
    elif message.text == "Главное меню":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
    else:
        await message.answer("Ошибка!", reply_markup=main_keyboard)

async def ask_phone_number(message: Message):
    if message.text == "☎️Контакты":
        await message.answer("Telefon raqamingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Ошибка!", reply_markup=main_keyboard)

async def handle_phone_number(message: Message):
    phone_number = message.text.strip()
    if phone_number.startswith("+998") and len(phone_number) == 13 and phone_number[1:].isdigit():
        # Telefon raqamini bazaga saqlash
        owner_phone(phone_number)
        await message.reply("Telefon raqamingiz saqlandi! Rahmat!", reply_markup=main_keyboard)
    else:
        # Noto'g'ri format bo'lsa, qayta so'rash
        await message.reply("Noto'g'ri format! Iltimos, telefon raqamingizni +998YYXXXXXXX shaklida kiriting.")