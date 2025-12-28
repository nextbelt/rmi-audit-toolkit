# RMI Audit Toolkit

Professional Reliability Maturity Index (RMI) audit software built by **NextBelt LLC**.

## 🎯 What Is This?

A complete, production-ready web application for conducting professional reliability audits in industrial facilities.

**Tech Stack:**
- **Backend**: FastAPI (Python) → Railway
- **Frontend**: React + TypeScript → Railway  
- **Auth**: Supabase
- **Database**: PostgreSQL (Railway)

## ✨ Features

✅ **16 Pre-loaded Questions** across People, Process, Technology pillars  
✅ **Evidence-Based Scoring** (scores ≥4 require proof)  
✅ **CMMS Data Analysis** - Upload work orders for automated metrics  
✅ **ISO 14224 Validation** - Data quality checks  
✅ **Field Observations** - Tablet-friendly checklists  
✅ **Executive Reports** - Auto-generated PDFs with charts  
✅ **Role-Weighted Scoring** - Technicians 60%, Managers 20%, Auditors 20%  

## 📁 Project Structure

```
RMI Audit Toolkit/
├── backend/           # FastAPI backend (Railway)
│   ├── main.py
│   ├── models.py
│   ├── scoring_engine.py
│   ├── supabase_auth.py
│   └── railway.json
├── frontend/          # React frontend (Railway)
│   ├── src/
│   ├── railway.json
│   └── package.json
└── DEPLOYMENT.md      # Step-by-step deployment guide
```

## 🚀 Quick Start (Local)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python init_db.py
python main.py
# → http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

**Demo Login:**
- Email: `admin@nextbelt.com`
- Password: `admin123`

## ☁️ Deployment to Production

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete Railway + Supabase setup guide.

**Quick summary:**
1. Create Supabase project (auth)
2. Deploy backend to Railway (+ PostgreSQL)
3. Deploy frontend to Railway
4. Link from next-belt.com

## 🎨 Design System

Matches NextBelt website:
- **Colors**: Deep teal (#0D4F4F) + copper (#C65D3B)
- **Typography**: Space Grotesk + IBM Plex Mono
- **Style**: Industrial, editorial, clean

## 📊 RMI Methodology

**Three Pillars:**
1. **People** - Training, culture, knowledge transfer
2. **Process** - Planning, procedures, PM compliance
3. **Technology** - CMMS quality, data integrity

**Maturity Levels:**
- 1 = Reactive (firefighting)
- 2 = Developing (inconsistent)
- 3 = Preventive (planned maintenance)
- 4 = Predictive (data-driven)
- 5 = Prescriptive (optimized, world-class)

**Evidence Lock:** Scores ≥4 require proof, else capped at 3.0  
**Weakest Link:** Critical failures cap pillar at 3.0 max

## 🔧 Customization

**Add Questions:**  
Edit `backend/question_bank.py`

**Customize Reports:**  
Edit `backend/report_generator.py`

**Adjust Scoring:**  
Edit `backend/scoring_engine.py`

## 📚 Documentation

- **Backend**: `backend/README.md`
- **Frontend**: `frontend/README.md`
- **Deployment**: `DEPLOYMENT.md`
- **API Docs**: `/docs` endpoint

## 📞 Support

Built by **NextBelt LLC**  
🌐 https://next-belt.com  
📧 nextbelt@next-belt.com

---

**Ready to conduct world-class reliability audits!** 🚀
