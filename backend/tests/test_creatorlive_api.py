import subprocess
import time

import imageio_ffmpeg
import pytest
import requests

from conftest import API

FF = imageio_ffmpeg.get_ffmpeg_exe()
MP4 = "/tmp/TEST_clip.mp4"


@pytest.fixture(scope="module", autouse=True)
def clip():
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30", "-f", "lavfi",
                    "-i", "sine", "-t", "5", "-c:v", "libx264", "-c:a", "aac", MP4], check=True)


# Health / auth guard
class TestAuthGuard:
    def test_root(self):
        r = requests.get(f"{API}/")
        assert r.status_code == 200 and r.json()["app"] == "CreatorLive24/7"

    def test_clerk_config(self):
        r = requests.get(f"{API}/clerk/config")
        assert r.status_code == 200 and r.json()["enabled"] is True

    @pytest.mark.parametrize("method,path", [("get", "/destinations"), ("put", "/destinations"), ("get", "/videos"),
                                             ("post", "/videos"), ("delete", "/videos/x"), ("get", "/videos/x/file"),
                                             ("post", "/streams/video"), ("post", "/streams/stop"),
                                             ("get", "/streams/status"), ("get", "/streams/history")])
    def test_401_without_token(self, method, path):
        r = requests.request(method, f"{API}{path}")
        assert r.status_code == 401, f"{method} {path} -> {r.status_code}"

    def test_401_bad_token(self):
        r = requests.get(f"{API}/videos", headers={"Authorization": "Bearer abc.def.ghi"})
        assert r.status_code == 401


# Destinations (Step 1)
class TestDestinations:
    def test_defaults(self, user_b):
        r = requests.get(f"{API}/destinations", headers=user_b["headers"])
        assert r.status_code == 200
        d = r.json()
        assert d["youtube"]["url"].startswith("rtmp") and d["facebook"]["url"].startswith("rtmp")

    def test_enabled_without_key_400(self, user_a):
        r = requests.put(f"{API}/destinations", headers=user_a["headers"], json={
            "youtube": {"enabled": True, "url": "", "key": ""}, "facebook": {"enabled": False, "url": "", "key": ""}})
        assert r.status_code == 400 and "youtube" in r.json()["detail"]

    def test_bad_url_400(self, user_a):
        r = requests.put(f"{API}/destinations", headers=user_a["headers"], json={
            "youtube": {"enabled": True, "url": "http://x", "key": "k"}, "facebook": {"enabled": False, "url": "", "key": ""}})
        assert r.status_code == 400

    def test_save_and_persist(self, user_a):
        body = {"youtube": {"enabled": True, "url": "rtmp://127.0.0.1:1935/live2", "key": " testkey "},
                "facebook": {"enabled": False, "url": "", "key": ""}}
        r = requests.put(f"{API}/destinations", headers=user_a["headers"], json=body)
        assert r.status_code == 200 and r.json()["youtube"]["key"] == "testkey"
        g = requests.get(f"{API}/destinations", headers=user_a["headers"]).json()
        assert g["youtube"] == {"enabled": True, "url": "rtmp://127.0.0.1:1935/live2", "key": "testkey"}
        assert g["facebook"]["url"] == "rtmps://live-api-s.facebook.com:443/rtmp"


