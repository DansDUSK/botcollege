import asyncio
import logging
import os
from datetime import datetime, timedelta
import time

from aiogram import Bot, Dispatcher, F
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiohttp import web

from config import BOT_TOKEN
from keyboards import (
    main_menu, courses_keyboard, groups_keyboard, days_keyboard, back_keybord,
    bug_report_keyboard, bug_report_keyboard_no_group, cabinets_days_keyboard,
)
from gdrive import download_pdf_by_name, list_files_in_folder, GDRIVE_FOLDER_ID
from parser import parse_pdf, format_zameni, format_legend
from database import (
    init_db, add_user, get_users_for_notification, get_last_notified, set_last_notified
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кэш для PDF
pdf_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL = 3 * 60 * 60  # 3 часа

dp.callback_query.middleware(CallbackAnswerMiddleware())

last_bug_msg: dict[int, int] = {}

# --- Проверка уведомлений ---
async def check_and_notify():
    """Проверяет новые файлы на Google Drive и рассылает уведомления."""
    try:
        files = list_files_in_folder(GDRIVE_FOLDER_ID)
        if not files:
            print("[notify] Список файлов пуст")
            return

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y") + ".pdf"
        print(f"[notify] Ищем файл: {tomorrow}")

        found = any(f.get("path") == tomorrow for f in files)
        if not found:
            print(f"[notify] Файл {tomorrow} ещё не выложен")
            return

        users = get_users_for_notification()
        print(f"[notify] Файл найден! Рассылаем {len(users)} пользователям")

        for user_id in users:
            last = get_last_notified(user_id)
            if last != tomorrow:
                try:
                    await bot.send_message(
                        user_id,
                        f"🔔 *Новые замены!*\n\n"
                        f"На завтра ({tomorrow}) выложили замены.\n"
                        f"Загляни в бота, чтобы посмотреть.",
                        parse_mode="Markdown"
                    )
                    set_last_notified(user_id, tomorrow)
                    print(f"[notify] Отправлено {user_id}")
                except Exception as e:
                    print(f"[notify] Ошибка для {user_id}: {e}")
    except Exception as e:
        print(f"[notify] Ошибка проверки: {e}")

# --- Веб-сервер для Render ---
async def handle_health(request):
    """Эндпоинт для cron-job.org."""
    asyncio.create_task(check_and_notify())  # Запускаем проверку в фоне
    return web.Response(text="OK")

async def handle_root(request):
    return web.Response(text="Бот замен активен и работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[Render] Веб-сервер запущен на порту {port}")

# --- Хендлеры ---

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
    add_user(message.from_user.id)  # Регистрируем пользователя
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
        "На данный момент бот все также разрабатывается (убираются ошибки с распознованием замен) - *спасибо за понимание!*\n"
        "Разработчик💻: \n*Скрыт*\n"
        "Тестировщики📱:\n@nelokhe\n@desoolatee\n\n"
        "🔗 Исходный код есть на GitHub: [Тык](https://github.com/DansDUSK/botcollege)\n\n"
        "*Все права защищены.*",
        parse_mode="Markdown",
        reply_markup=back_keybord()
    )

@dp.callback_query(F.data == "menu:notifications")
async def toggle_notif(call: CallbackQuery):
    from database import toggle_notifications
    new_state = toggle_notifications(call.from_user.id)
    status = "включены" if new_state else "выключены"
    await call.answer(f"Уведомления {status}", show_alert=True)

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
    await call.message.edit_text(
        "📚 *Кабинеты*\nНа какой день показать расписание кабинетов?",
        parse_mode="Markdown",
        reply_markup=cabinets_days_keyboard()
    )

@dp.callback_query(F.data.startswith("course:"))
async def choose_course(call: CallbackQuery):
    await delete_previous_bug(call)
    course = call.data.split(":", 1)[1]
    await call.message.edit_text(
        f"📚 *{course}*\nВыбери группу:",
        parse_mode="Markdown",
        reply_markup=groups_keyboard(course)
    )

@dp.callback_query(F.data.startswith("cabinets_day:"))
async def cabinets_by_day(call: CallbackQuery):
    _, day = call.data.split(":")
    await delete_previous_bug(call)
    await call.answer("Загружаю...")

    filename, day_label, date_label = get_filename_and_labels(day)
    pdf_path = f"temp_{filename}"

    try:
        now = time.time()
        cached = pdf_cache.get(filename)
        if cached and (now - cached[1]) < CACHE_TTL:
            data = cached[0]
        else:
            if not os.path.exists(pdf_path):
                ok = download_pdf_by_name(filename, pdf_path)
                if not ok:
                    await call.message.edit_text(
                        f"❌ Не удалось скачать PDF `{filename}`.",
                        parse_mode="Markdown",
                        reply_markup=cabinets_days_keyboard()
                    )
                    return
            data = parse_pdf(pdf_path)
            pdf_cache[filename] = (data, now)

        legend = data.get("__legend__", [])
        text = format_legend(legend)
        text = text.replace(
            "📚 *Расписание кабинетов*",
            f"📚 *Расписание кабинетов*\n📅 {day_label}, {date_label}",
            1
        )

        try:
            await call.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=cabinets_days_keyboard()
            )
        except Exception as e:
            if "message is not modified" in str(e):
                await call.answer("Данные уже актуальны ✅")
            else:
                raise

        bug_msg = await call.message.answer(
            "Если не хватает данных о кабинетах — нажмите кнопку ниже.",
            reply_markup=bug_report_keyboard_no_group(day)
        )
        last_bug_msg[call.from_user.id] = bug_msg.message_id

    except Exception as e:
        logging.exception("Ошибка в cabinets_by_day")
        if "message is not modified" not in str(e):
            await call.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_keybord())
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass

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
        now = time.time()
        cached = pdf_cache.get(filename)
        if cached and (now - cached[1]) < CACHE_TTL:
            data = cached[0]
            print(f"[cache] Используем кэш для {filename}")
        else:
            if not os.path.exists(pdf_path):
                ok = download_pdf_by_name(filename, pdf_path)
                if not ok:
                    await call.message.edit_text(
                        f"❌ Не удалось скачать PDF `{filename}`.\n"
                        f"Возможно, замены на этот день ещё не выложили.",
                        parse_mode="Markdown",
                        reply_markup=main_menu()
                    )
                    return

            data = parse_pdf(pdf_path)
            pdf_cache[filename] = (data, now)
            print(f"[cache] Обновили кэш для {filename}")

        zameni = data.get(group, [])
        
        if not zameni:
            if not os.path.exists(pdf_path):
                download_pdf_by_name(filename, pdf_path)
            doc = FSInputFile(pdf_path, filename=filename)
            await call.message.edit_text(
                f"😊 На завтра замен у группы *{group}* нету.\n",
                parse_mode="Markdown", reply_markup=back_keybord()
            )
            await call.message.answer("Если заметили ошибки или недостающие данные, ниже оригинальный файл замен! (Возможны ошибки в автоматическом распозновании)\n")
            await call.message.answer_document(doc)
            return
        
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

    except Exception as e:
        logging.exception("Ошибка в send_zameni")
        await call.message.edit_text(f"❌ Ошибка: {e}", reply_markup=main_menu())
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
                    f"❌ Не удалось скачать оригинал `{filename}`",
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
    init_db()  # Инициализация БД
    await start_web_server()  # Запуск веб-сервера
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
