# Render.com Deployment Guide

Complete guide to deploy the PDF Question Document Generator on Render.com.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Option 1: Blueprint Deployment (Recommended)](#option-1-blueprint-deployment-recommended)
- [Option 2: Manual Deployment](#option-2-manual-deployment)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)

---

## Prerequisites

1. **GitHub Repository**: Code must be pushed to GitHub
   - Repository: https://github.com/Clientwala/Question-mcq-

2. **Render Account**: Create account at https://render.com
   - Sign up with GitHub for easy integration

3. **Environment Variables Ready**:
   - CORS_ORIGINS (will be set after frontend deployment)
   - SECRET_KEY (auto-generated or manual)

---

## Deployment Options

### Option 1: Blueprint Deployment (Recommended)

**Advantages**:
- Deploy all services at once
- Automatic service linking
- Infrastructure as Code
- Easy updates

**Steps**:

#### 1. Push render.yaml to GitHub

```bash
cd D:/Question
git add render.yaml RENDER_DEPLOYMENT.md
git commit -m "Add Render deployment configuration"
git push origin main
```

#### 2. Create Blueprint on Render

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository: `Clientwala/Question-mcq-`
4. Render will detect `render.yaml` automatically
5. Click **"Apply"**

#### 3. Configure Environment Variables

After blueprint creation, update these variables:

**Backend Service (`question-backend`)**:
```
CORS_ORIGINS=["https://question-frontend.onrender.com","http://localhost:5174"]
```

**Frontend Service (`question-frontend`)**:
```
VITE_API_URL=https://question-backend.onrender.com
```

**Note**: Replace URLs with your actual Render service URLs.

#### 4. Wait for Deployment

- PostgreSQL: ~2 minutes
- Redis: ~1 minute
- Backend: ~5-7 minutes
- Worker: ~5-7 minutes
- Frontend: ~3-5 minutes

**Total Time**: ~15-20 minutes

---

### Option 2: Manual Deployment

If you prefer manual control, deploy services individually:

#### Step 1: Create PostgreSQL Database

1. Dashboard → **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `question-postgres`
   - **Database**: `questionmcq`
   - **User**: `questionuser`
   - **Region**: Singapore (or nearest)
   - **Plan**: Starter ($7/month)
3. Click **"Create Database"**
4. **Copy the Internal Database URL** (starts with `postgresql://`)

#### Step 2: Create Redis Instance

1. Dashboard → **"New +"** → **"Redis"**
2. Configure:
   - **Name**: `question-redis`
   - **Region**: Singapore (same as database)
   - **Plan**: Starter ($10/month)
3. Click **"Create Redis"**
4. **Copy the Internal Redis URL** (starts with `redis://`)

#### Step 3: Deploy Backend API

1. Dashboard → **"New +"** → **"Web Service"**
2. Connect GitHub repository: `Clientwala/Question-mcq-`
3. Configure:
   - **Name**: `question-backend`
   - **Region**: Singapore
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT`
   - **Plan**: Starter ($7/month)

4. **Add Environment Variables**:
   ```
   PYTHON_VERSION=3.12.0
   DATABASE_URL=<paste PostgreSQL Internal URL>
   REDIS_URL=<paste Redis Internal URL>
   CELERY_BROKER_URL=<paste Redis Internal URL>
   CELERY_RESULT_BACKEND=<paste Redis Internal URL>
   SECRET_KEY=<generate random string - use: openssl rand -hex 32>
   ENVIRONMENT=production
   DEBUG=False
   LOG_LEVEL=INFO
   CORS_ORIGINS=["http://localhost:5174"]
   STORAGE_PATH=/opt/render/project/data
   MAX_UPLOAD_SIZE=52428800
   ```

5. **Add Disk Storage**:
   - Click **"Add Disk"**
   - **Name**: `question-storage`
   - **Mount Path**: `/opt/render/project/data`
   - **Size**: 10 GB
   - Click **"Create Disk"**

6. Click **"Create Web Service"**

#### Step 4: Deploy Celery Worker

1. Dashboard → **"New +"** → **"Background Worker"**
2. Connect same GitHub repository
3. Configure:
   - **Name**: `question-worker`
   - **Region**: Singapore (same region)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `celery -A app.core.celery_app worker --loglevel=info --pool=solo`
   - **Plan**: Starter ($7/month)

4. **Add Same Environment Variables as Backend** (except CORS_ORIGINS not needed)

5. **Add Disk Storage** (same configuration as backend)

6. Click **"Create Background Worker"**

#### Step 5: Deploy Frontend

1. Dashboard → **"New +"** → **"Static Site"**
2. Connect GitHub repository
3. Configure:
   - **Name**: `question-frontend`
   - **Region**: Singapore
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
   - **Plan**: Free

4. **Add Environment Variables**:
   ```
   NODE_VERSION=20.10.0
   VITE_API_URL=https://question-backend.onrender.com
   ```
   (Replace with your actual backend URL after it deploys)

5. Click **"Create Static Site"**

#### Step 6: Update CORS Settings

After frontend deploys, update backend CORS:

1. Go to Backend service → **"Environment"**
2. Edit `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=["https://question-frontend.onrender.com","http://localhost:5174"]
   ```
   (Replace with your actual frontend URL)
3. Save changes (backend will redeploy automatically)

---

## Post-Deployment Configuration

### 1. Run Database Migrations

After backend first deploys:

```bash
# In Render Shell (Backend service → "Shell" tab)
cd backend
alembic upgrade head
```

Or add to backend build command:
```
pip install -r requirements.txt && alembic upgrade head
```

### 2. Test the Application

1. Open frontend URL: `https://question-frontend.onrender.com`
2. Upload a test PDF
3. Configure ranges
4. Check real-time progress
5. Download generated document

### 3. Monitor Services

Check all services are running:
- ✅ PostgreSQL: Active
- ✅ Redis: Active
- ✅ Backend: Running (green)
- ✅ Worker: Running (green)
- ✅ Frontend: Published

---

## Important Configuration Notes

### Database URL Format

Render provides database URL in this format:
```
postgresql://user:password@host:port/database
```

For **async SQLAlchemy**, you need to modify it:
```
postgresql+asyncpg://user:password@host:port/database
```

**Update in backend/.env or Environment Variables**:
```bash
# Original from Render
DATABASE_URL=postgresql://user:pass@host:5432/db

# For async (used by FastAPI)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
```

### Redis Connection

Redis URL works as-is:
```
redis://host:port
```

### File Storage

Render provides persistent disks:
- Mount Path: `/opt/render/project/data`
- Shared between Backend and Worker
- 10 GB included in Starter plan
- Files persist across deployments

### Auto-Deploy on Git Push

Enable in each service:
1. Service Settings → **"Build & Deploy"**
2. Enable **"Auto-Deploy"**
3. Select branch: `main`

Now every `git push` triggers redeployment!

---

## Monitoring & Logs

### View Logs

1. **Backend Logs**:
   - Dashboard → `question-backend` → **"Logs"**
   - Real-time FastAPI logs

2. **Worker Logs**:
   - Dashboard → `question-worker` → **"Logs"**
   - Celery task execution logs

3. **Build Logs**:
   - Click on any build to see detailed logs

### Health Checks

Add health endpoint monitoring:
```
GET https://question-backend.onrender.com/health
```

Render automatically monitors:
- HTTP response codes
- Response time
- Service availability

### Metrics

View in Dashboard:
- CPU usage
- Memory usage
- Request count
- Response times

---

## Troubleshooting

### Issue 1: Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Check Root Directory is set to: backend
# Check Start Command is: uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT
```

### Issue 2: Database Connection Failed

**Error**: `asyncpg.exceptions.ConnectionError`

**Solution**:
1. Check DATABASE_URL has `+asyncpg`:
   ```
   postgresql+asyncpg://user:pass@host:5432/db
   ```

2. Ensure database is in same region as backend

3. Check database is running (PostgreSQL service status)

### Issue 3: CORS Errors

**Error**: `Access to XMLHttpRequest blocked by CORS`

**Solution**:
Update backend CORS_ORIGINS with exact frontend URL:
```python
CORS_ORIGINS=["https://question-frontend.onrender.com"]
```

### Issue 4: Celery Worker Not Processing

**Error**: Worker running but tasks not executing

**Solution**:
1. Check Redis connection in worker logs
2. Verify `CELERY_BROKER_URL` matches Redis Internal URL
3. Restart worker service

### Issue 5: File Upload Fails

**Error**: `No such file or directory`

**Solution**:
1. Ensure disk is mounted at `/opt/render/project/data`
2. Check STORAGE_PATH environment variable
3. Verify disk is attached to both backend AND worker

### Issue 6: Frontend Shows Old Version

**Solution**:
1. Clear browser cache (Ctrl+Shift+R)
2. Manual redeploy: Service → **"Manual Deploy"** → **"Deploy latest commit"**

---

## Cost Estimation

### Monthly Costs (All on Starter Plan)

| Service | Plan | Cost |
|---------|------|------|
| PostgreSQL | Starter | $7 |
| Redis | Starter | $10 |
| Backend API | Starter | $7 |
| Celery Worker | Starter | $7 |
| Frontend | Free | $0 |
| **Total** | | **$31/month** |

### Cost Optimization

**For Development/Testing**:
- Use Free plan for backend/worker (with limitations)
- Total: $17/month (PostgreSQL + Redis)

**For Production**:
- Upgrade to Standard plan for better performance
- Add monitoring and alerts
- Total: ~$50-70/month

### Free Tier Limitations

Free Web Services:
- ❌ Auto-sleep after 15 mins inactivity
- ❌ 750 hours/month limit
- ❌ Cold starts (slow first request)
- ✅ Good for testing only

**Recommendation**: Use Starter plan for production.

---

## Security Best Practices

### 1. Environment Variables

Never commit these to Git:
- DATABASE_URL
- REDIS_URL
- SECRET_KEY
- API keys

Use Render's environment variable management.

### 2. CORS Configuration

Only allow your frontend domain:
```python
CORS_ORIGINS=["https://question-frontend.onrender.com"]
```

### 3. Database Security

- Use Render's internal URLs (not public)
- Enable SSL: `?ssl=require` in DATABASE_URL
- Regular backups (Render automated)

### 4. File Upload Limits

Keep MAX_UPLOAD_SIZE reasonable:
```
MAX_UPLOAD_SIZE=52428800  # 50MB
```

---

## Updating the Application

### Method 1: Git Push (Auto-Deploy)

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Render auto-deploys all services
```

### Method 2: Manual Deploy

1. Dashboard → Service → **"Manual Deploy"**
2. Select branch or commit
3. Click **"Deploy"**

### Method 3: Rollback

If deployment breaks:
1. Service → **"Events"**
2. Find previous successful deploy
3. Click **"Rollback to this version"**

---

## Advanced Configuration

### Custom Domains

1. Service → **"Settings"** → **"Custom Domain"**
2. Add your domain: `app.yourdomain.com`
3. Configure DNS (CNAME record)
4. Render provides free SSL certificate

### Environment-Specific Configs

Create separate environments:
- `main` branch → Production
- `develop` branch → Staging
- Deploy each to different Render services

### Scheduled Tasks (Celery Beat)

For cleanup tasks, add another worker:

**Start Command**:
```bash
celery -A app.core.celery_app beat --loglevel=info
```

This runs periodic tasks like file cleanup.

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Render Status**: https://status.render.com
- **Community**: https://community.render.com
- **Support**: dashboard → "Help" → "Contact Support"

---

## Checklist After Deployment

- [ ] All 5 services deployed successfully
- [ ] Database migrations completed
- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] Can upload PDF and see it in logs
- [ ] WebSocket connection established
- [ ] Celery worker processing tasks
- [ ] Can download generated documents
- [ ] CORS configured correctly
- [ ] Auto-deploy enabled
- [ ] Environment variables secured
- [ ] Monitoring/alerts configured

---

**Deployment Complete!** 🎉

Your PDF Question Document Generator is now live on Render.com.

Frontend: https://question-frontend.onrender.com
Backend: https://question-backend.onrender.com
