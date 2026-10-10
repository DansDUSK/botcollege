from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import GROUPS_BY_COURSE


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Замены", callback_data="menu:zameni")],
        [InlineKeyboardButton(text="📚 Кабинеты", callback_data="menu:cabinets")],
        [InlineKeyboardButton(text="👾 О нас", callback_data="about_me")]
    ])

def back_keybord() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
    ])
def courses_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for course in GROUPS_BY_COURSE:
        buttons.append([InlineKeyboardButton(text=course, callback_data=f"course:{course}")])
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def groups_keyboard(course: str) -> InlineKeyboardMarkup:
    groups = GROUPS_BY_COURSE.get(course, [])
    buttons = []
    row = []
    for g in groups:
        row.append(InlineKeyboardButton(text=g, callback_data=f"group:{g}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:zameni")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def days_keyboard(group: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data=f"day:{group}:today"),
            InlineKeyboardButton(text="📅 Завтра", callback_data=f"day:{group}:tomorrow"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:zameni")],
    ])
    
def bug_report_keyboard(group: str, day: str) -> InlineKeyboardMarkup:
    """Кнопка 'Нашли ошибку' для экрана замен."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🐞 Нашли ошибку или недостающие данные?",
            callback_data=f"bug:{group}:{day}"
        )],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:zameni")],
    ])


def bug_report_keyboard_no_group(day: str = "today") -> InlineKeyboardMarkup:
    """Кнопка 'Нашли ошибку' для раздела Кабинеты."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🐞 Нашли ошибку или недостающие данные?",
            callback_data=f"bug:none:{day}"
        )],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")],
    ])