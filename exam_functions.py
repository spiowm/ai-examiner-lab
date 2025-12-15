# exam_functions.py
import random
from storage import STUDENTS, save_exam_start, save_exam_end

TOPICS_POOL = [
    "Python basics",
    "OOP",
    "Data structures",
    "SQL"
]


def start_exam(email: str, name: str) -> list[str]:
    student = STUDENTS.get(email)
    if not student or student["name"] != name:
        raise ValueError("Student not found")

    topics = random.sample(TOPICS_POOL, k=3)
    save_exam_start(email, topics)
    return topics


def get_next_topic(topics_queue: list[str]) -> str | None:
    return topics_queue.pop(0) if topics_queue else None


def end_exam(email: str, score: float, history: list[dict]) -> None:
    save_exam_end(email, score, history)
