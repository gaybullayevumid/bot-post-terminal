from aiogram.types import Message
from keyboards.default.menu_keyboard import *

# menu_handler funksiyasi
async def menu_handler(message: Message):
    if message.text == "Накладные":
        await message.reply("Ойларни танланг:", reply_markup=delivery_notes)
    elif message.text == "Главный меню":
        await message.reply("Асосий меню:", reply_markup=main_keyboard)
