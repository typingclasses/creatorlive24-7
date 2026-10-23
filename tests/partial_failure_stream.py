# Valid YouTube key + invalid Facebook key: expect platforms ['youtube'], failed_platforms ['facebook'], keys masked in log (public URL)
import os, json, time, urllib.request, requests
from dotenv import load_dotenv
load_dotenv("/app/backend/.env", override=True)
load_dotenv("/app/frontend/.env")
SK = os.environ["CLERK_SECRET_KEY"]
YT = os.environ["YOUTUBE_TEST_STREAM_KEY"].strip()
BAD = "FB-invalid-123"
API = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"


def bapi(p, b):
    r = urllib.request.Request("https://api.clerk.com/v1" + p, data=json.dumps(b).encode(), method="POST",
                               headers={"Authorization": "Bearer " + SK, "Content-Type": "application/json", "User-Agent": "t"})
    return json.load(urllib.request.urlopen(r))


def mask(t):
    return str(t).replace(YT, "<YTKEY>")


s = bapi("/sessions", {"user_id": "user_3L6hhploCiep0mzXWVPKBKQmMP8"})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 600})["jwt"]}
res = {}
try:
    requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": True, "url": "rtmp://a.rtmp.youtube.com/live2", "key": YT},
                                                         "facebook": {"enabled": True, "url": "rtmps://live-api-s.facebook.com:443/rtmp", "key": BAD}})
    vid = requests.get(f"{API}/videos", headers=H).json()[0]["id"]
    t0 = time.time()
    r = requests.post(f"{API}/streams/video", headers=H, json={"video_id": vid, "loop": True, "quality": "720p", "fps": 30})
    print("start", r.status_code, round(time.time() - t0, 1), mask(r.text)[:300])
    leaks = 0
    for i in range(int(os.environ.get("SECS", "20")) // 5):
        time.sleep(5)
        raw = requests.get(f"{API}/streams/status", headers=H).text
        st = json.loads(raw)
        if YT in raw or BAD in raw:
            leaks += 1
        print(f"t+{5*(i+1)}s live={st.get('live')} platforms={st.get('platforms')} failed={st.get('failed_platforms')}")
        print("   log:", mask(st.get("log")))
        res = st
        if not st.get("live"):
            break
    print("KEY_LEAK_POLLS", leaks)
    print("RESULT", res.get("platforms") == ["youtube"] and res.get("failed_platforms") == ["facebook"] and leaks == 0)
finally:
    print("stop", requests.post(f"{API}/streams/stop", headers=H).json())
    requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": False, "url": "", "key": ""}, "facebook": {"enabled": False, "url": "", "key": ""}})
    d = requests.get(f"{API}/destinations", headers=H).json()
    print("dest cleared", all(not d[p]["enabled"] and not d[p]["key"] for p in d))
