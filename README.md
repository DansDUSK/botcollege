# 🎓 College Schedule Bot / Бот замен для колледжа

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-red)](./LICENSE)

Telegram-бот для просмотра замен в расписании колледжа.  
Автоматически скачивает PDF с Яндекс.Диска, парсит таблицу и отдаёт студенту только нужную группу и день.

---

## 🇷🇺 Русский

### ✨ Что умеет бот

- 📅 **Замены на сегодня и завтра** — выбираешь группу и день, получаешь актуальный список.
- 🔄 **Формат «замена / вместо чего»** — видно, что меняется и на что.
- ⏸ **Обработка «Урок снят»** — отдельный статус для отменённых пар.
- 📚 **Раздел «Кабинеты»** — справочник аудиторий преподавателей.
- 🐞 **Кнопка «Нашли ошибку / недостающие данные?»** — присылает оригинальный PDF для проверки.
- 👥 **Удобный выбор по курсам и группам** — 40+ групп разбиты по годам поступления.
- 🧹 **Автоудаление мусорных сообщений** — чат не засоряется при переключении между группами.
- 📎 **Оригинал PDF** — всегда можно сверить данные вручную.

### 🏗️ Как это работает
Яндекс.Диск (PDF) → pdfplumber (парсинг таблицы) → Telegram Bot → Студент


1. Бот получает публичную ссылку на папку с PDF-файлами замен.
2. По названию файла (`ДД.ММ.ГГГГ.pdf`) определяет нужный день.
3. Скачивает PDF и парсит таблицу через `pdfplumber` (без OCR — точность 100%).
4. Разбирает данные по группам, урокам, предметам и преподавателям.
5. Отдаёт студенту красиво оформленный текст.

### 🚀 Установка и запуск
**1. Клонируй репозиторий:**
```
```bash
git clone https://github.com/your-username/college-bot.git
cd college-bot
```
2. Установи зависимости:

```bash
pip install -r requirements.txt
```
3. Настрой config.py:

```python
BOT_TOKEN = "ТОКЕН_ОТ_BOTFATHER"
YADISK_PUBLIC_URL = "https://disk.yandex.by/d/XXXXX"
```
4. Запусти:

```bash
python bot.py
```

📦 Зависимости
Библиотека	Назначение
aiogram	Telegram Bot API
requests	Скачивание PDF с Яндекс.Диска
pdfplumber	Парсинг PDF-таблиц

📁 Структура проекта
text
college-bot/
├── bot.py              # Основная логика бота
├── config.py           # Токен, ссылки, список групп
├── keyboards.py        # Инлайн-клавиатуры
├── parser.py           # Парсинг PDF
├── yandisk.py          # Скачивание с Яндекс.Диска
├── requirements.txt    # Зависимости
└── README.md
⚙️ Требования
Python 3.11+

Токен бота от @BotFather

Публичная папка на Яндекс.Диске с PDF-файлами замен

🇬🇧 English
✨ Features
📅 Today & tomorrow substitutions — pick your group and day, get the actual list.

🔄 "Substitution / instead of" format — clearly shows what's changing and to what.

⏸ "Class cancelled" handling — dedicated status for cancelled lessons.

📚 "Classrooms" section — teacher-to-room reference.

🐞 "Found a bug / missing data?" button — sends the original PDF for verification.

👥 Course & group navigation — 40+ groups organized by enrollment year.

🧹 Auto-cleanup of redundant messages — chat stays clean when switching groups.

📎 Original PDF access — always verify parsed data manually.

🏗️ How It Works
text
Yandex.Disk (PDF)  →  pdfplumber (table parsing)  →  Telegram Bot  →  Student
Bot receives a public link to a folder with substitution PDFs.

Determines the target day by filename (DD.MM.YYYY.pdf).

Downloads the PDF and parses it via pdfplumber (no OCR — 100% accuracy).

Extracts data by group, lesson, subject and teacher.

Sends a nicely formatted message back to the student.

🚀 Setup
1. Clone the repo:
```
bash
git clone https://github.com/your-username/college-bot.git
cd college-bot
```
2. Install dependencies:

```bash
pip install -r requirements.txt
```
3. Configure config.py:

```python
BOT_TOKEN = "YOUR_BOTFATHER_TOKEN"
YADISK_PUBLIC_URL = "https://disk.yandex.by/d/XXXXX"
```
4. Run:

```bash
python bot.py
```
📦 Dependencies
Library	Purpose
aiogram	Telegram Bot API
requests	PDF download from Yandex.Disk
pdfplumber	PDF table parsing

📁 Project Structure
text
college-bot/
├── bot.py              # Main bot logic
├── config.py           # Token, links, groups list
├── keyboards.py        # Inline keyboards
├── parser.py           # PDF parsing
├── yandisk.py          # Yandex.Disk downloader
├── requirements.txt    # Dependencies
└── README.md

⚙️ Requirements
Python 3.11+

Bot token from @BotFather

Public Yandex.Disk folder with substitution PDFs

🛡️ License / Лицензия
All Rights Reserved.
Все права защищены.

© 2026 DansDagger.
Копирование, распространение и использование кода без письменного разрешения автора запрещено.
Copying, distribution, or use of this code without the author's written permission is prohibited.

🙏 Credits
Developer: @daggerka

Testers: @nelokhe, @desoolatee

Built with: aiogram, pdfplumber

⭐ Если бот оказался полезным — поставь звезду на GitHub!
⭐ If you found this bot useful — drop a star on GitHub!


**All Rights Reserved.**
**Copyright (c) 2026 DansDagger**
**No part of this software may be reproduced, distributed, or transmitted**
**In any form or by any means without the prior written permission of the author.**
