# Prep for watermark UI test: local RTMP dest + TEST video for creator; mode: free|paid|off|restore. Prints VID + TICKET
import sys, subprocess, requests, imageio_ffmpeg
sys.path.insert(0, '/app/backend/tests')
from conftest import bapi, make_user, token_for, API
FF = imageio_ffmpeg.get_ffmpeg_exe()
mode = sys.argv[1]
u, s = make_user("creator+clerk_test@example.com")
H = {"Authorization": "Bearer " + token_for(s)}
_, asess = make_user("admin+clerk_test@example.com")
AH = {"Authorization": "Bearer " + token_for(asess)}
st = requests.get(f"{API}/settings").json()
plan = requests.get(f"{API}/plans").json()[0]
requests.patch(f"{API}/admin/users/{u['id']}", json={"plan_id": plan["id"] if mode == "paid" else ""}, headers=AH)
requests.put(f"{API}/admin/settings", headers=AH, json={**st, "watermark_enabled": mode != "off"})
if mode == "restore":
    for v in requests.get(f"{API}/videos", headers=H).json():
        if v["title"].startswith("TEST_ui_wm"):
            requests.delete(f"{API}/videos/{v['id']}", headers=H)
    print("restored", requests.get(f"{API}/settings").json()["watermark_enabled"], requests.get(f"{API}/me", headers=H).json()["plan_valid"])
    sys.exit()
requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": True, "url": "rtmp://127.0.0.1:1935/live2", "key": "testkey"},
                                                     "facebook": {"enabled": False, "url": "", "key": ""}})
vids = [v for v in requests.get(f"{API}/videos", headers=H).json() if v["title"].startswith("TEST_ui_wm")]
if not vids:
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30", "-f", "lavfi", "-i", "sine",
                    "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "/tmp/ui_wm.mp4"], check=True)
    vids = [requests.post(f"{API}/videos", headers=H, files={"file": ("TEST_ui_wm.mp4", open("/tmp/ui_wm.mp4", "rb"), "video/mp4")}).json()]
print("VID", vids[0]["id"])
print("TICKET", bapi("/sign_in_tokens", {"user_id": u["id"], "expires_in_seconds": 3600})["token"])
