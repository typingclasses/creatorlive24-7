# Custom watermark logo upload/reset (admin) + custom logo burned into free user's live stream.
# Run alone: pytest backend/tests/test_watermark_upload.py -p no:xdist
import glob
import io
import os

import pytest
import requests
from PIL import Image

from conftest import API
from test_watermark import admin_h, setup, record_stream  # noqa: F401  (fixtures reused)

DEFAULT = open("/app/backend/assets/watermark.png", "rb").read()


def img_bytes(color, size=(600, 400), fmt="PNG"):
    b = io.BytesIO()
    Image.new("RGB", size, color).save(b, fmt)
    return b.getvalue()


def upload(h, data, name="logo.png", ctype="image/png"):
    return requests.post(f"{API}/admin/watermark", headers=h, files={"file": (name, data, ctype)})


def red_logo_present(img):
    # logo area at 720p: margin ~22px, height 40px => sample inside the box
    px = list(img.crop((26, 26, 70, 58)).getdata())
    red = sum(1 for r, g, b in px if r > 170 and g < 90 and b < 90) / len(px)
    print(f"red ratio in logo box={red:.3f}")
    return red > 0.6


@pytest.fixture(scope="module", autouse=True)
def reset_after(admin_h):  # noqa: F811
    yield
    requests.delete(f"{API}/admin/watermark", headers=admin_h)
    s = requests.get(f"{API}/settings").json()
    requests.put(f"{API}/admin/settings", headers=admin_h, json={**s, "watermark_enabled": True})


class TestWatermarkUpload:
    def test_no_token_401(self):
        r = upload({}, img_bytes("red"))
        assert r.status_code in (401, 403)

    def test_non_admin_403(self, user_a):
        assert upload(user_a["headers"], img_bytes("red")).status_code == 403
        assert requests.delete(f"{API}/admin/watermark", headers=user_a["headers"]).status_code == 403

    def test_non_image_400(self, admin_h):  # noqa: F811
        r = upload(admin_h, b"hello world", "a.txt", "text/plain")
        assert r.status_code == 400, r.text
        r = upload(admin_h, b"not really a png", "a.png", "image/png")
        assert r.status_code == 400, r.text

    def test_too_big_413(self, admin_h):  # noqa: F811
        r = upload(admin_h, b"\x89PNG" + os.urandom(5 * 1024 * 1024 + 10), "big.png", "image/png")
        assert r.status_code == 413, r.text

    def test_jpeg_webp_accepted(self, admin_h):  # noqa: F811
        for fmt, ct in (("JPEG", "image/jpeg"), ("WEBP", "image/webp")):
            r = upload(admin_h, img_bytes("green", (100, 50), fmt), "l." + fmt.lower(), ct)
            assert r.status_code == 200, r.text
            g = requests.get(f"{API}/watermark")
            im = Image.open(io.BytesIO(g.content))
            assert im.format == "PNG" and im.size == (100, 50)

    def test_upload_png_normalized(self, admin_h):  # noqa: F811
        r = upload(admin_h, img_bytes("red"))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["custom"] is True and isinstance(body["watermark_version"], str)
        s = requests.get(f"{API}/settings").json()
        assert s["watermark_version"] == body["watermark_version"] and s["watermark_path"]
        g = requests.get(f"{API}/watermark")
        assert g.status_code == 200 and g.headers["content-type"] == "image/png"
        im = Image.open(io.BytesIO(g.content))
        assert im.size == (360, 240)
        assert im.convert("RGB").getpixel((10, 10))[0] > 200

    def test_stream_burns_custom_logo(self, setup, admin_h):  # noqa: F811
        assert upload(admin_h, img_bytes("red")).status_code == 200
        st, img = record_stream(setup, "wm_custom")
        assert st["live"] is True and st["watermark"] is True, st
        img.save("/tmp/wm_custom_frame.png")
        assert red_logo_present(img)

    def test_redownload_after_cache_cleared(self, setup, admin_h):  # noqa: F811
        assert upload(admin_h, img_bytes("red")).status_code == 200
        for f in glob.glob("/tmp/creatorlive_branding/*"):
            os.remove(f)
        st, img = record_stream(setup, "wm_custom2")
        assert st["live"] is True and st["watermark"] is True, st
        assert red_logo_present(img)
        assert glob.glob("/tmp/creatorlive_branding/*.png"), "logo not re-downloaded to cache"

    def test_reset_to_default(self, admin_h):  # noqa: F811
        r = requests.delete(f"{API}/admin/watermark", headers=admin_h)
        assert r.status_code == 200 and r.json()["custom"] is False
        s = requests.get(f"{API}/settings").json()
        assert not s.get("watermark_path")
        assert requests.get(f"{API}/watermark").content == DEFAULT

    def test_stream_default_logo_after_reset(self, setup):  # noqa: F811
        st, img = record_stream(setup, "wm_default")
        assert st["watermark"] is True
        assert not red_logo_present(img)
