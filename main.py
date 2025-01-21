from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.filters import Command
from handlers.start import start_answer
from handlers.help import help_answer
from functions.utility import menu_handler, ask_phone_number
from data.config import BOT_TOKEN, ADMINS, IP
from asyncio import run
from utils.db_api.postgresql import add_user

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

async def startup_answer(bot: Bot):
    await bot.send_message(5323321097, "Бот начал свою работу. ✅")

async def shutdown_answer(bot: Bot):
    await bot.send_message(5323321097, "Бот приостановил свою работу ❌")

async def start():
    dp.startup.register(startup_answer)

    # functions.py dan start_answer va help_answer funksiyalarini chaqiramiz
    dp.message.register(start_answer, Command("start"))
    dp.message.register(help_answer, Command("help"))
    dp.message.register(menu_handler, lambda message: message.text in ["Накладные", "Главное меню", "☎️Контакты"])
    dp.message.register(ask_phone_number, lambda message: message.text in ["☎️Контакты"])

    dp.shutdown.register(shutdown_answer)


    await bot.set_my_commands([
        BotCommand(command='/start', description='Botni ishga tushirish.'),
        BotCommand(command='/help', description='Yordam.')
    ])
    await dp.start_polling(bot, polling_timeout=1)


run(start())