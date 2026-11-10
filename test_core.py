import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from core import Database, reminder_items, parse_due_at, validate_status, verify_password

NOW = datetime(2026, 11, 9, 17, 0)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'test.sqlite3')
        self.user = self.db.create_student('Alex Student', 'alex@scu.edu', 'password123')

    def tearDown(self):
        self.temp.cleanup()

    def test_register_and_login(self):
        self.assertEqual(self.db.authenticate('alex@scu.edu','password123')['id'], self.user)

    def test_wrong_password_and_none(self):
        self.assertIsNone(self.db.authenticate('alex@scu.edu','wrongpass'))
        self.assertIsNone(self.db.authenticate('alex@scu.edu',None))

    def test_duplicate_registration_rejected(self):
        with self.assertRaises(ValueError):
            self.db.create_student('Another','alex@scu.edu','password123')

    def test_password_not_plaintext(self):
        with self.db.connect() as conn:
            stored = conn.execute('SELECT password_hash FROM students WHERE id=?',(self.user,)).fetchone()[0]
        self.assertNotEqual(stored,'password123')
        self.assertTrue(verify_password('password123',stored))

    def test_unknown_email_rejected(self):
        self.assertIsNone(self.db.authenticate('unknown@scu.edu', 'password123'))

    def test_empty_and_wrong_type_credentials(self):
        for email, password in [('', 'password123'), ('alex@scu.edu', ''), (None, 'password123'), ('alex@scu.edu', 123)]:
            with self.subTest(email=email, password=password):
                self.assertIsNone(self.db.authenticate(email, password))

    def test_add_list_and_update_task(self):
        task_id=self.db.add_task(self.user,'Math homework','MATH 11','2026-11-10T12:00')
        self.assertEqual(self.db.list_tasks(self.user)[0]['status'],'not_started')
        self.assertTrue(self.db.update_status(self.user,task_id,'completed'))
        self.assertEqual(self.db.list_tasks(self.user)[0]['status'],'completed')

    def test_invalid_status(self):
        for status in (None,'done',50):
            with self.assertRaises(ValueError):
                validate_status(status)

    def test_task_isolation(self):
        another=self.db.create_student('Taylor','taylor@scu.edu','password123')
        task_id=self.db.add_task(self.user,'Private essay','ENGL','2026-11-10T10:00')
        self.assertEqual(self.db.list_tasks(another),[])
        self.assertFalse(self.db.update_status(another,task_id,'completed'))
        self.assertFalse(self.db.delete_task(another,task_id))

    def test_remove_task(self):
        task=self.db.add_task(self.user,'Quiz','CSEN','2026-11-11T10:00')
        self.assertTrue(self.db.delete_task(self.user,task))
        self.assertEqual(self.db.list_tasks(self.user),[])

    def test_reminders_only_upcoming_unfinished(self):
        tasks=[{'title':'soon','due_at':'2026-11-10T10:00','status':'not_started'}, {'title':'done','due_at':'2026-11-10T09:00','status':'completed'}, {'title':'later','due_at':'2026-11-15T09:00','status':'in_progress'}]
        self.assertEqual([t['title'] for t in reminder_items(tasks,NOW)],['soon'])

    def test_reminder_boundaries_and_empty_list(self):
        self.assertEqual(reminder_items([],NOW),[])
        tasks=[{'title':'boundary','due_at':'2026-11-11T17:00','status':'in_progress'}]
        self.assertEqual(len(reminder_items(tasks,NOW)),1)
        self.assertEqual(len(reminder_items(tasks,NOW,hours=47)),0)

    def test_invalid_due_date(self):
        with self.assertRaises(ValueError):
            parse_due_at('not-a-date')


if __name__ == '__main__':
    unittest.main(verbosity=2)
