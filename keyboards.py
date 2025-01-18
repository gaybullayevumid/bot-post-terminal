from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

delivery_notes = ReplyKeyboardMarkup(
    keyboard = [
        [
            KeyboardButton(text="Январь"),
            KeyboardButton(text="Февраль"),
            KeyboardButton(text="Март")
        ],
        [
            KeyboardButton(text="Апрель"),
            KeyboardButton(text="Май"),
            KeyboardButton(text="Июнь")
        ],
        [
            KeyboardButton(text="Июль"),
            KeyboardButton(text="Август"),
            KeyboardButton(text="Сентябрь")
        ],
        [
            KeyboardButton(text="Октябрь"),
            KeyboardButton(text="Ноябрь"),
            KeyboardButton(text="Декабрь")
        ],
        [
            KeyboardButton(text="Главный меню")
        ]
    ],
    resize_keyboard=True
)