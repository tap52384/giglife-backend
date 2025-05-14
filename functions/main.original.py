# functions/main.py
from firebase_functions import https_fn
from firebase_admin import auth, credentials, initialize_app, firestore
from flask import Request, abort
import firebase_admin
import functions_framework
import json
import re

# initialize_app()
# One-time init
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    initialize_app(cred)

# Provides shorthand access to the Firestore database
# and Firebase Authentication.
db = firestore.client()

def is_valid_email(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return len(digits) == 10

def normalize_gmail(email: str) -> str:
    """Normalize Gmail address by removing dots and plus aliases."""
    if not email or not is_valid_email(email):
        return ""
    local, domain = email.lower().strip().split("@")
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split('+')[0].replace('.', '')
        return f"{local}@{domain}"
    return email.lower()

# ---------------------------
# 🔐 Reusable Token Verifier
# ---------------------------

def verify_id_token_from_request(req: https_fn.Request) -> dict:
    """
    Extracts and verifies the Firebase ID token from the Authorization header.

    Returns a dict with:
      - decoded_token: dict if verified, else None
      - error: error message string or None
      - http_status: HTTP status code (200 if valid, 401/403 if not)
    """
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {
            "decoded_token": None,
            "error": "Missing or malformed Authorization header",
            "http_status": 401
        }

    id_token = auth_header.split("Bearer ")[1].strip()

    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            "decoded_token": decoded_token,
            "error": None,
            "http_status": 200
        }
    except Exception as e:
        return {
            "decoded_token": None,
            "error": f"Invalid token: {str(e)}",
            "http_status": 401
        }

# --- Endpoint function definitions ---
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello world!")

# --- Routing table ---

ROUTES = {
    "/on_request_example": {
        "handler": on_request_example,
        "methods": ["GET", "POST"]
    },
    "/api/on_request_example": {
        "handler": on_request_example,
        "methods": ["GET", "POST"]
    },
}

@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    path = req.path # like "/api/on_request_example"
    method = req.method # like "GET", "POST", etc.

    handler = ROUTES.get(path)
    if handler and method in handler.get("methods", []):
        return handler.get("handler")(req)

    return https_fn.Response(f"No route found for {path} with method {method}", status=404)

# ---------------------------
# 🔧 Register or Retrieve User
# ---------------------------

@https_fn.on_request()
def register_user(req: Request) -> https_fn.Response:
    """
    Cloud Function to register or retrieve a user after Firebase Authentication.
    - Verifies the Firebase ID token from the request
    - Checks Firestore for an existing user document
    - Creates a new document if the user is new
    - Returns the user document as JSON
    """

    # 🔐 Step 1: Verify the token
    auth_result = verify_id_token_from_request(req)
    if auth_result["error"]:
        return https_fn.Response(
            auth_result["error"],
            status=auth_result["http_status"]
        )

    decoded_token = auth_result.get("decoded_token")
    uid = decoded_token.get("uid")
    phone = decoded_token.get("phone_number")
    email = decoded_token.get("email")

    if not uid:
        return https_fn.Response("Missing UID in token", status=400)

    # 🔍 Step 2: Look up the user in Firestore
    user_ref = db.collection("users")
    user_doc = user_ref.document(uid).get()

    # Existing user – allow to proceed
    if user_doc.exists:
        return https_fn.Response(json.dumps(user_doc.to_dict()), status=200, content_type="application/json")
    
    # Stop here if both email and phone are missing
    if not email and not phone:
        return https_fn.Response("Unable to determine login method", status=400)
    
    

    # User does not exist yet, check if we have enough info
    if not email or not phone:
        return https_fn.Response(
            {
                "error": "Missing email or phone number",
                "requires_additional_verification": True,
                "needs": "phone" if not phone else "email"
            },
            status=200
        )

    # Normalize Gmail
    email_normalized = normalize_gmail(email)

    # Create a new user in Firebase Authentication
    new_user = {
        "uid": uid,
        "email_entered": email,
        "email_normalized": email_normalized,
        "phone": phone,
        "role": "trial",
        "created_at": firestore.SERVER_TIMESTAMP,
        "first_name": None,
        "last_name": None
    }

    user_ref.document(uid).set(new_user)

    # Check if the user document was created successfully
    user_doc = user_ref.document(uid).get()

    if user_doc.exists:
        # User document was created successfully
        return https_fn.Response(
            new_user,
            status=200,
            mimetype="application/json"
        )

    return https_fn.Response(
        {
            "error": "Failed to create user account, try again",
            "requires_additional_verification": True,
        },
        status=500
    )
