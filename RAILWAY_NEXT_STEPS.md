# Railway Deployment - Next Steps ✅

## ✅ Deployment Verified!

Your Railway backend is live and working:
- **URL:** https://web-production-24d4c.up.railway.app
- **Health Check:** ✅ Working (`{"status": "healthy"}`)
- **API Docs:** ✅ Accessible
- **Django Admin:** ✅ Accessible

## 🔧 Step 1: Run Database Migrations

**Important:** You need to run migrations on Railway before using the API.

### Option A: Railway Dashboard (Easiest)

1. Go to https://railway.app
2. Click on your **web-production-24d4c** project
3. Click on your **web service**
4. Go to **"Settings"** tab
5. Scroll to **"Shell"** or find **"Open Shell"** button
6. Run these commands:

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
railway link  # Select your project

# Run migrations
railway run poetry run python manage.py migrate
railway run poetry run python manage.py initial_setup
```

**Expected Output:**
- ✅ Migrations applied successfully
- ✅ Practice and Provider records created
- ✅ (If env vars set) Superuser created

## 👤 Step 2: Create Admin User

If you didn't set `DJANGO_SUPERUSER_*` environment variables, create an admin user:

```bash
# In Railway shell or CLI
railway run poetry run python manage.py createsuperuser
```

Enter:
- Username: `admin` (or your choice)
- Email: `admin@peerlogic.com` (or your choice)  
- Password: (choose a secure password)

**Then test login:**
- Go to: https://web-production-24d4c.up.railway.app/admin/
- Login with your credentials

## 🔗 Step 3: Set Up NetSapiens Connection (Optional)

If you want to connect to NetSapiens instead of using mock data:

### Using Railway Shell:

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

**Important:** Save the Connection ID from the output! Update `frontend/.env.local` and `frontend/.env.production` with the new ID.

## 🌐 Step 4: Test Frontend Connection (Local)

The frontend is already configured to connect to Railway! 

### Test Locally:

1. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Open:** http://localhost:5173

3. **Login:** 
   - Frontend will redirect to Railway admin login
   - Login at: https://web-production-24d4c.up.railway.app/admin/
   - After login, you'll be redirected back to frontend

4. **Test Features:**
   - View connections
   - List users
   - Create user
   - List devices

### Update Connection ID (If Needed)

If you created a new NetSapiens connection, update the Connection ID:

**Edit `frontend/.env.local`:**
```env
VITE_API_URL=https://web-production-24d4c.up.railway.app/api
VITE_CONNECTION_ID=your-new-connection-id-here
```

Then restart the frontend dev server.

## 🚀 Step 5: Deploy Frontend to Vercel

Once everything works locally, deploy frontend to Vercel:

### Quick Deploy:

```bash
cd frontend

# Install Vercel CLI (if needed)
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### Add Environment Variables in Vercel:

1. Go to Vercel dashboard → Your project → **Settings** → **Environment Variables**
2. Add:
   - `VITE_API_URL` = `https://web-production-24d4c.up.railway.app/api`
   - `VITE_CONNECTION_ID` = `your-connection-id`

### Update Railway CORS (After Vercel Deployment):

1. Get your Vercel URL (e.g., `https://peerlogic-voip.vercel.app`)
2. Go to Railway → Your web service → **Variables**
3. Add/Update:
   - `FRONTEND_URL` = `https://your-vercel-app.vercel.app`
4. Railway will automatically restart and apply CORS

## ✅ Verification Checklist

- [ ] Migrations run successfully
- [ ] Admin user created and can login
- [ ] NetSapiens connection created (optional)
- [ ] Frontend connects to Railway backend (local test)
- [ ] Can view connections in frontend
- [ ] Can list users in frontend
- [ ] Frontend deployed to Vercel (optional)
- [ ] CORS configured for Vercel URL (if deployed)

## 🐛 Troubleshooting

### Frontend Can't Connect

**Check:**
1. Railway backend is running (test health endpoint)
2. You're logged into Django admin
3. Browser console for CORS errors
4. `frontend/.env.local` has correct `VITE_API_URL`

### 403 Forbidden Errors

**Fix:**
1. Login to Django admin: https://web-production-24d4c.up.railway.app/admin/
2. Verify user is a superuser
3. Check browser cookies are being sent
4. Clear cookies and login again

### CORS Errors

**Fix:**
1. Verify `FRONTEND_URL` is set in Railway (if using Vercel)
2. Check Railway logs for CORS errors
3. Verify frontend URL matches exactly (no trailing slash)

### Database Errors

**Fix:**
1. Run migrations: `poetry run python manage.py migrate`
2. Check Railway logs for database connection errors
3. Verify PostgreSQL database is running in Railway

## 📚 Quick Reference

**Railway Backend:**
- URL: https://web-production-24d4c.up.railway.app
- Admin: https://web-production-24d4c.up.railway.app/admin/
- API: https://web-production-24d4c.up.railway.app/api
- Health: https://web-production-24d4c.up.railway.app/api/health/

**Frontend (Local):**
- URL: http://localhost:5173
- API: https://web-production-24d4c.up.railway.app/api

**Files Created:**
- `frontend/.env.local` - Local development config
- `frontend/.env.production` - Production config
- `RAILWAY_URL.txt` - Quick reference

---

**Next:** Run migrations (Step 1) and create admin user (Step 2), then test the frontend!

