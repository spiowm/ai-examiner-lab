import random
from typing import Literal, cast
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from src.models import AnswerEvaluation


class ExaminerLLMAgent:
    def __init__(self, project_id: str, model: str, api_key: str = None):
        if not project_id:
            raise ValueError("GCP Project ID must be provided")

        if api_key:
            import os
            os.environ["GOOGLE_API_KEY"] = api_key

        vertexai.init(project=project_id, location="europe-west1")
        self.model = GenerativeModel(model_name=model)

    def ask_question(self, topic: str, history: list[dict]) -> str:
        templates = [
            f"Поясніть основну концепцію '{topic}'.",
            f"Як би ви описали ключову ідею '{topic}' своїми словами?",
            f"Наведіть приклад, що ілюструє '{topic}'.",
            f"Що важливо знати про '{topic}'? Поясніть коротко."
        ]
        return random.choice(templates)

    def evaluate_answer(self, answer: str, history: list[dict], dont_know_count: int = 0) -> AnswerEvaluation:
        last_question = "Попереднє питання відсутнє."
        for msg in reversed(history):
            if msg["role"] == "system" and msg.get("type") is None:
                last_question = msg["content"]
                break

        answer_lower = answer.lower().strip()
        dont_know_phrases = ["i don't know", "idk", "я не знаю", "не знаю"]
        is_dont_know = any(phrase in answer_lower for phrase in dont_know_phrases)

        if is_dont_know and len(answer.strip()) < 50:
            if dont_know_count >= 1:
                return AnswerEvaluation(
                    understanding="low",
                    confidence=0.1,
                    should_continue=False,
                    feedback="Переходимо до наступної теми."
                )
            return AnswerEvaluation(
                understanding="low",
                confidence=0.2,
                should_continue=True,
                feedback="Спробуйте пояснити своїми словами або наведіть приклад."
            )

        system_prompt = """Ти екзаменатор. Оціни відповідь коротко (1-2 речення).

Формат:
ОЦІНКА: [низька/середня/висока]
ПРОДОВЖИТИ: [так/ні]
КОМЕНТАР: [конкретний коментар]

Правила:
- низька + так = слабка відповідь, дай шанс покращити
- середня + так = частково правильно, уточни
- середня + ні = достатньо
- висока + ні = відмінно, переходь далі"""

        try:
            response = self.model.generate_content(
                f"{system_prompt}\n\nПитання: {last_question}\nВідповідь: {answer}",
                generation_config=GenerationConfig(max_output_tokens=200, temperature=0.2)
            )

            raw = response.text.strip().lower()

            if "низька" in raw or "low" in raw:
                understanding_str = "low"
                confidence = 0.3
            elif "висока" in raw or "high" in raw:
                understanding_str = "high"
                confidence = 1.0
            else:
                understanding_str = "medium"
                confidence = 0.6

            should_continue = "так" in raw or "yes" in raw

            feedback = response.text.strip()
            for line in feedback.split('\n'):
                if "КОМЕНТАР:" in line.upper():
                    feedback = line.split(':', 1)[1].strip()
                    break

            return AnswerEvaluation(
                cast(Literal["low", "medium", "high"], understanding_str),
                confidence,
                should_continue,
                feedback
            )

        except Exception as e:
            print(f"Error evaluating: {e}")
            return AnswerEvaluation("medium", 0.6, False, "Відповідь прийнято.")
