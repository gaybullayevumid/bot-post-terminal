from aiogram import Bot
from aiogram.types import Message

async def help_answer(message: Message, bot: Bot):
    matn = """
        <b>Команды бота:</b>

    /start - Запуск бота
    /help - Помощь!
    """
    await bot.send_message(message.from_user.id, matn, parse_mode='HTML')
