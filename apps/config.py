import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")


EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URL = os.getenv("GOOGLE_AUTH_URL")
GOOGLE_TOKEN_URL = os.getenv("GOOGLE_TOKEN_URL")
GOOGLE_USERINFO_URL = os.getenv("GOOGLE_USERINFO_URL")


STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY")
PRICE_IDS=os.getenv("PRICE_IDS")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET")
DOMAIN=os.getenv("DOMAIN")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", f"{DOMAIN}/payment/success")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", f"{DOMAIN}/payment/cancel")


GROQ_API_KEY=os.getenv("GROQ_API_KEY")
HF_TOKEN=os.getenv("HF_TOKEN")

EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exercises.csv")


groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)



