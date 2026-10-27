"""
AssessmentService tests — Syllab.Us Study Assessment
Requirements covered:
  * Assessment result from students' answers
  * Student study preference (service updates the StudyProfile)

5 tests. Docstrings start with the case type: [Normal], [Edge] or [Invalid].
"""

import uuid
import pytest

from assessment_service import AssessmentService
from assessment_result import AssessmentResult


def answers_of(letter, count=5):
    return {f"q{i}": letter for i in range(1, count + 1)}


@pytest.fixture
def sid():
    return uuid.uuid4()


@pytest.fixture
def service():
    return AssessmentService()


class TestAssessmentService:

    def test_submit_answers_returns_scored_result(self, service, sid):
        """[Normal] submitAnswers turns the student's answers into a scored AssessmentResult."""
        result = service.submitAnswers(sid, {"q1": "A", "q2": "B", "q3": "C", "q4": "D"})

        assert isinstance(result, AssessmentResult)
        assert result.studentId == sid
        assert result.score == 50

    def test_submit_answers_sets_study_preference(self, service, sid):
        """[Normal] Submitting answers creates the StudyProfile with the student's study preferences."""
        service.submitAnswers(sid, answers_of("D"))
        profile = service.getStudyProfile(sid)

        assert profile.profileId == sid
        assert (profile.preferredSessionMinutes, profile.preferredBreakMinutes,
                profile.sessionsPerWeek) == (60, 15, 6)

    def test_single_answer_submission(self, service, sid):
        """[Edge] A single answer is enough to produce a result and a study preference."""
        result = service.submitAnswers(sid, {"q1": "C"})

        assert result.score == 67
        assert service.getStudyProfile(sid).preferredSessionMinutes == 45

    def test_none_and_wrong_type_answers_rejected(self, service, sid):
        """[Invalid] None, a list, or a non-UUID student ID is rejected and no profile is made."""
        with pytest.raises(TypeError):
            service.submitAnswers(sid, None)
        with pytest.raises(TypeError):
            service.submitAnswers(sid, ["A", "B", "C"])
        with pytest.raises(TypeError):
            service.submitAnswers("student-123", answers_of("B"))

        assert service.getStudyProfile(sid) is None

    def test_large_input_rejected_and_preference_unchanged(self, service, sid):
        """[Invalid] A 10,000-answer submission is rejected; the existing study preference stays the same."""
        service.submitAnswers(sid, answers_of("A"))

        with pytest.raises(ValueError):
            service.submitAnswers(sid, answers_of("D", 10_000))

        assert service.getStudyProfile(sid).preferredSessionMinutes == 25
