import json
import os
import urllib.parse
import urllib.request

import pytest
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


# Clerk Backend API helper (secret never printed)
def bapi(path, body=None, method="POST"):
    req = urllib.request.Request("https://api.clerk.com/v1" + path, data=json.dumps(body).encode() if body else None,
                                 method=method, headers={"Authorization": "Bearer " + os.environ["CLERK_SECRET_KEY"],
                                                         "Content-Type": "application/json", "User-Agent": "emergent-test"})
    return json.load(urllib.request.urlopen(req))


def make_user(email):
    users = bapi(f"/users?email_address={urllib.parse.quote(email)}", method="GET")
    user = users[0] if users else bapi("/users", {"email_address": [email], "password": "Test-pass-12345!",
                                                  "skip_password_checks": True})
    sess = bapi("/sessions", {"user_id": user["id"]})
    return user, sess


def token_for(sess):
    return bapi(f"/sessions/{sess['id']}/tokens", {"expires_in_seconds": 1200})["jwt"]


@pytest.fixture(scope="session")
def user_a():
    user, sess = make_user("creator+clerk_test@example.com")
    return {"user": user, "headers": {"Authorization": f"Bearer {token_for(sess)}"}}


@pytest.fixture(scope="session")
def user_b():
    user, sess = make_user("creator2+clerk_test@example.com")
    return {"user": user, "headers": {"Authorization": f"Bearer {token_for(sess)}"}}
