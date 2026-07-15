import sqlite3
from datetime import datetime
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
CREATE TABLE IF NOT EXISTS deadlines(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   title TEXT,
                   deadline_date TEXT,
                   created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                   done BOOLEAN DEFAULT 0)
''')
    
    cursor.execute('''
CREATE TABLE IF NOT EXISTS links(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   category TEXT,
                   title TEXT, 
                   url TEXT,
                   created_at TEXT DEFAULT CURRENT_TIMESTAMP)
                   ''')
    

    cursor.execute('''
CREATE TABLE IF NOT EXISTS users(
                   user_id INTEGER PRIMARY KEY, 
                   first_name TEXT,
                   username TEXT,
                   joined_at TEXT DEFAULT CURRENT_TIMESTAMP)
                   ''')
    
    conn.commit()
    conn.close()
    print('БД инициализирована')


def add_deadline(user_id: int, title: str, deadline_date: str):
    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO deadlines (user_id, title, deadline_date) VALUES (?,?,?)',
        (user_id, title,deadline_date)
    )
    conn.commit()
    conn.close()
    print('Дедлайн добавлен: {title} ({deadline_date})')

def get_one_deadline(deadline_id: int, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, deadline_date, done FROM deadlines WHERE id = ? AND user_id = ?', (deadline_id, user_id))
    deadline = cursor.fetchone()
    conn.close()
    return deadline


def get_deadlines(user_id: int, only_active:bool = False):
    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    

    if only_active:
        cursor.execute(
            'SELECT id, title, deadline_date, done FROM deadlines WHERE user_id = ? AND done = 0 ORDER BY deadline_date',
            (user_id,)
        )

    else:
        cursor.execute(
            'SELECT id, title, deadline_date, done FROM deadlines WHERE user_id = ? ORDER BY deadline_date',
            (user_id,)
        )

    deadlines = cursor.fetchall()
    conn.close()
    return deadlines

def complete_deadline(deadline_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE deadlines SET done = 1 WHERE id = ?', (deadline_id,))
    conn.commit()
    conn.close()
    print('Дедлайн #{deadline_id} выполнен')


def delete_deadline(deadline_id: int):
    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM deadlines WHERE id = ?', (deadline_id,))
    conn.commit()
    conn.close()
    print(f'Дедлайн #{deadline_id} удалён')


def add_link(user_id: int, category: str, title: str, url: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO links (user_id, category, title, url) VALUES (?,?,?,?)',
        (user_id, category.lower(), title, url)
    )

    conn.commit()
    conn.close()
    print('Ссылка добавлена: {title} ({category})')


def get_links(user_id: int, category: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if category:
        cursor.execute(
            'SELECT id, title, url FROM links WHERE user_id = ? AND category = ? ORDER BY created_at',
            (user_id, category.lower())
        )

    else:
        cursor.execute(
            'SELECT id, title, url, category FROM links WHERE user_id = ? ORDER BY category',
            (user_id,)
        )

    links = cursor.fetchall()
    conn.close()
    return links if links is not None else []
    
def delete_link(link_id: int, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM links WHERE id = ? AND user_id = ?', (link_id, user_id)
    )
    exists = cursor.fetchone() is not None
    if exists:
        cursor.execute('DELETE FROM links WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_categories(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category FROM links WHERE user_id = ?',
                   (user_id,))
    categories = cursor.fetchall()
    conn.close()
    return [c[0] for c in categories]

def add_user(user_id: int, first_name: str = '', username: str = ''):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?,?,?)',
    (user_id, first_name, username)
    )
    conn.commit()
    conn.close()


def get_stats(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM deadlines WHERE user_id = ? AND done = 0',
                   (user_id,))
    active_deadlines = cursor.fetchall()[0]
    cursor.execute('SELECT COUNT(*) FROM deadlines WHERE user_id = ?',(user_id,))
    total_deadlines = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM links WHERE user_id = ?', (user_id,))
    total_links = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT category) FROM links WHERE user_id = ?',(user_id,))
    total_categories = cursor.fetchone()[0]
    conn.close()
    return{
        'active_deadlines': active_deadlines,
        'total_deadlines': total_deadlines,
        'total_links': total_links,
        'total_categories': total_categories
    }

def get_user_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def clear_deadlines(user_id:int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM deadlines WHERE user_id = ?', (user_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count

def clear_active_deadlines(user_id:int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM deadlines WHERE user_id = ? AND done = 1', (user_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


def get_deadlines_by_date(user_id: int, target_date:str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, title, deadline_date, done FROM deadlines WHERE user_id = ? AND deadline_date = ?', (user_id, target_date) 
    )
    deadlines = cursor.fetchall()
    conn.close()
    return deadlines

def get_all_active_deadlines():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, user_id, title, deadline_date FROM deadlines WHERE done = 0'
    )
    deadlines = cursor.fetchall()
    conn.close()
    return deadlines


def deadline_exists_for_user(user_id: int, title: str, date: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM deadlines  WHERE user_id = ? AND title = ? AND deadline_date =? AND done = 0',
        (user_id, title, date)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def link_exists_for_user(user_id: int, category: str, title: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM links WHERE user_id = ? AND category = ? AND title =?',
        (user_id, category.lower(), title)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def delete_category(user_id: int, category: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM links WHERE user_id = ? AND category = ?',
        (user_id, category.lower())
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted