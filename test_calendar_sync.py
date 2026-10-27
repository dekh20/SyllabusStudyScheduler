from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from calendar_sync import CalendarService, ExternalCalendarAdapter, ManualEvent, Reminder


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
