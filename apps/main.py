from fastapi import FastAPI, status, HTTPException
from .database import Base, engine
from .models.users_model import User
from .models.cv_model import CV, CVForm, CoverLetter
from .models.ultimate_request import UltimateRequest
from .routers import register_users, login_user, admin_user, cv_router, users, form_and_to_cv, cv_ultimate, cover_letter
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps')))


Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get('/health', status_code=status.HTTP_200_OK)
def health():
    return HTTPException(
        status_code=status.HTTP_200_OK,
        detail="API is healthy and running correctly.",
        headers={"Iron_Ready Healthcheack": "healthy"}
    )


app.include_router(register_users.router)
app.include_router(login_user.router)
app.include_router(users.router)
app.include_router(admin_user.router)
app.include_router(cv_router.router)
app.include_router(form_and_to_cv.router)
app.include_router(cv_ultimate.router)
app.include_router(cover_letter.router)