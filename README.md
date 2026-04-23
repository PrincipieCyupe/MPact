# Mpact — AI-Powered Recruiter Screening Platform

> **Umurava AI Hackathon 2026** · Team M&P — Mugisha & Principie · Kigali, Rwanda

Mpact is a production-quality AI recruiter screening platform that scores every applicant against job requirements using a transparent two-layer scoring system (deterministic + Gemini AI), then surfaces a ranked shortlist with full explainability. Built for African hiring teams.

**Live Demo:** _(deploy URL here)_  
**Stack:** Python · Flask · SQLite/PostgreSQL · Gemini 2.5 Flash · Gunicorn

---

## Why Flask Instead of Next.js / Node.js

The Umurava brief recommends TypeScript/Next.js/Node.js but explicitly permits alternatives with justification. We chose Flask because:

1. **Python owns the AI ecosystem.** Google's `google-generativeai` SDK, `pdfplumber`, and prompt engineering patterns are first-class in Python. Node.js equivalents require wrapper libraries.
2. **Zero-config server rendering.** Jinja2 templates eliminate the hydration complexity of SSR React, letting us ship a polished UI without a build pipeline.
3. **Hackathon velocity.** SQLAlchemy + Flask Blueprints let a 2-person team implement all CRUD, AI orchestration, file parsing, CSV ingestion, and SSE in hours, not days.
4. **Gemini remains mandatory.** We use `gemini-2.5-flash` (the latest model) via the official Python SDK, fully satisfying the core AI requirement.

