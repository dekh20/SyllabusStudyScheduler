from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from calendar_sync_prototype import (
    CalendarService, DeadlineEvent, ExternalCalendarAdapter, ManualEvent, Reminder, StudySession,
)
from study_scheduler import StudyScheduler


START = datetime(2026, 10, 26, 16, tzinfo=timezone.utc)
END = datetime(2026, 10, 26, 17, tzinfo=timezone.utc)


def test_save_update_and_remove_event():
    service = CalendarService()
    student_id = uuid4()
    service.create_calendar(student_id)
    event = ManualEvent("Lab", START, END)

    service.save_event(student_id, event)
    events = service.list_events(student_id)
    assert len(events) == 1
    assert events[0].title == "Lab"

    event.reschedule(START + timedelta(days=1), END + timedelta(days=1))
    service.save_event(student_id, event)
    events = service.list_events(student_id)
    assert len(events) == 1
    assert events[0].starts_at == START + timedelta(days=1)
    assert events[0].ends_at == END + timedelta(days=1)

    service.remove_event(student_id, event.event_id)
    assert service.list_events(student_id) == []


def test_export_calendar():
    service = CalendarService()
    student_id = uuid4()
    calendar = service.create_calendar(student_id)
    event = ManualEvent("Lab", START, END)
    service.save_event(student_id, event)
    adapter = ExternalCalendarAdapter(service)

    assert adapter.export_events(calendar.calendar_id) is True
    exported = adapter.get_exported_events(calendar.calendar_id)
    assert len(exported) == 1
    assert exported[0].event_id == event.event_id
    assert exported[0].title == "Lab"

    event.edit_details("Bring worksheet")
    service.save_event(student_id, event)
    assert adapter.get_exported_events(calendar.calendar_id)[0].notes == ""
    assert adapter.export_events(calendar.calendar_id) is True
    exported = adapter.get_exported_events(calendar.calendar_id)
    assert len(exported) == 1
    assert exported[0].notes == "Bring worksheet"
    assert adapter.export_events(uuid4()) is False


def test_export_empty_calendar():
    service = CalendarService()
    calendar = service.create_calendar(uuid4())
    adapter = ExternalCalendarAdapter(service)

    assert adapter.export_events(calendar.calendar_id) is True
    assert adapter.get_exported_events(calendar.calendar_id) == []


def test_reminder_at_due_time():
    service = CalendarService()
    student_id = uuid4()
    service.create_calendar(student_id)
    reminder = Reminder(START)
    event = ManualEvent("Lab", START, END)
    event.reminders.append(reminder)
    service.save_event(student_id, event)

    before = START - timedelta(microseconds=1)
    assert service.send_due_reminders(before) == []

    delivered = service.send_due_reminders(START)
    assert len(delivered) == 1
    assert delivered[0].reminder_id == reminder.reminder_id
    assert delivered[0].delivered is True
    assert service.send_due_reminders(START + timedelta(microseconds=1)) == []


def test_export_large_calendar():
    service = CalendarService()
    student_id = uuid4()
    calendar = service.create_calendar(student_id)
    adapter = ExternalCalendarAdapter(service)

    for number in range(1000):
        start = START + timedelta(minutes=number)
        end = END + timedelta(minutes=number)
        event = ManualEvent("Event " + str(number), start, end)
        service.save_event(student_id, event)

    assert len(service.list_events(student_id)) == 1000
    assert adapter.export_events(calendar.calendar_id) is True
    exported = adapter.get_exported_events(calendar.calendar_id)
    assert len(exported) == 1000
    assert exported[0].title == "Event 0"
    assert exported[-1].title == "Event 999"


def test_invalid_event_titles():
    for title in (None, 123, ["Lab"]):
        with pytest.raises(TypeError):
            ManualEvent(title, START, END)

    for title in ("", "   "):
        with pytest.raises(ValueError):
            ManualEvent(title, START, END)


def test_invalid_event_times():
    for bad_time in (None, "4 PM", 123):
        with pytest.raises(TypeError):
            ManualEvent("Lab", bad_time, END)
        with pytest.raises(TypeError):
            ManualEvent("Lab", START, bad_time)

    with pytest.raises(ValueError):
        ManualEvent("Lab", START, START)
    with pytest.raises(ValueError):
        ManualEvent("Lab", END, START)
    with pytest.raises(ValueError):
        ManualEvent("Lab", START.replace(tzinfo=None), END)


def test_regenerating_plan_replaces_sessions_without_removing_other_events():
    service = CalendarService()
    service.create_calendar("student")
    deadline = DeadlineEvent("Paper due", START, END, event_id="paper")
    manual = ManualEvent("Office hours", START, END)
    completed = StudySession("Finished reading", START, END, completed=True)
    for event in (deadline, manual, completed):
        service.save_event("student", event)

    scheduler = StudyScheduler()
    scheduler.add_availability(START, END)
    old_session, = scheduler.generate_schedule()
    service.replace_study_sessions("student", [old_session])

    new_session, = scheduler.generate_schedule()
    stale_completed = StudySession("Finished reading", START, END, event_id=completed.event_id)
    for _ in range(2):
        service.replace_study_sessions("student", [new_session, stale_completed])
    events = {event.event_id: event for event in service.list_events("student")}

    assert set(events) == {deadline.event_id, manual.event_id, completed.event_id,
                           new_session.event_id}
    assert events[completed.event_id].completed is True


