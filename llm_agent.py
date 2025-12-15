# llm_agent.py
import json
import random
from groq import Groq
from models import AnswerEvaluation

class ExaminerLLMAgent:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        if not api_key:
            raise ValueError("API key must be provided")
        
        self.client = Groq(api_key=api_key)
        self.model = model

    def ask_question(self, topic: str, history: list[dict]) -> str:
        messages = [
            {"role": "system", "content": f"You are an English-speaking examiner. Conduct an oral exam in English.\nTopic: {topic}"},
        ]
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})

        # Various question templates in English
        question_templates = [
            f"Explain the main concept of '{topic}'.",
            f"How would you describe the key idea of '{topic}' in your own words?",
            f"Give an example illustrating '{topic}'.",
            f"What is important to know about '{topic}'? Explain briefly."
        ]
        template_prompt = random.choice(question_templates)

        messages.append({
            "role": "user",
            "content": f"Ask one clear question based on this template: {template_prompt}. Do not repeat, do not leave empty lines."
        })

        result = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )

        question = result.choices[0].message.content.strip()
        if not question:
            question = template_prompt

        return question

    def evaluate_answer(self, answer: str, history: list[dict]) -> AnswerEvaluation:
        """
        Evaluates the student's response in English:
        - understanding -> confidence
        - feedback in English
        - should_continue: whether to ask more questions on the topic
        """

        # Get the last question as context
        last_question = None
        for msg in reversed(history):
            if msg["role"] == "system" and msg.get("type") is None:
                last_question = msg["content"]
                break
        if not last_question:
            last_question = "Previous question is missing."

        # Few-shot prompt for stable JSON in English
        messages = [
            {
                "role": "system",
                "content": """
You are an English-speaking examiner. Evaluate the student's answer in English.
Return only JSON with fields:
- understanding: "low", "medium", "high"
- should_continue: true/false
- feedback: short comment on what is good and what can be improved

Use the previous question as context.
Examples:
Student answer: "Encapsulation hides the data and methods of the class."
JSON: {"understanding": "high", "should_continue": false, "feedback": "The answer is correct and clear."}

Student answer: "I don't know."
JSON: {"understanding": "low", "should_continue": true, "feedback": "The student did not answer; they need to know the material."}
"""
            },
            {
                "role": "user",
                "content": f"Question: {last_question}\nStudent answer: {answer}"
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.0
            )

            raw_content = response.choices[0].message.content.strip()

            # Parse JSON from LLM response
            start = raw_content.find("{")
            end = raw_content.rfind("}") + 1
            if start == -1 or end == -1:
                raise ValueError("JSON not found in LLM response")

            data = json.loads(raw_content[start:end])

            understanding = data.get("understanding", "medium")
            should_continue = data.get("should_continue", False)
            feedback = data.get("feedback", "Answer evaluated.")

            # Convert understanding -> confidence
            confidence_map = {"low": 0.2, "medium": 0.5, "high": 0.9}

            # Penalize "I don't know"
            if any(x in answer.lower() for x in ["i don't know", "idk", "not sure"]):
                confidence = 0.0
                feedback = "The student did not provide an answer; they need to know the material."
            else:
                confidence = confidence_map.get(understanding, 0.5)

            return AnswerEvaluation(
                understanding=understanding,
                confidence=confidence,
                should_continue=should_continue,
                feedback=feedback
            )

        except Exception:
            return AnswerEvaluation(
                understanding="low",
                confidence=0.2,
                should_continue=False,
                feedback="Failed to evaluate the answer correctly."
            )
