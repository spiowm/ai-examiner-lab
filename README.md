# AI Examiner

Interactive oral examination system powered by Google Vertex AI.

## Features

- Automated oral examination in Ukrainian
- AI-powered answer evaluation
- Cloud storage with Firestore
- Real-time scoring and feedback

## Tech Stack

- **UI**: Gradio
- **LLM**: Google Vertex AI Gemini
- **Database**: Google Cloud Firestore
- **Language**: Python 3.11+

## Setup

### Prerequisites

1. Google Cloud Project with Vertex AI and Firestore enabled
2. API key from GCP Console
3. Python 3.11+

### Installation

```bash
uv sync
```

### Configuration

Create `.env` file:

```bash
GCP_PROJECT_ID=your-project-id
VERTEX_AI_API_KEY=your-api-key
MODEL_NAME=gemini-2.0-flash-lite
```

### Create Firestore Database

1. Open Firestore Console
2. Create Database in Native mode
3. Select region: europe-west1

## Usage

```bash
python app.py
```

Open http://localhost:7860 in your browser.

## Project Structure

```
├── app.py
└── src/
    ├── llm_agent.py          # Vertex AI integration
    ├── exam_controller.py    # Exam flow
    ├── exam_functions.py     # Exam operations
    ├── firestore_storage.py  # Database layer
    ├── models.py             # Data models
    └── config.py             # Configuration
```

## Database Schema

**students**: email, name, created_at

**exams**: exam_id, student_email, student_name, topics, score, status, started_at, finished_at

**messages**: message_id, exam_id, role, content, type, timestamp

## License

MIT

