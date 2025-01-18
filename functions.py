from aiogram import Bot
from aiogram.types import Message
from keyboards import *


# start_answer funksiyasi aniqlanadi
async def start_answer(message: Message, bot: Bot):
    await bot.send_message(
        message.from_user.id,
        f"Salom, {message.from_user.mention_html(message.from_user.first_name)}",
        reply_markup=main_keyboard,
        parse_mode='HTML'
    )


# help_answer funksiyasi
async def help_answer(message: Message, bot: Bot):
    matn = """
        <b>Bot buyruqlari:</b>

    /start - Botni ishga tushurish
    /help - Yordam!
    """
    await bot.send_message(message.from_user.id, matn, parse_mode='HTML')


# menu_handler funksiyasi
async def menu_handler(message: Message):
    if message.text == "Накладные":
        await message.reply("Ойларни танланг:", reply_markup=delivery_notes)
    elif message.text == "Главный меню":
        await message.reply("Асосий меню:", reply_markup=main_keyboard)
