# Mpact — Intelligent Recruiter Screening Platform

> **Umurava AI Hackathon 2026** · Team M&P — Mugisha Kayishema & Principie Cyubahiro · Kigali, Rwanda

**Live Demo:** [mpact.up.railway.app](https://mpact.up.railway.app)

Mpact is a full-stack recruiting platform that automates candidate screening using a transparent two-layer scoring system — deterministic heuristics combined with Gemini AI — then surfaces a ranked shortlist with complete explainability for every decision. Built specifically for African hiring teams.

---

## The Problem

Hiring teams in Africa receive dozens to hundreds of applications per role. Manual screening is slow, inconsistent, and susceptible to unconscious bias. Recruiters spend most of their time reading CVs before any real evaluation even begins.

Mpact solves this by automating the first-pass screening: every applicant is scored across four axes, evaluated by Gemini AI, and ranked in a shortlist with full reasoning — in seconds, not days.

---

## Why Flask Instead of Next.js

The Umurava brief permits alternative stacks with justification. We chose Python + Flask because:

1. **Python owns the AI ecosystem.** Google's `google-generativeai` SDK, `pdfplumber`, and prompt engineering patterns are first-class in Python. Equivalent Node.js wrappers lag behind.
2. **Zero build pipeline.** Jinja2 server-side templates eliminate the hydration complexity of SSR React, enabling a polished UI without webpack, ESBuild, or a separate frontend process.
3. **Hackathon velocity.** SQLAlchemy + Flask Blueprints let a two-person team deliver all CRUD, AI orchestration, PDF parsing, CSV ingestion, and email notifications in hours, not days.
4. **Gemini remains central.** `gemini-2.5-flash` is used via the official Python SDK, fully satisfying the core AI requirement.

Architecturally, the structure mirrors the recommended stack: Blueprint routes map to Next.js pages/API routes, Flask-SQLAlchemy maps to Prisma, Jinja2 maps to React components.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      MPACT — System Overview                         │
├──────────────────┬────────────────────────────┬──────────────────────┤
│  PUBLIC SITE     │   ADMIN / RECRUITER         │   AI LAYER           │
│                  │                             │                      │
│  Landing Page    │  Recruiter Auth             │  Gemini 2.5 Flash    │
│  Job Browse      │  Dashboard + Stats          │                      │
│  Job Detail      │  Job CRUD                   │  Batch Evaluation    │
│  Apply Form      │  Applicant Management       │  JD Auto-Extraction  │
│  PDF Resume      │  AI Screening               │  Bias Detection      │
│  CSV Import      │  Ranked Results             │                      │
│  Status Lookup   │  Bulk Status Actions        │  Heuristic Fallback  │
│                  │  Resume Download            │                      │
│                  │  CSV Export                 │                      │
└──────────────────┴────────────────────────────┴──────────────────────┘
         │                     │                          │
         └───────────┬─────────┘                          │
                     ▼                                    ▼
           ┌──────────────────┐             ┌──────────────────────────┐
           │  SQLite (dev)    │             │  services/               │
           │  PostgreSQL (prod)│            │  ├── gemini_service.py   │
           │                  │             │  ├── scoring_engine.py   │
           │  recruiters      │             │  ├── email_service.py    │
           │  jobs            │             │  ├── resume_parser.py    │
           │  applicants      │             │  └── file_parser.py      │
           │  job_fields      │             └──────────────────────────┘
           └──────────────────┘
```

### Project Structure

```
mpact/
├── app.py                    Flask application factory + blueprint registration
├── config.py                 Environment-based configuration
├── models.py                 Recruiter, Job, Applicant, JobField SQLAlchemy models
├── extensions.py             SQLAlchemy singleton
├── Procfile                  Gunicorn production entrypoint
├── requirements.txt          Python dependencies
│
├── routes/
│   ├── __init__.py           admin_required decorator
│   ├── public.py             Landing, job browse, job detail, apply form, status lookup
│   ├── admin_auth.py         Recruiter register, login, logout, email verification
│   ├── admin_jobs.py         Job CRUD, CSV import, JD extraction
│   └── admin_screening.py    AI screening, results, CSV export, bulk actions, notes
│
├── services/
│   ├── gemini_service.py     Batch AI evaluation, bias detection, JD extraction
│   ├── scoring_engine.py     Deterministic 4-axis scoring engine
│   ├── email_service.py      Candidate email notifications (application, shortlist, rejection)
│   ├── email.py              Recruiter verification email
│   ├── resume_parser.py      PDF resume field extraction with Gemini
│   └── file_parser.py        PDF text extraction via pdfplumber
│
├── templates/
│   ├── public/               Candidate-facing pages (landing, jobs, apply, status)
│   ├── admin/                Recruiter dashboard (screening, results, jobs, auth)
│   └── icons.html            Inline SVG icon macros — zero CDN dependency
│
└── static/
    ├── css/styles.css        Full custom design system (~900 lines, Stripe-inspired)
    └── js/
        ├── app.js            Public JS (toasts, animations, resume autofill)
        └── admin.js          Admin JS (candidate drawer, scoring rings, bulk select)
```

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd mpact

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — minimum required: GEMINI_API_KEY
# Without it, the heuristic fallback runs automatically — the demo still works

# 5. Seed demo data (recommended)
python seed.py
# Creates 4 jobs and 12 Rwandan candidate profiles

# 6. Run the development server
python app.py
```

Open [http://localhost:5000](http://localhost:5000) for the candidate-facing site.

Recruiter dashboard: [http://localhost:5000/recruiter/login](http://localhost:5000/recruiter/login)

Register a recruiter account, verify your email, and you're in.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `FLASK_SECRET_KEY` | Yes (prod) | `mpact-dev-secret` | Session encryption key |
| `GEMINI_API_KEY` | Recommended | — | Google AI API key — enables real AI screening |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model ID |
| `DATABASE_URL` | Yes (prod) | SQLite local | PostgreSQL connection string |
| `RESEND_API_KEY` | For email | — | Resend API key for transactional email |
| `MAIL_SERVER` | For email | — | SMTP server (alternative to Resend) |
| `MAIL_PORT` | For email | `587` | SMTP port |
| `MAIL_USERNAME` | For email | — | SMTP username |
| `MAIL_PASSWORD` | For email | — | SMTP password |
| `MAIL_FROM` | For email | — | Sender email address |

> **Email transport priority:** Resend API → SMTP → silent fallback with console log. The app runs fully without email configured; a verification link is shown on screen during development.

---

## Scoring System

### Two-Layer Architecture

Every applicant is scored through two independent layers. The final score blends both.

```
                   ┌────────────────────────────────────────┐
                   │          MPACT SCORING ENGINE           │
                   └───────────────┬────────────────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             ▼                                           ▼
  ┌──────────────────────┐                 ┌──────────────────────┐
  │   DETERMINISTIC 60%  │                 │     GEMINI AI  40%   │
  │                      │                 │                      │
  │  Skills Match        │                 │  Batch evaluation    │
  │  Experience Score    │                 │  Strengths (3–5)     │
  │  Education Score     │                 │  Gaps (2–4)          │
  │  Projects Score      │                 │  Recommendation      │
  │                      │                 │  Reasoning (2–3 sen) │
  │  Configurable        │                 │  Bias flag + notes   │
  │  weights per job     │                 │                      │
  └──────────┬───────────┘                 └──────────┬───────────┘
             │                                        │
             └──────────────────┬─────────────────────┘
                                ▼
                 Final Score = Weighted × 0.6 + AI × 0.4
                                ▼
                    Ranked Shortlist (Top 10 / 20 / 50)
```

### Scoring Formulas

```
Skills Score     = (matched_required_skills / total_required) × 100
                   Token-based matching avoids false positives ("Go" ≠ "PostgreSQL")

Experience Score = ratio ≥ 1.5×  → 100
                   ratio ≥ 1.0×  → 85 + (ratio − 1) × 30
                   ratio < 1.0×  → max(20, ratio × 80)

Education Score  = level_weight[level]   (PhD=100, Masters=85, Bachelors=70, Diploma=50)
                   × 0.6 penalty if below required level

Projects Score   = 30 + (project_count × 14), capped at 100

Weighted Score   = Σ(axis_score × weight) / 100    (weights sum to 100, recruiter-configurable)

Final Score      = Weighted × 0.6 + AI_Score × 0.4
```

### Batch Evaluation

All candidates for a job are sent to Gemini in a **single API call**, returning a JSON array with all evaluations simultaneously. This is significantly faster than sequential calls and satisfies the hackathon requirement for multi-candidate evaluation in a single prompt.

```python
# services/gemini_service.py
results = analyze_batch(job, all_applicants, weighted_scores)
# One Gemini call → dict[applicant_id → {ai_score, strengths, gaps, recommendation, reasoning, bias_flag}]
```

If the batch call fails (quota, network), the system automatically falls back to individual calls per candidate. If Gemini is entirely unavailable, a deterministic heuristic produces the same JSON schema using skill intersection, experience ratios, and education level — ensuring the demo always works without an API key.

### Bias Detection

Gemini flags potential unconscious bias signals in each candidate's profile:
- Name-based cultural or ethnic bias
- Location or institution prestige bias
- Experience gap interpretations that may disadvantage non-traditional career paths

Flagged candidates display a ⚠ indicator on result cards and in the candidate detail drawer, prompting recruiters to review those decisions more carefully before acting.

---

## Email Notifications

The platform sends transactional emails at three key moments:

| Event | Recipient | Content |
|---|---|---|
| Recruiter registers | Recruiter | Email verification link |
| Candidate applies | Candidate | Confirmation with reference number + next steps |
| New application received | Recruiter | Alert with candidate details + dashboard link |
| Candidate shortlisted | Candidate | Shortlist notification |
| Candidate rejected | Candidate | Respectful rejection with encouragement |

All emails are built as responsive HTML with a plain-text fallback. The system tries Resend API first, then SMTP, then logs the link to console for development.

---

## Candidate Features

### Application Form
- Full profile with skills, experience, education, projects, location
- PDF resume upload (up to 16 MB) with automatic text extraction
- Resume autofill: upload a PDF and Gemini parses all fields automatically
- Custom questions per job (text, textarea, yes/no, select)
- Structured talent profile compatible with Umurava's schema (headline, bio, availability, LinkedIn, GitHub, portfolio)

### Application Status Page
Candidates can look up their application status at any time using their email address and reference number (format: `MPT-0001-00001`). The status page shows:
- Current stage in the hiring pipeline
- Visual progress timeline
- Contextual messages for shortlisted and interview-stage candidates

---

## Recruiter Features

### Dashboard
- Stats at a glance: total jobs, total applicants, screened, shortlisted, average score
- Recent activity feed across all jobs

### Job Management
- Create, edit, publish, and unpublish jobs
- Configurable scoring weights per job (skills / experience / education / projects — must sum to 100)
- Custom application questions (up to 10 per job)
- JD auto-extraction: paste any job description text and Gemini extracts structured requirements automatically

### Candidate Screening
- Run AI screening on all applicants for a job with a single click
- Real-time progress modal with step-by-step status
- Ranked results table with score breakdown (skills, experience, education, projects, weighted, AI, final)
- Candidate detail drawer: full profile, structured experience timeline, certifications, AI reasoning, bias notes
- Inline recruiter notes per candidate
- Status management: new → reviewed → shortlisted → interview → rejected

### Bulk Actions
- Select multiple candidates and update status in one action
- Bulk shortlist triggers automatic email notifications to all selected candidates

### CSV Import
- Import applicants from any CSV or TSV file (LinkedIn exports, Indeed, ATS exports)
- Flexible column mapping — the system auto-detects common header formats
- Imported candidates run through the full AI screening pipeline

### CSV Export
- Export ranked results as CSV for sharing with hiring managers
- Includes all scores, AI strengths, gaps, reasoning, bias flags, and status

---

## Functional Coverage

### Scenario 1 — Umurava Platform Profiles
- ✅ Job creation with required skills, experience, education, seniority
- ✅ Structured talent profile ingestion (Umurava schema: headline, bio, skills with proficiency, experience timeline, education, certifications, projects, languages, availability)
- ✅ PDF resume upload with automatic text extraction and field autofill
- ✅ AI batch screening → ranked Top 10/20/50
- ✅ Per-candidate: score breakdown, strengths, gaps, AI reasoning, bias flag
- ✅ Configurable scoring weights per job

### Scenario 2 — External Job Boards
- ✅ CSV/TSV file upload with flexible column mapping
- ✅ Supports LinkedIn exports, Indeed CSVs, custom ATS exports
- ✅ Imported candidates run through the same AI screening pipeline
- ✅ JD auto-extraction: paste any job description → Gemini extracts structured requirements

### Recruiter Experience
- ✅ Secure recruiter registration with email verification
- ✅ Multi-recruiter support (each recruiter owns their jobs and candidates)
- ✅ Dashboard with live stats
- ✅ Complete job lifecycle management
- ✅ Bulk candidate status actions
- ✅ Resume PDF download from the admin panel
- ✅ Recruiter notes saved per candidate
- ✅ Candidate application status self-service portal

---

## Production Deployment

The app is deployed on Railway with a PostgreSQL database.

```bash
# Required environment variables for production
FLASK_SECRET_KEY=<random 32+ char secret>
GEMINI_API_KEY=<your Google AI key>
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=<postgresql://...>
RESEND_API_KEY=<your Resend key>
MAIL_FROM=noreply@yourdomain.com
```

The `Procfile` handles the web process:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60
```

Database migrations run automatically on startup via `_migrate_db()` in `app.py` — adding new columns to existing tables without data loss.

---

## Technology Decisions

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.11 | Best AI/ML ecosystem; Gemini SDK is first-class |
| Web framework | Flask 3.0 | Rapid development; Blueprint architecture scales cleanly |
| ORM | SQLAlchemy 3.1 | Mature, supports SQLite → PostgreSQL with no code changes |
| AI | Gemini 2.5 Flash | Mandatory per brief; most capable Gemini model available |
| PDF parsing | pdfplumber | Accurate text extraction from standard PDFs |
| Email | Resend API | HTTP-based; works from all cloud providers |
| Deployment | Gunicorn + Railway | Standard Python production stack |
| CSS | Custom design system | Zero CDN dependency; Stripe-inspired design tokens |
| Icons | Inline SVG macros | No icon font CDN; renders instantly, fully accessible |
| Database (dev) | SQLite | Zero setup; automatic migration to PostgreSQL in production |
| Database (prod) | PostgreSQL | Full relational support; hosted on Railway |

---

## Known Limitations

- **PDF parsing quality**: `pdfplumber` handles standard PDFs well but may struggle with scanned documents or heavily formatted templates.
- **Skills scoring**: Token-based matching reduces false positives but may miss synonyms (e.g., "Node" vs "Node.js"). A production system would use embedding similarity.
- **Gemini batch limits**: Very large batches (100+ candidates) may exceed the context window. The system falls back to individual calls automatically.
- **File storage**: Uploaded resumes are stored on the local filesystem (`instance/uploads/`). Production scale would require object storage (S3, GCS).
- **No CSRF protection**: Acceptable for a hackathon prototype. Flask-WTF would be added for production.

---

## Team

**Team M&P** — Mugisha Kayishema & Principie Cyubahiro

Built for the Umurava AI Hackathon 2026, Kigali, Rwanda.

> *"Every score is explainable. Every recommendation is reasoned. Humans stay in control."*
