# PDF Question Generator - Quick Start Guide

Complete guide to get the application running in minutes.

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker Desktop installed
- Git

### Steps

1. **Clone and navigate**
```bash
cd D:\Question
```

2. **Start all services**
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI Backend (port 8000)
- Celery Worker
- Celery Beat

3. **Run database migrations**
```bash
docker-compose exec backend alembic upgrade head
```

4. **Access the API**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

5. **View logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

6. **Stop services**
```bash
docker-compose down
```

---

## 💻 Manual Setup (Without Docker)

### Prerequisites
- Python 3.10+
- PostgreSQL 15+
- Redis 7+

### 1. Setup Database

**PostgreSQL:**
```bash
# Start PostgreSQL service
# Windows: Services → PostgreSQL → Start
# Mac: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Create database
psql -U postgres
CREATE DATABASE pdf_questions;
CREATE USER admin WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE pdf_questions TO admin;
\q
```

**Redis:**
```bash
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis && brew services start redis
# Linux: sudo apt install redis-server && sudo systemctl start redis

# Test Redis
redis-cli ping  # Should return PONG
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your database credentials
```

### 3. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 4. Start Services

Open **4 terminal windows**:

**Terminal 1: FastAPI Server**
```bash
cd backend
uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Celery Worker**
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

**Terminal 3: Celery Beat (optional)**
```bash
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

**Terminal 4: Redis**
```bash
redis-server
```

### 5. Verify Installation

Visit http://localhost:8000/docs - you should see the API documentation.

---

## 📝 Testing the Backend

### Option 1: Using API Docs (Swagger UI)

1. Go to http://localhost:8000/docs
2. Click on `POST /api/v1/jobs/`
3. Click "Try it out"
4. Fill in the form:
   - Upload a PDF file
   - Set page_start, page_end
   - Set question_start, question_end
   - Add optional chapter_name
5. Click "Execute"
6. Copy the `job_id` from response
7. Use `GET /api/v1/jobs/{job_id}` to check status
8. When status is "completed", use `GET /api/v1/jobs/{job_id}/download` to download

### Option 2: Using Test Script

```bash
cd backend
python test_parser.py
```

**Before running, edit test_parser.py:**
```python
PDF_PATH = "../chapter -2 168-221 (1).pdf"  # Your PDF
PAGE_START = 1        # Adjust
PAGE_END = 5          # Adjust
QUESTION_START = 168  # Adjust
QUESTION_END = 175    # Adjust
```

### Option 3: Using cURL

```bash
# Create job
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "pdf_file=@path/to/your.pdf" \
  -F "page_start=1" \
  -F "page_end=10" \
  -F "question_start=1" \
  -F "question_end=20" \
  -F "chapter_name=Test Chapter"

# Check status (replace with actual job_id)
curl "http://localhost:8000/api/v1/jobs/{job_id}"

# Download result
curl "http://localhost:8000/api/v1/jobs/{job_id}/download" -o output.docx
```

---

## 🔧 Troubleshooting

### Port Already in Use

```bash
# Windows - Kill process on port
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error

```bash
# Check PostgreSQL is running
# Windows: Services → PostgreSQL
# Mac: brew services list
# Linux: sudo systemctl status postgresql

# Test connection
psql -U admin -d pdf_questions -h localhost
```

### Redis Connection Error

```bash
# Check Redis is running
redis-cli ping

# If not running
# Windows: Start redis-server.exe
# Mac: brew services start redis
# Linux: sudo systemctl start redis
```

### Celery Worker Not Processing

```bash
# Check worker is running
celery -A app.core.celery_app inspect active

# Restart worker
# Ctrl+C to stop
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

### PDF Parsing Fails

- **Check PDF is not password-protected**
- **Verify page range is correct**
- **Ensure question numbers match PDF**
- **Check regex patterns in `backend/app/services/question_parser.py`**

### Import Errors

