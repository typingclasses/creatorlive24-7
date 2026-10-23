import os, subprocess, imageio_ffmpeg
from dotenv import load_dotenv
load_dotenv("/app/backend/.env", override=True)
key = os.environ["YOUTUBE_TEST_STREAM_KEY"].strip()
ff = imageio_ffmpeg.get_ffmpeg_exe()
args = [ff, "-hide_banner", "-loglevel", "warning", "-re",
        "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
        "-t", "120", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-g", "60",
        "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-f", "flv", f"rtmp://a.rtmp.youtube.com/live2/{key}"]
r = subprocess.run(args, capture_output=True, text=True)
print("exit", r.returncode)
print(r.stderr.replace(key, "***")[-1500:])
