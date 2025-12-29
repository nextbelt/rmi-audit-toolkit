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

### Core Functionality
✅ **16 Pre-loaded Questions** across People, Process, Technology pillars  
✅ **Evidence-Based Scoring** (scores ≥4 require proof - enforced at submission)  
✅ **AI-Assisted Scoring** - GPT-4o-mini evaluates narrative text responses  
✅ **CMMS Data Analysis** - Upload work orders for automated metrics  
✅ **ISO 14224 Validation** - Data quality checks  
✅ **Field Observations** - Tablet-friendly checklists  
✅ **Executive Reports** - Auto-generated PDFs with charts  
✅ **Role-Weighted Scoring** - Technicians 60%, Managers 20%, Auditors 20%  

### 🆕 Data Saving & UX Improvements (Dec 2024)
✅ **Autosave with Debouncing** - Saves drafts 1 second after typing stops  
✅ **Save & Exit Fixed** - Now actually saves before navigating away  
✅ **Evidence Validation** - Blocks high scores without evidence checkbox  
✅ **N/A (Not Applicable)** - Exclude irrelevant questions from scoring  
✅ **Offline Queue** - Works in basements/remote sites, syncs when connection restored  
✅ **Safari Compatibility** - Full support for macOS/iOS Safari browsers  

### Security & Methodology
✅ **Draft vs Final Responses** - Drafts excluded from RMI calculations  
✅ **Cleaner Logs** - Suppressed 401 auth noise in terminal  
✅ **Environment-Based Credentials** - No hardcoded passwords  

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
python init_local_db.py  # Creates SQLite database with admin user
$env:LOCAL_DEV_MODE="true"  # Windows PowerShell
# export LOCAL_DEV_MODE=true  # Mac/Linux
python -m uvicorn main:app --reload --port 8000
# → http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3001 (or 3000)
```

**Demo Login:**
- Email: `admin@local.com`
- Password: `admin123`

**Database Migration (if updating):**
```bash
cd backend
python migrate_add_draft_na.py  # Adds is_draft and is_na columns
```

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

**Scoring Logic:**
- **Evidence Lock:** Scores ≥4 require proof (enforced at submission, not after-the-fact)
- **Weakest Link:** Critical failures cap pillar at 3.0 max
- **Draft Exclusion:** Only final responses count toward RMI score
- **N/A Handling:** Non-applicable questions excluded from total score calculation

**AI Scoring (Optional):**
- Uses OpenAI GPT-4o-mini to evaluate narrative text responses
- Provides 1-5 score + rationale + confidence level
- Add `OPENAI_API_KEY` to `.env` to enable
- Costs ~$0.002 per text response

## 🔧 Customization

**Add Questions:**  
Edit `backend/question_bank.py`

**Customize Reports:**  
Edit `backend/report_generator.py`

**Adjust Scoring:**  
Edit `backend/scoring_engine.py`

## 📚 Documentation

### User Guides
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md) - Railway + production setup
- **Data Saving**: [DATA_SAVING_IMPROVEMENTS.md](DATA_SAVING_IMPROVEMENTS.md) - Autosave, N/A, offline queue
- **Safari Issues**: [SAFARI_COMPATIBILITY.md](SAFARI_COMPATIBILITY.md) - Troubleshooting for Safari users

### Technical References
- **Backend**: `backend/README.md`
- **Frontend**: `frontend/README.md`
- **Roadmap**: [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) - Security fixes & methodology improvements
- **API Docs**: `/docs` endpoint (Swagger UI)

### Testing
- **Database Migration**: `backend/migrate_add_draft_na.py`
- **Data Validation**: `backend/test_data_saving.py`

## 📞 Support

Built by **NextBelt LLC**  
🌐 https://next-belt.com  
📧 nextbelt@next-belt.com

---

**Ready to conduct world-class reliability audits!** 🚀
