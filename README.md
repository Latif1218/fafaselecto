# 🎯 Postulae — AI-Powered CV Optimization, generation and gidence Platform

[![Live](https://img.shields.io/badge/Live-postulae.com-brightgreen)](https://postulae.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF)](https://github.com/features/actions)

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

### 🚀 CV Optimization
- AI-optimized CV based on your existing document
- Tailored to job market standards
- Available in **English** and **French**

### 🤖 AI CV Generation
- Generate a brand new CV from provided information
- Professional formatting and layout
- Powered by **OpenAI** and **Anthropic Claude**

### 👨‍🏫 Tutor Support
- Connect with professional career tutors
- Personalized CV coaching sessions
- Admin dashboard for tutor management

### 💳 Subscription Plans
| Plan | Features |
|------|----------|
| **Starter** | CV scoring + basic optimization |
| **Premium** | Full CV optimization + new CV generation |
| **Ultimate** | Everything + personal tutor access |

---

## 🏗️ Project Structure

```
postulae/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── apps/
│   ├── ai/                     # AI engine (OpenAI + Anthropic)
│   ├── authentication/         # OAuth & auth logic
│   ├── models/                 # Database models
│   │   ├── cv_model.py
│   │   ├── users_model.py
│   │   ├── subs_model.py
│   │   ├── ultimate_request.py
│   │   └── forgot_password_m.py
│   ├── routers/                # API routes
│   │   ├── cv_router.py
│   │   ├── cover_letter.py
│   │   ├── cv_ultimate.py
│   │   ├── login_user.py
│   │   ├── register_users.py
│   │   ├── subscription.py
│   │   ├── tutor_register.py
│   │   ├── tutor_requests.py
│   │   ├── users.py
│   │   ├── admin_user.py
│   │   ├── admin_tutor_dashboard.py
│   │   ├── admin_ultimate_req.py
│   │   ├── forgot_password.py
│   │   └── conte_with_google.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── cv_schema.py
│   │   ├── users_schema.py
│   │   ├── cover_letter_schema.py
│   │   ├── subs_schema.py
│   │   ├── tutor_schema.py
│   │   └── ultimate_schema.py
│   ├── utils/                  # Utility functions
│   ├── config.py               # App configuration
│   ├── database.py             # Database connection
│   └── main.py                 # FastAPI app entry point
├── cv/                         # CV templates & storage
├── uploads/                    # User uploaded files
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI 0.128.0 |
| **Database** | PostgreSQL (Neon Cloud) |
| **ORM** | SQLAlchemy 2.0 |
| **AI Engine** | OpenAI GPT + Anthropic Claude |
| **Authentication** | JWT + Google OAuth |
| **Payments** | Stripe |
| **Email** | SMTP (Gmail) |
| **Containerization** | Docker |
| **CI/CD** | GitHub Actions |
| **Web Server** | Nginx + Uvicorn |
| **Hosting** | Hostinger VPS (Ubuntu 24.04) |

---

## 🤖 AI Engine

Postulae uses a **dual AI approach** for maximum accuracy:

- **Anthropic Claude** — CV analysis, scoring, and structured feedback
- **OpenAI GPT** — CV content generation and optimization
- **LangChain** — Orchestrating AI workflows
- **Groq** — Fast inference for real-time responses

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL
- Docker (optional)

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

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the application
uvicorn apps.main:app --reload
```

Visit `http://localhost:8000/docs` for the API documentation.

### Docker

```bash
# Build and run with Docker
docker build -t postulae .
docker run -p 8080:8080 --env-file .env postulae
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
| GET | `/cv/score` | Get CV score |
| POST | `/cv/optimize` | Optimize CV |
| POST | `/cv/generate` | Generate new CV |
| POST | `/cover-letter` | Generate cover letter |
| GET | `/subscription/plans` | Get plans |
| POST | `/subscription/subscribe` | Subscribe to plan |
| GET | `/admin/users` | Admin: list users |
| GET | `/admin/tutors` | Admin: list tutors |

Full API documentation available at `/docs` (Swagger UI).
🔗 **API Docs:** [https://postulae.com/docs](http://69.62.72.197:8080/docs) 
---

## 🌍 Supported Languages

- 🇬🇧 **English**
- 🇫🇷 **French**

---

## 👨‍💻 Author

**Md. Abdul Latif Sumon**  
AI Engineer  
📧 mdabdullatifdelta@gmail.com  
🔗 [GitHub](https://github.com/Latif1218)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

> *Postulae — Empowering job seekers with AI-driven career tools.*
python-dotenv==1.1.1





torch==2.9.0
transformers==5.1.0
sentence-transformers==5.2.2
chromadb==1.5.0
