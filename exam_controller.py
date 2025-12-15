from exam_functions import start_exam, get_next_topic, end_exam
from models import ExamState
from datetime import datetime

class ExamController:
    def __init__(self, llm_agent):
        self.state = ExamState.COLLECTING_IDENTITY
        self.name = None
        self.email = None
        self.topics = []
        self.current_topic = None
        self.history = []
        self.score_sum = 0.0
        self.answer_count = 0
        self.llm = llm_agent
        self.exam_finished = False

    def start_exam_for_student(self, name: str, email: str):
        self.name = name
        self.email = email
        self.topics = start_exam(email, name)
        self.state = ExamState.ASKING_QUESTIONS
        self.current_topic = get_next_topic(self.topics)
        first_question = self.llm.ask_question(self.current_topic, self.history)
        self._add_message("system", first_question)
        return first_question

    def handle_user_input(self, text: str) -> str:
        self._add_message("user", text)
        if self.state != ExamState.ASKING_QUESTIONS:
            return "The exam hasn't started yet."

        evaluation = self.llm.evaluate_answer(text, self.history)

        # Add score
        self.score_sum += evaluation.confidence
        self.answer_count += 1

        # Add feedback in history, if present
        if evaluation.feedback:
            self._add_message("system", evaluation.feedback, msg_type="feedback")

        # Checking whether to continue the current topic
        if evaluation.should_continue:
            question = self.llm.ask_question(self.current_topic, self.history)
            self._add_message("system", question)
            return question

        # Move on to the next topic.
        self.current_topic = get_next_topic(self.topics)
        if self.current_topic:
            question = self.llm.ask_question(self.current_topic, self.history)
            self._add_message("system", question)
            return question

        # The exam is complete
        return self._finish_exam()

    def _add_message(self, role, content, msg_type=None):
        self.history.append({
            "role": role,
            "content": content,
            "type": msg_type,  # "feedback" for comments from LLM
            "datetime": datetime.utcnow().isoformat()
        })

    def _finish_exam(self):
        self.state = ExamState.FINISHING
        self.exam_finished = True
        final_score = round((self.score_sum / max(self.answer_count, 1)) * 10, 2)
        end_exam(self.email, final_score, self.history)
        self.state = ExamState.COMPLETED
        return f"The exam is complete!\nGrade: {final_score}/10\nThank you for participating!"

    def get_result(self):
        """Returns the final grade and aggregated feedback for the chat"""
        final_score = round((self.score_sum / max(self.answer_count, 1)) * 10, 2)

        # Collect only real feedback
        feedbacks = [m["content"] for m in self.history
                     if m.get("type") == "feedback" and m.get("content")]
        overall_feedback = "\n".join(feedbacks) if feedbacks else "Well done! You can still improve your knowledge on some topics."

        return final_score, overall_feedback
