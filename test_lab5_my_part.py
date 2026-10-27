"""Seven PyUnit tests assigned to login/2FA and assignment progress/reminders."""
import unittest
from datetime import datetime, timedelta
from syllabus_prototype import AuthService, VerificationCode, AcademicTask, ReminderService

NOW = datetime(2026, 10, 26, 12, 0, 0)


class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.auth = AuthService()
        self.auth.register('student@example.edu', 'MySecurePass123')

    def test_01_valid_login_and_two_factor(self):
        self.assertTrue(self.auth.begin_two_factor('student@example.edu', 'MySecurePass123', '123456', NOW))
        self.assertTrue(self.auth.verify_two_factor('student@example.edu', '123456', NOW + timedelta(minutes=1)))

    def test_02_invalid_password_and_none(self):
        self.assertFalse(self.auth.login('student@example.edu', 'incorrect'))
        self.assertFalse(self.auth.login('student@example.edu', None))
        self.assertFalse(self.auth.login(None, 'MySecurePass123'))

    def test_03_code_expiration_boundary(self):
        valid = VerificationCode('123456', NOW + timedelta(minutes=5))
        self.assertTrue(valid.verify('123456', NOW + timedelta(minutes=4, seconds=59)))
        expired = VerificationCode('123456', NOW + timedelta(minutes=5))
        self.assertFalse(expired.verify('123456', NOW + timedelta(minutes=5)))

    def test_04_wrong_reused_and_bad_format_codes(self):
        code = VerificationCode('123456', NOW + timedelta(minutes=5))
        self.assertFalse(code.verify('000000', NOW))
        self.assertTrue(code.verify('123456', NOW))
        self.assertFalse(code.verify('123456', NOW + timedelta(seconds=1)))
        with self.assertRaises(ValueError):
            VerificationCode('abc', NOW + timedelta(minutes=5))


class TestProgressAndReminders(unittest.TestCase):
    def test_05_progress_transition(self):
        task = AcademicTask('Midterm', NOW + timedelta(days=2))
        self.assertEqual(task.status, 'not_started')
        task.update_status('in_progress')
        self.assertEqual(task.status, 'in_progress')
        task.update_status('completed')
        self.assertEqual(task.status, 'completed')

    def test_06_invalid_status_inputs(self):
        task = AcademicTask('Essay', NOW + timedelta(days=1))
        for invalid in (None, 10**50, '', 'done'):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    task.update_status(invalid)
        self.assertEqual(task.status, 'not_started')

    def test_07_reminder_normal_boundary_empty_and_bad_entry(self):
        service = ReminderService()
        due_now = AcademicTask('Due now', NOW)
        due_24h = AcademicTask('Due 24h', NOW + timedelta(hours=24))
        late = AcademicTask('Later', NOW + timedelta(hours=25))
        completed = AcademicTask('Finished', NOW + timedelta(hours=1), 'completed')
        result = service.eligible_tasks([due_now, due_24h, late, completed], NOW)
        self.assertEqual([t.title for t in result], ['Due now', 'Due 24h'])
        self.assertEqual(service.eligible_tasks([], NOW), [])
        self.assertEqual(service.eligible_tasks([due_now], NOW), [due_now])
        with self.assertRaises(TypeError):
            service.eligible_tasks([due_now, None], NOW)


if __name__ == '__main__':
    unittest.main(verbosity=2)
