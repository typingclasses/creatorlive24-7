# Real stream to YouTube + Facebook simultaneously (keys from backend/.env, never printed)
import os, json, time, urllib.request, requests
from dotenv import load_dotenv
load_dotenv("/app/backend/.env", override=True)
SK = os.environ["CLERK_SECRET_KEY"]
YT, FB = os.environ["YOUTUBE_TEST_STREAM_KEY"].strip(), os.environ["FACEBOOK_TEST_STREAM_KEY"].strip()
API = "http://localhost:8001/api"


def mask(t):
    return str(t).replace(YT, "***").replace(FB, "***")


def bapi(p, b):
    r = urllib.request.Request("https://api.clerk.com/v1" + p, data=json.dumps(b).encode(), method="POST",
                               headers={"Authorization": "Bearer " + SK, "Content-Type": "application/json", "User-Agent": "t"})
    return json.load(urllib.request.urlopen(r))


s = bapi("/sessions", {"user_id": "user_3L6hhploCiep0mzXWVPKBKQmMP8"})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 600})["jwt"]}
try:
    requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": True, "url": "rtmp://a.rtmp.youtube.com/live2", "key": YT},
                                                         "facebook": {"enabled": True, "url": "rtmps://live-api-s.facebook.com:443/rtmp", "key": FB}})
    vid = requests.get(f"{API}/videos", headers=H).json()[0]["id"]
    r = requests.post(f"{API}/streams/video", headers=H, json={"video_id": vid, "loop": True, "quality": "720p", "fps": 30})
    print("start", r.status_code, mask(r.text)[:300])
    for _ in range(int(os.environ.get("SECS", "30")) // 10):
        time.sleep(10)
        st = requests.get(f"{API}/streams/status", headers=H).json()
        print("status", st.get("live"), st.get("platforms"), mask(st.get("log") or st.get("last_error"))[-250:], flush=True)
        if not st.get("live"):
            break
finally:
    print("stop", requests.post(f"{API}/streams/stop", headers=H).json())
    requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": False, "url": "", "key": ""}, "facebook": {"enabled": False, "url": "", "key": ""}})
    d = requests.get(f"{API}/destinations", headers=H).json()
    print("dest cleared", all(not d[p]["enabled"] and not d[p]["key"] for p in d))
