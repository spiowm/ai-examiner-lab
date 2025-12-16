from google.cloud import firestore
from datetime import datetime, UTC
from typing import Optional, List, Dict
import uuid


class FirestoreStorage:
    def __init__(self, project_id: str):
        self.db = firestore.Client(project=project_id)
        self.students_ref = self.db.collection('students')
        self.exams_ref = self.db.collection('exams')
        self.messages_ref = self.db.collection('messages')

    def get_student(self, email: str) -> Optional[Dict]:
        doc = self.students_ref.document(email).get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def create_student(self, email: str, name: str) -> None:
        self.students_ref.document(email).set({
            'name': name,
            'email': email,
            'created_at': datetime.now(UTC)
        })

    def student_exists(self, email: str, name: str) -> bool:
        student = self.get_student(email)
        if not student:
            return False
        return student.get('name') == name

    def create_exam(self, email: str, name: str, topics: List[str]) -> str:
        exam_id = str(uuid.uuid4())
        
        self.exams_ref.document(exam_id).set({
            'exam_id': exam_id,
            'student_email': email,
            'student_name': name,
            'topics': topics,
            'score': None,
            'started_at': datetime.now(UTC),
            'finished_at': None,
            'status': 'in_progress'
        })
        
        return exam_id
    
    def finish_exam(self, exam_id: str, score: float) -> None:
        self.exams_ref.document(exam_id).update({
            'score': score,
            'finished_at': datetime.now(UTC),
            'status': 'completed'
        })

    def get_exam(self, exam_id: str) -> Optional[Dict]:
        doc = self.exams_ref.document(exam_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def get_student_exams(self, email: str, limit: int = 10) -> List[Dict]:
        docs = self.exams_ref \
            .where('student_email', '==', email) \
            .order_by('started_at', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()
        return [doc.to_dict() for doc in docs]

    def add_message(self, exam_id: str, role: str, content: str, msg_type: Optional[str] = None) -> str:
        message_id = str(uuid.uuid4())
        self.messages_ref.document(message_id).set({
            'message_id': message_id,
            'exam_id': exam_id,
            'role': role,
            'content': content,
            'type': msg_type,
            'timestamp': datetime.now(UTC)
        })
        return message_id

    def get_exam_messages(self, exam_id: str) -> List[Dict]:
        docs = self.messages_ref \
            .where('exam_id', '==', exam_id) \
            .order_by('timestamp') \
            .stream()
        return [doc.to_dict() for doc in docs]

    def get_exam_with_history(self, exam_id: str) -> Optional[Dict]:
        exam = self.get_exam(exam_id)
        if not exam:
            return None
        exam['history'] = self.get_exam_messages(exam_id)
        return exam

    def get_average_score(self, email: str) -> Optional[float]:
        docs = self.exams_ref \
            .where('student_email', '==', email) \
            .where('status', '==', 'completed') \
            .stream()
        scores = [doc.to_dict()['score'] for doc in docs if doc.to_dict().get('score')]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def count_exams(self, email: str) -> int:
        docs = self.exams_ref.where('student_email', '==', email).stream()
        return len(list(docs))

