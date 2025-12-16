from src.exam_functions import start_exam, get_next_topic, end_exam
from src.firestore_storage import FirestoreStorage
from src.models import ExamState
from datetime import datetime, UTC
from src.config import GCP_PROJECT_ID


class ExamController:
    def __init__(self, llm_agent):
        self.state = ExamState.COLLECTING_IDENTITY
        self.name = None
        self.email = None
        self.exam_id = None
        self.topics = []
        self.current_topic = None
        self.history = []
        self.score_sum = 0.0
        self.answer_count = 0
        self.dont_know_count = 0
        self.llm = llm_agent
        self.exam_finished = False
        self.storage = FirestoreStorage(project_id=GCP_PROJECT_ID)

    def start_exam_for_student(self, name: str, email: str):
        self.name = name
        self.email = email
        self.topics, self.exam_id = start_exam(email, name)
        self.state = ExamState.ASKING_QUESTIONS
        self.dont_know_count = 0
        self.current_topic = get_next_topic(self.topics)
        first_question = self.llm.ask_question(self.current_topic, self.history)
        self._add_message("system", first_question)
        return first_question

    def handle_user_input(self, text: str) -> str:
        self._add_message("user", text)
        if self.state != ExamState.ASKING_QUESTIONS:
            return "Іспит ще не розпочато."

        evaluation = self.llm.evaluate_answer(text, self.history, self.dont_know_count)

        if evaluation.understanding == "low" and ("не знаю" in text.lower() or "don't know" in text.lower()):
            self.dont_know_count += 1
        else:
            self.dont_know_count = 0

        self.score_sum += evaluation.confidence
        self.answer_count += 1

        response_parts = []

        if evaluation.feedback and evaluation.feedback != "Відповідь оцінено.":
            self._add_message("system", evaluation.feedback, msg_type="feedback")
            response_parts.append(evaluation.feedback)

        if evaluation.should_continue and self.dont_know_count < 2:
            question = self.llm.ask_question(self.current_topic, self.history)
            self._add_message("system", question)
            if response_parts:
                response_parts.append(f"\n{question}")
            else:
                response_parts.append(question)
            return "\n\n".join(response_parts)

        self.current_topic = get_next_topic(self.topics)
        self.dont_know_count = 0
        if self.current_topic:
            if response_parts:
                response_parts.append(f"\nНаступна тема: {self.current_topic}\n")
            else:
                response_parts.append(f"Наступна тема: {self.current_topic}\n")
            question = self.llm.ask_question(self.current_topic, self.history)
            self._add_message("system", question)
            response_parts.append(question)
            return "\n\n".join(response_parts)

        return self._finish_exam()

    def _add_message(self, role, content, msg_type=None):
        message = {
            "role": role,
            "content": content,
            "type": msg_type,
            "datetime": datetime.now(UTC).isoformat()
        }
        self.history.append(message)

        if self.exam_id:
            self.storage.add_message(exam_id=self.exam_id, role=role, content=content, msg_type=msg_type)

    def _finish_exam(self):
        self.state = ExamState.FINISHING
        self.exam_finished = True
        final_score = round((self.score_sum / max(self.answer_count, 1)) * 10, 2)
        end_exam(self.exam_id, final_score)
        self.state = ExamState.COMPLETED

        final_score, overall_feedback = self.get_result()

        return f"""**Іспит завершено!**

**Оцінка:** {final_score}/10

**Відгук:**
{overall_feedback}

Дякуємо за участь, {self.name}! Ваші результати збережено."""

    def get_result(self):
        final_score = round((self.score_sum / max(self.answer_count, 1)) * 10, 2)

        feedbacks = [m["content"] for m in self.history if m.get("type") == "feedback" and m.get("content")]

        if feedbacks:
            positive_words = ['правильно', 'добре', 'чудово', 'відмінно', 'гарн', 'чітк', 'good', 'excellent', 'great', 'correct', 'well']
            negative_words = ['але', 'однак', 'спробуйте', 'додайте', 'покращ', 'більше', 'пропусти', 'but', 'however', 'try', 'should', 'need', 'improve']

            positive = [f for f in feedbacks if any(word in f.lower() for word in positive_words)]
            mixed = [f for f in feedbacks if any(word in f.lower() for word in negative_words)]

            overall_feedback = "Що вдалося:\n"
            if positive:
                unique_positive = list(dict.fromkeys(positive))[:3]
                overall_feedback += "• " + "\n• ".join(unique_positive) + "\n\n"
            else:
                overall_feedback += "• Ви намагалися відповідати на питання\n\n"

            if mixed:
                overall_feedback += "Над чим попрацювати:\n"
                unique_mixed = list(dict.fromkeys(mixed))[:3]
                overall_feedback += "• " + "\n• ".join(unique_mixed)
            else:
                overall_feedback += "Рекомендації:\n• Продовжуйте вивчати матеріал"
        else:
            overall_feedback = "Продовжуйте практикуватися."

        return final_score, overall_feedback
