"""
AssessmentResult — Syllab.Us Study Assessment

One completed study-habit / learning-style assessment, built from the
student's answers. Handles score calculation. Every result (first attempt
and every retake) is stored in the student's history by AssessmentService.
"""

import uuid
from datetime import datetime

# Each answer is a letter A-D. A = least study stamina / focus, D = most.
ANSWER_POINTS = {"A": 1, "B": 2, "C": 3, "D": 4}
MAX_QUESTIONS = 50  # anything larger is rejected as invalid input


class AssessmentResult:
    def __init__(self, studentId, answers):
        if not isinstance(studentId, uuid.UUID):
            raise TypeError("studentId must be a UUID")
        if answers is None:
            raise TypeError("answers cannot be None")
        if not isinstance(answers, dict):
            raise TypeError("answers must be a dict of {question: letter}")
        if len(answers) == 0:
            raise ValueError("answers cannot be empty")
        if len(answers) > MAX_QUESTIONS:
            raise ValueError(f"too many answers (max {MAX_QUESTIONS})")
        for question, answer in answers.items():
            if not isinstance(question, str) or not isinstance(answer, str):
                raise TypeError("questions and answers must be strings")
            if answer.upper() not in ANSWER_POINTS:
                raise ValueError(f"invalid answer '{answer}' for '{question}'")

        self.resultId = uuid.uuid4()
        self.studentId = studentId
        self.completedAt = datetime.now()
        self.answers = {q: a.upper() for q, a in answers.items()}
        self.score = self.calculateScore()

    def calculateScore(self):
        """Score calculation: 0 to 100. All 'A' -> 0, all 'D' -> 100."""
        n = len(self.answers)
        total = sum(ANSWER_POINTS[a] for a in self.answers.values())
        return round((total - n) / (3 * n) * 100)
