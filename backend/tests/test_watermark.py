# Watermark (CreatorLive24/7 logo burned into live stream) tests: free vs paid vs admin toggle, video + WS paths.
# Run alone (not with xdist in parallel with other stream tests): pytest backend/tests/test_watermark.py -p no:xdist
import asyncio
import os
import subprocess
import time

import imageio_ffmpeg
import pytest
import requests
import websockets
from PIL import Image

from conftest import API, BASE_URL, make_user, token_for

FF = imageio_ffmpeg.get_ffmpeg_exe()
ADMIN_EMAIL = "admin+clerk_test@example.com"
RTMP = "rtmp://127.0.0.1:1935/live2/testkey"


@pytest.fixture(scope="module")
def admin_h():
    _, sess = make_user(ADMIN_EMAIL)
    return {"Authorization": f"Bearer {token_for(sess)}"}


@pytest.fixture(scope="module")
def setup(user_a, admin_h):
    h = user_a["headers"]
    uid = user_a["user"]["id"]
    dest_before = requests.get(f"{API}/destinations", headers=h).json()
    requests.put(f"{API}/destinations", headers=h, json={"youtube": {"enabled": True, "url": "rtmp://127.0.0.1:1935/live2", "key": "testkey"},
                                                          "facebook": {"enabled": False, "url": "", "key": ""}})
    # solid blue clip so the logo stands out
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=blue:size=1280x720:rate=30", "-f", "lavfi",
                    "-i", "sine", "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "/tmp/wm_blue.mp4"], check=True)
    v = requests.post(f"{API}/videos", headers=h, files={"file": ("TEST_wm.mp4", open("/tmp/wm_blue.mp4", "rb"), "video/mp4")}).json()
    requests.patch(f"{API}/admin/users/{uid}", json={"plan_id": ""}, headers=admin_h)
    requests.put(f"{API}/admin/settings", headers=admin_h, json={**requests.get(f"{API}/settings").json(), "watermark_enabled": True})
    yield {"vid": v["id"], "h": h, "uid": uid}
    requests.post(f"{API}/streams/stop", headers=h)
    requests.delete(f"{API}/videos/{v['id']}", headers=h)
    requests.patch(f"{API}/admin/users/{uid}", json={"plan_id": ""}, headers=admin_h)
    requests.put(f"{API}/admin/settings", headers=admin_h, json={**requests.get(f"{API}/settings").json(), "watermark_enabled": True})
    requests.put(f"{API}/destinations", headers=h, json={k: dest_before[k] for k in ("youtube", "facebook")})


def record_stream(setup, name):
    """Start listener recording, start video stream, return (status, frame image)."""
    h = setup["h"]
    requests.post(f"{API}/streams/stop", headers=h)
    out = f"/tmp/{name}.flv"
    if os.path.exists(out):
        os.remove(out)
    rec = subprocess.Popen([FF, "-y", "-loglevel", "error", "-listen", "1", "-i", RTMP, "-t", "12", "-c", "copy", out])
    time.sleep(1)
    try:
        r = requests.post(f"{API}/streams/video", headers=h, json={"video_id": setup["vid"], "loop": True, "quality": "720p"})
        assert r.status_code == 200, r.text
        time.sleep(3)
        st = requests.get(f"{API}/streams/status", headers=h).json()
        rec.wait(timeout=20)
    finally:
        rec.kill()
        requests.post(f"{API}/streams/stop", headers=h)
    png = f"/tmp/{name}.png"
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "3", "-i", out, "-frames:v", "1", png], check=True)
    return st, Image.open(png).convert("RGB")


def logo_present(img):
    """Top-left region (logo area) deviates from solid blue; bottom-right stays blue."""
    w, h = img.size
    def non_blue(box):
        px = list(img.crop(box).getdata())
        return sum(1 for r, g, b in px if not (b > 150 and r < 80 and g < 80)) / len(px)
    tl = non_blue((0, 0, int(w * 0.3), int(h * 0.12)))
    br = non_blue((int(w * 0.7), int(h * 0.88), w, h))
    print(f"size={img.size} top-left non-blue={tl:.3f} bottom-right non-blue={br:.3f}")
    assert br < 0.01
    return tl > 0.03


