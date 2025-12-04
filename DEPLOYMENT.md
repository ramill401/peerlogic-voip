# Deployment Checklist

## ✅ Completed

- [x] Created `Procfile` for Railway (uses Poetry)
- [x] Created `runtime.txt` (Python 3.11.6)
- [x] Created `pyproject.toml` with Poetry dependencies
- [x] Created `poetry.lock` for reproducible builds
- [x] Updated Django settings for production:
  - [x] Database URL configuration (PostgreSQL in production, SQLite locally)
  - [x] WhiteNoise for static files
  - [x] CORS configuration for production
  - [x] ALLOWED_HOSTS for Railway
- [x] Updated frontend API configuration for environment variables
- [x] Created `vercel.json` for Vercel deployment

## 📋 Next Steps

### 1. Collect Static Files (Local)
```bash
python manage.py collectstatic --noinput
```

### 2. Push to GitHub
```bash
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

### 3. Deploy Backend to Railway

1. Go to https://railway.app/ and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `peerlogic-voip` repository
4. Railway will auto-detect Django

**Add PostgreSQL Database:**
- Click "+ New" → "Database" → "PostgreSQL"
- Railway will auto-connect it via `DATABASE_URL`

**Add Environment Variables:**
- Click on your web service → "Variables" tab
- Add:
  - `SECRET_KEY` = (generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
  - `DEBUG` = `False`
  - `ALLOWED_HOSTS` = `.railway.app`
  - `FRONTEND_URL` = (add after deploying frontend)

**Deploy:**
- Railway will auto-deploy from GitHub
- Get your Railway URL (e.g., `https://peerlogic-voip-production.up.railway.app`)

### 4. Run Migrations on Railway

**Option A: Railway Dashboard**
- Click your web service → "Settings" → Use the shell/CLI option
- Run:
  ```bash
  poetry run python manage.py migrate
  poetry run python manage.py initial_setup
  ```

**Option B: Railway CLI**
```bash
npm install -g @railway/cli
railway login
railway link
railway run poetry run python manage.py migrate
railway run poetry run python manage.py initial_setup
```

**Note:** Railway supports Poetry natively! It will auto-detect `pyproject.toml` and use Poetry for dependency management.

**Note the Connection ID** from the setup_mock_connection output.

### 5. Deploy Frontend to Vercel

1. Go to https://vercel.com/ and sign in with GitHub
2. Click "Add New" → "Project"
3. Import your `peerlogic-voip` repository
4. **Configure:**
   - Framework Preset: **Vite**
   - Root Directory: **frontend**
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Add Environment Variables:**
   - `VITE_API_URL` = `https://YOUR-RAILWAY-URL.railway.app/api`
   - `VITE_CONNECTION_ID` = (your connection ID from Railway)
6. Click "Deploy"
7. Get your Vercel URL (e.g., `https://peerlogic-voip.vercel.app`)

### 6. Update CORS on Railway

1. Go to Railway dashboard → Your web service → Variables
2. Add: `FRONTEND_URL` = `https://your-app.vercel.app`
3. Railway will auto-redeploy

## 🔗 Final URLs

| Service | URL |
|---------|-----|
| Backend API | `https://your-app.railway.app/api/` |
| API Docs | `https://your-app.railway.app/api/docs/` |
| Django Admin | `https://your-app.railway.app/admin/` |
| Frontend | `https://your-app.vercel.app/` |

## 🧪 Testing

1. Test backend health: `https://your-app.railway.app/api/health/`
2. Test API docs: `https://your-app.railway.app/api/docs/`
3. Test frontend: `https://your-app.vercel.app/`
4. Verify CORS: Frontend should be able to call backend API

## 📝 Notes

- Railway provides a free PostgreSQL database
- Vercel provides free hosting for frontend
- Both auto-deploy from GitHub on push
- Environment variables are set in each platform's dashboard

