# models.py
from enum import Enum
from dataclasses import dataclass
from typing import Literal
from datetime import datetime


class ExamState(Enum):
    COLLECTING_IDENTITY = "collecting_identity"
    ASKING_QUESTIONS = "asking_questions"
    FINISHING = "finishing"
    COMPLETED = "completed"


@dataclass
class Message:
    role: Literal["system", "user", "tool_call"]
    content: str
    datetime: str


@dataclass
class AnswerEvaluation:
    understanding: Literal["low", "medium", "high"]
    confidence: float
    should_continue: bool
    feedback: str
