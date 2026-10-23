# Chunked video upload (long/short format) + format patch + file streaming tests
import os
import subprocess

import imageio_ffmpeg
import pytest
import requests

from conftest import API

FF = imageio_ffmpeg.get_ffmpeg_exe()


def make(path, size, secs, rate="300k"):
    if not os.path.exists(path):
        subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30",
                        "-f", "lavfi", "-i", "sine", "-t", str(secs), "-c:v", "libx264", "-preset", "ultrafast",
                        "-b:v", rate, "-c:a", "aac", path], check=True)
    return path


def init(h, size, name="TEST_v.mp4", ctype="video/mp4"):
    return requests.post(f"{API}/uploads", headers=h, json={"filename": name, "size": size, "content_type": ctype})


def put(h, uid, i, data):
    return requests.put(f"{API}/uploads/{uid}/chunks/{i}", headers={**h, "Content-Type": "application/octet-stream"}, data=data)


def chunked(h, path, cs=None):
    size = os.path.getsize(path)
    r = init(h, size, "TEST_" + os.path.basename(path))
    assert r.status_code == 200, r.text
    uid, cs = r.json()["upload_id"], cs or r.json()["chunk_size"]
    with open(path, "rb") as f:
        i = 0
        while data := f.read(cs):
            assert put(h, uid, i, data).status_code == 200
            i += 1
    return requests.post(f"{API}/uploads/{uid}/complete", headers=h)


@pytest.fixture(scope="module")
def created(user_a):
    ids = []
    yield ids
    for v in ids:
        requests.delete(f"{API}/videos/{v}", headers=user_a["headers"])


class TestUploadInit:
    def test_init_ok(self, user_a):
        r = init(user_a["headers"], 1000)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["upload_id"], str) and d["chunk_size"] == 20 * 1024 * 1024

    def test_too_large_413(self, user_a):
        assert init(user_a["headers"], 5 * 1024 ** 3 + 1).status_code == 413

    def test_exact_5gb_ok(self, user_a):
        assert init(user_a["headers"], 5 * 1024 ** 3).status_code == 200

    def test_non_video_400(self, user_a):
        assert init(user_a["headers"], 100, "a.txt", "text/plain").status_code == 400

    def test_no_auth_401(self):
        assert requests.post(f"{API}/uploads", json={"filename": "a.mp4", "size": 1, "content_type": "video/mp4"}).status_code == 401

    def test_negative_size(self, user_a):
        r = init(user_a["headers"], -5)
        print("negative size status", r.status_code)
        assert r.status_code in (400, 422)


class TestChunks:
    def test_wrong_index_409_retry_idempotent_incomplete_400(self, user_a):
        h = user_a["headers"]
        uid = init(h, 30).json()["upload_id"]
        assert put(h, uid, 1, b"x" * 10).status_code == 409
        r = put(h, uid, 0, b"x" * 10)
        assert r.status_code == 200 and r.json()["received"] == 10
        r = put(h, uid, 0, b"x" * 10)  # retry same index
        assert r.status_code == 200 and r.json()["received"] == 10
        assert requests.post(f"{API}/uploads/{uid}/complete", headers=h).status_code == 400
        assert put(h, uid, 1, b"x" * 25).status_code == 400  # overflow size

    def test_other_user_upload_404(self, user_a, user_b):
        uid = init(user_a["headers"], 30).json()["upload_id"]
        assert put(user_b["headers"], uid, 0, b"x").status_code == 404
        assert requests.post(f"{API}/uploads/{uid}/complete", headers=user_b["headers"]).status_code == 404

    def test_empty_chunk_400(self, user_a):
        uid = init(user_a["headers"], 30).json()["upload_id"]
        assert put(user_a["headers"], uid, 0, b"").status_code == 400


class TestFormatFlow:
    def test_long_and_short_detect(self, user_a, created):
        h = user_a["headers"]
        # 200s landscape -> long; multi-chunk forced by 1MB chunk size client side
        r = chunked(h, make("/tmp/TEST_long200.mp4", "640x360", 200), cs=1024 * 1024)
        assert r.status_code == 200, r.text
        d = r.json()
        created.append(d["id"])
        assert d["format"] == "long" and d["width"] == 640 and d["height"] == 360 and 199 <= d["duration"] <= 201
        assert "storage_parts" not in d and "_id" not in d and "user_id" not in d
        r = chunked(h, make("/tmp/TEST_vert.mp4", "360x640", 300))
        d2 = r.json()
        created.append(d2["id"])
        assert d2["format"] == "short"  # vertical even if long duration
        r = chunked(h, make("/tmp/TEST_short.mp4", "640x360", 30))
        d3 = r.json()
        created.append(d3["id"])
        assert d3["format"] == "short"  # <=180s
        lst = {v["id"]: v for v in requests.get(f"{API}/videos", headers=h).json()}
        assert lst[d["id"]]["format"] == "long" and lst[d2["id"]]["format"] == "short"

    def test_patch_format(self, user_a, user_b, created):
        h, vid = user_a["headers"], created[0]
        r = requests.patch(f"{API}/videos/{vid}", headers=h, json={"format": "short"})
        assert r.status_code == 200 and r.json()["format"] == "short"
        lst = {v["id"]: v for v in requests.get(f"{API}/videos", headers=h).json()}
        assert lst[vid]["format"] == "short"
        assert requests.patch(f"{API}/videos/{vid}", headers=h, json={"format": "medium"}).status_code == 422
        assert requests.patch(f"{API}/videos/{vid}", headers=user_b["headers"], json={"format": "long"}).status_code == 404
        assert requests.patch(f"{API}/videos/{vid}", headers=h, json={"format": "long"}).json()["format"] == "long"

    def test_file_stream_auth(self, user_a, created):
        vid = created[0]
        size = os.path.getsize("/tmp/TEST_long200.mp4")
        tok = user_a["headers"]["Authorization"][7:]
        assert requests.get(f"{API}/videos/{vid}/file").status_code == 401
        assert requests.get(f"{API}/videos/{vid}/file?auth=bad").status_code == 401
        r = requests.get(f"{API}/videos/{vid}/file?auth={tok}")
        assert r.status_code == 200 and len(r.content) == size
        assert r.content == open("/tmp/TEST_long200.mp4", "rb").read()

    def test_cache_rebuild_from_parts(self, user_a, created):
        vid = created[0]
        local = f"/tmp/creatorlive_videos/{vid}.mp4"
        assert os.path.exists(local)
        os.remove(local)
        tok = user_a["headers"]["Authorization"][7:]
        r = requests.get(f"{API}/videos/{vid}/file?auth={tok}")
        assert r.status_code == 200 and r.content == open("/tmp/TEST_long200.mp4", "rb").read()
        assert os.path.exists(local)

    def test_range_request(self, user_a, created):
        tok = user_a["headers"]["Authorization"][7:]
        r = requests.get(f"{API}/videos/{created[0]}/file?auth={tok}", headers={"Range": "bytes=0-99"})
        print("range status", r.status_code, "len", len(r.content), r.headers.get("accept-ranges"))
        assert r.status_code == 206