# Videos + streaming + isolation
class TestVideosAndStreams:
    vid = None

    def test_reject_non_video(self, user_a):
        r = requests.post(f"{API}/videos", headers=user_a["headers"], files={"file": ("a.txt", b"hello", "text/plain")})
        assert r.status_code == 400

    def test_upload_list_file(self, user_a):
        r = requests.post(f"{API}/videos", headers=user_a["headers"],
                          files={"file": ("TEST_clip.mp4", open(MP4, "rb"), "video/mp4")}, timeout=120)
        assert r.status_code == 200, r.text
        v = r.json()
        assert v["title"] == "TEST_clip.mp4" and "storage_path" not in v and "_id" not in v
        TestVideosAndStreams.vid = v["id"]
        lst = requests.get(f"{API}/videos", headers=user_a["headers"]).json()
        assert any(x["id"] == v["id"] for x in lst)
        f = requests.get(f"{API}/videos/{v['id']}/file", headers=user_a["headers"], timeout=120)
        assert f.status_code == 200 and f.headers["content-type"].startswith("video/mp4") and len(f.content) == v["size"]

    def test_isolation(self, user_a, user_b):
        vid = TestVideosAndStreams.vid
        lst = requests.get(f"{API}/videos", headers=user_b["headers"]).json()
        assert all(x["id"] != vid for x in lst)
        assert requests.get(f"{API}/videos/{vid}/file", headers=user_b["headers"]).status_code == 404
        assert requests.delete(f"{API}/videos/{vid}", headers=user_b["headers"]).status_code == 404
        assert requests.post(f"{API}/streams/video", headers=user_b["headers"], json={"video_id": vid}).status_code == 404
        d = requests.get(f"{API}/destinations", headers=user_b["headers"]).json()
        assert d["youtube"]["key"] != "testkey"

    def test_stream_requires_destination(self, user_b):
        # user_b has no enabled destinations -> needs own video
        r = requests.post(f"{API}/videos", headers=user_b["headers"],
                          files={"file": ("TEST_b.mp4", open(MP4, "rb"), "video/mp4")}, timeout=120)
        vb = r.json()["id"]
        s = requests.post(f"{API}/streams/video", headers=user_b["headers"], json={"video_id": vb})
        assert s.status_code == 400 and "Step 1" in s.json()["detail"]
        requests.delete(f"{API}/videos/{vb}", headers=user_b["headers"])

    def test_invalid_quality_422(self, user_a):
        r = requests.post(f"{API}/streams/video", headers=user_a["headers"],
                          json={"video_id": TestVideosAndStreams.vid, "quality": "4k"})
        assert r.status_code == 422

    def test_stream_lifecycle(self, user_a):
        requests.post(f"{API}/streams/stop", headers=user_a["headers"])
        before = len(requests.get(f"{API}/streams/history", headers=user_a["headers"]).json())
        listener = subprocess.Popen([FF, "-loglevel", "error", "-listen", "1", "-i",
                                     "rtmp://127.0.0.1:1935/live2/testkey", "-f", "null", "-"])
        time.sleep(1)
        try:
            r = requests.post(f"{API}/streams/video", headers=user_a["headers"],
                              json={"video_id": TestVideosAndStreams.vid, "loop": True, "quality": "1080p", "fps": 60})
            assert r.status_code == 200 and r.json()["live"] is True, r.text
            dup = requests.post(f"{API}/streams/video", headers=user_a["headers"], json={"video_id": TestVideosAndStreams.vid})
            assert dup.status_code == 409
            time.sleep(6)
            st = requests.get(f"{API}/streams/status", headers=user_a["headers"]).json()
            assert st["live"] is True and st["platforms"] == ["youtube"], st
            stop = requests.post(f"{API}/streams/stop", headers=user_a["headers"]).json()
            assert stop["live"] is False
            assert requests.get(f"{API}/streams/status", headers=user_a["headers"]).json()["live"] is False
            hist = requests.get(f"{API}/streams/history", headers=user_a["headers"]).json()
            assert len(hist) == min(before + 1, 20) and hist[0]["title"] == "TEST_clip.mp4" and hist[0]["kind"] == "video"
        finally:
            listener.kill()

    def test_delete_video(self, user_a):
        vid = TestVideosAndStreams.vid
        assert requests.delete(f"{API}/videos/{vid}", headers=user_a["headers"]).status_code == 200
        assert all(x["id"] != vid for x in requests.get(f"{API}/videos", headers=user_a["headers"]).json())
        assert requests.delete(f"{API}/videos/{vid}", headers=user_a["headers"]).status_code == 404
        assert requests.get(f"{API}/videos/{vid}/file", headers=user_a["headers"]).status_code == 404
