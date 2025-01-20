from aiogram import Bot
from aiogram.types import Message

# help_answer funksiyasi
async def help_answer(message: Message, bot: Bot):
    matn = """
        <b>Bot buyruqlari:</b>

    /start - Botni ishga tushurish
    /help - Yordam!
    """
    await bot.send_message(message.from_user.id, matn, parse_mode='HTML')
