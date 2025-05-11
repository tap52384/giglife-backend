# giglife-backend

The backend for joingiglife.com.

## Firebase

### Functions

```bash
# Run this command to setup Firebase Functions, which is needed to run the backend code
firebase init functions

# To test your code locally, Firebase provides emulators.
# To test our Python code running in a function, use the "functions" emulator
# To test the rewrites so that our function endpoints can be accessed with the "/api/**" prefix
# defined in firebase.json, we need to start the "hosting" emulator as well.
firebase emulators:start --only hosting,functions

# Since this is the backend, ONLY deploy functions
# 2025/05/04 - You can deploy functions,hosting, and anything else from the frontend repo only
# since the firebase.json references the backend repo for functions.
firebase deploy --only functions
```

To get started, I ran the commands above. When using `firebase init functions`, I chose **Python**
as my language.

I also allowed `firebase.json` to be committed since it will not contain sensitive information.

In `functions/main.py`, I uncommented the code that it recommended, which created at least one endpoint
for me to test. This is the contents of `functions.main.py`:

```python
# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import auth, credentials, initialize_app, firestore
import firebase_admin

# initialize_app()
# One-time init
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    initialize_app(cred)

@https_fn.on_request()
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello world!")
```

#### Adding packages to requirements.txt

When you add a package to `requirements.txt`, remember that in the `functions` folder there is a
`venv` folder for the virtualenv. If you activate that virtualenv, you can do the following:

```bash
source ./venv/bin/activate
pip install -r requirements.txt
deactivate
```

#### What your backend is for

| Task  | Done by Frontend? | Done by Backend? |
| ----- | ----------------- | ---------------- |
| Send code to phone/email | ✅ Yes | ❌ No |
| Validate verification code | ✅ Yes | ❌ No |
| Authenticate user | ✅ Yes | ❌ No |
| Get ID token | ✅ Yes | ❌ No |
| Verify token | ❌ No | ✅ Yes |
| Create Firestore user doc | ❌ No | ✅ Yes |
| Assign role / enforce access | ❌ No | ✅ Yes |
