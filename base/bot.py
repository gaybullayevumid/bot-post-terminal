import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from asyncio import run
import psycopg2
import pandas as pd
import datetime

BOT_TOKEN = "7769778979:AAFNG8nuj0m2rbWbJFHz8Jb2-FHS_Bv5qIc"

DB_CONFIG = {
    "dbname": "avtolider",
    "user": "postgres",
    "password": "8505",
    "host": "localhost",
    "port": "5432"
}

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

month_mapping = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}

months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Регистрация"), KeyboardButton(text="Накладные")]
    ],
    resize_keyboard=True
)

delivery_notes = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="January"), KeyboardButton(text="February"), KeyboardButton(text="March")],
        [KeyboardButton(text="April"), KeyboardButton(text="May"), KeyboardButton(text="June")],
        [KeyboardButton(text="July"), KeyboardButton(text="August"), KeyboardButton(text="September")],
        [KeyboardButton(text="October"), KeyboardButton(text="November"), KeyboardButton(text="December")],
        [KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

def export_to_excel(month_name: str):
    try:
        connection = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        cursor = connection.cursor()

        query = """
            SELECT * FROM base_product 
            WHERE EXTRACT(MONTH FROM created_at) = %s 
            AND TO_CHAR(created_at, 'FMMonth') = %s
        """
        cursor.execute(query, (months.index(month_name) + 1, month_name.capitalize()))

        data = cursor.fetchall()

        if data:
            for i, row in enumerate(data):
                data[i] = list(row)
                if isinstance(data[i][4], datetime.datetime):
                    data[i][4] = data[i][4].replace(tzinfo=None)

            df = pd.DataFrame(data, columns=["ID", "Description", "Amount", "Price", "CreatedAt", "Month", "TotalAmount"])

            file_path = f"накладные_{month_name}.xlsx"
            df.to_excel(file_path, index=False)

            cursor.close()
            connection.close()
            return file_path
        else:
            cursor.close()
            connection.close()
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


async def startup_answer(bot: Bot):
    await bot.send_message(5323321097, "Бот начал работу. ✅")

async def shutdown_answer(bot: Bot):
    await bot.send_message(5323321097, "Бот завершил работу ❌")

async def start_answer(message: Message):
    await message.answer(
        f"Hello, {message.from_user.mention_html(message.from_user.first_name)}",
        reply_markup=main_keyboard,
        parse_mode='HTML'
    )

async def help_answer(message: Message):
    text = """
        <b>Команды бота:</b>

    /start - Запустить бота
    /help - Помощь!
    """
    await message.answer(text, parse_mode='HTML')

async def menu_handler(message: Message):
    if message.text in month_mapping:
        await message.answer(f"Вы выбрали месяц {message.text}")
    elif message.text == "Накладные":
        await message.answer("Выберите месяц:", reply_markup=delivery_notes)
    elif message.text == "Главное меню":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
    else:
        await message.answer("Ошибка!", reply_markup=main_keyboard)


# async def month_handler(message: Message):
#     if message.text in months:
#         try:
#             new_file_name = f"{message.text.capitalize()}.xlsx"
#             os.rename("main.xlsx", new_file_name)
            
#             document = FSInputFile(new_file_name)
#             await message.bot.send_document(chat_id=message.chat.id, document=document)
#         except FileNotFoundError:
#             await message.reply("File not found.")
#         except Exception as e:
#             await message.reply(f"An error occurred: {e}")
#         finally:
#             os.rename(new_file_name, "main.xlsx")

# async def send_excel_by_month(message: Message):
#     if not message.text:
#         await message.reply("Error: month name not provided.")
#         return

#     month_name = message.text.strip().capitalize()

#     # Foydalanuvchiga xabar yuborish
#     await message.reply(f"Loading data for {month_name} month, please wait...")

#     # Excel faylni eksport qilish
#     file_path = export_to_excel(month_name)

#     if file_path:
#         # Faylni yuborish
#         document = FSInputFile(file_path)
#         await message.bot.send_document(chat_id=message.chat.id, document=document)
#         logging.info(f"File for {month_name} month has been sent!")
#     else:
#         await message.reply("Sorry, an error occurred while loading the data.")

async def month_handler(message: Message):
    if message.text in months:
        month_name = message.text.strip().capitalize()


        file_path = export_to_excel(month_name)

        if file_path:
            try:
                document = FSInputFile(file_path)
                await message.bot.send_document(chat_id=message.chat.id, document=document)
                logging.info(f"Файл за месяц {month_name} отправлен!")
            except Exception as e:
                await message.reply(f"Произошла ошибка при отправке файла: {e}")
        else:
            await message.reply("Извините, произошла ошибка при загрузке данных.")

async def start():
    dp.startup.register(startup_answer)

    dp.message.register(start_answer, Command("start"))
    dp.message.register(help_answer, Command("help"))
    dp.message.register(menu_handler, F.text.in_(["Накладные", "Главное меню"]))
    dp.message.register(month_handler, F.text.in_(months))

    dp.shutdown.register(shutdown_answer)

    await bot.set_my_commands([
        BotCommand(command='/start', description='Запустить бота.'),
        BotCommand(command='/help', description='Помощь.')
    ])
    await dp.start_polling(bot, polling_timeout=1)

run(start())