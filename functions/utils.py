# functions/utils.py
import re
import time
from firebase_admin import auth
from firebase_functions import https_fn


def is_valid_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return len(digits) == 10


def normalize_gmail(email: str) -> str:
    if not email:
        return ""
    local, domain = email.lower().split("@")
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split('+')[0].replace('.', '')
        return f"{local}@{domain}"
    return email.lower()


def get_id_token(request: https_fn.Request, max_age_minutes: int = None) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise ValueError("Missing or invalid Authorization header")

    id_token = auth_header.split("Bearer ")[-1].strip()
    decoded_token = auth.verify_id_token(id_token)

    if max_age_minutes:
        iat = decoded_token.get("iat")
        now = int(time.time())
        max_age_seconds = max_age_minutes * 60
        if not iat or now - iat > max_age_seconds:
            raise ValueError("Token expired. Please sign in again.")

    return decoded_token
