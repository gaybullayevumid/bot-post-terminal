import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from asyncio import run
import pandas as pd
import django
from asgiref.sync import sync_to_async

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from base.models import Company, Product

# Bot token
BOT_TOKEN = "7769778979:AAFNG8nuj0m2rbWbJFHz8Jb2-FHS_Bv5qIc"

# Initialize bot and dispatcher
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Months list
months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Keyboards
keyboards = {
    "main": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Invoices")],
            [KeyboardButton(text="📊Balance Act (SUM)"), KeyboardButton(text="📊Balance Act (USD)"), KeyboardButton(text="☎️Contacts")],
            [KeyboardButton(text="📜About the Company")]
        ],
        resize_keyboard=True
    ),
    "months": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=m) for m in months[i:i + 3]] for i in range(0, 12, 3)] + [[KeyboardButton(text="Main Menu")]],
        resize_keyboard=True
    ),
    "request_contact": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Send phone number", request_contact=True)]],
        resize_keyboard=True
    ),
    "registration_only": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Registration")]],
        resize_keyboard=True
    ),
}

# Helper function to format phone number
def phone_number_format(phone_number):
    phone_number = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone_number.startswith("998"):
        phone_number = "+" + phone_number
    elif not phone_number.startswith("+998"):
        phone_number = "+998" + phone_number
    return phone_number

# Async function to check company
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

# Async function to export data to Excel for a specific month
@sync_to_async
def export_to_excel(month_name, phone_number):
    try:
        month_index = months.index(month_name) + 1
        products = Product.objects.filter(
            created_at__month=month_index,
            company__phone_number=phone_number
        ).values('id', 'title', 'count', 'price', 'created_at', 'total_price')

        if products:
            df = pd.DataFrame(list(products))
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)

            file_path = f"invoice_{month_name.lower()}.xlsx"
            df.to_excel(file_path, index=False)

            if os.path.exists(file_path):
                logging.info(f"File created: {file_path}")
                return file_path
            else:
                logging.error("File creation failed!")
                return None
        else:
            logging.warning(f"No data found for {month_name} with phone number {phone_number}")
            return None
    except Exception as e:
        logging.error(f"Error: {e}")
        return None

# Async function to export total sum to Excel with USD
@sync_to_async
def export_total_sum_to_excel_sum(phone_number):
    try:
        products = Product.objects.filter(
            company__phone_number=phone_number
        ).values('id', 'title', 'count', 'price', 'created_at', 'total_price')

        if products:
            df = pd.DataFrame(list(products))
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)

            # Jami summani hisoblash
            total_sum = df['total_price'].sum()

            # Jami summa bilan yangi qatorni qo'shish (SUM)
            total_sum_row = pd.DataFrame({
                'id': ['Total (SUM)'],
                'title': [''],
                'count': [''],
                'price': [''],
                'created_at': [''],
                'total_price': [total_sum]
            })

            # Asl DataFrame-ga jami summa qatorini qo'shish
            df = pd.concat([df, total_sum_row], ignore_index=True)

            # Excel faylini saqlash
            file_path = "total_sum_sum.xlsx"
            df.to_excel(file_path, index=False)

            if os.path.exists(file_path):
                logging.info(f"File created: {file_path}")
                return file_path
            else:
                logging.error("File creation failed!")
                return None
        else:
            logging.warning(f"No data found for phone number {phone_number}")
            return None
    except Exception as e:
        logging.error(f"Error: {e}")
        return None





# Registration process tracker
user_registration_status = {}
user_phone_numbers = {}


@sync_to_async
def export_total_sum_to_excel_usd(phone_number):
    try:
        products = Product.objects.filter(
            company__phone_number=phone_number
        ).values('id', 'title', 'count', 'price', 'created_at', 'total_price')

        if products:
            df = pd.DataFrame(list(products))
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)

            # Jami summani hisoblash
            total_sum = df['total_price'].sum()

            # Jami summani USD ga aylantirish
            exchange_rate = 11000  # 1 USD = 11000 SUM
            total_usd = total_sum / exchange_rate

            # Jami summa bilan yangi qatorni qo'shish (USD)
            total_usd_row = pd.DataFrame({
                'id': ['Total (USD)'],
                'title': [''],
                'count': [''],
                'price': [''],
                'created_at': [''],
                'total_price': [total_usd]
            })

            # Asl DataFrame-ga jami summa qatorini qo'shish
            df = pd.concat([df, total_usd_row], ignore_index=True)

            # Excel faylini saqlash
            file_path = "total_sum_usd.xlsx"
            df.to_excel(file_path, index=False)

            if os.path.exists(file_path):
                logging.info(f"File created: {file_path}")
                return file_path
            else:
                logging.error("File creation failed!")
                return None
        else:
            logging.warning(f"No data found for phone number {phone_number}")
            return None
    except Exception as e:
        logging.error(f"Error: {e}")
        return None

# Menu handler
async def menu_handler(message: Message):
    logging.info(f"Menu handler triggered with text: {message.text}")
    if message.from_user.id not in user_phone_numbers:
        if message.text == "Registration":
            user_registration_status[message.from_user.id] = True
            await message.answer("Iltimos, telefon raqamingizni yuboring.", reply_markup=keyboards["request_contact"])
        else:
            await message.answer("You are not registered. Please register first.", reply_markup=keyboards["registration_only"])
        return

    if message.text == "Invoices":
        await message.answer("Select the month:", reply_markup=keyboards["months"])
    elif message.text == "Main Menu":
        await message.answer("Main menu:", reply_markup=keyboards["main"])

