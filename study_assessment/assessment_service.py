"""
AssessmentService — Syllab.Us Study Assessment

Takes the student's answers, sends them to AssessmentResult to be scored,
stores every completed assessment in history (including retakes), and
updates the student's StudyProfile (their study preferences).
"""

from assessment_result import AssessmentResult
from study_profile import StudyProfile


class AssessmentService:
    def __init__(self):
        self._history = {}   # studentId -> [AssessmentResult, ...] oldest first
        self._profiles = {}  # studentId -> StudyProfile

    def submitAnswers(self, studentId, answers):
        """Score the answers, save the result to history, update the profile."""
        result = AssessmentResult(studentId, answers)
        self._history.setdefault(studentId, []).append(result)
        self.updateStudyProfile(studentId)
        return result

    def retakeAssessment(self, studentId, answers):
        """Retake is only allowed after a first assessment exists."""
        if studentId not in self._history:
            raise LookupError("no previous assessment to retake")
        return self.submitAnswers(studentId, answers)

    def updateStudyProfile(self, studentId):
        """Apply the student's most recent result to their StudyProfile."""
        latest = self.getLatestResult(studentId)
        if latest is None:
            raise LookupError("student has no completed assessment")
        profile = self._profiles.setdefault(studentId, StudyProfile(studentId))
        profile.updateFromResult(latest)
        return profile

    def getHistory(self, studentId):
        """Copy of all completed results for a student, oldest first."""
        return list(self._history.get(studentId, []))

    def getLatestResult(self, studentId):
        results = self._history.get(studentId)
        return results[-1] if results else None

    def getStudyProfile(self, studentId):
        return self._profiles.get(studentId)
