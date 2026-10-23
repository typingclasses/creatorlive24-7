import os, json, time, urllib.request, requests
from dotenv import load_dotenv
load_dotenv("/app/backend/.env", override=True)
SK, KEY = os.environ["CLERK_SECRET_KEY"], os.environ["FACEBOOK_TEST_STREAM_KEY"].strip()
API = "http://localhost:8001/api"


def bapi(p, b):
    r = urllib.request.Request("https://api.clerk.com/v1" + p, data=json.dumps(b).encode(), method="POST",
                               headers={"Authorization": "Bearer " + SK, "Content-Type": "application/json", "User-Agent": "t"})
    return json.load(urllib.request.urlopen(r))


s = bapi("/sessions", {"user_id": "user_3L6hhploCiep0mzXWVPKBKQmMP8"})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 600})["jwt"]}
requests.put(f"{API}/destinations", headers=H, json={"facebook": {"enabled": True, "url": "rtmps://live-api-s.facebook.com:443/rtmp", "key": KEY},
                                                     "youtube": {"enabled": False, "url": "", "key": ""}})
vid = requests.get(f"{API}/videos", headers=H).json()[0]["id"]
r = requests.post(f"{API}/streams/video", headers=H, json={"video_id": vid, "loop": True, "quality": "720p", "fps": 30})
print("start", r.status_code, r.text.replace(KEY, "***")[:300])
for _ in range(int(os.environ.get("SECS", "150")) // 15):
    time.sleep(15)
    st = requests.get(f"{API}/streams/status", headers=H).json()
    print("status", st.get("live"), str(st.get("log") or st.get("last_error"))[-200:].replace(KEY, "***"), flush=True)
    if not st.get("live"):
        break
print("stop", requests.post(f"{API}/streams/stop", headers=H).json())
requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": False, "url": "", "key": ""}, "facebook": {"enabled": False, "url": "", "key": ""}})