# Contact handler
async def handle_contact(message: Message):
    if message.contact:
        if message.contact.user_id != message.from_user.id:
            await message.answer("Iltimos, faqat o'z telefon raqamingizni jo'nating!")
            return

        phone_number = phone_number_format(message.contact.phone_number)
        logging.info(f"Received phone number: {phone_number}")

        if user_registration_status.get(message.from_user.id, False):
            company = await check_company(phone_number, message.from_user.id)

            if company:
                await message.answer(f"Your phone number {phone_number} has been successfully registered. Welcome!", reply_markup=keyboards["main"])
                user_phone_numbers[message.from_user.id] = phone_number
            else:
                await message.answer("Your phone number was not found in the database or is registered with another company. Please contact the administration.")

            user_registration_status[message.from_user.id] = False
        else:
            await message.answer("You can only send your phone number during registration. Please press the 'Registration' button.")
    else:
        await message.answer("Please send your phone number.")

# About the Company handler
async def about_company_handler(message: Message):
    logging.info(f"About the Company handler triggered with text: {message.text}")
    
    # Kampaniya haqida ma'lumot (qo'lda yozilgan)
    company_info = (
        "🏢 Company Name: Example Company\n"
        "📍 Address: Navoiy, Uzbekistan\n"
        "📞 Phone: +998930850955\n"
        "🌐 Website: www.example.com\n"
        "📧 Email: info@example.com\n"
        "📝 Description: We are a leading company in the industry, providing high-quality services and products."
    )
    
    await message.answer(company_info)

async def phone_handler(message: Message):
    logging.info(f"About the Company handler triggered with text: {message.text}")
    
    # Kampaniya haqida ma'lumot (qo'lda yozilgan)
    phone_info = (
        "Tel:\n"
        "+998912518505 Umid\n"
        "+998912518505 Umid"
    )
    
    await message.answer(phone_info)

# Month handler
async def month_handler(message: Message):
    logging.info(f"Month handler triggered with text: {message.text}")
    if message.from_user.id not in user_phone_numbers:
        await message.answer("You are not registered. Please register first.", reply_markup=keyboards["registration_only"])
        return

    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.reply("You are not a registered user or logged in with another account. Please register first.")
        return

    month_name = message.text
    file_path = await export_to_excel(month_name, phone_number)

    if file_path:
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption=f"Data for the month of {month_name}.")
    else:
        await message.reply("No data found for this month. Please make sure there is data for the selected month or check your database.")

# Balance Act (SUM) handler
async def balance_act_sum_handler(message: Message):
    logging.info(f"Balance Act (SUM) handler triggered with text: {message.text}")
    if message.from_user.id not in user_phone_numbers:
        await message.answer("You are not registered. Please register first.", reply_markup=keyboards["registration_only"])
        return

    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.reply("You are not a registered user or logged in with another account. Please register first.")
        return

    # SUM uchun Excel faylini yaratish
    file_path = await export_total_sum_to_excel_sum(phone_number)

    if file_path:
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption="All products with total sum in SUM.")
    else:
        await message.reply("No data found. Please make sure there is data in the database.")

# Balance Act (USD) handler
async def balance_act_usd_handler(message: Message):
    logging.info(f"Balance Act (USD) handler triggered with text: {message.text}")
    if message.from_user.id not in user_phone_numbers:
        await message.answer("You are not registered. Please register first.", reply_markup=keyboards["registration_only"])
        return

    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.reply("You are not a registered user or logged in with another account. Please register first.")
        return

    # USD uchun Excel faylini yaratish
    file_path = await export_total_sum_to_excel_usd(phone_number)

    if file_path:
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption="All products with total sum in USD.")
    else:
        await message.reply("No data found. Please make sure there is data in the database.")





# Help handler
async def help_handler(message: Message):
    logging.info("Help command triggered.")
    await message.answer(
        "This is a bot for registration and data export.\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "You can also use the buttons for interaction."
    )

# Start handler
async def start_handler(message: Message):
    logging.info("Start command triggered.")
    await message.answer("Welcome! Please register to continue.", reply_markup=keyboards["registration_only"])
# Main start function
async def start():
    logging.info("Starting bot...")
    await bot.set_my_commands([
        BotCommand(command="/start", description="Start the bot"),
        BotCommand(command="/help", description="Help!")
    ])

    dp.message.register(start_handler, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(menu_handler, F.text.in_(["Invoices", "Main Menu", "Registration"]))
    dp.message.register(handle_contact, F.contact)
    dp.message.register(month_handler, F.text.in_(months))
    dp.message.register(balance_act_sum_handler, F.text == "📊Balance Act (SUM)")  # SUM uchun handler
    dp.message.register(balance_act_usd_handler, F.text == "📊Balance Act (USD)")
    dp.message.register(about_company_handler, F.text == "📜About the Company")
    dp.message.register(phone_handler, F.text == "☎️Contacts")

    await dp.start_polling(bot)

if __name__ == "__main__":
    run(start())