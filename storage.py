# storage.py
from datetime import datetime
import json


STUDENTS = {
    "alice@example.com": {"name": "Alice"},
    "bob@example.com": {"name": "Bob"},
}

EXAMS = {}  # in-memory


def save_exam_start(email: str, topics: list[str]) -> None:
    EXAMS[email] = {
        "topics": topics,
        "started_at": datetime.utcnow().isoformat()
    }


def save_exam_end(email: str, score: float, history: list[dict]) -> None:
    payload = {
        "email": email,
        "score": score,
        "history": history,
        "finished_at": datetime.utcnow().isoformat()
    }

    with open(f"exam_{email}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
