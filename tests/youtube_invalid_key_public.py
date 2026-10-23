# Invalid YouTube key via PUBLIC URL: expect 422 JSON friendly detail and no new history entry
import os, json, time, subprocess, urllib.request, requests
from dotenv import load_dotenv
load_dotenv("/app/backend/.env", override=True)
SK = os.environ["CLERK_SECRET_KEY"]
API = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"


def bapi(p, b):
    r = urllib.request.Request("https://api.clerk.com/v1" + p, data=json.dumps(b).encode(), method="POST",
                               headers={"Authorization": "Bearer " + SK, "Content-Type": "application/json", "User-Agent": "t"})
    return json.load(urllib.request.urlopen(r))


def listeners():
    out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if "127.0.0.1:" in l]


s = bapi("/sessions", {"user_id": "user_3L6hhploCiep0mzXWVPKBKQmMP8"})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 600})["jwt"]}
requests.post(f"{API}/streams/stop", headers=H)
requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": True, "url": "rtmp://a.rtmp.youtube.com/live2", "key": "invalid-key-123"},
                                                     "facebook": {"enabled": False, "url": "", "key": ""}})
vid = requests.get(f"{API}/videos", headers=H).json()[0]["id"]
h0 = len(requests.get(f"{API}/streams/history", headers=H).json()); print("history before", h0)
t0 = time.time()
r = requests.post(f"{API}/streams/video", headers=H, json={"video_id": vid, "loop": True, "quality": "720p", "fps": 30})
print("start", r.status_code, r.text[:400], f"{time.time()-t0:.1f}s")
print("listeners after start", listeners())
for i in range(6):
    st = requests.get(f"{API}/streams/status", headers=H).json()
    print("status", i, st.get("live"), str(st.get("last_error") or st.get("log"))[-300:])
    if not st.get("live"):
        break
    time.sleep(5)
print("stop", requests.post(f"{API}/streams/stop", headers=H).json())
time.sleep(1)
print("listeners after stop", listeners())
hist = requests.get(f"{API}/streams/history", headers=H).json()
print("history after", len(hist), "unchanged" if len(hist)==h0 else "CHANGED", hist[:1])
requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": False, "url": "", "key": ""}, "facebook": {"enabled": False, "url": "", "key": ""}})
