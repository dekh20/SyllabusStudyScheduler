
# Study Scheduler Tests
# Checks if the study scheduler works

import unittest
from datetime import datetime, timedelta, timezone
from study_scheduler import StudyScheduler

start = datetime(2026, 10, 26, 14, tzinfo=timezone.utc)
end = datetime(2026, 10, 26, 16, tzinfo=timezone.utc)

class TestStudyScheduler(unittest.TestCase):
    # Start with a new scheduler for each test
    def setUp(self):
        self.scheduler = StudyScheduler()

    # Test 1: Add available time
    def test_add_availability(self):
        self.scheduler.add_availability(start, end)
        self.assertEqual(len(self.scheduler.availability), 1)

    # Test 2: Reject invalid time
    def test_invalid_time(self):
        with self.assertRaises(ValueError):
            self.scheduler.add_availability(end, start)

    # Test 3: Create a study session
    def test_generate_schedule(self):
        self.scheduler.add_availability(start, end)
        sessions = self.scheduler.generate_schedule()
        self.assertEqual(len(sessions), 1)

    # Test 4: Empty schedule
    def test_empty_schedule(self):
        sessions = self.scheduler.generate_schedule()
        self.assertEqual(len(sessions), 0)

    # Test 5: Check overlapping times
    def test_conflict(self):
        result = self.scheduler.check_conflicts(
            start, end,
            start + timedelta(hours=1),
            end + timedelta(hours=1)
        )
        self.assertTrue(result)

    # Test 6: Check times that don't overlap
    def test_no_conflict(self):
        result = self.scheduler.check_conflicts(
            start, end,
            end, end + timedelta(hours=2)
        )
        self.assertFalse(result)

    # Test 7: Change a study session
    def test_modify_schedule(self):
        self.scheduler.add_availability(start, end)
        session = self.scheduler.generate_schedule()[0]

        new_start = start + timedelta(hours=2)
        new_end = end + timedelta(hours=2)

        self.scheduler.modify_schedule(session, new_start, new_end)
        self.assertEqual(session.starts_at, new_start)

if __name__ == "__main__":
    unittest.main()

