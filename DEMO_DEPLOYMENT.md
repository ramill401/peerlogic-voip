# Demo Environment Deployment Guide

This guide walks you through deploying the Peerlogic VoIP Admin from local development to a demo environment.

## Architecture

- **Backend (Django)**: Railway.app (free tier available)
- **Frontend (Vue.js/Vite)**: Vercel (free tier available)
- **Database**: PostgreSQL (provided by Railway)

## Prerequisites

1. GitHub account with your code pushed
2. Railway account (free): https://railway.app
3. Vercel account (free): https://vercel.com

---

## Step 1: Prepare Your Code

### 1.1 Commit and Push Changes

```bash
# Make sure all changes are committed
git add .
git commit -m "Prepare for demo deployment"
git push origin main
```

### 1.2 Generate Secret Key (for Railway)

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Save this key - you'll need it for Railway environment variables.

---

## Step 2: Deploy Backend to Railway

### 2.1 Create Railway Project

1. Go to https://railway.app and sign in with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Select your `peerlogic-voip` repository
5. Railway will auto-detect Django and start deploying

### 2.2 Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically:
   - Create a PostgreSQL database
   - Set the `DATABASE_URL` environment variable
   - Connect it to your Django app

### 2.3 Configure Environment Variables

1. Click on your **web service** (the Django app)
2. Go to the **"Variables"** tab
3. Add these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `SECRET_KEY` | `[generated key from Step 1.2]` | Your Django secret key |
| `DEBUG` | `False` | Production mode |
| `ALLOWED_HOSTS` | `.railway.app` | Allow Railway domain |
| `DJANGO_SUPERUSER_USERNAME` | `admin` | (Optional) Admin username |
| `DJANGO_SUPERUSER_EMAIL` | `admin@example.com` | (Optional) Admin email |
| `DJANGO_SUPERUSER_PASSWORD` | `[your-secure-password]` | (Optional) Admin password |

**Note:** The `DATABASE_URL` is automatically set by Railway when you add PostgreSQL.

### 2.4 Wait for Deployment

- Railway will automatically deploy when you push to GitHub
- Watch the deployment logs in the Railway dashboard
- Once deployed, note your Railway URL (e.g., `https://peerlogic-voip-production.up.railway.app`)

### 2.5 Run Database Migrations

**Option A: Using Railway Dashboard**
1. Click your web service → **"Settings"**
2. Use the **"Shell"** or **"CLI"** option
3. Run:
   ```bash
   python manage.py migrate
   python manage.py initial_setup
   ```

**Option B: Using Railway CLI**
```bash
npm install -g @railway/cli
railway login
railway link  # Links to your project
railway run python manage.py migrate
railway run python manage.py initial_setup
```

**Important:** Note the **Connection ID** from the `setup_mock_connection` output - you'll need it for the frontend!

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Project

1. Go to https://vercel.com and sign in with GitHub
2. Click **"Add New"** → **"Project"**
3. Import your `peerlogic-voip` repository

### 3.2 Configure Build Settings

In the project configuration:

- **Framework Preset**: `Vite`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install` (auto-detected)

### 3.3 Add Environment Variables

Add these environment variables in Vercel:

| Variable | Value | Example |
|----------|-------|---------|
| `VITE_API_URL` | `https://YOUR-RAILWAY-URL.railway.app/api` | `https://peerlogic-voip-production.up.railway.app/api` |
| `VITE_CONNECTION_ID` | `[connection-id-from-step-2.5]` | `ad35319c-e6cb-4253-a66d-fd2736bff0e1` |

### 3.4 Deploy

1. Click **"Deploy"**
2. Wait for the build to complete
3. Note your Vercel URL (e.g., `https://peerlogic-voip.vercel.app`)

---

## Step 4: Update CORS Settings

### 4.1 Update Railway Environment Variables

1. Go back to Railway dashboard → Your web service → **"Variables"**
2. Add:
   - `FRONTEND_URL` = `https://your-app.vercel.app` (your actual Vercel URL)
3. Railway will automatically redeploy

This allows your frontend to make API calls to the backend.

---

## Step 5: Verify Deployment

### 5.1 Test Backend

- **Health Check**: `https://your-app.railway.app/api/health/`
- **API Docs**: `https://your-app.railway.app/api/docs/`
- **Django Admin**: `https://your-app.railway.app/admin/`
  - Login with: `admin` / `[your-password]`

### 5.2 Test Frontend

- **Frontend**: `https://your-app.vercel.app/`
- Verify it can connect to the backend API

### 5.3 Test Integration

1. Open the frontend in your browser
2. Check browser console for any CORS errors
3. Try making API calls from the frontend

---

## Troubleshooting

### Backend Issues

**Database Connection Errors:**
- Verify `DATABASE_URL` is set in Railway (should be automatic)
- Check PostgreSQL service is running in Railway

**Static Files Not Loading:**
- Ensure `collectstatic` ran during deployment
- Check WhiteNoise is configured (already done in settings.py)

**CORS Errors:**
- Verify `FRONTEND_URL` is set correctly in Railway
- Check `CORS_ALLOWED_ORIGINS` in settings.py includes your Vercel URL

### Frontend Issues

**API Connection Errors:**
- Verify `VITE_API_URL` is correct in Vercel
- Check the backend URL is accessible
- Verify CORS is configured correctly

**Build Errors:**
- Check Node.js version compatibility
- Verify all dependencies are in `package.json`

---

## Updating Your Demo

### To Update Backend:

```bash
git add .
git commit -m "Update backend"
git push origin main
# Railway auto-deploys
```

### To Update Frontend:

```bash
git add .
git commit -m "Update frontend"
git push origin main
# Vercel auto-deploys
```

---

## Environment Variables Reference

### Railway (Backend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | Auto-set | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | Django secret key |
| `DEBUG` | Yes | `False` | Debug mode |
| `ALLOWED_HOSTS` | Yes | `.railway.app` | Allowed hostnames |
| `FRONTEND_URL` | Yes | - | Vercel frontend URL |
| `DJANGO_SUPERUSER_USERNAME` | No | `admin` | Admin username |
| `DJANGO_SUPERUSER_EMAIL` | No | `admin@example.com` | Admin email |
| `DJANGO_SUPERUSER_PASSWORD` | No | `admin123` | Admin password |

### Vercel (Frontend)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API URL |
| `VITE_CONNECTION_ID` | Yes | Mock connection ID |

---

## Cost

Both Railway and Vercel offer free tiers that should be sufficient for a demo:

- **Railway**: $5/month free credit (usually enough for small demos)
- **Vercel**: Free tier includes generous bandwidth

---

## Next Steps

1. Set up custom domains (optional)
2. Configure monitoring/logging
3. Set up CI/CD for automated testing
4. Add SSL certificates (automatic with Railway/Vercel)

---

## Support

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/

