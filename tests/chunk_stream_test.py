# Streams a chunk-uploaded video (cache deleted -> rebuilt from storage parts) to a local RTMP listener via PUBLIC URL.
# usage: python chunk_stream_test.py <video_id>
import os, sys, time, subprocess, requests, imageio_ffmpeg
sys.path.insert(0, "/app/backend/tests")
from conftest import API, make_user, token_for
FF = imageio_ffmpeg.get_ffmpeg_exe()
vid = sys.argv[1]
_, sess = make_user("creator+clerk_test@example.com")
H = {"Authorization": f"Bearer {token_for(sess)}"}
orig = requests.get(f"{API}/destinations", headers=H).json()
cache = f"/tmp/creatorlive_videos/{vid}.mp4"
if os.path.exists(cache):
    os.remove(cache)
print("cache deleted", not os.path.exists(cache))
listener = subprocess.Popen([FF, "-loglevel", "error", "-listen", "1", "-i", "rtmp://127.0.0.1:1935/live2/testkey", "-f", "null", "-"])
time.sleep(1)
try:
    print("dest", requests.put(f"{API}/destinations", headers=H, json={"youtube": {"enabled": True, "url": "rtmp://127.0.0.1:1935/live2", "key": "testkey"},
                                                                      "facebook": {"enabled": False, "url": "", "key": ""}}).status_code)
    t = time.time()
    r = requests.post(f"{API}/streams/video", headers=H, json={"video_id": vid, "loop": True}, timeout=300)
    print("start", r.status_code, round(time.time() - t, 1), "s", r.text[:300])
    print("cache rebuilt", os.path.exists(cache), os.path.getsize(cache) if os.path.exists(cache) else None)
    time.sleep(8)
    print("status", requests.get(f"{API}/streams/status", headers=H).json())
    print("listener alive", listener.poll() is None)
    print("stop", requests.post(f"{API}/streams/stop", headers=H).json())
finally:
    listener.kill()
    requests.put(f"{API}/destinations", headers=H, json=orig)
    print("restored destinations")
