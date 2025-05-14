# functions/main.py
from firebase_functions import https_fn
from firebase_admin import auth, initialize_app, firestore
from utils import get_id_token, normalize_gmail, is_valid_email, is_valid_phone
import json

initialize_app()
db = firestore.client()

@https_fn.on_request()
def register_user(request: https_fn.Request) -> https_fn.Response:
    # Validate token and enforce 5-minute expiry for registration
    try:
        decoded_token = get_id_token(request, max_age_minutes=5)
    except ValueError as e:
        return https_fn.Response(
            json.dumps({"error": str(e), "action": "signout_and_redirect"}),
            status=401,
            content_type="application/json"
        )

    uid = decoded_token.get("uid")
    firebase_email = decoded_token.get("email")
    firebase_phone = decoded_token.get("phone_number")
    email_verified = decoded_token.get("email_verified", False)

    if not uid:
        return https_fn.Response("Missing UID in token", status=400)

    users_ref = db.collection("users")
    user_doc = users_ref.document(uid).get()

    # If user already exists, return it
    if user_doc.exists:
        return https_fn.Response(json.dumps(user_doc.to_dict()), status=200, content_type="application/json")

    # Collect missing contact method from UI input
    data = request.get_json(silent=True) or {}
    input_email = data.get("email")
    input_phone = data.get("phone")

    # Determine login method and validate second method
    if firebase_email:
        if not is_valid_phone(input_phone):
            return https_fn.Response(
                json.dumps({
                    "requires_additional_verification": True,
                    "missing": ["phone"],
                    "message": "Valid 10-digit phone number required."
                }),
                status=200,
                content_type="application/json"
            )
        email_entered = firebase_email
        email_validated = email_verified
        phone_entered = input_phone
        phone_validated = False

    elif firebase_phone:
        if not is_valid_email(input_email):
            return https_fn.Response(
                json.dumps({
                    "requires_additional_verification": True,
                    "missing": ["email"],
                    "message": "Valid email address required."
                }),
                status=200,
                content_type="application/json"
            )
        email_entered = input_email
        email_validated = False
        phone_entered = firebase_phone
        phone_validated = True

    else:
        return https_fn.Response("Unable to determine login method.", status=400)

    email_normalized = normalize_gmail(email_entered)

    new_user = {
        "uid": uid,
        "email_entered": email_entered,
        "email_normalized": email_normalized,
        "email_validated": email_validated,
        "phone": phone_entered,
        "phone_validated": phone_validated,
        "role": "trial",
        "first_name": None,
        "last_name": None
    }

    users_ref.document(uid).set(new_user)

    return https_fn.Response(json.dumps(new_user), status=200, content_type="application/json")
