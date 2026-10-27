"""
AssessmentResult tests — Syllab.Us Study Assessment
Requirements covered:
  * Score calculation
  * Retake assessment
  * Store history of completed assessments

5 tests. Docstrings start with the case type: [Normal], [Edge] or [Invalid].
"""

import uuid
import pytest

from assessment_result import AssessmentResult, MAX_QUESTIONS
from assessment_service import AssessmentService


def answers_of(letter, count=5):
    return {f"q{i}": letter for i in range(1, count + 1)}


@pytest.fixture
def sid():
    return uuid.uuid4()


@pytest.fixture
def service():
    return AssessmentService()


class TestAssessmentResult:

    def test_score_calculation(self, sid):
        """[Normal] calculateScore: A,B,C,D -> 50; lowercase 'd','c' -> 83."""
        assert AssessmentResult(sid, {"q1": "A", "q2": "B", "q3": "C", "q4": "D"}).score == 50
        assert AssessmentResult(sid, {"q1": "d", "q2": "c"}).score == 83

    def test_retake_creates_new_result_and_stores_history(self, service, sid):
        """[Normal] Retaking makes a new result; both attempts are stored in history in order."""
        first = service.submitAnswers(sid, answers_of("A"))
        second = service.retakeAssessment(sid, answers_of("D"))

        assert first.resultId != second.resultId
        assert service.getHistory(sid) == [first, second]
        assert service.getLatestResult(sid).score == 100

    def test_score_boundaries(self, sid):
        """[Edge] All 'A' -> 0, all 'D' -> 100, single answer and exactly MAX_QUESTIONS answers are scored."""
        assert AssessmentResult(sid, answers_of("A")).score == 0
        assert AssessmentResult(sid, answers_of("D")).score == 100
        assert AssessmentResult(sid, {"q1": "C"}).score == 67
        assert AssessmentResult(sid, answers_of("B", MAX_QUESTIONS)).score == 33

    def test_many_retakes_history(self, service, sid):
        """[Edge] 100 completed assessments are all stored, oldest first; empty history before any."""
        assert service.getHistory(sid) == []

        service.submitAnswers(sid, answers_of("A"))
        for _ in range(99):
            service.retakeAssessment(sid, answers_of("B"))
        history = service.getHistory(sid)

        assert len(history) == 100
        assert history[0].score == 0 and history[-1].score == 33

    def test_invalid_answers_and_retake(self, service, sid):
        """[Invalid] Empty, oversized, or bad-letter answers raise; retake before a first attempt raises."""
        with pytest.raises(ValueError):
            AssessmentResult(sid, {})
        with pytest.raises(ValueError):
            AssessmentResult(sid, answers_of("B", 10_000))
        with pytest.raises(ValueError):
            AssessmentResult(sid, {"q1": "E"})
        with pytest.raises(TypeError):
            AssessmentResult(sid, {"q1": 3})
        with pytest.raises(LookupError):
            service.retakeAssessment(sid, answers_of("B"))
        assert service.getHistory(sid) == []
