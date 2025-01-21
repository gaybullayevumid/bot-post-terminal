from aiogram.types import Message
from keyboards.default.menu_keyboard import *
import openpyxl
import psycopg2
from data.config import DB_CONFIG
# from utils.db_api.postgresql import add_user


def create_excel(month_name):
    connection = psycopg2.connect(DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute(
        """
            SELECT * FROM data
            WHERE month = %s
        """
        , (month_name)
    )
    records = cursor.fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = month_name

    headers = ['id', 'name', 'amount', 'date']
    ws.append(headers)

    for row in records:
        ws.append(row)

        file_name = f"{month_name}_data.xlsx"
        wb.save(file_name)

        cursor.close()
        connection.close()

        return file_name


# menu_handler funksiyasi
async def menu_handler(message: Message):
    if message.text == "Накладные":
        await message.reply("Ойларни танланг:", reply_markup=delivery_notes)
    elif message.text == "Главный меню":
        await message.reply("Асосий меню:", reply_markup=main_keyboard)
    # elif message.text in

# async def registration(message: Message):
#     if message.text == "Регистрация":
#         await



    # user_id = message.from_user.id
    # username = message.from_user.username
    #
    # try:
    #     add_user(user_id, username)
    #     await message.reply("Muvaffaqiyatli ro'yhatdan o'tdingiz.")
    # except Exception as error:
    #     await message.reply(f"Xatolik bor {error}")