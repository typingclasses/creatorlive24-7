# Prep for UI test: point test user's youtube dest at a given rtmp url, print sign-in ticket + first video id
import sys, requests
sys.path.insert(0, '/app/backend/tests')
from conftest import bapi
UID = "user_3L6hhploCiep0mzXWVPKBKQmMP8"
API = "http://localhost:8001/api"
s = bapi("/sessions", {"user_id": UID})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 600})["jwt"]}
url, key = sys.argv[1], sys.argv[2]
enabled = url != "none"
requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": enabled, "url": url if enabled else "", "key": key if enabled else ""},
                                                     "facebook": {"enabled": False, "url": "", "key": ""}})
print("VID", requests.get(f"{API}/videos", headers=H).json()[0]["id"])
print("TICKET", bapi("/sign_in_tokens", {"user_id": UID, "expires_in_seconds": 3600})["token"])
