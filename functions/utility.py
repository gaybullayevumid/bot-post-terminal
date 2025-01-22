from aiogram.types import Message, InputFile
from keyboards.default.menu_keyboard import *
from utils.db_api.postgresql import export_to_excel
import logging


async def menu_handler(message: Message):
    if message.text == "Накладные":
        await message.answer("Выберите месяц:", reply_markup=delivery_notes)
    elif message.text == "Главное меню":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
    else:
        await message.answer("Ошибка!", reply_markup=main_keyboard)


async def send_excel_by_month(message: Message):
    month_name = message.text.strip()  # Xabardan faqat matnni olish
    await message.reply(f"{month_name} ойига тегишли маълумотлар юкланмоқда, кутиб туринг...")

    # Ma'lumotlarni Excelga eksport qilish
    file_path = export_to_excel(month_name)

    if file_path:
        try:
            excel_file = InputFile(file_path)
            await message.reply_document(excel_file)
            logging.info(f"{month_name} ойига тегишли файл юборилди!")
        except Exception as e:
            await message.reply("Файлни юборишда хато юз берди.")
            logging.error(f"Fayl yuborishda xato: {e}")
    else:
        await message.reply("Кечирасиз, маълумотларни юклашда хато юз берди.")