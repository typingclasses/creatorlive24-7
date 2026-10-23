# UI prep for partial-failure test: YT valid key + FB invalid key; prints VID + TICKET (keys never printed). Arg "clear" resets destinations.
import os, sys, requests
sys.path.insert(0, '/app/backend/tests')
from dotenv import load_dotenv
load_dotenv("/app/backend/.env", override=True)
from conftest import bapi
UID = "user_3L6hhploCiep0mzXWVPKBKQmMP8"
API = "http://localhost:8001/api"
s = bapi("/sessions", {"user_id": UID})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 600})["jwt"]}
if len(sys.argv) > 1 and sys.argv[1] == "clear":
    requests.post(f"{API}/streams/stop", headers=H)
    requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": False, "url": "", "key": ""}, "facebook": {"enabled": False, "url": "", "key": ""}})
    d = requests.get(f"{API}/destinations", headers=H).json()
    print("cleared", all(not d[p]["enabled"] and not d[p]["key"] for p in d), "live", requests.get(f"{API}/streams/status", headers=H).json().get("live"))
else:
    requests.put(f"{API}/destinations", headers=H, json={
        "youtube": {"enabled": True, "url": "rtmp://a.rtmp.youtube.com/live2", "key": os.environ["YOUTUBE_TEST_STREAM_KEY"].strip()},
        "facebook": {"enabled": True, "url": "rtmps://live-api-s.facebook.com:443/rtmp", "key": "FB-invalid-123"}})
    print("VID", requests.get(f"{API}/videos", headers=H).json()[0]["id"])
    print("TICKET", bapi("/sign_in_tokens", {"user_id": UID, "expires_in_seconds": 3600})["token"])