```bash
# Make sure you're in the right directory
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📊 Project Status

### ✅ Completed (Backend - Weeks 1-3)

- [x] FastAPI application with CORS, logging, error handling
- [x] PostgreSQL database with async SQLAlchemy
- [x] PDF text extraction (pdfplumber)
- [x] Question parsing with regex (multi-stage, confidence scoring)
- [x] Word document generation (exact formatting from existing scripts)
- [x] Celery + Redis background processing
- [x] Socket.IO WebSocket for real-time progress
- [x] REST API endpoints (create, status, list, download, delete)
- [x] File management with 24-hour auto-cleanup
- [x] Docker development environment
- [x] Alembic database migrations
- [x] Comprehensive documentation

### 📁 File Structure

```
D:\Question\
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   └── jobs.py          ✅ Complete
│   │   ├── core/
│   │   │   ├── config.py        ✅ Complete
│   │   │   └── celery_app.py    ✅ Complete
│   │   ├── db/
│   │   │   └── base.py          ✅ Complete
│   │   ├── models/
│   │   │   └── job.py           ✅ Complete
│   │   ├── schemas/
│   │   │   ├── config.py        ✅ Complete
│   │   │   └── job.py           ✅ Complete
│   │   ├── services/
│   │   │   ├── pdf_parser.py    ✅ Complete
│   │   │   ├── question_parser.py ✅ Complete
│   │   │   ├── document_generator.py ✅ Complete
│   │   │   ├── file_manager.py  ✅ Complete
│   │   │   └── websocket_manager.py ✅ Complete
│   │   ├── tasks/
│   │   │   ├── processing.py    ✅ Complete
│   │   │   └── cleanup.py       ✅ Complete
│   │   ├── utils/
│   │   │   └── formatters.py    ✅ Complete
│   │   └── main.py              ✅ Complete
│   ├── alembic/                 ✅ Complete
│   ├── test_parser.py           ✅ Complete
│   ├── requirements.txt         ✅ Complete
│   ├── .env.example             ✅ Complete
│   └── README.md                ✅ Complete
├── docker-compose.yml           ✅ Complete
└── QUICK_START.md               ✅ Complete
```

### ⏳ Remaining Work

- [ ] Frontend (React + Shadcn UI)
- [ ] Production Docker configuration
- [ ] Render deployment setup
- [ ] End-to-end testing

---

## 🎯 Next Steps

### Immediate (Testing)

1. **Test PDF parser** with your actual PDF
2. **Verify** Word document formatting matches requirements
3. **Adjust** regex patterns if needed for your PDF format
4. **Test** full pipeline: Upload → Parse → Generate → Download

### Short-term (Frontend)

1. React app setup
2. File upload component (drag & drop)
3. Configuration form
4. Real-time progress tracker (WebSocket)
5. Download button

### Long-term (Deployment)

1. Production Docker images
2. Render.com configuration
3. Environment variables setup
4. SSL/HTTPS setup
5. Monitoring and logging

---

## 📞 API Endpoints Reference

### Jobs

```
POST   /api/v1/jobs/              Create new job
GET    /api/v1/jobs/{job_id}      Get job status
GET    /api/v1/jobs/              List recent jobs (24h)
GET    /api/v1/jobs/{job_id}/download  Download Word document
DELETE /api/v1/jobs/{job_id}      Delete job and files
```

### WebSocket Events

```javascript
// Client → Server
socket.emit('subscribe', { job_id: 'uuid' })
socket.emit('unsubscribe', { job_id: 'uuid' })
socket.emit('ping', { timestamp: Date.now() })

// Server → Client
socket.on('connected', (data) => {})
socket.on('subscribed', (data) => {})
socket.on('progress', (data) => {})  // { progress: 0-100, step: "...", timestamp: "..." }
socket.on('complete', (data) => {})  // { output_filename, total_questions, diagrams_detected }
socket.on('error', (data) => {})     // { message: "...", details: {...} }
socket.on('pong', (data) => {})
```

---

## 🎉 Success Indicators

Backend is working correctly if:

- ✅ http://localhost:8000/health returns `{"status": "healthy"}`
- ✅ http://localhost:8000/docs shows API documentation
- ✅ Can create job via API
- ✅ Job status updates in real-time
- ✅ Can download generated Word document
- ✅ Word document has correct formatting (8×3 table, Times New Roman 14pt, etc.)
- ✅ Questions, options, solutions extracted correctly
- ✅ WebSocket connection works (test via browser console)

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **Celery Docs**: https://docs.celeryq.dev
- **Socket.IO Docs**: https://socket.io/docs/v4/
- **Docker Docs**: https://docs.docker.com

---

**Happy Coding! 🚀**
