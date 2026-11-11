import sqlite3

DB_PATH = "bot.db"

def init_db():
    """Создаёт таблицу пользователей, если её нет."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            notifications_enabled INTEGER DEFAULT 1,
            last_notified_file TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int):
    """Добавляет пользователя в базу при /start."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_users_for_notification() -> list[int]:
    """Возвращает список user_id, у которых включены уведомления."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE notifications_enabled = 1")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_last_notified(user_id: int) -> str:
    """Возвращает имя последнего файла, о котором пользователь получил уведомление."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT last_notified_file FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

def set_last_notified(user_id: int, filename: str):
    """Сохраняет имя файла, о котором отправлено уведомление."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_notified_file = ? WHERE user_id = ?", (filename, user_id))
    conn.commit()
    conn.close()

def toggle_notifications(user_id: int) -> bool:
    """Переключает уведомления (вкл/выкл) и возвращает новое состояние."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT notifications_enabled FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        # Если пользователя нет, добавляем и включаем уведомления
        cursor.execute("INSERT INTO users (user_id, notifications_enabled) VALUES (?, 1)", (user_id,))
        new_state = True
    else:
        new_state = not bool(row[0])
        cursor.execute("UPDATE users SET notifications_enabled = ? WHERE user_id = ?", (int(new_state), user_id))
        
    conn.commit()
    conn.close()
    return new_state
