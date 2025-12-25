# PDF Question Document Generator

Professional web application for extracting questions from PDF files and generating formatted Word documents with real-time progress tracking.

![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![React](https://img.shields.io/badge/react-18-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### Core Functionality
- 📄 **PDF Upload**: Drag & drop interface with 50MB limit
- 🔍 **Question Extraction**: Automatic parsing with regex patterns
- 📝 **Word Generation**: Professional 8×3 table format (Times New Roman, 14pt)
- ⚡ **Real-time Progress**: WebSocket-based live updates
- 📊 **Progress Tracking**: Visual progress bar and step indicators
- 📥 **Document Download**: Instant download of generated files
- 🗑️ **Auto Cleanup**: 24-hour file retention with automatic deletion

### Configuration Options
- Page range selection (start/end)
- Question range selection (start/end)
- Chapter name (optional)
- Unit name (optional)
- Custom output filename (optional)

### Technical Features
- Asynchronous processing with Celery
- Persistent storage with disk mounting
- Database-backed job tracking
- Error handling and recovery
- Diagram detection in questions
- Animated loading indicators

## Tech Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL (Neon cloud) with SQLAlchemy 2.0
- **Task Queue**: Celery 5.3.6 + Redis 5.0
- **WebSocket**: Socket.IO (python-socketio 5.11)
- **PDF Processing**: pdfplumber 0.10.4
- **Document Generation**: python-docx 1.1.0

### Frontend
- **Framework**: React 18.2 with TypeScript
- **Build Tool**: Vite 5.0
- **HTTP Client**: Axios
- **WebSocket**: Socket.io-client
- **File Upload**: react-dropzone
- **Styling**: Custom CSS (no framework)

### Infrastructure
- **Deployment**: Render.com (Docker-ready)
- **Database**: Neon PostgreSQL (cloud-hosted)
- **Cache/Queue**: Redis
- **Storage**: Persistent disk (10GB)

## Project Structure

```
Question/
├── backend/                  # FastAPI backend
│   ├── alembic/             # Database migrations
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Core configurations
│   │   ├── db/              # Database setup
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery tasks
│   │   └── utils/           # Utility functions
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment template
│
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── App.tsx          # Main component
│   │   ├── App.css          # Styling
│   │   └── main.tsx         # Entry point
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
│
├── data/                     # Storage directory
│   ├── uploads/             # Temporary PDF uploads
│   └── outputs/             # Generated documents
│
├── docker-compose.yml        # Local development setup
├── render.yaml              # Render deployment config
├── RENDER_DEPLOYMENT.md     # Deployment guide
└── DEPLOYMENT_CHECKLIST.md  # Deployment checklist
```

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Local Development

#### 1. Clone Repository
```bash
git clone https://github.com/Clientwala/Question-mcq-.git
cd Question
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
```

#### 3. Start Redis
```bash
# Windows
redis-server

# Linux/Mac
redis-server /usr/local/etc/redis.conf
```

#### 4. Start Celery Worker
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

#### 5. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

#### 6. Access Application
- Frontend: http://localhost:5174
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Setup (Alternative)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Deployment

### Render.com (Recommended)

**Quick Deploy**:
1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Create new Blueprint
4. Select repository: `Clientwala/Question-mcq-`
5. Click "Apply"

**Detailed Guide**: See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)

**Checklist**: See [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)

### Manual Deployment

See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for step-by-step manual deployment instructions.

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here

# CORS
CORS_ORIGINS=["http://localhost:5174","https://your-frontend.com"]

# Storage
STORAGE_PATH=../data
MAX_UPLOAD_SIZE=52428800

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

## API Documentation

### Endpoints

**POST /api/v1/jobs/**
- Upload PDF and create processing job
- Returns job ID and initial status

**GET /api/v1/jobs/{job_id}**
- Get job status and details
- Returns progress, current step, results

**GET /api/v1/jobs/**
- List all recent jobs (24h)
- Returns paginated job list

**GET /api/v1/jobs/{job_id}/download**
- Download generated Word document
- Returns .docx file

**WebSocket: /socket.io**
- Real-time progress updates
- Events: `progress`, `complete`, `error`

### Request Example
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -F "pdf_file=@question.pdf" \
  -F "page_start=1" \
  -F "page_end=10" \
  -F "question_start=1" \
  -F "question_end=15" \
  -F "chapter_name=Chapter 1" \
  -F "unit_name=Introduction"
```

### Response Example
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "pdf_filename": "question.pdf",
  "created_at": "2025-12-25T12:00:00"
}
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm run test
```

### End-to-End Test
```bash
# Upload test PDF
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -F "pdf_file=@test.pdf" \
  -F "page_start=1" \
  -F "page_end=2" \
  -F "question_start=1" \
  -F "question_end=5"

# Check status (use job_id from response)
curl "http://localhost:8000/api/v1/jobs/{job_id}"

# Download result when complete
curl "http://localhost:8000/api/v1/jobs/{job_id}/download" -o output.docx
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
# Backend
tail -f backend/logs/app.log

# Celery
tail -f backend/logs/celery.log

# Redis
redis-cli monitor
```

### Metrics
- Request count: `/metrics` endpoint (Prometheus format)
- Database connections: PostgreSQL logs
- Queue size: Redis LLEN commands

## Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check DATABASE_URL format
postgresql+asyncpg://user:pass@host:port/database

# Test connection
python -c "from app.db.base import engine; engine.connect()"
```

**2. Redis Connection Error**
```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG
```

**3. CORS Error**
```bash
# Update backend .env
CORS_ORIGINS=["http://localhost:5174"]

# Restart backend server
```

**4. File Upload Fails**
```bash
# Check storage directory exists
mkdir -p data/uploads data/outputs

# Check permissions
chmod -R 755 data/
```

**5. Celery Worker Not Processing**
```bash
# Check worker is running
celery -A app.core.celery_app inspect active

# Restart worker
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

## Performance

### Benchmarks
- PDF Upload: <1 second (10MB file)
- Question Parsing: ~2 seconds (50 questions)
- Document Generation: ~3 seconds (50 questions)
- Total Processing: <10 seconds (typical job)

### Optimization Tips
- Use Redis for caching
- Enable database connection pooling
- Compress static assets
- Enable CDN for frontend
- Use worker auto-scaling on Render

## Security

### Best Practices
- ✅ Environment variables for secrets
- ✅ CORS restricted to frontend domain
- ✅ File size limits (50MB)
- ✅ SQL injection prevention (SQLAlchemy)
- ✅ HTTPS enforced (Render auto-SSL)
- ✅ Input validation (Pydantic)
- ✅ Rate limiting (FastAPI middleware)

### Security Headers
```python
# Added in app/main.py
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

### Code Style
- **Backend**: Follow PEP 8
- **Frontend**: ESLint configuration
- **Commits**: Conventional Commits format

## License

This project is licensed under the MIT License.

## Support

- **Documentation**: See `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/Clientwala/Question-mcq-/issues)
- **Email**: support@example.com

## Roadmap

### Version 2.0 (Planned)
- [ ] AI-powered question parsing (OpenAI/Claude)
- [ ] Multiple document formats (PDF output)
- [ ] Batch processing (multiple PDFs)
- [ ] User authentication
- [ ] Question bank/history
- [ ] Advanced formatting options
- [ ] Export to LMS formats (Moodle, Canvas)

## Changelog

### v1.0.0 (2025-12-25)
- ✅ Initial release
- ✅ PDF upload and processing
- ✅ Real-time progress tracking
- ✅ Word document generation
- ✅ Render.com deployment ready
- ✅ Docker support
- ✅ Complete documentation

---

**Built with ❤️ for educators and students**
