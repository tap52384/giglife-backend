# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import auth, credentials, initialize_app, firestore
from flask import Request
import firebase_admin
import json

# initialize_app()
# One-time init
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    initialize_app(cred)

# Provides shorthand access to the Firestore database
# and Firebase Authentication.
db = firestore.client()

# ---------------------------
# 🔐 Reusable Token Verifier
# ---------------------------

def verify_id_token_from_request(req: Request) -> dict:
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

    id_token = auth_header.split("Bearer ")[1]

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

    decoded_token = auth_result["decoded_token"]
    uid = decoded_token["uid"]
    phone = decoded_token.get("phone_number")
    email = decoded_token.get("email")

    # 🔍 Step 2: Look up the user in Firestore
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        # 🆕 Step 3: Create user if not found
        user_data = {
            "first_name": None,
            "last_name": None,
            "phone": phone,
            "email": email,
            "role": "trial",
            "created_at": firestore.SERVER_TIMESTAMP
        }
        user_ref.set(user_data)
        user_doc = user_ref.get()

    # ✅ Step 4: Return the user document
    return https_fn.Response(
        json.dumps(user_doc.to_dict()),
        status=200,
        mimetype="application/json"
    )
