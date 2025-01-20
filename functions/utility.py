from aiogram.types import Message
from keyboards.default.menu_keyboard import *
from utils.db_api.postgresql import add_user


# menu_handler funksiyasi
async def menu_handler(message: Message):
    if message.text == "Накладные":
        await message.reply("Ойларни танланг:", reply_markup=delivery_notes)
    elif message.text == "Главный меню":
        await message.reply("Асосий меню:", reply_markup=main_keyboard)

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