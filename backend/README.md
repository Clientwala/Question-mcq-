# PDF Question Document Generator - Backend

FastAPI backend service for converting PDF question papers to formatted Word documents.

## Features

- 📄 **PDF Text Extraction** - Extract text from PDFs using pdfplumber
- 🔍 **Question Parsing** - Intelligent regex-based question, option, and solution extraction
- 📝 **Word Generation** - Generate formatted .docx files with exact table structure
- ⚡ **Background Processing** - Celery + Redis for async task execution
- 📊 **Real-time Progress** - Track processing progress (via WebSocket in future)
- 🗄️ **Database** - PostgreSQL with async SQLAlchemy
- 🧹 **Auto-cleanup** - 24-hour file retention

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy 2.0** - Async ORM
- **Celery** - Distributed task queue
- **Redis** - Message broker and caching
- **PostgreSQL** - Primary database
- **pdfplumber** - PDF text extraction
- **python-docx** - Word document generation

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # REST API endpoints
│   ├── core/                # Config, Celery setup
│   ├── db/                  # Database session, base
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── pdf_parser.py
│   │   ├── question_parser.py
│   │   ├── document_generator.py
│   │   └── file_manager.py
│   ├── tasks/               # Celery tasks
│   │   ├── processing.py
│   │   └── cleanup.py
│   ├── utils/               # Utilities
│   │   └── formatters.py    # Word formatting
│   └── main.py              # FastAPI app
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- Redis 7+

### Setup

1. **Clone repository**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

5. **Create database**
```bash
# PostgreSQL
createdb pdf_questions
```

6. **Run migrations**
```bash
alembic upgrade head
```

## Running the Application

### Development Mode

**Terminal 1: FastAPI Server**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Celery Worker**
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

**Terminal 3: Celery Beat (optional - for scheduled cleanup)**
```bash
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

**Terminal 4: Redis**
```bash
redis-server
```

### Access API

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## Testing

### Test PDF Parser

```bash
cd backend
python test_parser.py
```

This will:
1. Extract text from the PDF
2. Parse questions using regex patterns
3. Generate a test Word document
4. Show statistics and confidence scores

### Unit Tests

```bash
pytest tests/
```

## Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/pdf_questions

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Storage
STORAGE_PATH=../data
MAX_UPLOAD_SIZE=52428800  # 50MB

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# App
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

## API Endpoints (Planned)

```
POST   /api/v1/jobs/                - Upload PDF and create job
GET    /api/v1/jobs/{job_id}        - Get job status
GET    /api/v1/jobs/                - List recent jobs
GET    /api/v1/jobs/{job_id}/download - Download Word document
```

## Database Schema

### Jobs Table

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    pdf_filename VARCHAR(500),
    pdf_path TEXT,
    output_filename VARCHAR(500),
    output_path TEXT,
    config JSONB,                    -- {page_start, page_end, question_start, question_end, chapter_name}
    status VARCHAR(50),              -- pending, parsing, generating, completed, failed
    progress INTEGER,                -- 0-100
    current_step VARCHAR(200),
    total_questions INTEGER,
    diagrams_detected INTEGER,
    error_message TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP             -- Auto-delete after 24 hours
);
```

## Processing Flow

1. **Upload PDF** → Saved to `data/uploads/{job_id}/input.pdf`
2. **Create Job** → Record created in database with `status=pending`
3. **Queue Task** → Celery task `process_pdf_task` queued
4. **Extract Text** → pdfplumber extracts text from specified pages
5. **Parse Questions** → Regex patterns extract questions, options, answers
6. **Generate Document** → python-docx creates formatted Word file
7. **Save Output** → Saved to `data/outputs/{job_id}/output.docx`
8. **Update Job** → Status set to `completed`, progress=100
9. **Download** → User downloads Word document
10. **Auto-cleanup** → Files deleted after 24 hours

## Question Parser

Uses multi-stage regex parsing:

```python
PATTERNS = {
    'question_number': r'(?:Q\.?\s*)?(\d+)[\.\)]\s*',
    'option_marker': r'\(?\s*([a-dA-D])\s*[\)\.]?\s*',
    'answer': r'(?:Ans(?:wer)?|Correct)\s*[:\.]\s*\(?\s*([a-dA-D])\s*\)?',
    'solution': r'(?:Solution|Explanation|Sol)\s*[:\.]\s*',
    'diagram': r'(?:diagram|figure|image|graph|chart)',
}
```

**Confidence Scoring:**
- Has question text: +0.3
- Has 4 options: +0.3
- Has correct answer: +0.2
- Has solution: +0.2

## Document Format

**Table Structure** (8 rows × 3 columns):
```
┌──────────┬────────────────────────────────────┬──────────────┐
│ Question │ Question text (merged)             │              │
├──────────┼────────────────────────────────────┴──────────────┤
│ Type     │ Multiple_choice (merged)                         │
├──────────┼────────────────────────────────────┬──────────────┤
│ Option   │ Option A text                      │ correct      │
│ Option   │ Option B text                      │ incorrect    │
│ Option   │ Option C text                      │ incorrect    │
│ Option   │ Option D text                      │ incorrect    │
├──────────┼────────────────────────────────────┴──────────────┤
│ Solution │ Solution text (merged)                           │
├──────────┼────────────────────────────────────┬──────────────┤
│ Marks    │ 1                                  │ 0.25         │
└──────────┴────────────────────────────────────┴──────────────┘
```

**Formatting:**
- Font: Times New Roman, 14pt, Bold
- Column widths: 1.5cm, 8.5cm, 3.0cm
- Cell padding: 120 twips top/bottom, 100 twips left/right
- Page margins: 3.5cm top, 2.4cm others

## Troubleshooting

### Database connection error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Create database
createdb pdf_questions
```

### Redis connection error
```bash
# Check Redis is running
redis-cli ping  # Should return PONG
```

### Celery not processing tasks
```bash
# Check Celery worker is running
celery -A app.core.celery_app inspect active

# Restart worker
pkill -f celery
celery -A app.core.celery_app worker --loglevel=info
```

### PDF parsing fails
- Check PDF is not password-protected
- Check page range is valid
- Check question numbers match PDF content
- Adjust regex patterns in `question_parser.py`

## Development

### Code Style
```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Production Deployment

See main README for Docker and Render deployment instructions.

## License

Proprietary - Client Work

## Support

For issues or questions, check:
- API documentation: http://localhost:8000/docs
- Logs: Check console output
- Database: `psql pdf_questions`
