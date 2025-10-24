import sqlite3
import logging
from datetime import datetime, timedelta
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deffer_id INTEGER,
                victim_info TEXT,
                status TEXT DEFAULT 'pending',
                admin_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deffer_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                user_id INTEGER PRIMARY KEY,
                week_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()

    def get_user_role(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 'user'

    def add_user(self, user_id, username, role='user'):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, role) 
            VALUES (?, ?, ?)
        ''', (user_id, username, role))
        
        cursor.execute('''
            INSERT OR IGNORE INTO statistics (user_id) VALUES (?)
        ''', (user_id,))
        
        self.conn.commit()

    def add_review(self, deffer_id, victim_info):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO reviews (deffer_id, victim_info) 
            VALUES (?, ?)
        ''', (deffer_id, victim_info))
        review_id = cursor.lastrowid
        self.conn.commit()
        return review_id

    def update_review_status(self, review_id, status, admin_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE reviews SET status = ?, admin_id = ? 
            WHERE id = ?
        ''', (status, admin_id, review_id))
        
        if status == 'accepted':
            cursor.execute('SELECT deffer_id FROM reviews WHERE id = ?', (review_id,))
            deffer_id = cursor.fetchone()[0]
            self.increment_stats(deffer_id)
        
        self.conn.commit()

    def increment_stats(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE statistics 
            SET week_count = week_count + 1, total_count = total_count + 1,
                last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()

    def get_stats(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT week_count, total_count FROM statistics WHERE user_id = ?', (user_id,))
        return cursor.fetchone() or (0, 0)

    def get_all_deffers_stats(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.username, s.week_count, s.total_count
            FROM users u
            JOIN statistics s ON u.user_id = s.user_id
            WHERE u.role = 'deffer'
            ORDER BY s.week_count DESC
        ''')
        return cursor.fetchall()

    def clear_week_stats(self):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE statistics SET week_count = 0')
        self.conn.commit()

    def set_user_role(self, user_id, role):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
        self.conn.commit()

    def get_pending_reviews_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM reviews WHERE status = "pending"')
        return cursor.fetchone()[0]

    def manual_update_stats(self, user_id, week_count, total_count):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE statistics 
            SET week_count = ?, total_count = ?
            WHERE user_id = ?
        ''', (week_count, total_count, user_id))
        self.conn.commit()