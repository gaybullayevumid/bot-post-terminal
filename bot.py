import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from asyncio import run
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor

# Database connection settings
DB_SETTINGS = {
    'dbname': 'avtolider',
    'user': 'postgres',
    'password': '8505',
    'host': 'localhost',
    'port': 5432
}

# Bot token
BOT_TOKEN = "7769778979:AAFNG8nuj0m2rbWbJFHz8Jb2-FHS_Bv5qIc"

# Initialize bot and dispatcher
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Months list
months = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

# Keyboards
keyboards = {
    "months": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=m) for m in months[i:i + 3]] for i in range(0, 12, 3)] + [[KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    ),
    "request_contact": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
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

# Function to get database connection
def get_db_connection():
    return psycopg2.connect(**DB_SETTINGS)

# Async function to check company
async def check_company(phone_number, chat_id):
    logging.info(f"Проверка компании для номера телефона: {phone_number}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM base_company WHERE phone_number = %s", (phone_number,))
            company = cursor.fetchone()

            if company:
                if company['chat_id'] is None:
                    cursor.execute("UPDATE base_company SET chat_id = %s WHERE id = %s", (chat_id, company['id']))
                    conn.commit()
                    logging.info(f"Chat ID обновлен для компании: {company['name']}")
                elif company['chat_id'] == chat_id:
                    logging.info(f"Компания с номером телефона {phone_number} уже зарегистрирована с этим chat_id.")
                return company
            else:
                logging.warning(f"Компания с номером телефона {phone_number} не найдена.")
                return None
    except Exception as e:
        logging.error(f"Ошибка при проверке компании: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Async function to export data to Excel
async def export_to_excel(phone_number, month_name=None, currency=None):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = """
                SELECT id, title, count, price, created_at, total_price
                FROM base_product
                WHERE company_id IN (SELECT id FROM base_company WHERE phone_number = %s)
            """
            params = [phone_number]

            if month_name:
                month_index = months.index(month_name) + 1
                query += " AND EXTRACT(MONTH FROM created_at) = %s"
                params.append(month_index)

            cursor.execute(query, params)
            products = cursor.fetchall()

            if not products:
                logging.warning(f"Данные для номера телефона {phone_number} не найдены")
                return None

            df = pd.DataFrame(products, columns=['id', 'title', 'count', 'price', 'created_at', 'total_price'])
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)

            if currency == "SUM":
                total_sum = df['total_price'].sum()
                total_sum_row = pd.DataFrame({
                    'id': ['Итого (SUM)'],
                    'title': [''],
                    'count': [''],
                    'price': [''],
                    'created_at': [''],
                    'total_price': [total_sum]
                })
                df = pd.concat([df, total_sum_row], ignore_index=True)
                file_path = "total_sum_sum.xlsx"
            elif currency == "USD":
                total_sum = df['total_price'].sum()
                exchange_rate = 11000  # 1 USD = 11000 SUM
                total_usd = total_sum / exchange_rate
                total_usd_row = pd.DataFrame({
                    'id': ['Итого (USD)'],
                    'title': [''],
                    'count': [''],
                    'price': [''],
                    'created_at': [''],
                    'total_price': [total_usd]
                })
                df = pd.concat([df, total_usd_row], ignore_index=True)
                file_path = "total_sum_usd.xlsx"
            else:
                file_path = f"invoice_{month_name.lower()}.xlsx" if month_name else "invoice.xlsx"

            df.to_excel(file_path, index=False)
            logging.info(f"Файл создан: {file_path}")
            return file_path
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Registration process tracker
user_registration_status = {}
user_phone_numbers = {}

# Start handler
async def start_handler(message: Message):
    logging.info("Команда старта вызвана.")
    if message.from_user.id in user_phone_numbers:
        await message.answer("С возвращением!", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Накладные")],
                [KeyboardButton(text="📊Балансовый акт (SUM)"), KeyboardButton(text="📊Балансовый акт (USD)"), KeyboardButton(text="☎️Контакты")],
                [KeyboardButton(text="📜О компании")]
            ],
            resize_keyboard=True
        ))
    else:
        await message.answer("Добро пожаловать! Пожалуйста, зарегистрируйтесь, чтобы продолжить.", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Регистрация")]],
            resize_keyboard=True
        ))

# Menu handler
async def menu_handler(message: Message):
    logging.info(f"Обработчик меню вызван с текстом: {message.text}")
    if message.from_user.id in user_phone_numbers:
        main_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Накладные")],
                [KeyboardButton(text="📊Балансовый акт (SUM)"), KeyboardButton(text="📊Балансовый акт (USD)"), KeyboardButton(text="☎️Контакты")],
                [KeyboardButton(text="📜О компании")]
            ],
            resize_keyboard=True
        )
    else:
        main_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Регистрация")]
            ],
            resize_keyboard=True
        )
    if message.text == "Накладные":
        await message.answer("Выберите месяц:", reply_markup=keyboards["months"])
    elif message.text == "Главное меню":
        await message.answer("Главное меню:", reply_markup=main_keyboard)
    elif message.text == "Регистрация":
        if message.from_user.id not in user_phone_numbers:
            user_registration_status[message.from_user.id] = True
            await message.answer("Пожалуйста, отправьте ваш номер телефона.", reply_markup=keyboards["request_contact"])
        else:
            await message.answer("Вы уже зарегистрированы.", reply_markup=main_keyboard)

