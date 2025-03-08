import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncio import run
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

DB_SETTINGS = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

months = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

class Form(StatesGroup):
    phone_number = State()
    month = State()

def phone_number_format(phone_number):
    phone_number = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone_number.startswith("998"):
        phone_number = phone_number
    elif phone_number.startswith("+998"):
        phone_number = phone_number[1:]
    return phone_number

def get_db_connection():
    return psycopg2.connect(**DB_SETTINGS)

def export_to_excel(phone_number, month_name=None):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = """
                SELECT
                    o.obj_name AS "Магазин/Склад",
                    g.gd_code AS "Код",
                    g.gd_name AS "Номенклатура",
                    s.sls_datetime AS "Дата/Время",
                    'Продажа' AS "Тип",
                    op.opr_quantity AS "Количество",
                    a.oap_price1 AS "Цена",
                    (op.opr_quantity * a.oap_price1) AS "Сумма",
                    dss.sords_name AS "Статус оплаты"
                FROM doc_sales s
                JOIN operations op
                    ON op.opr_document = s.sls_id AND op.opr_type = 2
                JOIN operations_additional_prop a
                    ON a.oap_operation = op.opr_id
                JOIN dir_goods g
                    ON g.gd_id = op.opr_good
                JOIN dir_objects o
                    ON o.obj_id = s.sls_object
                JOIN dir_customers c
                    ON c.cstm_id = s.sls_customer
                JOIN dir_sales_status dss
                    ON dss.sords_id = s.sls_status
                WHERE s.sls_datetime BETWEEN '2015-01-01' AND '2044-06-15'
                    AND s.sls_performed = 1
                    AND s.sls_deleted = 0
                    AND %s IN (c.cstm_phone, c.cstm_phone2, c.cstm_phone3, c.cstm_phone4)
                    AND dss.sords_name != 'Завершен'
            """
            params = [phone_number]

            if month_name:
                month_index = months.index(month_name) + 1
                query += " AND EXTRACT(MONTH FROM s.sls_datetime) = %s"
                params.append(month_index)

            query += " ORDER BY s.sls_datetime"
            logging.info(f"Executing query: {query} with params: {params}")
            cursor.execute(query, params)
            products = cursor.fetchall()

            if not products:
                logging.warning(f"Данные для номера телефона {phone_number} за месяц {month_name} не найдены")
                return None

            df = pd.DataFrame(products, columns=['Магазин/Склад', 'Код', 'Номенклатура', 'Дата/Время', 'Тип', 'Количество', 'Цена', 'Сумма', 'Статус оплаты'])
            df["Дата/Время"] = pd.to_datetime(df["Дата/Время"]).dt.tz_localize(None)

            file_path = f"накладные_{month_name.lower()}.xlsx" if month_name else "накладные.xlsx"
            df.to_excel(file_path, index=False)
            logging.info(f"Файл создан: {file_path}")
            return file_path
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return None
    finally:
        if conn:
            conn.close()

async def start_handler(message: Message, state: FSMContext):
    logging.info("Команда старта вызвана.")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Register"), KeyboardButton(text="📦 Накладные")],
            [KeyboardButton(text="📞 Контакт")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "Добро пожаловать! Пожалуйста, выберите действие:",
        reply_markup=keyboard
    )

