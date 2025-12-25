# Render.com Deployment Checklist

Quick checklist for deploying to Render.com

## Pre-Deployment

- [x] Code pushed to GitHub
- [x] `.env` files excluded from Git (in .gitignore)
- [x] `render.yaml` created
- [x] Dependencies listed in `requirements.txt` and `package.json`
- [ ] Test application locally (all services running)

## Render Setup

### 1. Create Render Account
- [ ] Sign up at https://render.com
- [ ] Connect GitHub account
- [ ] Add payment method (for paid plans)

### 2. Deploy via Blueprint (Recommended)

- [ ] Push `render.yaml` to GitHub
- [ ] Create new Blueprint on Render
- [ ] Select repository: `Clientwala/Question-mcq-`
- [ ] Click "Apply" to deploy all services

### 3. Configure Environment Variables

**Backend Service**:
- [ ] Wait for frontend to deploy first
- [ ] Copy frontend URL
- [ ] Update `CORS_ORIGINS`:
  ```
  CORS_ORIGINS=["https://YOUR-FRONTEND-URL.onrender.com"]
  ```

**Frontend Service**:
- [ ] Wait for backend to deploy first
- [ ] Copy backend URL
- [ ] Update `VITE_API_URL`:
  ```
  VITE_API_URL=https://YOUR-BACKEND-URL.onrender.com
  ```

## Post-Deployment

### 4. Database Setup
- [ ] Wait for PostgreSQL to be ready
- [ ] Backend should auto-connect
- [ ] Check backend logs for "Database connected"

### 5. Run Migrations
**Option A - Automatic** (Recommended):
- [ ] Update backend Build Command in Render:
  ```
  pip install -r requirements.txt && alembic upgrade head
  ```
- [ ] Redeploy backend service

**Option B - Manual**:
- [ ] Open backend Shell in Render dashboard
- [ ] Run: `cd backend && alembic upgrade head`

### 6. Verify All Services

- [ ] PostgreSQL: Status = "Available"
- [ ] Redis: Status = "Available"
- [ ] Backend: Status = "Live" (green)
- [ ] Worker: Status = "Live" (green)
- [ ] Frontend: Status = "Live" (green)

### 7. Test Application

- [ ] Open frontend URL in browser
- [ ] Check no console errors (F12)
- [ ] Upload a small test PDF (2-3 pages)
- [ ] Set page range: 1 to 2
- [ ] Set question range: 1 to 3
- [ ] Fill chapter and unit names
- [ ] Click "Generate Document"
- [ ] Watch real-time progress updates
- [ ] Wait for processing to complete
- [ ] Download generated Word document
- [ ] Open document and verify formatting

### 8. Check Logs

**Backend**:
- [ ] No error messages
- [ ] Shows "Job created" log
- [ ] Shows WebSocket connections

**Worker**:
- [ ] Shows "Connected to redis"
- [ ] Shows "celery@... ready"
- [ ] Shows task execution when processing

**Frontend**:
- [ ] Build completed successfully
- [ ] No build errors

## Monitoring Setup

### 9. Configure Alerts (Optional)

- [ ] Enable email notifications for service failures
- [ ] Set up Slack/Discord webhooks for alerts
- [ ] Configure health check endpoints

### 10. Performance Monitoring

- [ ] Check response times in Render metrics
- [ ] Monitor CPU/Memory usage
- [ ] Set up uptime monitoring (e.g., UptimeRobot)

## Security

### 11. Secure Environment Variables

- [ ] Verify no secrets in Git history
- [ ] Confirm `.env` files are gitignored
- [ ] Database URL uses internal connection (not public)
- [ ] CORS only allows your frontend domain

### 12. SSL/HTTPS

- [ ] Frontend served over HTTPS (automatic)
- [ ] Backend served over HTTPS (automatic)
- [ ] Mixed content warnings resolved

## Documentation

### 13. Update README

- [ ] Add deployment instructions
- [ ] Document environment variables
- [ ] List all service URLs
- [ ] Add troubleshooting section

## Cost Verification

### 14. Check Billing

- [ ] Verify plan selection (Starter recommended)
- [ ] Expected cost: ~$31/month
  - PostgreSQL Starter: $7
  - Redis Starter: $10
  - Backend Starter: $7
  - Worker Starter: $7
  - Frontend Free: $0
- [ ] Set billing alerts

## Auto-Deploy Configuration

### 15. Enable Auto-Deploy

For each service:
- [ ] Backend: Auto-deploy on `main` branch push
- [ ] Worker: Auto-deploy on `main` branch push
- [ ] Frontend: Auto-deploy on `main` branch push

Test:
- [ ] Make a small code change
- [ ] Push to GitHub
- [ ] Verify services auto-redeploy

## Final Verification

### 16. Full E2E Test

- [ ] Upload multiple PDFs (different sizes)
- [ ] Test with different page ranges
- [ ] Test with different question ranges
- [ ] Verify all generated documents are correct
- [ ] Test concurrent uploads (multiple browsers)
- [ ] Check file cleanup (24-hour retention)

### 17. Performance Test

- [ ] Upload maximum file size (50MB)
- [ ] Process maximum questions (50+)
- [ ] Verify completion within reasonable time (<5 min)
- [ ] No memory errors in logs

## Backup & Recovery

### 18. Database Backup

- [ ] Verify Render automated backups enabled
- [ ] Test manual backup/restore process
- [ ] Document restore procedure

### 19. Rollback Plan

- [ ] Test rollback to previous deployment
- [ ] Document rollback steps
- [ ] Keep last 3 working versions tagged

## Launch Checklist

### 20. Production Ready

- [ ] All services deployed and running
- [ ] All tests passing
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Monitoring configured
- [ ] Backups verified
- [ ] Team trained on access

---

## Quick Reference URLs

After deployment, fill these in:

- **Frontend**: https://______________________________.onrender.com
- **Backend**: https://______________________________.onrender.com
- **Render Dashboard**: https://dashboard.render.com
- **GitHub Repo**: https://github.com/Clientwala/Question-mcq-

---

## Support Contacts

- **Render Support**: https://render.com/support
- **Render Status**: https://status.render.com
- **Render Community**: https://community.render.com

---

## Common Issues & Quick Fixes

### Backend Won't Start
```bash
# Check Root Directory setting
Root Directory: backend

# Check Start Command
uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT
```

### Database Connection Error
```bash
# Verify DATABASE_URL format
postgresql+asyncpg://user:pass@host:port/database
```

### CORS Error
```bash
# Update backend CORS_ORIGINS with exact frontend URL
CORS_ORIGINS=["https://your-exact-frontend-url.onrender.com"]
```

### Worker Not Processing
```bash
# Check worker logs for Redis connection
# Verify CELERY_BROKER_URL matches REDIS_URL
# Restart worker service
```

---

**Deployment Status**: 🔴 Not Started | 🟡 In Progress | 🟢 Complete

Mark as complete when all items checked!
