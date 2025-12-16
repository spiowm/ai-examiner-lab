import gradio as gr
from typing import List, Tuple, Dict
from src.exam_controller import ExamController
from src.llm_agent import ExaminerLLMAgent
from src.exam_functions import start_exam, get_next_topic
from src.config import GCP_PROJECT_ID, VERTEX_AI_API_KEY, MODEL_NAME

controller: ExamController | None = None

def init_exam(name: str, email: str) -> Tuple[str, List[Dict[str, str]]]:
    global controller

    if not GCP_PROJECT_ID:
        return "GCP Project ID відсутній в .env файлі", []

    if not name or not email:
        return "Будь ласка, заповніть поля ім'я та email.", []

    try:
        llm_agent = ExaminerLLMAgent(
            project_id=GCP_PROJECT_ID,
            model=MODEL_NAME,
            api_key=VERTEX_AI_API_KEY
        )
        controller = ExamController(llm_agent)
        controller.name = name
        controller.email = email

        topics, exam_id = start_exam(email, name)
        controller.topics = topics
        controller.exam_id = exam_id
        controller.state = controller.state.ASKING_QUESTIONS
        controller.current_topic = get_next_topic(controller.topics)
        first_question = controller.llm.ask_question(controller.current_topic, controller.history)
        controller._add_message("system", first_question)
        return f"Розпочинаємо іспит для {name}", [{"role": "assistant", "content": first_question}]
    except ValueError as e:
        if controller:
            controller.name = None
            controller.email = None
        return f"Студента не знайдено: {str(e)}", []
    except Exception as e:
        error_msg = str(e)
        if "database" in error_msg.lower() and "does not exist" in error_msg.lower():
            return f"Помилка: Firestore база не створена. Створіть базу на console.cloud.google.com/firestore у режимі Native, регіон europe-west1.", []
        return f"Помилка: {error_msg}", []

def chat(user_input: str, chatbot_history: List[Dict[str, str]] | None) -> List[Dict[str, str]]:
    global controller
    if not controller:
        chatbot_history = chatbot_history or []
        chatbot_history.append({"role": "assistant", "content": "Будь ласка, спочатку розпочніть іспит, ввівши своє ім'я та email вгорі."})
        return chatbot_history

    chatbot_history = chatbot_history or []
    chatbot_history.append({"role": "user", "content": user_input})

    try:
        response = controller.handle_user_input(user_input)
        chatbot_history.append({"role": "assistant", "content": response})
    except Exception as e:
        error_message = f"Помилка: {str(e)}"
        chatbot_history.append({"role": "assistant", "content": error_message})

    return chatbot_history

with gr.Blocks() as demo:
    gr.Markdown("## AI Екзаменатор")
    gr.Markdown("1. Введіть ім'я та email\n2. Натисніть 'Розпочати іспит'\n3. Відповідайте на питання\n4. Отримайте оцінку")

    with gr.Row():
        name_input = gr.Textbox(label="Ваше ім'я", placeholder="наприклад, Аліса")
        email_input = gr.Textbox(label="Email", placeholder="наприклад, alice@example.com")

    with gr.Row():
        start_btn = gr.Button("Розпочати іспит", variant="primary")
        clear_btn = gr.Button("Скинути", variant="secondary")

    status_output = gr.Textbox(label="Статус", interactive=False)

    chatbot = gr.Chatbot(label="Чат іспиту", height=500)
    msg = gr.Textbox(label="Ваша відповідь", placeholder="Введіть вашу відповідь тут і натисніть Enter...")

    def reset_exam():
        global controller
        controller = None
        return "", [], ""

    start_btn.click(
        fn=init_exam,
        inputs=[name_input, email_input],
        outputs=[status_output, chatbot]
    )

    clear_btn.click(
        fn=reset_exam,
        inputs=[],
        outputs=[status_output, chatbot, msg]
    )

    msg.submit(chat, [msg, chatbot], chatbot)
    msg.submit(lambda: "", None, msg)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        theme=gr.themes.Soft()
    )

