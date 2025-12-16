import random
from src.firestore_storage import FirestoreStorage
from src.config import GCP_PROJECT_ID

storage = FirestoreStorage(project_id=GCP_PROJECT_ID)

TOPICS_POOL = [
    "Основи Python",
    "ООП (Об'єктно-орієнтоване програмування)",
    "Структури даних",
    "SQL"
]


def start_exam(email: str, name: str) -> tuple[list[str], str]:
    if not storage.student_exists(email, name):
        storage.create_student(email, name)

    topics = random.sample(TOPICS_POOL, k=3)
    exam_id = storage.create_exam(email, name, topics)

    return topics, exam_id


def get_next_topic(topics_queue: list[str]) -> str | None:
    return topics_queue.pop(0) if topics_queue else None


def end_exam(exam_id: str, score: float) -> None:
    storage.finish_exam(exam_id, score)

