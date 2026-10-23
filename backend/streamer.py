import asyncio
import collections
from datetime import datetime, timezone

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
QUALITY = {"720p": (720, "3000k"), "1080p": (1080, "4500k")}


class Session:
    def __init__(self, user_id, kind, title, outputs):
        self.user_id = user_id
        self.kind = kind
        self.title = title
        self.outputs = outputs
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.proc = None
        self.log = collections.deque(maxlen=15)
        self.ended = False


sessions: dict = {}


def build_tee(destinations):
    urls = [f"[f=flv:onfail=ignore]{d['url'].rstrip('/')}/{d['key']}" for d in destinations]
    return "|".join(urls)


def encode_args(quality: str, fps: int):
    height, bitrate = QUALITY.get(quality, QUALITY["720p"])
    return [
        "-vf", f"scale=-2:'min({height},ih)':flags=bicubic,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
        "-r", str(fps), "-g", str(fps * 2), "-keyint_min", str(fps * 2),
        "-b:v", bitrate, "-maxrate", bitrate, "-bufsize", "9000k",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-flags", "+global_header",
    ]


async def _drain(session: Session):
    while True:
        line = await session.proc.stderr.readline()
        if not line:
            break
        session.log.append(line.decode(errors="ignore").strip())


async def start_process(session: Session, input_args, quality, fps, stdin=False):
    args = [FFMPEG, "-hide_banner", "-loglevel", "warning", *input_args,
            "-map", "0:v:0", "-map", "0:a:0?", *encode_args(quality, fps),
            "-f", "tee", build_tee(session.outputs)]
    session.proc = await asyncio.create_subprocess_exec(
        *args, stdin=asyncio.subprocess.PIPE if stdin else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    asyncio.create_task(_drain(session))
    sessions[session.user_id] = session
    return session


async def stop(user_id: str):
    session = sessions.pop(user_id, None)
    if not session:
        return None
    session.ended = True
    if session.proc and session.proc.returncode is None:
        try:
            if session.proc.stdin:
                session.proc.stdin.close()
            session.proc.terminate()
            await asyncio.wait_for(session.proc.wait(), timeout=5)
        except Exception:
            session.proc.kill()
    return session


def status(user_id: str):
    s = sessions.get(user_id)
    if not s:
        return {"live": False}
    running = s.proc is not None and s.proc.returncode is None
    return {
        "live": running, "kind": s.kind, "title": s.title, "started_at": s.started_at,
        "platforms": [d["platform"] for d in s.outputs], "log": list(s.log)[-5:],
        "exit_code": None if running else s.proc.returncode,
    }
