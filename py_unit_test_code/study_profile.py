"""
StudyProfile — Syllab.Us Study Assessment

A student's study preferences, set from their latest AssessmentResult.
    profileId                UUID — the studentId from Account Management
    preferredSessionMinutes  int  — study session length based on the result
    preferredBreakMinutes    int  — minimum brain-break length
    sessionsPerWeek          int  — study sessions the student accepted this week
    updateFromResult(result) — takes the score from an AssessmentResult
"""

import uuid

from assessment_result import AssessmentResult


class StudyProfile:
    # (minimum score, session minutes, break minutes, sessions per week)
    SCORE_TIERS = [
        (75, 60, 15, 6),
        (50, 45, 10, 5),
        (25, 30, 5, 4),
        (0, 25, 5, 3),
    ]

    def __init__(self, profileId):
        if not isinstance(profileId, uuid.UUID):
            raise TypeError("profileId must be the student's UUID")
        self.profileId = profileId          # same as Student.studentId
        self.preferredSessionMinutes = None
        self.preferredBreakMinutes = None
        self.sessionsPerWeek = None

    def updateFromResult(self, result):
        """Set study preferences from an AssessmentResult's score."""
        if result is None:
            raise TypeError("result cannot be None")
        if not isinstance(result, AssessmentResult):
            raise TypeError("result must be an AssessmentResult")
        if result.studentId != self.profileId:
            raise ValueError("result belongs to a different student")
        for minScore, session, brk, perWeek in self.SCORE_TIERS:
            if result.score >= minScore:
                self.preferredSessionMinutes = session
                self.preferredBreakMinutes = brk
                self.sessionsPerWeek = perWeek
                return

    def acceptSessionsPerWeek(self, sessions):
        """Student sets how many sessions they accept for the week (1-14)."""
        if isinstance(sessions, bool) or not isinstance(sessions, int):
            raise TypeError("sessions must be an integer")
        if not 1 <= sessions <= 14:
            raise ValueError("sessions per week must be between 1 and 14")
        self.sessionsPerWeek = sessions
