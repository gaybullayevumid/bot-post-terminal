from aiogram import Bot
from aiogram.types import Message
from keyboards import *

async def start_answer(message: Message, bot: Bot):
    await bot.send_message(message.from_user.id, f"Salom, {message.from_user.mention_html(f"{message.from_user.first_name}")}", reply_markup=delivery_notes, parse_mode='HTML')

async def help_answer(message: Message, bot: Bot):
    matn = f"""
        <b>Bot buyruqlari:</b>
        
    /start - Botni ishga tushurish
    /help - Yordam!
    """

    await bot.send_message(message.from_user.id, matn, parse_mode='HTML')