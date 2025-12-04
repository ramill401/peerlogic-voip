# Railway Deployment Guide

Complete guide for deploying the Peerlogic VoIP Admin backend to Railway.

## Prerequisites

- GitHub account with code pushed
- Railway account (free): https://railway.app
- Poetry installed locally (for generating lock file)

## Step 1: Prepare Your Code

### 1.1 Ensure Poetry Lock File is Committed

```bash
# Make sure poetry.lock is committed (for reproducible builds)
git add poetry.lock
git commit -m "Ensure poetry.lock is committed for Railway"
git push origin main
```

### 1.2 Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Save this key - you'll need it for Railway environment variables.

## Step 2: Deploy to Railway

### 2.1 Create Railway Project

1. Go to https://railway.app and sign in with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Select your `peerlogic-voip` repository
5. Railway will auto-detect Django and start deploying

### 2.2 Configure Build Settings

Railway should auto-detect Python, but verify:

1. Click on your **web service**
2. Go to **"Settings"** tab
3. Verify:
   - **Build Command**: (leave empty - Railway will auto-detect Poetry)
   - **Start Command**: (leave empty - uses Procfile)
   - **Python Version**: Should auto-detect from `runtime.txt` (3.11.6)

**Note:** Railway supports Poetry natively! It will:
- Detect `pyproject.toml` and `poetry.lock`
- Run `poetry install` automatically
- Use Poetry for dependency management

### 2.3 Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically:
   - Create a PostgreSQL database
   - Set the `DATABASE_URL` environment variable
   - Connect it to your Django app

### 2.4 Configure Environment Variables

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

### 2.5 Wait for Deployment

- Railway will automatically deploy when you push to GitHub
- Watch the deployment logs in the Railway dashboard
- Once deployed, note your Railway URL (e.g., `https://peerlogic-voip-production.up.railway.app`)

## Step 3: Run Database Migrations

### Option A: Using Railway Dashboard

1. Click your web service → **"Settings"**
2. Use the **"Shell"** or **"CLI"** option
3. Run:
   ```bash
   poetry run python manage.py migrate
   poetry run python manage.py initial_setup
   ```

### Option B: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link to your project
railway login
railway link  # Links to your project

# Run migrations
railway run poetry run python manage.py migrate
railway run poetry run python manage.py initial_setup
```

**Important:** Note the **Connection ID** from any setup commands - you'll need it for the frontend!

## Step 4: Set Up NetSapiens Connection (Optional)

If you want to use NetSapiens instead of mock data:

```bash
railway run poetry run python manage.py setup_test_connection \
  --domain=hi.peerlogic.com \
  --client-id=peerlogic-api-stage \
  --client-secret=YOUR_CLIENT_SECRET \
  --username=YOUR_USERNAME \
  --password=YOUR_PASSWORD
```

Or use interactive mode:

```bash
railway run poetry run python manage.py setup_test_connection --interactive
```

## Step 5: Verify Deployment

### Test Backend Endpoints

- **Health Check**: `https://your-app.railway.app/api/health/`
- **API Docs**: `https://your-app.railway.app/api/docs/`
- **Django Admin**: `https://your-app.railway.app/admin/`

### Check Logs

1. Go to Railway dashboard → Your web service
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. Check logs for any errors

## Step 6: Update CORS for Frontend

After deploying your frontend (e.g., to Vercel):

1. Go back to Railway dashboard
2. Click your **web service** → **"Variables"** tab
3. Add:
   ```
   FRONTEND_URL=https://your-frontend-url.vercel.app
   ```
4. Railway will auto-redeploy

## Troubleshooting

### Build Fails

**Issue:** Poetry not found or build fails
- **Solution:** Railway should auto-detect Poetry. If not, check that `pyproject.toml` and `poetry.lock` are in the root directory.

**Issue:** Python version mismatch
- **Solution:** Check `runtime.txt` specifies the correct Python version (3.11.6)

### Database Connection Errors

**Issue:** `DATABASE_URL` not set
- **Solution:** Make sure you added a PostgreSQL database in Railway. The `DATABASE_URL` is set automatically.

**Issue:** Migration errors
- **Solution:** Run migrations manually using Railway CLI or dashboard shell:
  ```bash
  railway run poetry run python manage.py migrate
  ```

### Static Files Not Loading

**Issue:** Static files return 404
- **Solution:** WhiteNoise is already configured. Make sure `DEBUG=False` in production and static files are collected:
  ```bash
  railway run poetry run python manage.py collectstatic --noinput
  ```

### CORS Errors

**Issue:** Frontend can't connect to backend
- **Solution:** 
  1. Verify `FRONTEND_URL` is set in Railway variables
  2. Check that the frontend URL matches exactly (including `https://`)
  3. Check Django logs for CORS errors

## Railway-Specific Features

### Automatic Deployments

Railway automatically deploys when you push to GitHub. To disable:
1. Go to Settings → Source
2. Toggle "Auto Deploy" off

### Custom Domain

1. Go to Settings → Domains
2. Add your custom domain
3. Railway will provide DNS records to configure

### Environment Variables

- Set in Railway dashboard → Variables tab
- Available to your app via `os.getenv()`
- `DATABASE_URL` is automatically set when you add PostgreSQL

### Logs

- View real-time logs in Railway dashboard
- Logs are available for each deployment
- Use `logger` in Django code to write to Railway logs

## Quick Reference

### Railway Environment Variables

```bash
SECRET_KEY=[generated-key]
DEBUG=False
ALLOWED_HOSTS=.railway.app
DATABASE_URL=[auto-set-by-railway]
FRONTEND_URL=[your-frontend-url]
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=[your-password]
```

### Railway CLI Commands

```bash
# Install CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Run Django commands
railway run poetry run python manage.py migrate
railway run poetry run python manage.py createsuperuser
railway run poetry run python manage.py shell

# View logs
railway logs

# Open shell
railway shell
```

## Next Steps

After Railway is set up:

1. **Deploy Frontend** to Vercel (see `VERCEL_SETUP.md`)
2. **Update CORS** with your frontend URL
3. **Set up NetSapiens** connection if needed
4. **Test** all endpoints and functionality

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: Check GitHub issues

