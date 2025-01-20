from aiogram import Bot
from aiogram.types import Message
from keyboards.default.menu_keyboard import main_keyboard


# start_answer funksiyasi aniqlanadi
async def start_answer(message: Message, bot: Bot):
    await bot.send_message(
        message.from_user.id,
        f"Salom, {message.from_user.mention_html(message.from_user.first_name)}",
        reply_markup=main_keyboard,
        parse_mode='HTML'
    )
