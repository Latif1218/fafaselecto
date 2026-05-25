# 🎯 Postulae — AI-Powered CV Optimization, Generation and Guidance Platform

[![Live](https://img.shields.io/badge/Live-postulae.com-brightgreen)](https://postulae.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF)](https://github.com/features/actions)
[![Stripe](https://img.shields.io/badge/Payments-Stripe-635BFF)](https://stripe.com)

> **Postulae** is a SaaS platform that helps job seekers optimize their CVs using AI, generate new CVs, and connect with professional tutors — available in **English** and **French**.

---

## 🌐 Live Demo

🔗 **Website:** [https://postulae.com](https://postulae.com)  
🎨 **Figma Design:** [View Design](https://www.figma.com/design/CgC3uEfFzcOpeDha6aCzpk/fafaselecto16--Copy-?node-id=0-1&p=f&t=xHYmcOOCt5feWjnO-0)

---

## ✨ Features

### 📄 CV Analysis & Scoring
- Upload your CV and get an **AI-powered score**
- Detailed feedback on strengths and weaknesses
- Actionable suggestions for improvement
- Vision-based analysis for image/scanned CVs

### 🚀 CV Optimization
- AI-optimized CV based on your existing document
- Tailored to job market standards
- Available in **English** and **French**
- Overflow prevention for perfect single-page output

### 🤖 AI CV Generation
- Generate a brand new CV from provided information
- Professional formatting and layout with HTML templates
- Powered by **Anthropic Claude** and **OpenAI GPT**

### 💌 Cover Letter Generation
- AI-generated personalized cover letters
- Job offer extraction from text or URL
- Export to PDF and DOCX
- Available in **English** and **French**

### 👨‍🏫 Tutor Support
- Connect with professional career tutors
- Personalized CV coaching sessions
- Admin dashboard for tutor management

### 💳 Subscription Plans & Payments

Postulae uses **Stripe** for secure payment processing, supporting subscription plans, webhooks, and checkout sessions.

| Plan | Features |
|------|----------|
| **Starter** | CV scoring + basic optimization |
| **Premium** | Full CV optimization + new CV generation + cover letter |
| **Ultimate** | Everything + personal tutor access |

**Stripe Integration includes:**
- Secure checkout sessions via `stripe.checkout.Session`
- Webhook event handling (payment success, cancellation, renewal)
- Customer portal for subscription self-management
- Publishable & secret key separation for frontend/backend security

---

## 🏗️ Project Structure

```
postulae/
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD pipeline
├── apps/
│   ├── ai/                         # 🤖 AI Engine (see full breakdown below)
│   ├── authentication/             # OAuth & JWT auth logic
│   ├── models/                     # Database models
│   │   ├── cv_model.py
│   │   ├── users_model.py
│   │   ├── subs_model.py
│   │   ├── ultimate_request.py
│   │   └── forgot_password_m.py
│   ├── routers/                    # API routes
│   │   ├── cv_router.py
│   │   ├── cover_letter.py
│   │   ├── cv_ultimate.py
│   │   ├── login_user.py
│   │   ├── register_users.py
│   │   ├── subscription.py         # Stripe subscription management
│   │   ├── tutor_register.py
│   │   ├── tutor_requests.py
│   │   ├── users.py
│   │   ├── admin_user.py
│   │   ├── admin_tutor_dashboard.py
│   │   ├── admin_ultimate_req.py
│   │   ├── forgot_password.py
│   │   └── conte_with_google.py
│   ├── schemas/                    # Pydantic schemas
│   │   ├── cv_schema.py
│   │   ├── users_schema.py
│   │   ├── cover_letter_schema.py
│   │   ├── subs_schema.py
│   │   ├── tutor_schema.py
│   │   └── ultimate_schema.py
│   ├── utils/                      # Utility functions
│   ├── config.py                   # App configuration
│   ├── database.py                 # Database connection
│   └── main.py                     # FastAPI app entry point
├── cv/                             # CV templates & storage
├── uploads/                        # User uploaded files
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🤖 AI Engine — Deep Dive

The AI engine lives in `apps/ai/` and is the **core intelligence layer** of Postulae. It is a modular, multi-model system responsible for CV analysis, scoring, optimization, content generation, cover letter creation, and document export.

### 📁 Full AI Engine Structure

```
apps/ai/
├── app/
│   ├── prompts/                        # All LLM prompt templates
│   │   ├── base_system.txt             # Global system prompt
│   │   ├── enrich_content.txt          # CV content enrichment instructions
│   │   ├── extract_from_pdf.txt        # PDF text extraction guidance
│   │   ├── extract_job_requirements.txt# Job offer parsing prompt
│   │   ├── generate_cover_letter.txt   # Cover letter generation prompt
│   │   ├── generate_cover_letter_json.txt # JSON-mode cover letter prompt
│   │   └── translate_cover_letter.txt  # EN/FR translation prompt
│   │
│   ├── templates/                      # HTML rendering templates
│   │   ├── cover_letter_template.html  # Cover letter HTML layout
│   │   └── grid_template.html          # CV grid-based HTML layout
│   │
│   ├── llm_client.py                   # OpenAI GPT client wrapper
│   ├── llm_client_anthropic.py         # Anthropic Claude client wrapper
│   │
│   ├── cv_grader.py                    # Text-based CV scoring engine
│   ├── cv_grader_vision.py             # Vision-based CV scoring (image/scanned)
│   │
│   ├── generator.py                    # Full CV generation pipeline
│   ├── enrichment.py                   # CV content enrichment logic
│   ├── content_analyzer.py             # Structural CV content analysis
│   ├── domain_detector.py              # Detects job domain/industry
│   │
│   ├── density.py                      # CV layout density calculator
│   ├── bullet_trimmer.py               # Bullet point length optimizer
│   ├── layout_legacy.py                # Legacy HTML layout engine
│   ├── layout_playwright.py            # Playwright-based HTML→PDF renderer
│   │
│   ├── cover_letter_generator.py       # Cover letter generation pipeline
│   ├── cover_letter_exporter.py        # Export to PDF/DOCX
│   ├── cover_letter_layout.py          # Cover letter HTML layout engine
│   ├── cover_letter_density.py         # Cover letter overflow prevention
│   │
│   ├── job_offer_extractor.py          # Extracts requirements from job posts
│   ├── models.py                       # Internal AI data models (Pydantic)
│   └── logger.py                       # Structured AI logging
│
└── docs/                               # AI engine documentation
    ├── COVER_LETTER_README.md
    ├── COVER_LETTER_INTEGRATION.md
    ├── COVER_LETTER_FIXES_2026_04_01.md
    ├── COVER_LETTER_BEST_PRACTICES.md
    ├── cover_letter_api.md
    └── JSON_MIGRATION_SUMMARY.md
```

---

### ⚙️ How the AI Engine Works

#### 1. 🧠 Dual LLM Client Architecture

The engine uses **two separate LLM clients** for different tasks:

| Client | File | Model | Primary Use |
|--------|------|-------|-------------|
| **Anthropic Claude** | `llm_client_anthropic.py` | Claude 3.x | CV analysis, scoring, structured feedback, cover letters |
| **OpenAI GPT** | `llm_client.py` | GPT-4o | CV content generation, enrichment, translation |

Both clients share a common interface and are orchestrated by the pipeline modules.

---

#### 2. 📊 CV Scoring Pipeline

```
User uploads CV (PDF/image)
        │
        ▼
  ┌─────────────────┐
  │  cv_grader.py   │  ← Text-based PDF analysis via Claude
  │  (text mode)    │
  └────────┬────────┘
           │  (if scanned/image CV)
           ▼
  ┌──────────────────────┐
  │  cv_grader_vision.py │  ← Vision model analysis
  │  (vision mode)       │
  └────────┬─────────────┘
           │
           ▼
     Structured Score
     (sections, global score,
      strengths, improvements)
```

**Scored dimensions include:**
- Contact & personal information completeness
- Work experience quality and quantification
- Education and certifications
- Skills relevance
- Formatting and readability
- ATS (Applicant Tracking System) compatibility

---

#### 3. 🚀 CV Generation & Optimization Pipeline

```
User data / existing CV
        │
        ▼
  domain_detector.py      ← Detects job domain (tech, finance, etc.)
        │
        ▼
  content_analyzer.py     ← Analyzes existing content structure
        │
        ▼
  enrichment.py           ← AI enriches bullet points & descriptions
        │
        ▼
  generator.py            ← Generates full structured CV (JSON)
        │
        ▼
  bullet_trimmer.py       ← Trims overlong bullets for layout fit
        │
        ▼
  density.py              ← Checks page density / overflow risk
        │
        ▼
  layout_playwright.py    ← Renders HTML template → PDF via Playwright
        │
        ▼
  Final CV (PDF + DOCX)
```

---

#### 4. 💌 Cover Letter Pipeline

```
User inputs: CV + Job Offer (text or URL)
        │
        ▼
  job_offer_extractor.py     ← Parses requirements, skills, tone from job post
        │
        ▼
  cover_letter_generator.py  ← Generates personalized cover letter (JSON mode)
        │
        ▼
  cover_letter_layout.py     ← Applies HTML template + styling
        │
        ▼
  cover_letter_density.py    ← Prevents text overflow on page
        │
        ▼
  cover_letter_exporter.py   ← Exports to PDF (Playwright) and DOCX
        │
        ▼
  Final Cover Letter (PDF + DOCX, EN or FR)
```

---

#### 5. 📝 Prompt Engineering

All LLM instructions are stored as external `.txt` files in `app/prompts/`, making them easy to iterate without code changes:

| Prompt File | Purpose |
|-------------|---------|
| `base_system.txt` | Global AI persona and constraints |
| `enrich_content.txt` | Instructions for improving CV bullet points |
| `extract_from_pdf.txt` | Structured PDF text extraction guidance |
| `extract_job_requirements.txt` | Parsing job offers into structured fields |
| `generate_cover_letter.txt` | Full cover letter generation instructions |
| `generate_cover_letter_json.txt` | JSON-mode output for programmatic handling |
| `translate_cover_letter.txt` | EN ↔ FR translation with tone preservation |

---

#### 6. 🖨️ Document Rendering

| Renderer | Technology | Output |
|----------|-----------|--------|
| **layout_playwright.py** | Playwright (headless Chromium) | PDF |
| **layout_legacy.py** | WeasyPrint (legacy fallback) | PDF |
| **cover_letter_exporter.py** | Playwright + python-docx | PDF + DOCX |
| **grid_template.html** | CSS Grid layout | CV HTML |
| **cover_letter_template.html** | Professional letter layout | Cover Letter HTML |

---

### 🛠️ AI Tech Stack Summary

| Component | Technology |
|-----------|-----------|
| **Primary AI (Analysis)** | Anthropic Claude 3.x |
| **Primary AI (Generation)** | OpenAI GPT-4o |
| **Fast Inference** | Groq |
| **Embeddings / RAG** | HuggingFace + ChromaDB |
| **Orchestration** | LangChain |
| **Vector Store** | ChromaDB 1.5.0 |
| **Semantic Models** | sentence-transformers 5.2.2 |
| **Deep Learning** | PyTorch 2.9.0 + Transformers 5.1.0 |
| **PDF Rendering** | Playwright (headless Chromium) |
| **Document Export** | python-docx |

---

## 🛠️ Full Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI 0.128.0 |
| **Database** | PostgreSQL (Neon Cloud) |
| **ORM** | SQLAlchemy 2.0 |
| **AI Engine** | Anthropic Claude + OpenAI GPT + Groq |
| **Authentication** | JWT + Google OAuth |
| **Payments** | Stripe (Subscriptions + Webhooks) |
| **Email** | SMTP (Gmail) |
| **Containerization** | Docker |
| **CI/CD** | GitHub Actions |
| **Web Server** | Nginx + Uvicorn |
| **Hosting** | Hostinger VPS (Ubuntu 24.04) |

---

## 💳 Stripe Payment Integration

Postulae uses **Stripe** for all billing and subscription management.

### How it works

1. **Checkout Session** — User selects a plan → Stripe hosted checkout page
2. **Webhook** — Stripe notifies backend on payment events (`checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`)
3. **Access Control** — Backend verifies active subscription before unlocking premium features
4. **Customer Portal** — Users can manage, upgrade, or cancel subscriptions directly

### Stripe Setup

```bash
# Install Stripe
pip install stripe

# Set your keys in .env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Webhook Testing (local)

```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8000/subscription/webhook
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL
- Docker (optional)
- Node.js (for Playwright PDF rendering)

### Local Development

```bash
# Clone the repository
git clone https://github.com/Latif1218/fafaselecto.git
cd fafaselecto

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the application
uvicorn apps.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

---

## ⚙️ Environment Variables

```env
# Database
SQLALCHEMY_DATABASE_URL=postgresql://user:password@host/dbname

# JWT
JWT_SECRET_KEY=your_secret_key

# AI APIs
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
HF_TOKEN=your_huggingface_token

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback

# Stripe
STRIPE_SECRET_KEY=your_stripe_secret
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable
STRIPE_WEBHOOK_SECRET=your_webhook_secret

# Domain
DOMAIN=https://yourdomain.com
```

---

## 🔄 CI/CD Pipeline

Every push to `main` branch automatically:

1. ✅ Builds Docker image
2. ✅ Pushes to Docker Hub
3. ✅ Deploys to VPS via SSH

```
git push origin main → GitHub Actions → Docker Hub → VPS 🚀
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | User registration |
| POST | `/auth/login` | User login |
| GET | `/auth/google` | Google OAuth |
| POST | `/cv/upload` | Upload CV |
| GET | `/cv/score` | Get AI CV score |
| POST | `/cv/optimize` | Optimize existing CV |
| POST | `/cv/generate` | Generate new CV |
| POST | `/cover-letter` | Generate cover letter |
| GET | `/subscription/plans` | Get available plans |
| POST | `/subscription/subscribe` | Create Stripe checkout |
| POST | `/subscription/webhook` | Stripe webhook handler |
| GET | `/admin/users` | Admin: list users |
| GET | `/admin/tutors` | Admin: list tutors |

---

## 🌍 Supported Languages

- 🇬🇧 **English**
- 🇫🇷 **French**

---

## 👨‍💻 Author

**Md. Abdul Latif Sumon**  
AI Engineer  
📧 mdsabdullotif@gmail.com  
📧 mdabdullatifdelta@gmail.com  
🔗 [GitHub](https://github.com/Latif1218)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

> *Postulae — Empowering job seekers with AI-driven career tools.*
