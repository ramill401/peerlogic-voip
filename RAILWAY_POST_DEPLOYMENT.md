# Railway Post-Deployment Checklist ✅

## Step 1: Verify Railway Deployment

### Get Your Railway URL

1. Go to Railway dashboard → Your project
2. Click on your **web service** (Django app)
3. Find your **Public Domain** (e.g., `peerlogic-voip-production.up.railway.app`)
4. **Save this URL** - you'll need it!

### Test Your Deployment

Open these URLs in your browser (replace with your Railway URL):

- ✅ **Health Check:** `https://your-app.railway.app/api/health/`
  - Should return: `{"status": "ok"}`
  
- ✅ **API Docs:** `https://your-app.railway.app/api/docs/`
  - Should show Swagger UI
  
- ✅ **Django Admin:** `https://your-app.railway.app/admin/`
  - Should show login page

## Step 2: Run Database Migrations

### Option A: Railway Dashboard (Easiest)

1. Go to Railway dashboard → Your web service
2. Click **"Settings"** tab
3. Scroll to **"Shell"** or **"CLI"** section
4. Click **"Open Shell"** or use the terminal
5. Run these commands:

```bash
poetry run python manage.py migrate
poetry run python manage.py initial_setup
```

### Option B: Railway CLI

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

**Expected Output:**
- Migrations applied successfully
- Superuser created (if you set `DJANGO_SUPERUSER_*` env vars)
- Practice and Provider records created

## Step 3: Create Admin User (If Not Done)

If you didn't set `DJANGO_SUPERUSER_*` environment variables:

```bash
# In Railway shell or CLI
railway run poetry run python manage.py createsuperuser
```

Enter:
- Username: `admin` (or your choice)
- Email: `admin@peerlogic.com` (or your choice)
- Password: (choose a secure password)

## Step 4: Set Up NetSapiens Connection (Optional)

If you want to connect to NetSapiens:

### Using Railway Dashboard Shell:

```bash
poetry run python manage.py setup_test_connection --interactive
```

### Using Railway CLI:

```bash
railway run poetry run python manage.py setup_test_connection \
  --domain=hi.peerlogic.com \
  --client-id=peerlogic-api-stage \
  --client-secret=f9ded02d3a93db4675e07fc4d79d3ddc \
  --username=1551@peerlogic \
  --password=YJe3ut-k-cM
```

**Important:** Save the Connection ID from the output! You'll need it for the frontend.

## Step 5: Update CORS Settings for Frontend

### Add Frontend URL to Railway Environment Variables

1. Go to Railway dashboard → Your web service → **"Variables"** tab
2. Add new variable:
   - **Name:** `FRONTEND_URL`
   - **Value:** `https://your-frontend.vercel.app` (or your frontend URL)

**Note:** If deploying frontend to Vercel, add this after Vercel deployment.

### Verify CORS Configuration

The backend will automatically add `FRONTEND_URL` to allowed CORS origins when `DEBUG=False`.

## Step 6: Test API Endpoints

### Test Health Endpoint

```bash
curl https://your-app.railway.app/api/health/
```

Should return: `{"status": "ok"}`

### Test Connections Endpoint (Requires Auth)

```bash
# First, login to Django admin in browser
# Then use browser console or Postman with cookies

curl -X GET https://your-app.railway.app/api/connections/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  --cookie-jar cookies.txt \
  --cookie cookies.txt
```

Or test in browser console (after logging into Django admin):

```javascript
fetch('https://your-app.railway.app/api/connections/', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)
```

## Step 7: Configure Frontend for Railway

### Update Frontend Environment Variables

Create or update `frontend/.env.production`:

```env
VITE_API_URL=https://your-app.railway.app/api
VITE_CONNECTION_ID=your-connection-id-here
```

**For Local Development:**

Create `frontend/.env.local`:

```env
VITE_API_URL=https://your-app.railway.app/api
VITE_CONNECTION_ID=your-connection-id-here
```

### Update Frontend Build

After updating environment variables:

```bash
cd frontend
npm run build
```

## Step 8: Deploy Frontend to Vercel

See `DEPLOYMENT.md` for detailed Vercel deployment steps.

**Quick Steps:**

1. Install Vercel CLI: `npm install -g vercel`
2. Login: `vercel login`
3. Deploy: `cd frontend && vercel --prod`
4. Add environment variables in Vercel dashboard:
   - `VITE_API_URL` = `https://your-app.railway.app/api`
   - `VITE_CONNECTION_ID` = `your-connection-id`

## Step 9: Update Railway CORS (After Vercel Deployment)

Once frontend is deployed to Vercel:

1. Get your Vercel URL (e.g., `https://peerlogic-voip.vercel.app`)
2. Go to Railway → Variables
3. Update `FRONTEND_URL` = `https://peerlogic-voip.vercel.app`
4. Railway will automatically restart and apply CORS changes

## Step 10: Test End-to-End

1. **Open Frontend:** `https://your-frontend.vercel.app`
2. **Login:** Should redirect to Railway Django admin login
3. **After Login:** Should redirect back to frontend
4. **Test Features:**
   - View connections
   - List users
   - Create user
   - List devices

## Troubleshooting

### 500 Internal Server Error

**Check Railway Logs:**
1. Go to Railway dashboard → Your service → **"Deployments"** tab
2. Click on latest deployment → **"View Logs"**
3. Look for error messages

**Common Issues:**
- Missing `SECRET_KEY` → Add to Railway variables
- Database not migrated → Run migrations
- Missing environment variables → Check all required vars

### CORS Errors

**Symptoms:** Frontend can't connect to backend

**Fix:**
1. Verify `FRONTEND_URL` is set in Railway
2. Check that frontend URL matches exactly (no trailing slash)
3. Verify `CORS_ALLOW_CREDENTIALS = True` in settings
4. Check Railway logs for CORS errors

### 403 Forbidden

**Symptoms:** API returns 403 even after login

**Fix:**
1. Verify you're logged into Django admin
2. Check that user is a superuser (for MVP)
3. Verify cookies are being sent (`withCredentials: true`)
4. Check browser console for specific error messages

### Database Connection Errors

**Symptoms:** `OperationalError: could not connect to server`

**Fix:**
1. Verify PostgreSQL database is added in Railway
2. Check that `DATABASE_URL` is set (should be automatic)
3. Verify database is running (Railway dashboard)

### Static Files Not Loading

**Symptoms:** CSS/JS files return 404

**Fix:**
- WhiteNoise is configured - should work automatically
- If issues, check Railway logs
- Verify `STATIC_ROOT` and `STATIC_URL` settings

## Next Steps

✅ **Backend Deployed:** Railway is live
✅ **Database Migrated:** Tables created
✅ **Admin User Created:** Can login
✅ **NetSapiens Connected:** (Optional) Provider connection ready
⏭️ **Frontend Deployment:** Deploy to Vercel (next step)
⏭️ **End-to-End Testing:** Test full workflow

## Quick Reference

**Railway Dashboard:** https://railway.app
**Your Railway URL:** `https://your-app.railway.app`
**Django Admin:** `https://your-app.railway.app/admin/`
**API Health:** `https://your-app.railway.app/api/health/`
**API Docs:** `https://your-app.railway.app/api/docs/`

---

**Need Help?** Check:
- `RAILWAY_SETUP.md` - Full Railway setup guide
- `DEPLOYMENT.md` - General deployment guide
- Railway logs - For specific errors


