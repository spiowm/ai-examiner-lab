# app.py
import gradio as gr
from typing import List, Tuple, Dict, Any
from exam_controller import ExamController
from llm_agent import ExaminerLLMAgent
from exam_functions import start_exam, get_next_topic

controller: ExamController | None = None

def init_exam(api_key: str, name: str, email: str) -> Tuple[str, List[Dict[str, str]]]:
    global controller
    if not api_key or not name or not email:
        return "Please fill in all fields.", []

    llm_agent = ExaminerLLMAgent(api_key=api_key)
    controller = ExamController(llm_agent)
    controller.name = name
    controller.email = email

    try:
        controller.topics = start_exam(email, name)
        controller.state = controller.state.ASKING_QUESTIONS
        controller.current_topic = get_next_topic(controller.topics)
        first_question = controller.llm.ask_question(controller.current_topic, controller.history)
        controller._add_message("system", first_question)
        return f"Data accepted. We are starting the exam for {name}", [{"role": "assistant", "content": first_question}]
    except ValueError:
        controller.name = None
        controller.email = None
        return "Student not found. Please try again.", []

def chat(user_input: str, chatbot_history: List[Dict[str, str]] | None) -> List[Dict[str, str]]:
    global controller
    if not controller:
        chatbot_history = chatbot_history or []
        chatbot_history.append({"role": "system", "content": "First enter your API key and data"})
        return chatbot_history

    chatbot_history = chatbot_history or []
    chatbot_history.append({"role": "user", "content": user_input})
    response = controller.handle_user_input(user_input)
    chatbot_history.append({"role": "assistant", "content": response})

    if getattr(controller, "exam_finished", False):
        final_score, overall_feedback = controller.get_result()
        chatbot_history.append({
            "role": "system",
            "content": f"The exam is complete!\nGrade: {final_score}/10\nFeedback:\n{overall_feedback}"
        })

    return chatbot_history

with gr.Blocks() as demo:
    gr.Markdown("## 🎓 AI Examiner Agent")
    gr.Markdown(
        """
        1. Enter your Groq API key  
        2. Enter your name and email. 
        3. Start the exam in the chat  
        4. Once completed, you will see a rating and review.
        """
    )

    api_key_input = gr.Textbox(label="Groq API Key", type="password")
    name_input = gr.Textbox(label="Your name")
    email_input = gr.Textbox(label="Email")
    start_btn = gr.Button("Start Exam")
    status_output = gr.Textbox(label="Status", interactive=False)

    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Your message")

    start_btn.click(
        fn=init_exam,
        inputs=[api_key_input, name_input, email_input],
        outputs=[status_output, chatbot]
    )

    msg.submit(chat, [msg, chatbot], chatbot)
    msg.submit(lambda: "", None, msg)

demo.launch()
