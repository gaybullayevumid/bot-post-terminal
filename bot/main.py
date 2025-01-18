from aiogram import Bot, Dispatcher
from asyncio import run
from aiogram.types import BotCommand
from aiogram.filters import Command
from handlers.start_handler import start_answer
from handlers.help_handler import help_answer
from functions.utility import menu_handler

import functions  # functions.py faylini import qilish

dp = Dispatcher()

async def startup_answer(bot: Bot):
    await bot.send_message(5323321097, "Bot ishga tushdi! ✅")

async def shutdown_answer(bot: Bot):
    await bot.send_message(5323321097, "Bot ishdan toxtadi! ❌")

async def start():
    dp.startup.register(startup_answer)

    # functions.py dan start_answer va help_answer funksiyalarini chaqiramiz
    dp.message.register(start_answer, Command("start"))
    dp.message.register(help_answer, Command("help"))
    dp.message.register(menu_handler, lambda message: message.text in ["Накладные", "Главный меню"])

    dp.shutdown.register(shutdown_answer)

    bot = Bot("7769778979:AAFNG8nuj0m2rbWbJFHz8Jb2-FHS_Bv5qIc")
    await bot.set_my_commands([
        BotCommand(command='/start', description='Botni ishga tushirish.'),
        BotCommand(command='/help', description='Yordam.')
    ])
    await dp.start_polling(bot, polling_timeout=1)

run(start())
