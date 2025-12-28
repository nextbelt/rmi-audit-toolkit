# RMI Audit Toolkit - Backend

FastAPI backend for NextBelt's RMI Audit Toolkit.

## Deployment to Railway

### 1. Create Railway Project
- Go to https://railway.app
- Click "New Project" → "Deploy from GitHub repo"
- Select this repository
- Railway will auto-detect the backend

### 2. Add PostgreSQL Database
- In Railway dashboard, click "+ New"
- Select "Database" → "PostgreSQL"
- Railway will automatically set `DATABASE_URL` environment variable

### 3. Set Environment Variables
In Railway project settings, add:

```bash
SECRET_KEY=your-super-secret-jwt-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
FRONTEND_URL=https://your-frontend.railway.app
```

### 4. Deploy
- Railway will automatically build and deploy
- Your backend will be available at: `https://your-backend.railway.app`

## Local Development

```bash
cd backend
pip install -r requirements.txt
python init_db.py
python main.py
```

Backend runs at: http://localhost:8000

## API Documentation

Once deployed, visit:
- Swagger UI: `https://your-backend.railway.app/docs`
- ReDoc: `https://your-backend.railway.app/redoc`

## Environment Variables Needed

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | Auto-set by Railway |
| `SECRET_KEY` | JWT signing key | Random 64-char string |
| `SUPABASE_URL` | Supabase project URL | https://xxx.supabase.co |
| `SUPABASE_ANON_KEY` | Supabase anon key | eyJhbG... |
| `FRONTEND_URL` | CORS origin | https://your-app.railway.app |

## Database Initialization

Railway will automatically run migrations on first deploy. To manually initialize:

```bash
railway run python init_db.py
```

## File Uploads

Evidence files and reports are stored in Railway's ephemeral filesystem. For production, consider:
- Railway Volumes (persistent storage)
- AWS S3
- Cloudinary
- Supabase Storage (recommended)
