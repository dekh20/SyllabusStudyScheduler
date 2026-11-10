# Study Scheduler
# This class creates and manages study sessions based on when a student is free
# Use the study session and time checking code from calendar_sync

from calendar_sync_prototype import StudySession, validate_times


# Class that manages the student's study schedule
class StudyScheduler:

    # Start with empty lists
    def __init__(self):
        self.availability = []     # Times the student is free
        self.study_sessions = []   # Study sessions created

    # Add a time when the student is free
    def add_availability(self, start, end):
        validate_times(start, end)
        self.availability.append((start, end))

    # Create study sessions from available times
    def generate_schedule(self):
        self.study_sessions = []

        for start, end in self.availability:
            session = StudySession(
                "Study Session",
                start,
                end
            )
            self.study_sessions.append(session)
        return self.study_sessions.copy()

    # Check if two sessions overlap
    def check_conflicts(self, start1, end1, start2, end2):
        validate_times(start1, end1)
        validate_times(start2, end2)

        # True means they overlap, false means they don't
        return start1 < end2 and start2 < end1

    # Change the time of a study session
    def modify_schedule(self, session, new_start, new_end):
        validate_times(new_start, new_end)
        if session not in self.study_sessions:
            raise ValueError("Session not found")
        session.reschedule(new_start, new_end)

    # Remove a study session
    def remove_session(self, session):
        if session not in self.study_sessions:
            raise ValueError("Session does not exist")
        self.study_sessions.remove(session)

    # Show the current study schedule
    def get_weekly_schedule(self):
        return self.study_sessions.copy()