class TestWatermark:
    def test_public_settings_expose_flag(self):
        assert requests.get(f"{API}/settings").json()["watermark_enabled"] is True

    def test_non_admin_cannot_change(self, user_a):
        s = requests.get(f"{API}/settings").json()
        r = requests.put(f"{API}/admin/settings", headers=user_a["headers"], json={**s, "watermark_enabled": False})
        assert r.status_code == 403
        assert requests.get(f"{API}/settings").json()["watermark_enabled"] is True

    def test_free_user_has_logo(self, setup):
        st, img = record_stream(setup, "wm_free")
        assert st["live"] is True and st["watermark"] is True, st
        img.save("/tmp/wm_free_frame.png")
        assert img.size == (1280, 720)
        assert logo_present(img)

    def test_paid_user_no_logo(self, setup, admin_h):
        plan = requests.get(f"{API}/plans").json()[0]
        r = requests.patch(f"{API}/admin/users/{setup['uid']}", json={"plan_id": plan["id"]}, headers=admin_h)
        assert r.status_code == 200
        assert requests.get(f"{API}/me", headers=setup["h"]).json()["plan_valid"] is True
        try:
            st, img = record_stream(setup, "wm_paid")
            assert st["live"] is True and st["watermark"] is False, st
            assert not logo_present(img)
        finally:
            requests.patch(f"{API}/admin/users/{setup['uid']}", json={"plan_id": ""}, headers=admin_h)
        assert requests.get(f"{API}/me", headers=setup["h"]).json()["plan_valid"] is False

    def test_admin_disable_no_logo(self, setup, admin_h):
        s = requests.get(f"{API}/settings").json()
        r = requests.put(f"{API}/admin/settings", headers=admin_h, json={**s, "watermark_enabled": False})
        assert r.status_code == 200
        assert requests.get(f"{API}/settings").json()["watermark_enabled"] is False
        try:
            st, img = record_stream(setup, "wm_off")
            assert st["live"] is True and st["watermark"] is False, st
            assert not logo_present(img)
        finally:
            requests.put(f"{API}/admin/settings", headers=admin_h, json={**s, "watermark_enabled": True})
        assert requests.get(f"{API}/settings").json()["watermark_enabled"] is True

    def test_ws_camera_with_logo(self, setup, user_a):
        h = setup["h"]
        requests.post(f"{API}/streams/stop", headers=h)
        subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=blue:size=1280x720:rate=30", "-f", "lavfi",
                        "-i", "sine", "-t", "8", "-c:v", "libvpx", "-b:v", "1M", "-deadline", "realtime", "-c:a", "libopus",
                        "/tmp/wm_cam.webm"], check=True)
        data = open("/tmp/wm_cam.webm", "rb").read()
        token = user_a["headers"]["Authorization"].split()[1]
        out = "/tmp/wm_ws.flv"
        if os.path.exists(out):
            os.remove(out)
        rec = subprocess.Popen([FF, "-y", "-loglevel", "error", "-listen", "1", "-i", RTMP, "-t", "5", "-c", "copy", out])
        time.sleep(1)
        result = {}

        async def run():
            url = BASE_URL.replace("https://", "wss://") + f"/api/ws/live?token={token}&kind=camera&quality=720p&fps=30"
            async with websockets.connect(url, max_size=None) as ws:
                result["hello"] = await ws.recv()
                n = max(1, len(data) // 32)  # ~8s of media over ~8s, like MediaRecorder timeslices
                for k, i in enumerate(range(0, len(data), n)):
                    await ws.send(data[i:i + n])
                    await asyncio.sleep(0.25)
                    if k == 12:
                        result["status"] = await asyncio.to_thread(
                            lambda: requests.get(f"{API}/streams/status", headers=h).json())

        try:
            asyncio.run(run())
            rec.wait(timeout=20)
        finally:
            rec.kill()
            requests.post(f"{API}/streams/stop", headers=h)
        print(result)
        assert '"ok"' in result["hello"]
        st = result.get("status") or result["status_end"]
        assert st["live"] is True and st["watermark"] is True, st
        errs = [l for l in st.get("log", []) if "rror" in l]
        assert not errs, errs
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "1", "-i", out, "-frames:v", "1", "/tmp/wm_ws.png"], check=True)
        assert logo_present(Image.open("/tmp/wm_ws.png").convert("RGB"))
