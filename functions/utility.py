from aiogram.types import Message, ReplyKeyboardRemove
from keyboards.default.menu_keyboard import *


async def menu_handler(message: Message):
    if message.text == "Накладные":
        await message.answer("Выберите месяц:", reply_markup=delivery_notes)
    elif message.text == "Главное меню":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
    else:
        await message.answer("Ошибка!", reply_markup=main_keyboard)