def test_invalid_plan_leaves_current_calendar_unchanged():
    service = CalendarService()
    service.create_calendar("student")
    original = StudySession("Original", START, END)
    manual = ManualEvent("Office hours", START, END)
    service.save_event("student", original)
    service.save_event("student", manual)

    replacement = StudySession("Replacement", START, END)
    collision = StudySession("Collision", START, END, event_id=manual.event_id)
    for sessions in ([replacement, replacement], [replacement, collision]):
        with pytest.raises(ValueError):
            service.replace_study_sessions("student", sessions)
        assert [event.event_id for event in service.list_events("student")] == [
            original.event_id, manual.event_id,
        ]


def test_replaying_plan_preserves_delivery_of_unchanged_reminder():
    service = CalendarService()
    service.create_calendar("student")
    reminder = Reminder(START)
    session = StudySession("Write paper", START, END, reminders=[reminder])
    service.replace_study_sessions("student", [session])
    assert [r.reminder_id for r in service.send_due_reminders(START)] == [reminder.reminder_id]

    service.replace_study_sessions("student", [session])
    assert service.send_due_reminders(START) == []

    reminder.send_at = START + timedelta(minutes=15)
    service.replace_study_sessions("student", [session])
    assert [r.reminder_id for r in service.send_due_reminders(reminder.send_at)] == [
        reminder.reminder_id,
    ]


def test_ics_exports_deadline_at_due_time_and_keeps_uid_after_edit():
    service = CalendarService()
    pacific = ZoneInfo("America/Los_Angeles")
    service.create_calendar("student", pacific.key)
    start = datetime(2026, 11, 2, 16, tzinfo=pacific)
    due = start + timedelta(hours=1)
    deadline = DeadlineEvent("Paper due", due - timedelta(minutes=5), due, event_id="paper")
    service.save_event("student", deadline)
    service.replace_study_sessions("student", [
        StudySession("Write paper", start, start + timedelta(minutes=30)),
    ])

    first_export = service.export_ics("student").split(b"BEGIN:VEVENT\r\n")
    assert first_export[0].startswith(b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\n")
    assert len(first_export) == 3
    assert b"DTSTART:20261103T000000Z\r\nDTEND:20261103T003000Z\r\n" in first_export[1]
    assert b"DTSTART:20261103T010000Z\r\nSUMMARY:Paper due\r\n" in first_export[2]

    deadline.refresh_due_date(due + timedelta(days=1))
    service.save_event("student", deadline)
    second_export = service.export_ics("student").split(b"BEGIN:VEVENT\r\n")
    assert len(second_export) == 3
    assert first_export[2].splitlines()[0] == second_export[2].splitlines()[0]
    assert b"DTSTART:20261104T010000Z\r\n" in second_export[2]
    assert second_export[2].endswith(b"END:VEVENT\r\nEND:VCALENDAR\r\n")


def test_ics_folds_utf8_lines_and_escapes_event_text():
    service = CalendarService()
    service.create_calendar("student")
    service.save_event("student", ManualEvent(
        "Review " + "📚" * 40, START, END, notes="Read A,B; C\\D\r\nBring notes",
    ))

    exported = service.export_ics("student")
    for line in exported.split(b"\r\n"):
        assert len(line) <= 75
        line.decode("utf-8")
    unfolded = exported.replace(b"\r\n ", b"").decode("utf-8")
    assert f"SUMMARY:Review {'📚' * 40}\r\n" in unfolded
    assert r"DESCRIPTION:Read A\,B\; C\\D\nBring notes" + "\r\n" in unfolded


def test_ics_export_requires_an_event():
    service = CalendarService()
    service.create_calendar("student")
    with pytest.raises(ValueError, match="before exporting"):
        service.export_ics("student")


def test_fall_back_uses_actual_instants_for_event_and_reminder():
    pacific = ZoneInfo("America/Los_Angeles")
    start = datetime(2026, 11, 1, 1, 45, tzinfo=pacific, fold=0)
    end = datetime(2026, 11, 1, 1, 15, tzinfo=pacific, fold=1)
    service = CalendarService()
    service.create_calendar("student", pacific.key)
    reminder = Reminder(end)
    service.save_event("student", StudySession("Read", start, end, reminders=[reminder]))

    assert service.send_due_reminders(start) == []
    assert [r.reminder_id for r in service.send_due_reminders(end)] == [reminder.reminder_id]
    assert b"DTSTART:20261101T084500Z\r\nDTEND:20261101T091500Z\r\n" in service.export_ics("student")
