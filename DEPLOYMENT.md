# RMI Audit Toolkit

Professional Reliability Maturity Index (RMI) audit software for NextBelt LLC.

## 📁 Project Structure

```
RMI Audit Toolkit/
├── backend/                    # FastAPI backend (deploy to Railway)
│   ├── main.py                # Main API application
│   ├── models.py              # Database models
│   ├── scoring_engine.py      # RMI calculation logic
│   ├── report_generator.py    # PDF report generation
│   ├── supabase_auth.py       # Supabase authentication
│   ├── requirements.txt       # Python dependencies
│   ├── railway.json           # Railway deployment config
│   └── README.md              # Backend documentation
│
├── frontend/                   # React frontend (deploy to Railway)
│   ├── src/
│   │   ├── api/               # API client + Supabase auth
│   │   ├── components/        # Reusable UI components
│   │   ├── views/             # Page components
│   │   └── styles/            # NextBelt design system
│   ├── railway.json           # Railway deployment config
│   ├── package.json
│   └── README.md              # Frontend documentation
│
├── DEPLOYMENT.md              # Deployment guide (this file)
└── README.md                  # Project overview
```

## 🚀 Deployment Guide

### **Step 1: Set Up Supabase (Authentication)**

1. Go to https://supabase.com and create a new project
2. In project settings, copy:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon/Public key: `eyJhbG...`
   - Service role key: `eyJhbG...` (keep secret!)

3. In Supabase SQL Editor, run:
```sql
-- Create users table (syncs with auth.users)
CREATE TABLE public.users (
  id UUID REFERENCES auth.users ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  role TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (id)
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own data
CREATE POLICY "Users can view own data"
  ON public.users FOR SELECT
  USING (auth.uid() = id);
```

### **Step 2: Deploy Backend to Railway**

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `RMI Audit Toolkit` repository
4. Railway will detect `backend/` folder
5. Add PostgreSQL database:
   - Click "+ New" → "Database" → "PostgreSQL"
   - Railway auto-sets `DATABASE_URL`

6. Set environment variables in Railway:
```bash
SECRET_KEY=generate-random-64-char-string-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
FRONTEND_URL=https://your-frontend.railway.app
```

7. Deploy! Railway will:
   - Install Python dependencies
   - Run database migrations
   - Start the FastAPI server

8. Your backend will be live at: `https://your-backend.railway.app`

### **Step 3: Deploy Frontend to Railway**

1. In Railway, click "+ New Service"
2. Select "GitHub Repo" → Choose `RMI Audit Toolkit`
3. Set root directory to `frontend/`
4. Add environment variables:
```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=https://your-backend.railway.app
```

5. Deploy! Railway will:
   - Install npm dependencies
   - Build React app
   - Serve with Vite preview

6. Your frontend will be live at: `https://your-frontend.railway.app`

### **Step 4: Initialize Database**

Once backend is deployed, run database initialization:

```bash
# In Railway backend dashboard, go to "Settings" → "Variables"
# Click "New Variable" and run:
railway run python init_db.py
```

Or use the Railway CLI:
```bash
railway link
railway run python init_db.py
```

This creates:
- All database tables
- 16 pre-loaded questions
- Admin user: `admin@nextbelt.com` / `admin123`

### **Step 5: Link to next-belt.com**

Add a button to your NextBelt website:

```html
<a href="https://your-frontend.railway.app" 
   class="btn btn-primary"
   style="background: #0D4F4F; color: #fff; padding: 16px 24px; border-radius: 4px;">
  🔧 Launch RMI Audit Tool
</a>
```

Or create a subdomain:
1. In Railway, go to frontend service → "Settings" → "Domains"
2. Add custom domain: `audit.next-belt.com`
3. Update DNS in your domain registrar:
   - Type: CNAME
   - Name: audit
   - Value: your-frontend.railway.app

## 🔧 Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
python init_db.py
python main.py
# Runs at http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:3000
```

## 🔐 Authentication Flow

1. **User signs up/logs in** → Supabase Auth handles this
2. **Supabase returns JWT token** → Frontend stores it
3. **Frontend makes API requests** → Includes token in headers
4. **Backend verifies token** → Uses `supabase_auth.py`
5. **Backend returns data** → Only if token is valid

## 📊 Monitoring & Logs

- **Railway Dashboard**: View logs, metrics, deployments
- **Supabase Dashboard**: Monitor auth, database queries
- **Backend API Docs**: `https://your-backend.railway.app/docs`

## 💰 Costs

- **Supabase**: Free tier (50,000 users, 500MB database)
- **Railway**: ~$5-20/month depending on usage
  - Backend: ~$5/month (500MB RAM, 1GB storage)
  - Frontend: ~$5/month (static hosting)
  - PostgreSQL: Included with backend

**Total estimated cost**: $10-20/month

## 🔒 Security Checklist

- [x] Environment variables secured in Railway
- [x] Supabase Row Level Security enabled
- [x] CORS configured for production domains
- [ ] Change default admin password after first login
- [ ] Enable 2FA for Railway and Supabase accounts
- [ ] Set up Railway volume for persistent file storage
- [ ] Configure backup strategy for PostgreSQL

## 📞 Support

For issues, check:
- Backend logs: Railway dashboard
- Frontend console: Browser DevTools
- Database: Supabase SQL Editor
- API docs: `/docs` endpoint

## 🎉 You're Live!

Once deployed:
1. Visit your frontend URL
2. Login with: `admin@nextbelt.com` / `admin123`
3. Create your first assessment
4. Conduct an audit
5. Generate a PDF report

**Your RMI Audit Toolkit is now production-ready!** 🚀
