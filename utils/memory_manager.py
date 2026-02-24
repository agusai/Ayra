# utils/memory_manager.py
# Version tanpa chroma - guna simple vault

import sqlite3
import json
from datetime import datetime
from .chroma_vault_simple import ChromaVault  # GUNA SIMPLE VERSION

DB_PATH = "memory.db"

class MemoryManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()
        # Guna simple vault
        self.vault = ChromaVault()

    def _create_tables(self):
        cursor = self.conn.cursor()
        # Conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_message TEXT,
                ayra_response TEXT,
                mood_score REAL,
                model_used TEXT
            )
        """)
        # User profile
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        # Stories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TEXT,
                last_continued TEXT
            )
        """)
        # Dreams
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dreams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dream_text TEXT,
                date TEXT
            )
        """)
        # Stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        """)
        self.conn.commit()

    # ===== CONVERSATIONS =====
    def save_interaction(self, user_msg, ayra_msg, mood_score=0.0, model_used="Gemini"):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (timestamp, user_message, ayra_response, mood_score, model_used) VALUES (?, ?, ?, ?, ?)",
            (datetime.now(malaysia_tz).isoformat(), user_msg, ayra_msg, mood_score, model_used)
        )
        self.conn.commit()
        # Juga simpan ke vault (simple version tak buat apa-apa)
        self.vault.save_conversation(user_msg, ayra_msg, mood_score, model_used)

    def get_recent_conversations(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT user_message, ayra_response FROM conversations ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        context = []
        for user, ayra in reversed(rows):
            context.append({"role": "user", "content": user})
            context.append({"role": "assistant", "content": ayra})
        return context

    # ===== USER PROFILE =====
    def get_profile(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM user_profile WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_profile(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute(
            "REPLACE INTO user_profile (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now(malaysia_tz).isoformat())
        )
        self.conn.commit()

    # ===== STORIES =====
    def save_story(self, title, content):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO stories (title, content, created_at, last_continued) VALUES (?, ?, ?, ?)",
            (title, content, datetime.now(malaysia_tz).isoformat(), datetime.now(malaysia_tz).isoformat())
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_latest_story(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, content FROM stories ORDER BY last_continued DESC LIMIT 1")
        row = cursor.fetchone()
        return {"id": row[0], "title": row[1], "content": row[2]} if row else None

    def update_story(self, story_id, new_content):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE stories SET content = content || ? , last_continued = ? WHERE id = ?",
            (new_content, datetime.now(malaysia_tz).isoformat(), story_id)
        )
        self.conn.commit()

    # ===== DREAMS =====
    def save_dream(self, dream_text):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO dreams (dream_text, date) VALUES (?, ?)",
            (dream_text, datetime.now(malaysia_tz).isoformat())
        )
        self.conn.commit()

    # ===== STATS =====
    def increment_stat(self, key, inc=1):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO user_stats (key, value) VALUES (?, 0)", (key,))
        cursor.execute("UPDATE user_stats SET value = value + ? WHERE key = ?", (inc, key))
        self.conn.commit()

    def get_stat(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM user_stats WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else 0

    # ===== CRISIS LOG =====
    def log_crisis_event(self, user_message, detected_keyword):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crisis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_message TEXT,
                detected_keyword TEXT,
                handled BOOLEAN DEFAULT 1
            )
        """)
        cursor.execute(
            "INSERT INTO crisis_log (timestamp, user_message, detected_keyword) VALUES (?, ?, ?)",
            (datetime.now(malaysia_tz).isoformat(), user_message[:200], detected_keyword)
        )
        self.conn.commit()

    # ===== SIMPLE VAULT METHODS (untuk compatibility) =====
    def save_to_vault(self, user_msg, ayra_msg, mood_score=0.0, model_used="Gemini", is_important=False):
        # Simple version - tak buat apa-apa
        pass

    def search_memories(self, query, n_results=5):
        return []

    def get_important_memories(self, limit=5):
        return []

    def get_vault_stats(self):
        return {'total_memories': 0}