async def register_button_handler(message: Message, state: FSMContext):
    logging.info("Кнопка '📝 Register' нажата.")
    await message.answer(
        "Пожалуйста, отправьте ваш номер телефона в формате +998XXXXXXXXX.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.phone_number)

async def phone_number_handler(message: Message, state: FSMContext):
    phone_number = phone_number_format(message.text)
    logging.info(f"Получен номер телефона: {phone_number}")

    if not phone_number.startswith("998") or len(phone_number) != 12:
        await message.answer("Пожалуйста, введите корректный номер телефона в формате +998XXXXXXXXX.")
        return

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            logging.info(f"Проверка номера телефона в базе данных: {phone_number}")
            cursor.execute("""
                SELECT * FROM dir_customers c
                WHERE %s IN (c.cstm_phone, c.cstm_phone2, c.cstm_phone3, c.cstm_phone4)
            """, (phone_number,))
            customer = cursor.fetchone()
            logging.info(f"Результат запроса: {customer}")

            if customer:
                await state.update_data(phone_number=phone_number)
                await main_menu_handler(message, state)
            else:
                await message.answer(f"Ваш номер телефона {phone_number} не найден в базе данных. Пожалуйста, убедитесь, что вы зарегистрированы.")
                await state.clear()
    except psycopg2.Error as e:
        logging.error(f"Ошибка при проверке клиента: {e}")
        await message.answer("Произошла ошибка при проверке номера телефона. Пожалуйста, попробуйте позже.")
        await state.clear()
    finally:
        if conn:
            conn.close()

async def main_menu_handler(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Register"), KeyboardButton(text="📦 Накладные")],
            [KeyboardButton(text="📞 Контакт")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Выберите действие:", reply_markup=keyboard)

async def nakladnaya_button_handler(message: Message, state: FSMContext):
    logging.info("Кнопка '📦 Накладные' нажата.")
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")

    if not phone_number:
        await message.answer("Пожалуйста, сначала отправьте ваш номер телефона в формате +998XXXXXXXXX.")
        await state.set_state(Form.phone_number)
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=months[i]), KeyboardButton(text=months[i+1]), KeyboardButton(text=months[i+2])]
            for i in range(0, len(months), 3)
        ] + [[KeyboardButton(text="🏠 Главная")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Выберите месяц:", reply_markup=keyboard)
    await state.set_state(Form.month)

async def month_handler(message: Message, state: FSMContext):
    user_data = await state.get_data()
    phone_number = user_data.get("phone_number")
    month_name = message.text

    if month_name == "🏠 Главная":
        await message.answer("Вы вернулись в главное меню.", reply_markup=ReplyKeyboardRemove())
        await main_menu_handler(message, state)
        return

    if not phone_number:
        await message.answer("Пожалуйста, сначала отправьте ваш номер телефона в формате +998XXXXXXXXX.")
        await state.set_state(Form.phone_number)
        return

    file_path = export_to_excel(phone_number, month_name)
    if file_path:
        excel_file = FSInputFile(file_path)
        await message.answer_document(excel_file, caption=f"Данные за месяц {month_name}.")
    else:
        await message.reply(
            f"Данные за месяц {month_name} не найдены. Пожалуйста, убедитесь, что есть данные за выбранный месяц или проверьте вашу базу данных."
        )
    await state.set_state(Form.month)

async def contact_handler(message: Message):
    logging.info("Кнопка '📞 Контакт' нажата.")
    contact_info = (
        "🏢 Название компании: Пример Компании\n"
        "📍 Адрес: Навои, Узбекистан\n"
        "📞 Телефон: +998930850955\n"
        "🌐 Веб-сайт: www.example.com\n"
        "📧 Электронная почта: info@example.com\n"
        "📝 Описание: Мы являемся ведущей компанией в отрасли, предоставляющей высококачественные услуги и продукты."
    )
    await message.answer(contact_info)

async def help_handler(message: Message):
    logging.info("Команда помощи вызвана.")
    await message.answer(
        "Это бот для регистрации и экспорта данных.\n"
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Получить помощь\n"
        "Вы также можете отправить свой номер телефона для регистрации."
    )

async def start():
    try:
        logging.info("Запуск бота...")
        await bot.set_my_commands([
            BotCommand(command="/start", description="Запустить бота"),
            BotCommand(command="/help", description="Помощь!")
        ])
        dp.message.register(start_handler, Command("start"))
        dp.message.register(help_handler, Command("help"))
        dp.message.register(register_button_handler, F.text == "📝 Register")
        dp.message.register(nakladnaya_button_handler, F.text == "📦 Накладные")
        dp.message.register(contact_handler, F.text == "📞 Контакт")
        dp.message.register(phone_number_handler, F.text.startswith("+998") | F.text.startswith("998"))
        dp.message.register(month_handler, F.text.in_(months + ["🏠 Главная"]))
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    run(start())