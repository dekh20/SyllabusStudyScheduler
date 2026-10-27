"""Lab 5 prototype: authentication/2FA, assignment progress, and reminders.
Standard-library only. Not connected to a production app or email provider.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import hmac


class AuthService:
    def __init__(self):
        self._accounts = {}
        self._pending = {}

    @staticmethod
    def _hash(value):
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def register(self, email, password):
        if not isinstance(email, str) or '@' not in email or not isinstance(password, str) or len(password) < 8:
            raise ValueError('Valid email and password of at least 8 characters required')
        if email in self._accounts:
            raise ValueError('Email already registered')
        self._accounts[email] = self._hash(password)

    def login(self, email, password):
        if not isinstance(email, str) or not isinstance(password, str):
            return False
        saved = self._accounts.get(email)
        return saved is not None and hmac.compare_digest(saved, self._hash(password))

    def begin_two_factor(self, email, password, code, now):
        if not self.login(email, password):
            return False
        self._pending[email] = VerificationCode(code, now + timedelta(minutes=5))
        return True

    def verify_two_factor(self, email, code, now):
        verification = self._pending.get(email)
        return verification is not None and verification.verify(code, now)


class VerificationCode:
    def __init__(self, code, expires_at):
        if not isinstance(code, str) or len(code) != 6 or not code.isascii() or not code.isdigit():
            raise ValueError('Passcode must be six ASCII digits')
        self._code_hash = hashlib.sha256(code.encode()).hexdigest()
        self.expires_at = expires_at
        self.used = False

    def verify(self, code, now):
        if self.used or not isinstance(code, str) or now >= self.expires_at:
            return False
        expected = hashlib.sha256(code.encode()).hexdigest()
        if not hmac.compare_digest(self._code_hash, expected):
            return False
        self.used = True
        return True


@dataclass
class AcademicTask:
    title: str
    due_at: datetime
    status: str = 'not_started'

    VALID_STATUSES = ('not_started', 'in_progress', 'completed')

    def update_status(self, status):
        if not isinstance(status, str) or status not in self.VALID_STATUSES:
            raise ValueError('Invalid task status')
        self.status = status


class ReminderService:
    """Select due tasks that qualify for reminders; does not actually send messages."""

    def eligible_tasks(self, tasks, now, within_hours=24):
        if not isinstance(tasks, list):
            raise TypeError('tasks must be a list')
        if not isinstance(within_hours, (int, float)) or isinstance(within_hours, bool) or within_hours < 0:
            raise ValueError('within_hours must be nonnegative')
        if any(not isinstance(task, AcademicTask) for task in tasks):
            raise TypeError('Every entry must be an AcademicTask')
        cutoff = now + timedelta(hours=within_hours)
        return [task for task in tasks if task.status != 'completed' and now <= task.due_at <= cutoff]
