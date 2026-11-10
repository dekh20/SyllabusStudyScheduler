from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid4, uuid5
from zoneinfo import ZoneInfo


def require_aware(time):
    if not isinstance(time, datetime):
        raise TypeError("Time must be a datetime")
    if time.tzinfo is None or time.utcoffset() is None:
        raise ValueError("Time must include a time zone")


def validate_times(start, end):
    require_aware(start)
    require_aware(end)
    if end.astimezone(timezone.utc) <= start.astimezone(timezone.utc):
        raise ValueError("End time must be after start time")


def _ics_text(value):
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return (value.replace("\\", "\\\\").replace("\n", "\\n")
            .replace(",", "\\,").replace(";", "\\;"))


def _ics_datetime(value):
    return f"{value.year:04d}{value:%m%dT%H%M%SZ}"


def _fold_ics_line(line):
    chunks = []
    chunk = bytearray()
    for character in line:
        encoded = character.encode("utf-8")
        if len(chunk) + len(encoded) > 75:
            chunks.append(bytes(chunk))
            chunk = bytearray(b" ")
        chunk.extend(encoded)
    chunks.append(bytes(chunk))
    return b"\r\n".join(chunks)


class Reminder:
    def __init__(self, send_at, reminder_id=None, delivered=False, scheduled=True):
        require_aware(send_at)
        if reminder_id is None:
            reminder_id = uuid4()
        self.reminder_id = reminder_id
        self.send_at = send_at
        self.delivered = delivered
        self.scheduled = scheduled

    def schedule(self):
        self.scheduled = True
        self.delivered = False

    def cancel(self):
        self.scheduled = False


class CalendarEvent:
    def __init__(self, title, starts_at, ends_at, event_id=None, reminders=None):
        if event_id is None:
            event_id = uuid4()
        if reminders is None:
            reminders = []
        self.event_id = event_id
        self.title = title
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.reminders = reminders
        self.validate()

    def validate(self):
        if not isinstance(self.title, str):
            raise TypeError("Title must be a string")
        if not self.title.strip():
            raise ValueError("Title cannot be blank")
        validate_times(self.starts_at, self.ends_at)
        for reminder in self.reminders:
            require_aware(reminder.send_at)

    def reschedule(self, start, end):
        validate_times(start, end)
        self.starts_at = start
        self.ends_at = end


class StudySession(CalendarEvent):
    def __init__(self, title, starts_at, ends_at, event_id=None, reminders=None,
                 completed=False):
        super().__init__(title, starts_at, ends_at, event_id, reminders)
        self.completed = completed

    def mark_complete(self):
        self.completed = True


class DeadlineEvent(CalendarEvent):
    def refresh_due_date(self, due_at):
        require_aware(due_at)
        duration = (self.ends_at.astimezone(timezone.utc)
                    - self.starts_at.astimezone(timezone.utc))
        start = due_at.astimezone(timezone.utc) - duration
        self.reschedule(start.astimezone(due_at.tzinfo), due_at)


class ManualEvent(CalendarEvent):
    def __init__(self, title, starts_at, ends_at, event_id=None, reminders=None,
                 notes=""):
        super().__init__(title, starts_at, ends_at, event_id, reminders)
        self.notes = notes

    def edit_details(self, notes):
        self.notes = notes


class StudyCalendar:
    def __init__(self, time_zone="UTC", calendar_id=None, events=None):
        ZoneInfo(time_zone)
        if calendar_id is None:
            calendar_id = uuid4()
        if events is None:
            events = {}
        self.calendar_id = calendar_id
        self.time_zone = time_zone
        self.events = events

    def add_event(self, event):
        event.validate()
        if event.event_id in self.events:
            raise ValueError("Event is already in this calendar")
        self.events[event.event_id] = event

    def remove_event(self, event_id):
        del self.events[event_id]


