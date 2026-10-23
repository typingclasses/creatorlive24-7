import os, json, time, subprocess, urllib.request, requests, imageio_ffmpeg
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
SK = os.environ["CLERK_SECRET_KEY"]
API = "http://localhost:8001/api"
FF = imageio_ffmpeg.get_ffmpeg_exe()


def bapi(path, body=None, method="POST"):
    req = urllib.request.Request("https://api.clerk.com/v1" + path, data=json.dumps(body).encode() if body else None, method=method,
                                 headers={"Authorization": "Bearer " + SK, "Content-Type": "application/json", "User-Agent": "emergent-test"})
    return json.load(urllib.request.urlopen(req))


email = "creator+clerk_test@example.com"
users = bapi(f"/users?email_address={email}", method="GET")
user = users[0] if users else bapi("/users", {"email_address": [email], "password": "Test-pass-12345!", "skip_password_checks": True})
sess = bapi("/sessions", {"user_id": user["id"]})
tok = lambda: bapi(f"/sessions/{sess['id']}/tokens", {"expires_in_seconds": 600})["jwt"]
H = {"Authorization": f"Bearer {tok()}"}

subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30", "-f", "lavfi", "-i", "sine",
                "-t", "5", "-c:v", "libx264", "-c:a", "aac", "/tmp/t.mp4"], check=True)
listener = subprocess.Popen([FF, "-loglevel", "error", "-listen", "1", "-i", "rtmp://127.0.0.1:1935/live2/testkey", "-f", "null", "-"])
time.sleep(1)
print(requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": True, "url": "rtmp://127.0.0.1:1935/live2", "key": "testkey"},
                                                           "facebook": {"enabled": False, "url": "", "key": ""}}).status_code)
v = requests.post(f"{API}/videos", headers=H, files={"file": ("t.mp4", open("/tmp/t.mp4", "rb"), "video/mp4")}).json()
print("upload", v.get("id"))
print("list", len(requests.get(f"{API}/videos", headers=H).json()))
print("start", requests.post(f"{API}/streams/video", headers=H, json={"video_id": v["id"], "loop": True}).json())
time.sleep(8)
print("status", requests.get(f"{API}/streams/status", headers=H).json())
print("stop", requests.post(f"{API}/streams/stop", headers=H).json())
print("history", len(requests.get(f"{API}/streams/history", headers=H).json()))
listener.kill()
print("TOKEN_USER", user["id"])
