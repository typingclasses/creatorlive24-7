import os, json, math, subprocess, sys, urllib.request, requests, imageio_ffmpeg
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
SK = os.environ["CLERK_SECRET_KEY"]
API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
FF = imageio_ffmpeg.get_ffmpeg_exe()


def bapi(p, b):
    r = urllib.request.Request("https://api.clerk.com/v1" + p, data=json.dumps(b).encode(), method="POST",
                               headers={"Authorization": "Bearer " + SK, "Content-Type": "application/json", "User-Agent": "t"})
    return json.load(urllib.request.urlopen(r))


s = bapi("/sessions", {"user_id": "user_3L6hhploCiep0mzXWVPKBKQmMP8"})
H = {"Authorization": "Bearer " + bapi(f"/sessions/{s['id']}/tokens", {"expires_in_seconds": 3600})["jwt"]}


def make(path, size, secs, rate):
    if not os.path.exists(path):
        subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30", "-f", "lavfi", "-i", "sine",
                        "-t", str(secs), "-c:v", "libx264", "-preset", "ultrafast", "-b:v", rate, "-c:a", "aac", path], check=True)


def upload(path):
    size = os.path.getsize(path)
    init = requests.post(f"{API}/uploads", headers=H, json={"filename": os.path.basename(path), "size": size, "content_type": "video/mp4"}).json()
    cs = init["chunk_size"]
    with open(path, "rb") as f:
        for i in range(math.ceil(size / cs)):
            r = requests.put(f"{API}/uploads/{init['upload_id']}/chunks/{i}", headers={**H, "Content-Type": "application/octet-stream"}, data=f.read(cs))
            assert r.status_code == 200, (i, r.status_code, r.text[:200])
    return requests.post(f"{API}/uploads/{init['upload_id']}/complete", headers=H).json()


make("/tmp/long.mp4", "1280x720", 360, "4M")
make("/tmp/short.mp4", "720x1280", 20, "1M")
print("long size MB", os.path.getsize("/tmp/long.mp4") // 1e6)
for p in ("/tmp/long.mp4", "/tmp/short.mp4"):
    d = upload(p)
    print(p, {k: d.get(k) for k in ("id", "format", "duration", "width", "height", "size")})