# Contact handler
async def handle_contact(message: Message):
    if message.contact:
        if message.contact.user_id != message.from_user.id:
            await message.answer("Пожалуйста, отправьте только свой номер телефона!")
            return
        phone_number = phone_number_format(message.contact.phone_number)
        logging.info(f"Получен номер телефона: {phone_number}")
        if user_registration_status.get(message.from_user.id, False):
            company = await check_company(phone_number, message.from_user.id)
            if company:
                await message.answer(f"Ваш номер телефона {phone_number} успешно зарегистрирован. Добро пожаловать!", reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="Накладные")],
                        [KeyboardButton(text="📊Балансовый акт (SUM)"), KeyboardButton(text="📊Балансовый акт (USD)"), KeyboardButton(text="☎️Контакты")],
                        [KeyboardButton(text="📜О компании")]
                    ],
                    resize_keyboard=True
                ))
                user_phone_numbers[message.from_user.id] = phone_number
            else:
                await message.answer("Ваш номер телефона не найден в базе данных или зарегистрирован на другую компанию. Пожалуйста, свяжитесь с администрацией.")
                user_registration_status[message.from_user.id] = False
        else:
            await message.answer("Вы можете отправить свой номер телефона только во время регистрации. Пожалуйста, нажмите кнопку 'Регистрация'.")
    else:
        await message.answer("Пожалуйста, отправьте ваш номер телефона.")

# About the Company handler
async def about_company_handler(message: Message):
    logging.info(f"Обработчик 'О компании' вызван с текстом: {message.text}")
    company_info = (
        "🏢 Название компании: Пример Компании\n"
        "📍 Адрес: Навои, Узбекистан\n"
        "📞 Телефон: +998930850955\n"
        "🌐 Веб-сайт: www.example.com\n"
        "📧 Электронная почта: info@example.com\n"
        "📝 Описание: Мы являемся ведущей компанией в отрасли, предоставляющей высококачественные услуги и продукты."
    )
    await message.answer(company_info)

# Contacts handler
async def phone_handler(message: Message):
    logging.info(f"Обработчик контактов вызван с текстом: {message.text}")
    phone_info = (
        "Тел:\n"
        "+998912518505 Умид\n"
        "+998912518505 Умид"
    )
    await message.answer(phone_info)

# Month handler
async def month_handler(message: Message):
    logging.info(f"Обработчик месяца вызван с текстом: {message.text}")
    if message.from_user.id not in user_phone_numbers:
        await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь сначала.", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Регистрация")]],
            resize_keyboard=True
        ))
        return
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.reply("Вы не зарегистрированный пользователь или вошли в систему с другого аккаунта. Пожалуйста, зарегистрируйтесь сначала.")
        return
    month_name = message.text
    file_path = await export_to_excel(phone_number, month_name)
    if file_path:
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption=f"Данные за месяц {month_name}.")
    else:
        await message.reply("Данные за этот месяц не найдены. Пожалуйста, убедитесь, что есть данные за выбранный месяц или проверьте вашу базу данных.")

# Balance Act (SUM) handler
async def balance_act_sum_handler(message: Message):
    logging.info(f"Обработчик балансового акта (SUM) вызван с текстом: {message.text}")
    if message.from_user.id not in user_phone_numbers:
        await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь сначала.", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Регистрация")]],
            resize_keyboard=True
        ))
        return
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.reply("Вы не зарегистрированный пользователь или вошли в систему с другого аккаунта. Пожалуйста, зарегистрируйтесь сначала.")
        return
    file_path = await export_to_excel(phone_number, currency="SUM")
    if file_path:
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption="Все продукты с итоговой суммой в SUM.")
    else:
        await message.reply("Данные не найдены. Пожалуйста, убедитесь, что есть данные в базе данных.")

# Balance Act (USD) handler
async def balance_act_usd_handler(message: Message):
    logging.info(f"Обработчик балансового акта (USD) вызван с текстом: {message.text}")
    if message.from_user.id not in user_phone_numbers:
        await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь сначала.", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Регистрация")]],
            resize_keyboard=True
        ))
        return
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.reply("Вы не зарегистрированный пользователь или вошли в систему с другого аккаунта. Пожалуйста, зарегистрируйтесь сначала.")
        return
    file_path = await export_to_excel(phone_number, currency="USD")
    if file_path:
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption="Все продукты с итоговой суммой в USD.")
    else:
        await message.reply("Данные не найдены. Пожалуйста, убедитесь, что есть данные в базе данных.")

# Help handler
async def help_handler(message: Message):
    logging.info("Команда помощи вызвана.")
    await message.answer(
        "Это бот для регистрации и экспорта данных.\n"
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Получить помощь\n"
        "Вы также можете использовать кнопки для взаимодействия."
    )

# Main start function
async def start():
    try:
        logging.info("Запуск бота...")
        await bot.set_my_commands([
            BotCommand(command="/start", description="Запустить бота"),
            BotCommand(command="/help", description="Помощь!")
        ])
        dp.message.register(start_handler, Command("start"))
        dp.message.register(help_handler, Command("help"))
        dp.message.register(menu_handler, F.text.in_(["Накладные", "Главное меню", "Регистрация"]))
        dp.message.register(handle_contact, F.contact)
        dp.message.register(month_handler, F.text.in_(months))
        dp.message.register(balance_act_sum_handler, F.text == "📊Балансовый акт (SUM)")
        dp.message.register(balance_act_usd_handler, F.text == "📊Балансовый акт (USD)")
        dp.message.register(about_company_handler, F.text == "📜О компании")
        dp.message.register(phone_handler, F.text == "☎️Контакты")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    run(start())