from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Регистрация"),
            KeyboardButton(text="Накладные")
        ],
        [
            KeyboardButton(text="☎️Контакты")
        ]
    ],
    resize_keyboard=True
)

delivery_notes = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Январь"), KeyboardButton(text="Февраль"), KeyboardButton(text="Март")],
        [KeyboardButton(text="Апрель"), KeyboardButton(text="Май"), KeyboardButton(text="Июнь")],
        [KeyboardButton(text="Июль"), KeyboardButton(text="Август"), KeyboardButton(text="Сентябрь")],
        [KeyboardButton(text="Октябрь"), KeyboardButton(text="Ноябрь"), KeyboardButton(text="Декабрь")],
        [KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)
