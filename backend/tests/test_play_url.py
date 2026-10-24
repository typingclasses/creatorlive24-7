# Signed media play-url (HMAC, 6h) + /file signed access, parts-stream Content-Length, concurrent chunk 409 message
import hashlib
import hmac
import os
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

from conftest import API, BASE_URL
from test_chunked_upload import chunked, make, init, put

SRC = "/tmp/TEST_play60.mp4"


def sig(vid, uid, exp):
    key = hashlib.sha256(("media:" + os.environ["CLERK_SECRET_KEY"]).encode()).digest()
    return hmac.new(key, f"{vid}:{uid}:{exp}".encode(), hashlib.sha256).hexdigest()


@pytest.fixture(scope="module")
def video(user_a):
    r = chunked(user_a["headers"], make(SRC, "640x360", 60), cs=1024 * 1024)
    assert r.status_code == 200, r.text
    d = r.json()
    yield d
    requests.delete(f"{API}/videos/{d['id']}", headers=user_a["headers"])


class TestPlayUrl:
    def test_play_url_shape(self, user_a, video):
        r = requests.get(f"{API}/videos/{video['id']}/play-url", headers=user_a["headers"])
        assert r.status_code == 200
        url = r.json()["url"]
        assert url.startswith(f"/api/videos/{video['id']}/file?")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        assert q["uid"][0] == user_a["user"]["id"]
        exp = int(q["exp"][0])
        assert 6 * 3600 - 120 <= exp - time.time() <= 6 * 3600 + 60
        assert len(q["sig"][0]) == 64 and "auth" not in q

    def test_play_url_auth(self, user_b, video):
        assert requests.get(f"{API}/videos/{video['id']}/play-url").status_code == 401
        assert requests.get(f"{API}/videos/{video['id']}/play-url", headers=user_b["headers"]).status_code == 404
        assert requests.get(f"{API}/videos/nonexistent/play-url", headers=user_b["headers"]).status_code == 404

    def test_signed_file_full_and_range(self, user_a, video):
        url = BASE_URL + requests.get(f"{API}/videos/{video['id']}/play-url", headers=user_a["headers"]).json()["url"]
        src = open(SRC, "rb").read()
        r = requests.get(url)  # no Authorization header
        assert r.status_code == 200 and r.content == src
        r = requests.get(url, headers={"Range": "bytes=100-199"})
        assert r.status_code == 206 and r.content == src[100:200]
        assert r.headers["content-range"] == f"bytes 100-199/{len(src)}"

    def test_tampered_and_expired(self, user_a, user_b, video):
        vid, uid = video["id"], user_a["user"]["id"]
        url = requests.get(f"{API}/videos/{vid}/play-url", headers=user_a["headers"]).json()["url"]
        q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(url).query).items()}
        f = f"{API}/videos/{vid}/file"
        bad = dict(q, sig=("0" if q["sig"][0] != "0" else "1") + q["sig"][1:])
        assert requests.get(f, params=bad).status_code == 401
        assert requests.get(f, params=dict(q, uid=user_b["user"]["id"])).status_code == 401
        assert requests.get(f, params=dict(q, exp=int(q["exp"]) + 1)).status_code == 401
        # valid HMAC but expired
        past = int(time.time()) - 10
        assert requests.get(f, params={"uid": uid, "exp": past, "sig": sig(vid, uid, past)}).status_code == 401
        # sig of a video url used for another video id
        assert requests.get(f"{API}/videos/other-id/file", params=q).status_code == 401
        # user_b's own valid signature for user_a's video -> 404 (ownership check)
        ub, fut = user_b["user"]["id"], int(time.time()) + 600
        assert requests.get(f, params={"uid": ub, "exp": fut, "sig": sig(vid, ub, fut)}).status_code == 404
        assert requests.get(f).status_code == 401

    def test_parts_stream_content_length(self, user_a, video):
        vid = video["id"]
        local = f"/tmp/creatorlive_videos/{vid}.mp4"
        src = open(SRC, "rb").read()
        assert os.path.exists(local)
        os.remove(local)
        url = BASE_URL + requests.get(f"{API}/videos/{vid}/play-url", headers=user_a["headers"]).json()["url"]
        r = requests.get(url, stream=True)
        print("parts stream status", r.status_code, dict(r.headers))
        assert r.status_code == 200
        assert r.headers.get("content-length") == str(len(src))
        assert r.content == src
        for _ in range(60):
            if os.path.exists(local) and os.path.getsize(local) == len(src):
                break
            time.sleep(1)
        assert open(local, "rb").read() == src


class TestConcurrentMessage:
    def test_dup_chunk_in_progress_message(self, user_a):
        h = user_a["headers"]
        data = os.urandom(8 * 1024 * 1024)
        uid = init(h, len(data), "TEST_dup.mp4").json()["upload_id"]
        with ThreadPoolExecutor(4) as ex:
            rs = list(ex.map(lambda _: put(h, uid, 0, data), range(4)))
        codes = [r.status_code for r in rs]
        msgs = [r.json().get("detail") for r in rs if r.status_code == 409]
        print("codes", codes, "msgs", msgs)
        assert codes.count(200) >= 1 and all(c in (200, 409) for c in codes)
        assert all(m == "Chunk in progress, retry" for m in msgs)
        r = put(h, uid, 0, data)
        assert r.status_code == 200 and r.json()["received"] == len(data)
