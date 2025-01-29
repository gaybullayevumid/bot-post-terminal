import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from asyncio import run
import psycopg2
import pandas as pd
import django
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from base.models import Company

BOT_TOKEN = "7769778979:AAFNG8nuj0m2rbWbJFHz8Jb2-FHS_Bv5qIc"
DB_CONFIG = {"dbname": "avtolider", "user": "postgres", "password": "8505", "host": "localhost", "port": "5432"}

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

months = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

keyboards = {
    "main": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Регистрация"), KeyboardButton(text="Накладные")],
                  [KeyboardButton(text="📊Акт Сверка (СУМ)"), KeyboardButton(text="📊Акт Сверка (USD)"), KeyboardButton(text="☎️Контакты")],
                  [KeyboardButton(text="📜О компании")]],
        resize_keyboard=True
    ),
    "months": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=m) for m in months[i:i + 3]] for i in range(0, 12, 3)] + [[KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    ),
    "request_contact": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True
    ),
}

@sync_to_async
def export_to_excel(month_name, phone_number):
    try:
        logging.info(f"Exporting data for month: {month_name} and phone number: {phone_number}")

        month_index = months.index(month_name) + 1

        # Django ORM orqali so‘rov
        products = Product.objects.filter(
            created_at__month=month_index,
            company__phone_number=phone_number
        ).values("id", "title", "count", "price", "total_price", "created_at")

        if products:
            df = pd.DataFrame(list(products))
            file_path = f"export_{phone_number}_{month_name}.xlsx"
            df.to_excel(file_path, index=False)
            return file_path
        else:
            logging.warning(f"No data found for month: {month_name} and phone number: {phone_number}")
            return None
    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        return None









def phone_number_format(phone_number):
    """
    This function formats a phone number to the international format.
    It removes unnecessary characters and ensures the number starts with +998.
    """
    phone_number = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone_number.startswith("998"):
        phone_number = "+" + phone_number
    elif not phone_number.startswith("+998"):
        phone_number = "+998" + phone_number
    return phone_number

@sync_to_async
def check_company(phone_number, chat_id):
    logging.info(f"Checking company for phone number: {phone_number}")

    try:
        company = Company.objects.filter(phone_number=phone_number).first()
        if company:
            if company.chat_id is None:
                company.chat_id = chat_id
                company.save()
                logging.info(f"Chat ID updated for company: {company.name}")
            elif company.chat_id == chat_id:
                logging.info(f"Company with phone number {phone_number} is already registered with this chat_id.")
            return company
        else:
            logging.warning(f"Company with phone number {phone_number} not found.")
            return None
    except Exception as e:
        logging.error(f"Error checking company: {e}")
        return None




# Ro'yxatga olish jarayonini kuzatish uchun lug'at
user_registration_status = {}

async def menu_handler(message: Message):
    logging.info(f"Menu handler triggered with text: {message.text}")

    if message.text == "Регистрация":
        # Foydalanuvchi ro'yxatdan o'tish jarayonida ekanligini belgilash
        user_registration_status[message.from_user.id] = True
        await message.answer("Iltimos, telefon raqamingizni yuboring.", reply_markup=keyboards["request_contact"])
    elif message.text == "Накладные":
        await message.answer("Oylikni tanlang:", reply_markup=keyboards["months"])
    elif message.text == "Главное меню":
        await message.answer("Bosh menu:", reply_markup=keyboards["main"])

async def handle_contact(message: Message):
    if message.contact:
        phone_number = phone_number_format(message.contact.phone_number)
        logging.info(f"Received phone number: {phone_number}")

        # Foydalanuvchi ro'yxatdan o'tish jarayonida ekanligini tekshirish
        if user_registration_status.get(message.from_user.id, False):
            # Telefon raqamini faqat ro'yxatdan o'tish jarayonida yuborish mumkin
            company = await check_company(phone_number, message.from_user.id)

            if company:
                # Kompaniya topilsa va telefon raqami to'g'ri bo'lsa, ro'yxatdan o'tishni davom ettirish
                await message.answer(f"Sizning telefon raqamingiz {phone_number} muvaffaqiyatli ro‘yxatdan o‘tdi. Xush kelibsiz!", reply_markup=keyboards["main"])
            else:
                await message.answer("Sizning telefon raqamingiz bazada topilmadi yoki boshqa kompaniya bilan ro‘yxatdan o‘tgansiz. Iltimos, adminstratsiya bilan bog‘laning.")
            
            # Ro'yxatdan o'tishdan keyin, foydalanuvchi statusini yangilash
            user_registration_status[message.from_user.id] = False
        else:
            # Agar foydalanuvchi ro'yxatdan o'tish jarayonida bo'lmasa, telefon raqamini rad etish
            await message.answer("Telefon raqamingizni faqat ro‘yxatdan o‘tishda yuborishingiz mumkin. Iltimos, 'Регистрация' tugmasini bosing.")
    else:
        # Telefon raqami yuborilmasa, so'rash
        await message.answer("Iltimos, telefon raqamingizni yuboring.")


async def month_handler(message: Message):
    logging.info(f"Month handler triggered with text: {message.text}")

    phone_number = message.contact.phone_number if message.contact else None
    if phone_number:
        phone_number = phone_number_format(phone_number)

        company = await check_company(phone_number, message.from_user.id)

        if not company:
            await message.reply("Siz ro'yxatdan o'tmagan foydalanuvchisiz yoki boshqa akkaunt orqali kirgansiz. Iltimos, avval ro'yxatdan o'ting.")
            return

    month_name = message.text
    file_path = await export_to_excel(month_name, phone_number)

    if file_path:
        # Foydalanuvchiga faylni jo'natish
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption=f"{month_name} oyi uchun ma'lumotlar.")
    else:
        await message.reply("Bu oy uchun ma'lumotlar topilmadi.")








async def help_handler(message: Message):
    logging.info("Help command triggered.")
    await message.answer(
        "Это бот для регистрации и экспорта данных.\n"
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Получить помощь\n"
        "Вы также можете использовать кнопки для взаимодействия."
    )

async def start():
    logging.info("Starting bot...")
    await bot.set_my_commands([ 
        BotCommand(command="/start", description="Запустить бота"), 
        BotCommand(command="/help", description="Помощь!"), 
    ])

    dp.message.register(lambda msg: msg.answer("Добро пожаловать!", reply_markup=keyboards["main"]), Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(menu_handler, F.text.in_(["Накладные", "Главное меню", "Регистрация"]))
    dp.message.register(handle_contact, F.contact)
    dp.message.register(month_handler, F.text.in_(months))

    await dp.start_polling(bot)

if __name__ == "__main__":
    run(start())