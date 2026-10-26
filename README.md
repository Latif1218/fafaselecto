# Postulae — AI-Powered CV Optimization, Generation and Guidance Platform

[![Live](https://img.shields.io/badge/Live-postulae.com-brightgreen)](https://postulae.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF)](https://github.com/features/actions)
[![Stripe](https://img.shields.io/badge/Payments-Stripe-635BFF)](https://stripe.com)
[![Claude](https://img.shields.io/badge/AI-Anthropic%20Claude-D97757)](https://anthropic.com)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI%20GPT--4o-412991)](https://openai.com)

> **Postulae** is a SaaS platform that helps job seekers score, optimize and generate CVs and cover letters with AI, and optionally get a human review from a professional tutor. Output is available in **English** and **French**, as one-page PDF and editable DOCX.

**Website:** https://postulae.com
**Figma design:** [View design](https://www.figma.com/design/CgC3uEfFzcOpeDha6aCzpk/fafaselecto16--Copy-?node-id=0-1&p=f&t=xHYmcOOCt5feWjnO-0)

---

## Table of Contents

1. [Features](#1-features)
2. [Architecture](#2-architecture)
3. [What lives where](#3-what-lives-where)
4. [Core logic flows](#4-core-logic-flows)
5. [AI engine](#5-ai-engine)
6. [Subscription plans](#6-subscription-plans)
7. [API reference](#7-api-reference)
8. [Data model](#8-data-model)
9. [Tech stack](#9-tech-stack)
10. [Project structure](#10-project-structure)
11. [Getting started](#11-getting-started)
12. [Environment variables](#12-environment-variables)
13. [Deployment and CI/CD](#13-deployment-and-cicd)
14. [Token usage and cost model](#14-token-usage-and-cost-model)
15. [Extending the system](#15-extending-the-system)
16. [Known issues and roadmap](#16-known-issues-and-roadmap)
17. [Author and license](#17-author-and-license)

---

## 1. Features

| Feature | What it does |
|---|---|
| **CV evaluation** | Upload a PDF and get a score with strengths and improvement tips. Scoring is rule-based (no LLM call in the grader). |
| **CV optimization** | Rewrites an existing CV into a one-page, finance/consulting-style CV in **French and English** (PDF + DOCX). |
| **CV generation from a form** | Multi-step form (personal details, education, employment, languages, skills, activities) turned into a finished CV. |
| **Cover letters** | Generated from a CV plus a job offer (pasted text or URL). Exported to PDF and DOCX, FR or EN. |
| **Ultimate plan** | One-time purchase that adds a human tutor review of the CV. Admins assign and validate requests. |
| **Auth** | Email + password with OTP email verification, Google OAuth, OTP password reset. |
| **Payments** | Stripe Checkout (subscriptions and one-time payment) with webhooks. |
| **Admin and tutor dashboards** | User management, tutor statistics, assignment of review requests. |

---

## 2. Architecture

Postulae is a **modular monolith plus external services**, not a microservice system.

- **One deployable service of our own:** a FastAPI app in a single Docker container on a Hostinger VPS.
- **Six external services:** PostgreSQL, Redis, Stripe, SMTP email, OpenAI and Anthropic.
- **The AI engine** lives in `apps/ai/` as an in-process library. It is called directly by the routers, not over the network.

```mermaid
flowchart LR
    FE["Frontend<br/>postulae.com"] --> API
    GH["GitHub Actions<br/>build, push, SSH deploy"] --> API

    subgraph API["FastAPI monolith (1 Docker container)"]
        AUTH["Auth + users<br/>JWT, Google, OTP"]
        BILL["Billing + tutor<br/>Stripe, reviews"]
        CV["CV routes<br/>evaluate, optimize, form"]
        CL["Cover letter"]
        AI["AI engine (apps/ai)<br/>extract, score, write, PDF render"]
        CV --> AI
        CL --> AI
    end

    API --> PG[("PostgreSQL")]
    API --> RD[("Redis<br/>OTP reset keys")]
    API --> ST["Stripe"]
    API --> SM["SMTP email"]
    API --> OA["OpenAI<br/>GPT-4o, 4o-mini"]
    API --> AN["Anthropic<br/>Sonnet 4.5, Haiku 4.5"]
```

### Request path

```
Browser → Nginx (TLS) → Uvicorn :8080 → FastAPI router
          → JWT check (HS256, 60 min) → SQLAlchemy → PostgreSQL
                                      → apps/ai → OpenAI / Anthropic → Playwright → PDF/DOCX
```

### Design characteristics

| Aspect | Current design |
|---|---|
| Deployable units | 1 (FastAPI container) |
| Layering | Router → ORM model (no separate service layer) |
| Auth | Own JWT (HS256, 60 min expiry); Google OAuth as an alternative login |
| Long-running work | Done inline inside the request (the generator runs in `asyncio.to_thread`); no job queue |
| File storage | Local `uploads/` directory on the server |
| Schema management | `Base.metadata.create_all()` at startup (Alembic installed but unused) |
| Rate limiting | `slowapi` on `/token` (10/min) and the forgot-password endpoints |

---

## 3. What lives where

| Concern | Location |
|---|---|
| App entry, CORS, sessions, `/health` | `apps/main.py` |
| Env loading | `apps/config.py` |
| DB engine, session, Redis singleton | `apps/database.py` |
| JWT creation, current-user / admin / tutor dependencies | `apps/authentication/users_oauth.py` |
| Register + email OTP verification | `apps/routers/register_users.py` |
| Login (`/token`), `/me` | `apps/routers/login_user.py` |
| Google OAuth | `apps/routers/conte_with_google.py`, `apps/utils/google_oauth_url.py` |
| Forgot / reset / update password | `apps/routers/forgot_password.py` |
| Stripe checkout and webhook | `apps/routers/subscription.py` |
| CV evaluate, optimize, generate, list, download | `apps/routers/cv_router.py` |
| Multi-step CV form | `apps/routers/form_and_to_cv.py` |
| Cover letters | `apps/routers/cover_letter.py` |
| Ultimate (human review) requests | `apps/routers/cv_ultimate.py` |
| Tutor registration and review work | `apps/routers/tutor_register.py`, `tutor_requests.py` |
| Admin: users, tutors, review requests | `apps/routers/admin_*.py` |
| OTP email sending | `apps/utils/otp_and_mail.py` |
| File saving and URLs | `apps/utils/file_storage.py` |
| LLM clients | `apps/ai/app/llm_client.py` (OpenAI), `llm_client_anthropic.py` (Claude) |
| CV generation pipeline | `apps/ai/app/generator.py` |
| CV scoring (rule-based) | `apps/ai/app/cv_grader.py` |
| Vision scoring (not wired to any route) | `apps/ai/app/cv_grader_vision.py` |
| Cover letter pipeline | `apps/ai/app/cover_letter_generator.py` |
| Prompts | `apps/ai/app/prompts/*.txt` |
| HTML templates | `apps/ai/app/templates/` |
| CV PDF rendering | `apps/ai/app/layout_playwright.py` (Chromium) |
| Cover letter export | `apps/ai/app/cover_letter_exporter.py` (ReportLab PDF + python-docx) |

---

## 4. Core logic flows

### 4.1 Registration and login

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant DB as PostgreSQL
    participant M as SMTP
    U->>API: POST /register_user/
    API->>DB: create user (is_verified = false, plan = essential)
    API->>M: send 6-digit OTP (valid 10 min)
    U->>API: POST /register_user/verify_otp
    API->>DB: is_verified = true
    U->>API: POST /token (email + password)
    API-->>U: JWT access token (60 min)
```

### 4.2 Subscription

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant ST as Stripe
    U->>API: POST /subscription/checkout {plan}
    API->>ST: create Checkout Session (metadata: user_id, plan)
    API-->>U: checkout URL (subscription row = incomplete)
    ST->>API: POST /subscription/stripe (webhook)
    Note over API: signature verified with STRIPE_WEBHOOK_SECRET
    API->>API: subscription row = active
```

Handled Stripe events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`.
Starter and Premium use `subscription` mode; Ultimate uses one-time `payment` mode.

### 4.3 CV optimization (`POST /cv/optimize`)

```mermaid
flowchart LR
    A["Extract text<br/>GPT-4o"] --> B["Detect domain<br/>GPT-4o-mini"]
    B --> C["Structure FR<br/>Claude Sonnet 4.5"]
    C --> D["Translate EN<br/>Claude Haiku 4.5"]
    D --> E["Render PDF<br/>Playwright"]
    E --> F["Fit one page<br/>trim rules"]
    F --> G["Re-extract<br/>GPT-4o"]
    G --> H["Score<br/>rules, no LLM"]
```

The generator measures the **page fill ratio (PFR)** of the rendered PDF. It blocks generation below 65%, pads or enriches content when too short, and applies progressive trim levels (1 to 4) when the CV overflows one page.

### 4.4 Cover letter (`POST /cover-letter/generate`)

```
Job offer (text or URL) ──► Haiku 4.5: extract requirements
CV data ───────────────────► internal matching of achievements and skills
                          ──► Sonnet 4.5: generate letter (JSON mode)
                          ──► Haiku 4.5: translate (only if both languages requested)
                          ──► ReportLab PDF + python-docx DOCX ──► saved to uploads/
```

### 4.5 Ultimate (human review)

```
User buys Ultimate (€149) ──► POST /cv/ultimate/request ──► status: pending
Admin assigns a tutor ──► tutor reviews ──► admin validates ──► status: completed
```

---

## 5. AI engine

The engine lives in `apps/ai/` and uses a **hybrid model stack** (`USE_HYBRID_STACK = True` in `generator.py`).

| Task | Model | Where |
|---|---|---|
| PDF text extraction (file input, JSON output) | OpenAI **GPT-4o** | `llm_client.extract_text_from_pdf_bytes` |
| Structuring a CV into JSON | Claude **Sonnet 4.5** (`claude-sonnet-4-5-20250929`) | `llm_client_anthropic.generate_cv_content_claude` |
| FR ↔ EN translation | Claude **Haiku 4.5** (`claude-haiku-4-5`) | `translate_cv_content_claude` |
| Domain detection (3,500 chars, max 30 tokens) | OpenAI **GPT-4o-mini** | `domain_detector.py` |
| Job offer extraction and cover letter translation | Claude Haiku 4.5 | `cover_letter_generator.py` |
| Cover letter generation | Claude Sonnet 4.5 | `cover_letter_generator.py` |
| Structured data for scoring in `/cv/upload_and_evaluate` | OpenAI GPT-4o (legacy path) | `llm_client.generate_cv_content` |
| Extra bullet enrichment | `gpt-4-turbo-preview` (**retired**, see issues) | `enrichment.py` |

### Prompts

All instructions are external text files in `apps/ai/app/prompts/`:

| File | Size | Purpose |
|---|---|---|
| `base_system.txt` | ~27.8 KB (~7,000 tokens) | Global CV persona and constraints, used for every structuring call |
| `generate_cover_letter_json.txt` | ~12.2 KB | Cover letter generation (JSON mode) |
| `translate_cover_letter.txt` | ~8.6 KB | Cover letter translation |
| `extract_job_requirements.txt` | ~3.8 KB | Parsing a job offer |
| `enrich_content.txt` | ~1.7 KB | Legacy enrichment instructions |
| `extract_from_pdf.txt` | ~0.4 KB | PDF text extraction |

### Scoring

`cv_grader.py` is **rule-based Python**, not an LLM call. It produces a score plus tips from the extracted structure and metadata. `cv_grader_vision.py` (GPT-4o vision) exists but no route calls it.

### Rendering

| Output | Technology |
|---|---|
| CV PDF | HTML (Jinja2, `grid_template.html`) → Playwright / headless Chromium |
| CV DOCX | `pdf2docx` |
| Cover letter PDF | ReportLab |
| Cover letter DOCX | python-docx |
| Legacy renderer | xhtml2pdf (`layout_legacy.py`, used only if `USE_HYBRID_STACK = False`) |

---

## 6. Subscription plans

| Plan | Price | Mode | Access in code |
|---|---|---|---|
| **Essential** | Free | none | Default after registration |
| **Starter** | €4.90 / month | subscription | CV optimize and generate |
| **Premium** | €24.90 / month | subscription | Same checks as Starter today |
| **Ultimate** | €149 one-time | payment | Adds human tutor review (`/cv/ultimate/request`) |

Prices are hardcoded in `GET /subscription/config`; the Stripe price IDs come from env variables. Cover letter generation currently has no plan check.

---

## 7. API reference

Interactive docs: `/docs`. **Auth** = `Authorization: Bearer <JWT>`. About 54 endpoints in total; the tables list the main ones.

### System and auth
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Health check |
| POST | `/register_user/` | No | Register |
| POST | `/register_user/verify_otp` | No | Verify email OTP |
| POST | `/token` | No | Login (OAuth2 form, 10/min) |
| GET | `/me` | Yes | Current user |
| GET | `/auth/google/login` | No | Start Google OAuth |
| GET | `/auth/google/callback` | No | Google callback |
| POST | `/forgot/...forgot_pass` | No | Send reset OTP (3/hour) |
| POST | `/forgot/verify_otp` | No | Verify reset OTP |
| PUT | `/forgot/...update_password_without_token` | No | Reset password |
| PUT | `/forgot/...update_password` | Yes | Change password |

> The forgot-password paths are currently registered **without a slash** (for example `/forgotforgot_pass`). See [Known issues](#16-known-issues-and-roadmap).

### CV
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/cv/upload_and_evaluate` | **No** (takes `email` form field) | Score a CV |
| POST | `/cv/optimize` | Yes (Starter+) | Optimize a PDF to FR + EN |
| POST | `/cv/generate` | Yes (Starter+) | Generate CV from form data |
| GET | `/cv/list`, `/cv/my-cvs`, `/cv/my-favorite` | Yes | List CVs |
| GET / DELETE | `/cv/{cv_id}` | Yes | Detail / delete |
| GET | `/cv/download/{cv_id}` | Yes | Download PDF or DOCX |
| PATCH | `/cv/set_favorite/{cv_id}` | Yes | Toggle favorite |
| POST | `/cv/form/save` | Yes | Save a form step |
| GET | `/cv/form/current` | Yes | Load current form |
| POST | `/cv/form/submit` | Yes | Submit the form |
| POST | `/cv/ultimate/request` | Yes (Ultimate) | Request human review |
| GET | `/cv/ultimate/status/{request_id}` | Yes | Review status |

### Cover letter
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/cover-letter/generate` | Yes | Generate from CV + job offer |
| GET | `/cover-letter/`, `/cover-letter/{id}` | Yes | List / detail |
| GET | `/cover-letter/{id}/preview`, `/download/pdf`, `/download/docx` | Yes | Preview and download |

### Subscription
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/subscription/config` | No | Plans and price IDs |
| POST | `/subscription/checkout` | Yes | Create Stripe Checkout Session |
| POST | `/subscription/stripe` | Stripe signature | Webhook |

### Users, tutors, admin
| Method | Path | Auth | Description |
|---|---|---|---|
| GET / PATCH | `/users/me`, `/users/update/me` | Yes | Profile |
| GET | `/users/cvs_list/me` | Yes | My CVs |
| POST | `/tutor/register`, `/tutor/verify_tutor_otp` | No | Tutor onboarding |
| GET / POST | `/tutor/requests`, `/tutor/reviews/{request_id}` | Tutor | Review work |
| GET / PATCH / DELETE | `/admin/users/...` | Admin | User management and overview |
| GET / DELETE | `/admin/tutors/...` | Admin | Tutor statistics |
| GET / POST | `/admin/ultimate-requests/...` | Admin | List, assign, validate |

---

## 8. Data model

```mermaid
erDiagram
    USERS ||--o{ CV : owns
    USERS ||--o{ CV_FORMS : fills
    USERS ||--o{ COVER_LETTER : owns
    USERS ||--o| SUBSCRIPTIONS : has
    USERS ||--o{ PASSWORD_RESET_CODES : requests
    USERS ||--o{ ULTIMATE_REQUESTS : submits
    CV ||--o{ ULTIMATE_REQUESTS : reviewed_in
    CV ||--o{ COVER_LETTER : source_of

    USERS {
        uuid id PK
        string email
        string role
        string plan
        string status
        bool is_verified
    }
    CV {
        uuid id PK
        uuid user_id FK
        string file_path
        string docx_path
        int score
        string domain
        json tips
    }
    CV_FORMS {
        uuid id PK
        uuid user_id FK
        json personal_details
        json education
        json employment
        bool is_completed
    }
    COVER_LETTER {
        uuid id PK
        uuid user_id FK
        uuid cv_id FK
        string company_name
        string language
        string pdf_path
    }
    SUBSCRIPTIONS {
        uuid id PK
        uuid user_id FK
        string plan_type
        string status
        datetime current_period_end
    }
    ULTIMATE_REQUESTS {
        uuid id PK
        uuid user_id FK
        uuid cv_id FK
        uuid assigned_tutor_id FK
        string status
        datetime deadline
    }
    PASSWORD_RESET_CODES {
        uuid id PK
        uuid user_id FK
        string otp
        bool used
    }
```

Roles: `user`, `admin`, `tutor`. Plans: `essential`, `starter`, `premium`, `ultimate`.

---

## 9. Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.128, Uvicorn, Python 3.12 |
| ORM and DB | SQLAlchemy 2.0, psycopg2, PostgreSQL |
| Cache / OTP | Redis (via `redis` client) |
| Auth | PyJWT (HS256), Google OAuth, argon2 / pwdlib in requirements for password hashing |
| Payments | Stripe |
| Email | SMTP |
| LLMs | Anthropic (Sonnet 4.5, Haiku 4.5), OpenAI (GPT-4o, GPT-4o-mini) |
| Documents | Playwright (Chromium), Jinja2, pdf2docx, python-docx, ReportLab, pdfplumber |
| Rate limiting | slowapi |
| Containers and CI/CD | Docker, Docker Compose, GitHub Actions, Docker Hub |
| Hosting | Hostinger VPS (Ubuntu), Nginx |

`langchain`, `langchain-openai`, and `GROQ_API_KEY` / `HF_TOKEN` are present in requirements or config but **not used by any route**. Earlier versions of this README listed ChromaDB, sentence-transformers, PyTorch and WeasyPrint; none of them appear in the code or `requirements.txt`.

---

## 10. Project structure

```
postulae/
├── .github/workflows/deploy.yml     # CI/CD pipeline
├── apps/
│   ├── main.py                      # FastAPI entry point
│   ├── config.py                    # Environment configuration
│   ├── database.py                  # SQLAlchemy engine + Redis singleton
│   ├── authentication/              # JWT and current-user dependencies
│   ├── models/                      # 7 SQLAlchemy tables
│   ├── routers/                     # 15 router modules
│   ├── schemas/                     # Pydantic schemas
│   ├── utils/                       # Hashing, OTP mail, files, Google OAuth, stats
│   └── ai/                          # AI engine
│       ├── app/
│       │   ├── prompts/             # LLM prompt files
│       │   ├── templates/           # HTML templates
│       │   ├── llm_client.py        # OpenAI wrapper
│       │   ├── llm_client_anthropic.py
│       │   ├── generator.py         # CV pipeline
│       │   ├── cv_grader.py         # Rule-based scoring
│       │   ├── cover_letter_*.py    # Cover letter pipeline and export
│       │   ├── layout_playwright.py # HTML → PDF
│       │   └── ...
│       ├── docs/                    # AI engine documentation
│       └── tests/                   # Manual test and debug scripts
├── uploads/                         # User files (should not be in git)
├── dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 11. Getting started

**Prerequisites:** Python 3.12, PostgreSQL, **Redis** (password reset needs it), Chromium for Playwright, API keys for OpenAI and Anthropic.

```bash
git clone https://github.com/Latif1218/fafaselecto.git
cd fafaselecto

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install --with-deps chromium

cp .env.example .env               # fill in values, see below
uvicorn apps.main:app --reload
```

Open `http://localhost:8000/docs`.

**Docker**

```bash
docker-compose up --build
```

The current Dockerfile does **not** install Chromium, and `docker-compose.yml` has no Redis container. Add `RUN playwright install --with-deps chromium` and a Redis service before relying on it (see [Known issues](#16-known-issues-and-roadmap)).

**Local Stripe webhook testing**

```bash
stripe listen --forward-to localhost:8000/subscription/stripe
```

---

## 12. Environment variables

Names below match `apps/config.py` and `apps/routers/subscription.py`.

```env
# Database and security
SQLALCHEMY_DATABASE_URL=postgresql://user:password@host:5432/dbname
JWT_SECRET_KEY=
SESSION_SECRET_KEY=
DOMAIN=https://postulae.com

# AI providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=            # missing from the root .env.example, but required

# Redis (password reset)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=
EMAIL_FROM=
EMAIL_PASSWORD=
EMAIL_USE_TLS=True

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
GOOGLE_AUTH_URL=
GOOGLE_TOKEN_URL=
GOOGLE_USERINFO_URL=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
PRICE_STARTER_MONTHLY=
PRICE_PREMIUM_MONTHLY=
PRICE_ULTIMATE_ONETIME=
STRIPE_SUCCESS_URL=           # defaults to DOMAIN/payment/success
STRIPE_CANCEL_URL=            # defaults to DOMAIN/payment/cancel

# Optional / currently unused
GROQ_API_KEY=
HF_TOKEN=
```

`.env.example` still lists `STRIPE_MONTHLY_PRICE_ID` and `STRIPE_YEARLY_PRICE_ID`, which the code does not read. Use the `PRICE_*` names above.

**Never commit real keys.** Keep them in `.env` (git-ignored) or GitHub Secrets.

---

## 13. Deployment and CI/CD

Every push to `main`:

1. Builds the Docker image.
2. Pushes `mdsumon12ir/postulae:latest` to Docker Hub.
3. SSHes into the VPS, copies `.env` from `/root/fafaselecto/.env`, writes `docker-compose.yml`, then runs `docker compose pull` and `up -d --remove-orphans`.

```
git push origin main → GitHub Actions → Docker Hub → Hostinger VPS
```

Required GitHub secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `VPS_HOST`, `VPS_USER`, `VPS_PASSWORD`.

The container listens on port 8080 (`uvicorn apps.main:app`). Nginx terminates TLS in front of it.

---

## 14. Token usage and cost model

> **These are estimates.** No token usage is logged anywhere in the code, so the numbers come from prompt file sizes (about 4 characters per token) and assumed CV sizes (~900 tokens of CV text). Replace them with measured values from the API usage fields when available. Prices per 1M input / output tokens: GPT-4o $2.50 / $10, GPT-4o-mini $0.15 / $0.60, Claude Sonnet 4.5 $3 / $15, Claude Haiku 4.5 $1 / $5. Cache reads on Claude cost one tenth of normal input.

### Per call

| Call | Model | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| PDF text extraction | GPT-4o | ~2,100 | ~1,000 | $0.0152 |
| Domain detection | GPT-4o-mini | ~1,150 | ≤30 | $0.0002 |
| CV structuring | Sonnet 4.5 | ~8,200 | ~1,600 | $0.0486 |
| EN translation | Haiku 4.5 | ~2,100 | ~1,600 | $0.0101 |
| Job offer extraction | Haiku 4.5 | ~1,960 | ~500 | $0.0045 |
| Cover letter | Sonnet 4.5 | ~5,550 | ~800 | $0.0287 |
| Letter translation | Haiku 4.5 | ~2,700 | ~550 | $0.0054 |

### Per request

| Feature | Calls | Total tokens | Cost |
|---|---|---|---|
| Evaluate CV | 2× extraction + GPT-4o structuring | ~16,000 | **$0.067** |
| Optimize CV | 3× extraction + mini + Sonnet + Haiku | ~24,000 | **$0.105** |
| Form → CV (FR + EN) | Sonnet + Haiku | ~13,300 | **$0.058** |
| Cover letter | Haiku + Sonnet | ~8,800 | **$0.033** ($0.039 with translation) |

### Per user per month

Assumed usage: Starter 1 evaluate + 1 optimize + 1 form + 1 letter; Premium 2 / 3 / 2 / 4; Ultimate 3 / 3 / 2 / 5; Free 1 evaluate.

| User type | Revenue | AI cost |
|---|---|---|
| Free | €0 | $0.07 |
| Starter | €4.90 / month | $0.26 |
| Premium | €24.90 / month | $0.72 |
| Ultimate | €149 one-time | $0.82 plus **tutor payout (not in code)** |

### Whole project

Assumed mix: 70% Free, 20% Starter, 8% Premium, 2% Ultimate. Stripe fee 1.5% + €0.25 (assumed EU cards). € treated as ≈ $. Fixed infrastructure (VPS, database, Redis, email) is a guess of $40 / $80 / $400.

| Registered users | Revenue / month | AI | Stripe | Fixed | Total (excl. tutors, VAT) | Cost per user |
|---|---|---|---|---|---|---|
| 100 | ~$595 | $17 | $16 | $40 | $74 | $0.74 |
| 1,000 | ~$5,952 | $173 | $164 | $80 | $418 | $0.42 |
| 10,000 | ~$59,520 | $1,734 | $1,643 | $400 | $3,777 | $0.38 |

### Savings available

| Change | Effect |
|---|---|
| Extract text locally with `pdfplumber` (already installed) instead of GPT-4o | Optimize $0.105 → ~$0.059 (−44%) |
| Add Anthropic prompt caching for the ~7,000-token `base_system.txt` | About −$0.02 per Sonnet call (−41% of that call) |
| Use a small prompt with GPT-4o-mini for the grading data in `/cv/upload_and_evaluate` | Evaluate $0.067 → under $0.02 |
| Log `usage` from every API response | Replace estimates with real numbers |

---

## 15. Extending the system

**Adding a new AI feature** (for example a LinkedIn summary): add a prompt file in `apps/ai/app/prompts/`, a function in `apps/ai/app/`, a schema, and a router. Use the cover letter module as the template.

**Adding a language:** extend the language handling in `generator.py` (`fr` / `en` today), add translation prompts, and update the HTML templates.

**Splitting the AI engine into its own service** is the most natural first microservice, because `apps/ai/` is already a self-contained library. Recommended preparation:

1. Remove the `sys.path` manipulation and the mixed `app...` / `apps.ai.app...` imports; make `apps/ai` an installable package.
2. Add a job queue (Redis is already available) so optimize and cover-letter work stops running inside HTTP requests.
3. Move `uploads/` to object storage (S3 or similar) so several services can share files.
4. Introduce a `services/` layer between routers and the AI engine.
5. Introduce Alembic migrations in place of `create_all()`.

---

## 16. Known issues and roadmap

Found during code review. Ordered by priority. Items marked *verify* come from reading the code, not from running it.

**Revenue and access**
- [ ] **Paid users may never be upgraded** *(verify)*: no code sets `User.plan` after payment, and the webhook calls `int(user_id)` on a UUID, which raises. Optimize and generate require Starter or higher, so paying users may be blocked.
- [ ] The webhook also reads `session["line_items"]`, which Stripe does not include unless expanded, and compares `Subscription.id` (UUID column) with Stripe `sub_...` strings.
- [ ] Starter and Premium have identical access and there is no usage quota; cover letters have no plan check at all.

**Security and privacy**
- [ ] `POST /cv/upload_and_evaluate` has no authentication or rate limit and takes the user from an `email` form field. Each call costs about $0.067 and the route has no file-size limit.
- [ ] `job_link` is fetched with `requests.get` without validation (SSRF risk to internal addresses).
- [ ] The repository contains about 145 user files under `uploads/` and real people's CVs under `apps/ai/` input/output. Remove them from git history (GDPR).
- [ ] Forgot-password reveals whether an email exists (404). `get_current_active_user` reads a non-existent `.disabled` attribute.
- [ ] CORS allows localhost and an ngrok URL in production. Deploy logs in as root with a password; use an SSH key and a non-root user.

**Correctness**
- [ ] Forgot-password routes lack a leading slash (`/forgotforgot_pass`, `/forgotupdate_password`); the admin validate route has the same problem.
- [ ] `docker-compose.yml` has no Redis service, but password reset needs Redis and raises if it is unreachable.
- [ ] The Dockerfile does not run `playwright install chromium`, so CV PDF rendering can fail inside the container.
- [ ] `enrichment.py` calls `gpt-4-turbo-preview`, an alias community trackers report as shut off on 2026-03-26; the call fails silently and returns nothing. Check OpenAI's deprecations page for the GPT-4o snapshots too, and migrate before they retire.
- [ ] `.env.example` is out of date (missing `ANTHROPIC_API_KEY`, wrong Stripe price names).
- [ ] The Ultimate plan is one-time, but a `Subscription` row is still created for it at checkout.

**Performance and cost**
- [ ] The same PDF is sent to GPT-4o three times in `/cv/optimize` and twice in `/cv/upload_and_evaluate`.
- [ ] No prompt caching for the 7,000-token system prompt.
- [ ] `async def` routes call the synchronous OpenAI/Anthropic SDKs directly, which blocks the event loop.
- [ ] Cover letter cost is a hardcoded constant (`0.0145` etc.), not measured usage. Price notes in the Anthropic client are out of date (Haiku 4.5 costs 4× the Haiku 3 price quoted there).
- [ ] A separate `Limiter` per router with in-memory storage; use Redis-backed limits.

**Hygiene**
- [ ] Add Alembic migrations and an automated test suite (current `tests/` files are manual scripts).
- [ ] Remove unused code and dependencies: `groq_client`, `langchain*`, the unused vision grader wiring, the legacy renderer.
- [ ] Move `uploads/` out of git and into object storage.

---

## 17. Author and license

**Md. Abdul Latif Sumon**, AI Engineer
Email: mdsabdullotif@gmail.com | mdabdullatifdelta@gmail.com
GitHub: [Latif1218](https://github.com/Latif1218)

Licensed under the **MIT License**, see [LICENSE](LICENSE).

---

> *Postulae — Empowering job seekers with AI-driven career tools.*
