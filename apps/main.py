from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .database import Base, engine
from .models.users_model import User
from .models.cv_model import CV, CVForm, CoverLetter
from .models.ultimate_request import UltimateRequest
from .config import SESSION_SECRET_KEY
from .routers import register_users, login_user, admin_user, cv_router, users, form_and_to_cv, cv_ultimate, cover_letter, admin_ultimate_requests, tutor_requests, forgot_password, subscription, conte_with_google, tutor_register, admin_tutor_dashboard
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps')))


Base.metadata.create_all(bind=engine)

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)  
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:8000",
        "https://fafaseleto-frontend.vercel.app",
        "http://192.168.7.56:3000",
        "https://nonprinting-featherlight-leatrice.ngrok-free.dev",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(
    SessionMiddleware,
    secret_key = SESSION_SECRET_KEY,
    https_only = True,
    same_site="lax"
)


@app.get('/health', status_code=status.HTTP_200_OK)
def health():
    return HTTPException(
        status_code=status.HTTP_200_OK,
        detail="API is healthy and running correctly.",
        headers={"POSTULAE Healthcheack": "healthy"}
    )


app.include_router(register_users.router)
app.include_router(conte_with_google.router)
app.include_router(login_user.router)
app.include_router(forgot_password.router)
app.include_router(subscription.router)
app.include_router(users.router)
app.include_router(admin_user.router)
app.include_router(admin_tutor_dashboard.router)
app.include_router(cv_router.router)
app.include_router(form_and_to_cv.router)
app.include_router(cv_ultimate.router)
app.include_router(cover_letter.router)
app.include_router(admin_ultimate_requests.router)
app.include_router(tutor_register.router)
app.include_router(tutor_requests.router)