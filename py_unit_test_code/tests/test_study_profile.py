"""
StudyProfile tests — Syllab.Us Study Assessment
Requirements covered:
  * profileId: UUID (studentId) from Account Management
  * preferredSessionMinutes, preferredBreakMinutes, sessionsPerWeek (int values)
  * updateFromResult: takes the result from AssessmentResult

5 tests. Docstrings start with the case type: [Normal], [Edge] or [Invalid].
"""

import uuid
import pytest

from study_profile import StudyProfile
from assessment_result import AssessmentResult


def answers_of(letter, count=5):
    return {f"q{i}": letter for i in range(1, count + 1)}


@pytest.fixture
def sid():
    return uuid.uuid4()


class TestStudyProfile:

    def test_profile_id_is_student_uuid(self, sid):
        """[Normal] profileId is the student's UUID; preferences start empty until a result is applied."""
        profile = StudyProfile(sid)

        assert profile.profileId == sid
        assert profile.preferredSessionMinutes is None
        assert profile.preferredBreakMinutes is None
        assert profile.sessionsPerWeek is None

    def test_update_from_result_sets_int_values(self, sid):
        """[Normal] updateFromResult sets session minutes, break minutes and sessions/week as ints."""
        profile = StudyProfile(sid)
        profile.updateFromResult(AssessmentResult(sid, answers_of("C")))  # score 67

        assert (profile.preferredSessionMinutes, profile.preferredBreakMinutes,
                profile.sessionsPerWeek) == (45, 10, 5)
        assert all(isinstance(v, int) for v in (profile.preferredSessionMinutes,
                                                 profile.preferredBreakMinutes,
                                                 profile.sessionsPerWeek))

    def test_tier_boundaries(self, sid):
        """[Edge] Score 0 -> 25 min, score 50 -> 45 min (not 30), score 100 -> 60 min."""
        profile = StudyProfile(sid)

        profile.updateFromResult(AssessmentResult(sid, answers_of("A")))       # 0
        assert profile.preferredSessionMinutes == 25
        profile.updateFromResult(AssessmentResult(sid, {"q1": "B", "q2": "C"}))  # 50
        assert profile.preferredSessionMinutes == 45
        profile.updateFromResult(AssessmentResult(sid, answers_of("D")))       # 100
        assert profile.preferredSessionMinutes == 60

    def test_accept_sessions_per_week_limits(self, sid):
        """[Edge] Student can accept exactly 1 or 14 sessions/week; 0 and 15 are rejected."""
        profile = StudyProfile(sid)

        profile.acceptSessionsPerWeek(1)
        assert profile.sessionsPerWeek == 1
        profile.acceptSessionsPerWeek(14)
        assert profile.sessionsPerWeek == 14
        for bad in (0, 15):
            with pytest.raises(ValueError):
                profile.acceptSessionsPerWeek(bad)

    def test_invalid_profile_id_and_result(self, sid):
        """[Invalid] Non-UUID profileId, None result, or another student's result is rejected."""
        with pytest.raises(TypeError):
            StudyProfile("12345")

        profile = StudyProfile(sid)
        with pytest.raises(TypeError):
            profile.updateFromResult(None)
        with pytest.raises(ValueError):
            profile.updateFromResult(AssessmentResult(uuid.uuid4(), answers_of("D")))
        assert profile.preferredSessionMinutes is None
