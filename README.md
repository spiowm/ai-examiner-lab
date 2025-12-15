# AI Examiner Agent

AI Examiner Agent is an interactive LLM-based examiner that conducts oral exams in Ukrainian, asks questions on various topics, and evaluates student answers in real time.

The project uses **Gradio** for the UI and **Groq API** to work with the LLM.

---

## Features

- Dynamic questions on topics:
  - Python basics
  - OOP
  - Data structures
  - SQL
- Automatic answer evaluation
- Final score and aggregated feedback
- Clear separation of responsibilities:
  - UI
  - Controller (exam logic)
  - LLM agent
  - Storage (data)

---

## Environment Setup and Running

### Create a virtual environment
```
uv venv
```

### Activate the environment

Linux / macOS:
```
source .venv/bin/activate
```
Windows:
```
.venv\Scripts\activate
```

### Install dependencies

```
uv pip install .
```

### Run the application

```
python app.py
```
After launching, Gradio will display a local URL, for example:
```
http://127.0.0.1:7860
```
Open it in your browser.

### Test Students

For demonstration purposes, `storage.py` includes the following test students:
```
alice@example.com / Alice
bob@example.com / Bob
```
Use these credentials to start the exam.