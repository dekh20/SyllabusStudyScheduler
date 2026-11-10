"""Syllab.Us Lab 7 prototype data and business logic (standard library only)."""
from __future__ import annotations

from datetime import datetime
import sys
import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path

# Reuse the existing Lab 5 domain classes; do not replace team source files.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from py_unit_test_code.syllabus_prototype import AcademicTask, ReminderService

VALID_STATUSES = ('not_started', 'in_progress', 'completed')
ITERATIONS = 260_000


def hash_password(password: str, salt: str | None = None) -> str:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError('Password must contain at least 8 characters.')
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), ITERATIONS)
    return f'{salt}${digest.hex()}'


def verify_password(password: str, stored: str) -> bool:
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    try:
        salt, expected = stored.split('$', 1)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), ITERATIONS)
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def parse_due_at(raw: str) -> datetime:
    if not isinstance(raw, str):
        raise ValueError('A due date and time are required.')
    try:
        return datetime.strptime(raw, '%Y-%m-%dT%H:%M')
    except ValueError as exc:
        raise ValueError('Enter a valid due date and time.') from exc


def validate_status(status: str) -> str:
    # Reuse the team's AcademicTask status validation.
    sample = AcademicTask("Validation", datetime.now())
    sample.update_status(status)
    return status


def reminder_items(tasks: list[dict], now: datetime | None = None, hours: int = 48) -> list[dict]:
    """Use the team's ReminderService; return matching dashboard rows."""
    if not isinstance(tasks, list):
        raise TypeError("tasks must be a list")
    if not isinstance(hours, int) or isinstance(hours, bool) or hours < 0:
        raise ValueError("hours must be a non-negative integer")
    now = now or datetime.now()
    converted = []
    for row in tasks:
        if not isinstance(row, dict):
            raise TypeError("every task must be a dictionary")
        task = AcademicTask(row["title"], parse_due_at(row["due_at"]), row["status"])
        converted.append(task)
    eligible = ReminderService().eligible_tasks(converted, now, within_hours=hours)
    # Use object identity so duplicate task names/deadlines still map correctly.
    eligible_ids = {id(task) for task in eligible}
    return [row for row, task in sorted(zip(tasks, converted), key=lambda pair: pair[1].due_at)
            if id(task) in eligible_ids]


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._setup()

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _setup(self):
        with self.connect() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    course TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'not_started'
                        CHECK(status IN ('not_started', 'in_progress', 'completed'))
                );
            ''')

    def create_student(self, name: str, email: str, password: str) -> int:
        name = name.strip() if isinstance(name, str) else ''
        email = email.strip().lower() if isinstance(email, str) else ''
        if not name or len(name) > 80:
            raise ValueError('Enter a name (up to 80 characters).')
        if '@' not in email or not email.split('@')[-1].count('.') or len(email) > 254:
            raise ValueError('Enter a valid email address.')
        pw_hash = hash_password(password)
        try:
            with self.connect() as conn:
                cursor = conn.execute('INSERT INTO students (name, email, password_hash) VALUES (?, ?, ?)', (name, email, pw_hash))
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError('That email is already registered.') from exc

    def authenticate(self, email: str, password: str) -> dict | None:
        if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
            return None
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM students WHERE email = ?', (email.strip().lower(),)).fetchone()
        if not row or not verify_password(password, row['password_hash']):
            return None
        return dict(row)

    def get_student(self, student_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute('SELECT id, name, email FROM students WHERE id = ?', (student_id,)).fetchone()
        return dict(row) if row else None

    def add_task(self, student_id: int, title: str, course: str, due_at: str) -> int:
        title = title.strip() if isinstance(title, str) else ''
        course = course.strip() if isinstance(course, str) else ''
        if not title or len(title) > 150 or not course or len(course) > 80:
            raise ValueError('Enter a task title and course (150/80 characters max).')
        due = parse_due_at(due_at).strftime('%Y-%m-%dT%H:%M')
        with self.connect() as conn:
            cursor = conn.execute('INSERT INTO tasks (student_id, title, course, due_at) VALUES (?, ?, ?, ?)', (student_id, title, course, due))
            return int(cursor.lastrowid)

    def list_tasks(self, student_id: int) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM tasks WHERE student_id = ? ORDER BY due_at ASC, id ASC', (student_id,)).fetchall()
        return [dict(row) for row in rows]

    def update_status(self, student_id: int, task_id: int, status: str) -> bool:
        validate_status(status)
        with self.connect() as conn:
            cursor = conn.execute('UPDATE tasks SET status = ? WHERE id = ? AND student_id = ?', (status, task_id, student_id))
            return cursor.rowcount == 1

    def delete_task(self, student_id: int, task_id: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute('DELETE FROM tasks WHERE id = ? AND student_id = ?', (task_id, student_id))
            return cursor.rowcount == 1


