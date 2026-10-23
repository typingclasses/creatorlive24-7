# Invalid Facebook key via PUBLIC URL: expect 422 JSON friendly detail and no new history entry
import os, json, time, subprocess, urllib.request, requests
from dotenv import load_dotenv
load_dotenv("/app/backend/.env", override=True)
load_dotenv("/app/frontend/.env")
SK = os.environ["CLERK_SECRET_KEY"]
API = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"


def bapi(p, b):
    r = urllib.request.Request("https://api.clerk.com/v1" + p, data=json.dumps(b).encode(), method="POST",
                               headers={"Authorization": "Bearer " + SK, "Content-Type": "application/json", "User-Agent": "t"})
    return json.load(urllib.request.urlopen(r))


def listeners():
    out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    return [l.split()[3] for l in out.splitlines() if "127.0.0.1:" in l]


s = bapi("/sessions", {"user_id": "user_3L6hhploCiep0mzXWVPKBKQmMP8"})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 600})["jwt"]}
requests.post(f"{API}/streams/stop", headers=H)
requests.put(f"{API}/destinations", headers=H, json={"facebook": {"enabled": True, "url": "rtmps://live-api-s.facebook.com:443/rtmp", "key": "FB-invalid-123"},
                                                     "youtube": {"enabled": False, "url": "", "key": ""}})
vid = requests.get(f"{API}/videos", headers=H).json()[0]["id"]
h0 = requests.get(f"{API}/streams/history", headers=H).json()
first0 = h0[0]["id"] if h0 else None
print("history before", len(h0), first0)
l0 = listeners()
t0 = time.time()
r = requests.post(f"{API}/streams/video", headers=H, json={"video_id": vid, "loop": True, "quality": "720p", "fps": 30})
print("start", r.status_code, r.headers.get("content-type"), r.text[:400], f"{time.time()-t0:.1f}s")
st = requests.get(f"{API}/streams/status", headers=H).json()
print("status", st.get("live"), st.get("last_error"))
time.sleep(1)
print("new listeners after failed start", sorted(set(listeners()) - set(l0)))
h1 = requests.get(f"{API}/streams/history", headers=H).json()
print("history after", len(h1), "UNCHANGED" if (h1[0]["id"] if h1 else None) == first0 else "CHANGED", h1[:1])
requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": False, "url": "", "key": ""}, "facebook": {"enabled": False, "url": "", "key": ""}})
print("dest after cleanup", requests.get(f"{API}/destinations", headers=H).json())
