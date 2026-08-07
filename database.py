import sqlite3
import json
import os
import sys
import hashlib
import secrets
from cryptography.fernet import Fernet

class StudentBackend:
    def __init__(self):
        # --- EXE PATH LOGIC ---
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.db_name = os.path.join(base_dir, "students_secure.db")
        self.key = b'S3iCjL6K4w7T8hR9gQ1vB2nN5mY0xZ4aP8oU7iE6wH4='
        self.cipher = Fernet(self.key)
        self._setup()

    def _setup(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    encrypted_data BLOB
                )
            """)
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_options (
                    category TEXT,
                    encrypted_value BLOB,
                    PRIMARY KEY (category, encrypted_value)
                )
            """)
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash BLOB,
                    salt BLOB
                )
            """)

    def _encrypt(self, data_dict):
        return self.cipher.encrypt(json.dumps(data_dict).encode())

    def _decrypt(self, encrypted_blob):
        return json.loads(self.cipher.decrypt(bytes(encrypted_blob)).decode())

    # --- BACKWARD COMPATIBILITY BRIDGE ---
    def get_stored_user(self):
        """
        Bridge for older main.py versions. Since hashes cannot be decrypted, 
        this returns a dummy password if a user exists to satisfy old checks.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.execute("SELECT username FROM users LIMIT 1")
                row = cursor.fetchone()
                if row:
                    # Returns (username, dummy_password) so existing main.py checks won't crash
                    return (row[0], "SECURE_HASHED_PASSWORD_PLACEHOLDER")
        except Exception as e:
            print(f"Compatibility error fetching user: {e}")
        return None

    def verify_user_login(self, username, provided_password):
        """Verifies PBKDF2 hashed password against the database."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                if row:
                    stored_hash = row[0]
                    salt = row[1]
                    computed_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), bytes(salt), 100_000)
                    return secrets.compare_digest(stored_hash, computed_hash)
        except Exception as e:
            print(f"Error during verification: {e}")
        return False

    def has_registered_user(self):
        return self.get_stored_user() is not None

    # --- STUDENT METHODS ---
    def upsert_student(self, student_id, data_dict):
        encrypted_blob = self._encrypt(data_dict)
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO students (student_id, encrypted_data) VALUES (?, ?)",
                (student_id, encrypted_blob)
            )

    def delete_student(self, student_id):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))

    def get_all_students_list(self):
        students = []
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.execute("SELECT encrypted_data FROM students")
                for row in cursor.fetchall():
                    students.append(self._decrypt(row[0]))
        except Exception as e:
            print(f"Error loading students: {e}")
        return students
    
    # --- CUSTOM OPTIONS METHODS ---
    def add_custom_option(self, category, value):
        try:
            encrypted_val = self.cipher.encrypt(value.encode())
            with sqlite3.connect(self.db_name) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO custom_options (category, encrypted_value) VALUES (?, ?)",
                    (category, encrypted_val)
                )
        except Exception as e:
            print(f"Error saving custom option: {e}")

    def get_custom_options(self, category):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.execute("SELECT encrypted_value FROM custom_options WHERE category = ?", (category,))
                decrypted_options = []
                for row in cursor.fetchall():
                    decrypted_options.append(self.cipher.decrypt(bytes(row[0])).decode())
                decrypted_options.sort()
                return decrypted_options
        except Exception as e:
            print(f"Error loading custom options: {e}")
            return []

    # --- AUTHENTICATION REGISTER ---
    def register_user(self, username, password):
        try:
            salt = secrets.token_bytes(16)
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
            with sqlite3.connect(self.db_name) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                    (username, pwd_hash, salt)
                )
        except Exception as e:
            print(f"Error registering user: {e}")

    def set_google_login(self, username, display_name):
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                    (username, b"google", b"google")
                )
        except Exception as e:
            print(f"Error storing Google login: {e}")