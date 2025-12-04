# Railway Deployment - Ready to Deploy! 🚀

## ✅ Code Prepared

Your code has been committed and pushed to GitHub. You're ready to deploy to Railway!

## 🔑 Secret Key Generated

**Save this secret key** - you'll need it for Railway environment variables:

```
SECRET_KEY=ejuYj7bHkj6BIq0wcxZkO22ETSdasfCOAaG6aMU-rMLKNPvCus12526kquN9zkBKqVY
```

## 📋 Next Steps - Follow These in Order

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Sign in with GitHub
3. Click **"+ New"** → **"Deploy from GitHub repo"**
4. Select your `peerlogic-voip` repository
5. Railway will auto-detect Django and start deploying

### Step 2: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically set `DATABASE_URL` environment variable

### Step 3: Configure Environment Variables

1. Click on your **web service** (the Django app)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** and add these:

```
SECRET_KEY=ejuYj7bHkj6BIq0wcxZkO22ETSdasfCOAaG6aMU-rMLKNPvCus12526kquN9zkBKqVY
DEBUG=False
ALLOWED_HOSTS=.railway.app
```

**Optional** (for auto-creating admin user):
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@peerlogic.com
DJANGO_SUPERUSER_PASSWORD=[choose-a-secure-password]
```

**Note:** `DATABASE_URL` is automatically set by Railway - don't add it manually!

### Step 4: Wait for Deployment

- Railway will automatically deploy from GitHub
- Watch the deployment logs in Railway dashboard
- Once deployed, note your Railway URL (e.g., `https://peerlogic-voip-production.up.railway.app`)

### Step 5: Run Database Migrations

**Option A: Railway Dashboard (Easiest)**

1. Click your web service → **"Settings"**
2. Click **"Shell"** or **"CLI"**
3. Run these commands:
   ```bash
   poetry run python manage.py migrate
   poetry run python manage.py initial_setup
   ```

**Option B: Railway CLI**

```bash
# Install Railway CLI (if needed)
npm install -g @railway/cli

# Login and link
railway login
railway link  # Select your peerlogic-voip project

# Run migrations
railway run poetry run python manage.py migrate
railway run poetry run python manage.py initial_setup
```

### Step 6: Verify Deployment

Test these URLs (replace `your-app` with your actual Railway URL):

- ✅ Health Check: `https://your-app.railway.app/api/health/`
- ✅ API Docs: `https://your-app.railway.app/api/docs/`
- ✅ Django Admin: `https://your-app.railway.app/admin/`

### Step 7: Set Up NetSapiens Connection (Optional)

If you want to use NetSapiens instead of mock data:

**Using Railway Dashboard Shell:**
```bash
poetry run python manage.py setup_test_connection --interactive
```

**Using Railway CLI:**
```bash
railway run poetry run python manage.py setup_test_connection \
  --domain=hi.peerlogic.com \
  --client-id=peerlogic-api-stage \
  --client-secret=f9ded02d3a93db4675e07fc4d79d3ddc \
  --username=1551@peerlogic \
  --password=YJe3ut-k-cM
```

**Note:** Save the Connection ID from the output - you'll need it for the frontend!

## 🎯 What Happens Next?

After Railway is deployed:

1. **Deploy Frontend to Vercel** (see `DEPLOYMENT.md`)
2. **Update CORS** - Add `FRONTEND_URL` environment variable in Railway
3. **Test Everything** - Verify frontend can connect to backend

## 🐛 Troubleshooting

### Build Fails
- Check deployment logs in Railway dashboard
- Verify `poetry.lock` is in the repository
- Check that Python version matches `runtime.txt` (3.11.6)

### Database Errors
- Verify PostgreSQL database is added
- Check that `DATABASE_URL` is set (should be automatic)
- Run migrations manually if needed

### Static Files Not Loading
- WhiteNoise is configured - should work automatically
- If issues, run: `poetry run python manage.py collectstatic --noinput`

## 📚 Reference

- Full Railway Guide: `RAILWAY_SETUP.md`
- Deployment Checklist: `DEPLOYMENT.md`
- Local Testing: `LOCAL_TESTING_GUIDE.md`

---

**Ready to deploy?** Follow Steps 1-6 above, then come back if you need help!




