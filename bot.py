import asyncio
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile

from config import BOT_TOKEN
from keyboards import (
    main_menu, courses_keyboard, groups_keyboard, days_keyboard, back_keybord,
    bug_report_keyboard, bug_report_keyboard_no_group,
)
from yandisk import download_pdf_by_name
from parser import parse_pdf, format_zameni, format_legend

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.callback_query.middleware(CallbackAnswerMiddleware())

last_bug_msg: dict[int, int] = {}


async def delete_previous_bug(call: CallbackQuery) -> None:
    user_id = call.from_user.id
    msg_id = last_bug_msg.pop(user_id, None)
    if msg_id is None:
        return
    try:
        await call.message.bot.delete_message(
            chat_id=call.message.chat.id,
            message_id=msg_id
        )
        print(f"[bug] удалили сообщение {msg_id} для {user_id}")
    except Exception as e:
        print(f"[bug] не удалось удалить {msg_id}: {e}")


def get_filename_and_labels(day: str) -> tuple[str, str, str]:
    offset = 0 if day == "today" else 1
    target = datetime.now() + timedelta(days=offset)
    filename = target.strftime("%d.%m.%Y") + ".pdf"
    day_label = "Сегодня" if day == "today" else "Завтра"
    date_label = target.strftime("%d.%m.%Y")
    return filename, day_label, date_label


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! \nЯ твой бот для просмотра замен🚀\nВыбери, что тебе нужно:",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "menu:main")
async def back_main(call: CallbackQuery):
    await delete_previous_bug(call)
    await call.message.edit_text(
        "🎇 Главное меню:",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "about_me")
async def about_me(call: CallbackQuery):
    await delete_previous_bug(call)
    await call.message.edit_text(
        "*Бот создан в учебных целях*, для облегчения просмотра замен 😋\n"
        " Разработчик💻: \n@daggerka\n"
        "Тестировщики📱:\n@nelokhe\n@desoolatee\n\n"
        "🔗 Исходный код есть на GitHub: [Тык](https://github.com/DansDUSK)\n\n"
        "*Все права защищены.*",
        parse_mode="Markdown",
        reply_markup=back_keybord()
    )


@dp.callback_query(F.data == "menu:zameni")
async def menu_zameni(call: CallbackQuery):
    await delete_previous_bug(call)
    await call.message.edit_text(
        "📅 *Замены*\nВыбери свой курс:",
        parse_mode="Markdown",
        reply_markup=courses_keyboard()
    )


@dp.callback_query(F.data == "menu:cabinets")
async def menu_cabinets(call: CallbackQuery):
    await delete_previous_bug(call)
    await call.answer("Загружаю...")

    filename, _, _ = get_filename_and_labels("today")
    pdf_path = f"temp_{filename}"

    try:
        if not os.path.exists(pdf_path):
            ok = download_pdf_by_name(filename, pdf_path)
            if not ok:
                await call.message.edit_text(
                    f"❌ Не удалось скачать PDF `{filename}`.",
                    parse_mode="Markdown",
                    reply_markup=back_keybord()
                )
                return

        data = parse_pdf(pdf_path)
        legend = data.get("__legend__", [])
        text = format_legend(legend)

        await call.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=back_keybord()
        )

        bug_msg = await call.message.answer(
            "Если не хватает данных о кабинетах — нажмите кнопку ниже.",
            reply_markup=bug_report_keyboard_no_group("today")
        )
        last_bug_msg[call.from_user.id] = bug_msg.message_id
        print(f"[bug] сохранили {bug_msg.message_id} для {call.from_user.id}")

    except Exception as e:
        logging.exception("Ошибка в menu_cabinets")
        await call.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_keybord())
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass


@dp.callback_query(F.data.startswith("course:"))
async def choose_course(call: CallbackQuery):
    await delete_previous_bug(call)
    course = call.data.split(":", 1)[1]
    await call.message.edit_text(
        f"📚 *{course}*\nВыбери группу:",
        parse_mode="Markdown",
        reply_markup=groups_keyboard(course)
    )


@dp.callback_query(F.data.startswith("group:"))
async def choose_group(call: CallbackQuery):
    await delete_previous_bug(call)
    group = call.data.split(":", 1)[1]
    await call.message.edit_text(
        f"👥 Группа *{group}*\nНа какой день показать замены?",
        parse_mode="Markdown",
        reply_markup=days_keyboard(group)
    )


@dp.callback_query(F.data.startswith("day:"))
async def send_zameni(call: CallbackQuery):
    _, group, day = call.data.split(":")
    filename, day_label, date_label = get_filename_and_labels(day)

    await call.answer("Загружаю...")
    await call.message.edit_text(
        f"⏳ Загружаю замены для *{group}* на {day_label.lower()} ({date_label})...",
        parse_mode="Markdown"
    )

    pdf_path = f"temp_{filename}"

    try:
        if not os.path.exists(pdf_path):
            ok = download_pdf_by_name(filename, pdf_path)
            if not ok:
                await call.message.edit_text(
                    f"❌ Не удалось скачать PDF `{filename}`.\n"
                    f"Возможно, замены на этот день ещё не выложили.",
                    parse_mode="Markdown",
                    reply_markup=back_keybord()
                )
                return

        data = parse_pdf(pdf_path)
        zameni = data.get(group, [])
        text = format_zameni(group, zameni, day_label, date_label)

        await call.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=days_keyboard(group)
        )

        bug_msg = await call.message.answer(
            f"Если заметили ошибку или не хватает данных для группы *{group}* — "
            f"нажмите кнопку ниже.",
            parse_mode="Markdown",
            reply_markup=bug_report_keyboard(group, day)
        )
        last_bug_msg[call.from_user.id] = bug_msg.message_id
        print(f"[bug] сохранили {bug_msg.message_id} для {call.from_user.id}")

    except Exception as e:
        logging.exception("Ошибка в send_zameni")
        await call.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_keybord())
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass


@dp.callback_query(F.data.startswith("bug:"))
async def bug_report(call: CallbackQuery):
    _, group, day = call.data.split(":")
    filename, day_label, date_label = get_filename_and_labels(day)

    await call.answer("Отправляю оригинал...")
    await delete_previous_bug(call)

    pdf_path = f"temp_{filename}"

    try:
        if not os.path.exists(pdf_path):
            ok = download_pdf_by_name(filename, pdf_path)
            if not ok:
                await call.message.answer(
                    f"❌ Не удалось скачать оригинал `{filename}` с Яндекс.Диска.",
                    parse_mode="Markdown"
                )
                return

        doc = FSInputFile(pdf_path, filename=filename)
        caption = f"📎 Оригинал замен на {day_label.lower()} ({date_label})"
        if group and group != "none":
            caption += f"\nГруппа: {group}"
        caption += "\n\nПроверьте данные по оригиналу."

        await call.message.answer_document(doc, caption=caption)

    except Exception as e:
        logging.exception("Ошибка в bug_report")
        await call.message.answer(f"❌ Ошибка: {e}")
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())