class CalendarService:
    def __init__(self):
        self._calendars = {}

    def create_calendar(self, student_id, time_zone="UTC"):
        if student_id in self._calendars:
            raise ValueError("Student already has a calendar")
        calendar = StudyCalendar(time_zone)
        self._calendars[student_id] = calendar
        return calendar

    def get_calendar(self, student_id):
        return self._calendars[student_id]

    def get_calendar_by_id(self, calendar_id):
        for calendar in self._calendars.values():
            if calendar.calendar_id == calendar_id:
                return calendar
        raise KeyError(calendar_id)

    def save_event(self, student_id, event):
        event.validate()
        calendar = self.get_calendar(student_id)
        calendar.events[event.event_id] = deepcopy(event)

    def replace_study_sessions(self, student_id, sessions):
        """Replace the current plan and retain completed sessions and other events."""
        calendar = self.get_calendar(student_id)
        retained = {
            event_id: event for event_id, event in calendar.events.items()
            if not isinstance(event, StudySession) or event.completed
        }
        planned = {}
        for session in sessions:
            if not isinstance(session, StudySession):
                raise TypeError("A study plan must contain StudySession events")
            session.validate()
            event_id = session.event_id
            if event_id in planned:
                raise ValueError("Duplicate study session ID")
            previous = calendar.events.get(event_id)
            if previous is not None and not isinstance(previous, StudySession):
                raise ValueError("Study session ID belongs to another calendar event")
            updated = deepcopy(session)
            if previous is not None:
                delivered = {
                    (reminder.reminder_id, reminder.send_at.astimezone(timezone.utc))
                    for reminder in previous.reminders if reminder.delivered
                }
                for reminder in updated.reminders:
                    key = (reminder.reminder_id, reminder.send_at.astimezone(timezone.utc))
                    if key in delivered:
                        reminder.delivered = True
            planned[event_id] = updated
        # Publish the plan only after validating it, and keep completed versions.
        calendar.events = {**planned, **retained}

    def list_events(self, student_id):
        calendar = self.get_calendar(student_id)
        events = sorted(calendar.events.values(),
                        key=lambda event: event.starts_at.astimezone(timezone.utc))
        return deepcopy(events)

    def remove_event(self, student_id, event_id):
        calendar = self.get_calendar(student_id)
        calendar.remove_event(event_id)

    def export_ics(self, student_id):
        """Return an iCalendar snapshot as UTF-8 bytes."""
        calendar = self.get_calendar(student_id)
        events = self.list_events(student_id)
        if not events:
            raise ValueError("Add a calendar event before exporting")

        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Syllab.Us//Study Calendar//EN"]
        timestamp = _ics_datetime(datetime.now(timezone.utc))
        for event in events:
            uid = uuid5(NAMESPACE_URL, f"syllab.us/calendar/{(calendar.calendar_id, event.event_id)!r}")
            end = event.ends_at.astimezone(timezone.utc).replace(microsecond=0)
            lines.extend(["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{timestamp}"])
            if isinstance(event, DeadlineEvent):
                lines.append(f"DTSTART:{_ics_datetime(end)}")
            else:
                start = event.starts_at.astimezone(timezone.utc).replace(microsecond=0)
                # iCalendar timestamps have whole-second precision.
                if end == start:
                    end += timedelta(seconds=1)
                lines.extend([f"DTSTART:{_ics_datetime(start)}", f"DTEND:{_ics_datetime(end)}"])
            lines.append(f"SUMMARY:{_ics_text(event.title)}")
            if isinstance(event, ManualEvent) and event.notes:
                lines.append(f"DESCRIPTION:{_ics_text(event.notes)}")
            lines.append("END:VEVENT")
        lines.append("END:VCALENDAR")
        return b"\r\n".join(_fold_ics_line(line) for line in lines) + b"\r\n"

    def send_due_reminders(self, now):
        require_aware(now)
        now = now.astimezone(timezone.utc)
        delivered = []
        for calendar in self._calendars.values():
            for event in calendar.events.values():
                # Completed study sessions no longer need reminders.
                if isinstance(event, StudySession) and event.completed:
                    continue
                for reminder in event.reminders:
                    if not reminder.scheduled or reminder.delivered:
                        continue
                    if reminder.send_at.astimezone(timezone.utc) > now:
                        continue
                    # Only update the local flag. No notification is sent.
                    reminder.delivered = True
                    delivered.append(deepcopy(reminder))
        return delivered


class CalendarSyncGateway:
    def export_events(self, calendar_id):
        raise NotImplementedError("Calendar adapter must implement export_events")


class ExternalCalendarAdapter(CalendarSyncGateway):
    def __init__(self, calendar_service):
        self.provider = "local"
        self._calendar_service = calendar_service
        self._exports = {}

    def export_events(self, calendar_id):
        try:
            calendar = self._calendar_service.get_calendar_by_id(calendar_id)
        except KeyError:
            return False

        events = sorted(calendar.events.values(), key=lambda event: event.starts_at)
        # Keep a copy so edits to the calendar do not change the last export.
        self._exports[calendar_id] = deepcopy(events)
        return True

    def get_exported_events(self, calendar_id):
        return deepcopy(self._exports[calendar_id])
