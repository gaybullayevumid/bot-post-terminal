import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from asyncio import run
import psycopg2
import pandas as pd

BOT_TOKEN = "7769778979:AAFNG8nuj0m2rbWbJFHz8Jb2-FHS_Bv5qIc"
DB_CONFIG = {"dbname": "avtolider", "user": "postgres", "password": "8505", "host": "localhost", "port": "5432"}

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

months = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

keyboards = {
    "main": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Регистрация")]],
        resize_keyboard=True
    ),
    "months": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=m) for m in months[i:i+3]] for i in range(0, 12, 3)
        ] + [[KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    ),
    "registration_complete": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Накладные")],
            [
                KeyboardButton(text="📊Акт Сверка (СУМ)"),
                KeyboardButton(text="📊Акт Сверка (USD)"),
                KeyboardButton(text="☎️Контакты")
            ],
            [KeyboardButton(text="📜О компании")]
            ],
        resize_keyboard=True
    ),
    "request_contact": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True
    ),
}

def export_to_excel(month_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        month_index = months.index(month_name) + 1
        cursor.execute(
            "SELECT * FROM base_product WHERE EXTRACT(MONTH FROM created_at) = %s",
            [month_index]
        )
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        if data:
            df = pd.DataFrame(data, columns=["ID", "Description", "Amount", "Price", "CreatedAt", "Month", "TotalAmount"])
            
            if "CreatedAt" in df.columns:
                df["CreatedAt"] = pd.to_datetime(df["CreatedAt"]).dt.tz_localize(None)

            file_path = f"накладные_{month_name.lower()}.xlsx"
            df.to_excel(file_path, index=False)
            return file_path
        return None
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return None

async def menu_handler(message: Message):
    if message.text == "Регистрация":
        await message.answer("Пожалуйста, отправьте свой номер телефона.", reply_markup=keyboards["request_contact"])
    elif message.text == "Накладные":
        await message.answer("Выберите месяц:", reply_markup=keyboards["months"])
    elif message.text == "Главное меню":
        await message.answer("Выберите действие:", reply_markup=keyboards["registration_complete"])

async def handle_contact(message: Message):
    if message.contact:
        phone_number = message.contact.phone_number
        await message.answer(f"Ваш номер телефона: {phone_number} зарегистрирован.", reply_markup=keyboards["registration_complete"])

async def month_handler(message: Message):
    file_path = export_to_excel(message.text)
    if file_path:
        await message.answer_document(document=FSInputFile(file_path))
        os.remove(file_path)
    else:
        await message.reply("Произошла ошибка при экспорте данных.")

async def help_handler(message: Message):
    await message.answer(
        "Это бот для регистрации и экспорта данных.\n"
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Получить помощь\n"
        "Вы также можете использовать кнопки для взаимодействия."
    )

async def start():
    await bot.set_my_commands([
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Помощь!")
    ])

    dp.message.register(
        lambda msg: msg.answer("Добро пожаловать!", reply_markup=keyboards["main"]),
        Command("start")
    )
    dp.message.register(help_handler, Command("help"))  # Qo'shimcha: /help komandasi ro'yxatga olindi
    dp.message.register(menu_handler, F.text.in_(["Накладные", "Главное меню", "Регистрация"]))
    dp.message.register(handle_contact, F.contact)
    dp.message.register(month_handler, F.text.in_(months))

    await dp.start_polling(bot)

if __name__ == "__main__":
    run(start())