The architecture mirrors the recommended stack conceptually: Blueprint routes = Next.js pages/API routes, Flask-SQLAlchemy = Mongoose/Prisma, Jinja2 = React components.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MPACT — System Overview                     │
├─────────────────┬───────────────────────────┬───────────────────┤
│  PUBLIC SITE    │    ADMIN / RECRUITER       │    AI LAYER       │
│                 │                            │                   │
│  Landing Page   │  Recruiter Dashboard       │  Gemini 2.5 Flash │
│  Job Browse     │  Job CRUD                  │                   │
│  Job Detail     │  Applicant Management      │  Batch Evaluation │
│  Apply Form     │  AI Screening              │  JD Extraction    │
│  PDF Upload     │  Results (ranked cards)    │  Bias Detection   │
│  CSV Import UI  │  CSV Export                │                   │
│                 │  Bulk Status Actions       │  Heuristic        │
│                 │  Resume Download           │  Fallback         │
└─────────────────┴───────────────────────────┴───────────────────┘
         │                    │                       │
         └──────────┬─────────┘                       │
                    ▼                                 ▼
          ┌──────────────────┐            ┌──────────────────────┐
          │  SQLite (dev)    │            │  services/           │
          │  PostgreSQL (prod│            │  ├── gemini_service  │
          │                  │            │  ├── scoring_engine  │
          │  Jobs table      │            │  └── file_parser     │
          │  Applicants table│            └──────────────────────┘
          └──────────────────┘
```

### File Structure

```
mpact/
├── app.py                  Flask factory + blueprint registration
├── config.py               Environment config
├── models.py               Job + Applicant SQLAlchemy models
├── extensions.py           SQLAlchemy singleton
├── seed.py                 Demo data (4 jobs, 12 Rwandan candidates)
├── routes/
│   ├── public.py           Landing, job browse, apply form
│   ├── admin_auth.py       Login / logout
│   ├── admin_jobs.py       Job CRUD + CSV import
│   └── admin_screening.py  Screening, results, export, bulk actions
├── services/
│   ├── gemini_service.py   Batch AI evaluation + bias detection + JD extraction
│   ├── scoring_engine.py   Deterministic 4-axis scoring
│   └── file_parser.py      PDF resume text extraction
├── templates/
│   ├── public/             Applicant-facing pages (landing, jobs, apply)
│   ├── admin/              Recruiter dashboard (screening, results, import)
│   └── icons.html          20+ inline SVG icon macros (zero CDN dependency)
└── static/
    ├── css/styles.css      Full design system (~800 lines, Stripe-inspired)
    └── js/
        ├── app.js          Public JS (toasts, animations, file drop)
        └── admin.js        Admin JS (drawer, scoring rings, bulk select)
```

---

## Quick Start

```bash
# 1. Clone and enter the project directory
cd mpact

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY
# Without it, the heuristic fallback runs automatically

# 5. Seed demo data (optional but recommended)
python seed.py

# 6. Run development server
python app.py
# Visit: http://localhost:5000
# Admin:  http://localhost:5000/admin/login
#         Email: admin@mpact.rw  Password: mpact2026
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_SECRET_KEY` | _(random)_ | Session encryption key |
| `GEMINI_API_KEY` | — | Google AI API key (required for real AI) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model ID |
| `DATABASE_URL` | SQLite (local) | PostgreSQL URL for production |
| `ADMIN_EMAIL` | `admin@mpact.rw` | Recruiter login email |
| `ADMIN_PASSWORD` | `mpact2026` | Recruiter login password |

---

## AI Decision Flow

### Two-Layer Scoring Architecture

```
                    ┌─────────────────────────────────────┐
                    │         MPACT SCORING ENGINE         │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                                         ▼
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  DETERMINISTIC 60%  │                 │    GEMINI AI  40%   │
   │                     │                 │                     │
   │  Skills Match       │                 │  Batch evaluation   │
   │  (token matching)   │                 │  (all candidates    │
   │                     │                 │   in ONE prompt)    │
   │  Experience Score   │                 │                     │
   │  (ratio to minimum) │                 │  Strengths (3-5)    │
   │                     │                 │  Gaps (2-4)         │
   │  Education Score    │                 │  Recommendation     │
   │  (level mapping)    │                 │  Reasoning (2-3 sen)│
   │                     │                 │  Bias Flag + Notes  │
   │  Projects Score     │                 │                     │
   │  (count-based)      │                 └──────────┬──────────┘
   │                     │                            │
   └──────────┬──────────┘                            │
              │                                       │
              └─────────────────┬─────────────────────┘
                                ▼
                    Final Score = Weighted×0.6 + AI×0.4
                                ▼
                    Ranked Shortlist (Top 10/20/50)
```

### Batch Evaluation (Key Hackathon Requirement)

All candidates for a job are sent to Gemini in a **single API call**, returning a JSON array with all evaluations simultaneously. This is 10× faster than sequential calls and directly satisfies the hackathon brief's "multi-candidate evaluation in a single prompt" requirement.

```python
# services/gemini_service.py — analyze_batch()
results = analyze_batch(job, all_applicants, weighted_scores)
# One Gemini call → dict[applicant_id → {ai_score, strengths, gaps, recommendation, reasoning, bias_flag}]
```

### Bias Detection

Gemini automatically flags potential unconscious bias signals per candidate:
- Name-based cultural bias
- Location/institution prestige bias  
- Experience gap interpretations that may disadvantage non-traditional paths

Bias flags appear as ⚠ indicators on result cards and in the candidate drawer, giving recruiters a heads-up to review those decisions more carefully.

### Heuristic Fallback

When Gemini is unavailable (no API key, rate limit, network error), a deterministic heuristic produces the same JSON schema using skill intersection, experience ratios, and education level — ensuring the demo always works.

---

## Functional Coverage

### Scenario 1: Umurava Platform Profiles
- ✅ Job creation with required skills, experience, education, seniority
- ✅ Structured talent profile ingestion (apply form with PDF upload)
- ✅ AI batch screening → ranked Top 10/20/50
- ✅ Per-candidate: score breakdown, strengths, gaps, AI reasoning, bias flag
- ✅ Configurable scoring weights per job

### Scenario 2: External Job Boards
- ✅ CSV/TSV file upload with flexible column mapping
- ✅ Supports LinkedIn exports, Indeed CSVs, custom ATS exports
- ✅ Imported candidates run through the same AI screening pipeline
- ✅ JD auto-extraction: paste any job description → Gemini extracts structured requirements

### Recruiter Interface
- ✅ Dashboard with stats (jobs, applicants, screened, shortlisted, avg score)
- ✅ Job CRUD (create, edit, delete, publish/draft)
- ✅ Applicant management with inline status updates
- ✅ Bulk shortlist/reject multiple candidates
- ✅ CSV export of ranked results for sharing with hiring managers
- ✅ Resume PDF download from admin panel
- ✅ Screening progress modal with step-by-step feedback
- ✅ Candidate detail drawer with full score breakdown + AI analysis

---

## Deployment (Production)

```bash
# Render / Railway / Heroku
# 1. Set DATABASE_URL to your PostgreSQL connection string
# 2. Set GEMINI_API_KEY, FLASK_SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
# 3. The Procfile handles everything:
#    web: gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT
```

**Recommended hosting:**
- Frontend + Backend: Render Web Service (free tier available)
- Database: Render PostgreSQL or Supabase
- Files: stored in `instance/uploads/` (add object storage for production scale)

---

## Scoring Formulas

```
Skills Score     = (matched_required_skills / total_required) × 100
                   (token-based matching, avoids false positives like "Go" → "PostgreSQL")

Experience Score = if ratio ≥ 1.5×  → 100
                   if ratio ≥ 1.0×  → 85 + (ratio-1)×30
                   if ratio < 1.0×  → max(20, ratio×80)

Education Score  = EDUCATION_LEVELS[level]   (PhD=100, Masters=85, Bachelors=70…)
                   × 0.6 if below required level

Projects Score   = 30 + (project_count × 14), capped at 100

Weighted Score   = Σ(axis_score × weight) / total_weight

Final Score      = Weighted × 0.6 + AI_Score × 0.4
```

---

## Assumptions & Limitations

- **Single admin account**: This prototype uses one hardcoded admin credential. Production would require multi-tenant auth with role-based permissions.
- **PDF parsing quality**: `pdfplumber` handles standard PDFs well but may struggle with scanned or heavily formatted documents.
- **Gemini batch limits**: Very large batches (100+ candidates) may exceed Gemini's context window. The system falls back to sequential calls if the batch prompt fails.
- **Skills scoring**: Token-based matching reduces false positives but may miss synonyms (e.g., "Node" vs "Node.js"). A production system would use embedding similarity.
- **Education level extraction**: Currently relies on applicants selecting their level from a dropdown. Future versions would parse this from resume text.
- **No CSRF protection**: Acceptable for a hackathon prototype; Flask-WTF would be added for production.
- **SQLite for development**: Swaps to PostgreSQL via `DATABASE_URL` env var. No code changes required.

---

## Tech Decisions Summary

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.11 | Best AI/ML ecosystem; Gemini SDK is first-class |
| Web framework | Flask | Rapid development; Blueprint architecture scales cleanly |
| ORM | SQLAlchemy | Mature, type-safe, supports SQLite → PostgreSQL migration |
| AI | Gemini 2.5 Flash | Mandatory per brief; fastest/cheapest Gemini model |
| PDF parsing | pdfplumber | Accurate text extraction from PDFs |
| Deployment | Gunicorn + Render | Standard Python production stack |
| CSS | Custom design system | Zero runtime CDN dependency; Stripe-inspired tokens |
| Icons | Inline SVG macros | No icon font CDN; renders instantly |

---

## Team

**Team M&P** — Built for the Umurava AI Hackathon 2026, Kigali, Rwanda.

> _"Every score is explainable. Every recommendation is reasoned. Humans stay in control."_
