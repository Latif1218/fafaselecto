import secrets
from urllib.parse import urlencode
from ..config import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, GOOGLE_AUTH_URL


def get_google_oauth_url(state: str = None):
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state or secrets.token_urlsafe(32),
        "prompt": "select_ account consent"
    }

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"