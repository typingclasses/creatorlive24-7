import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import (APIRouter, Depends, FastAPI, File, HTTPException, Query, UploadFile, WebSocket,
                     WebSocketDisconnect)
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

try:
    from backend.clerk_auth import clerk_router, require_user, verify_session_token
    from backend import storage, streamer
except ModuleNotFoundError:
    from clerk_auth import clerk_router, require_user, verify_session_token
    import storage
    import streamer

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
app = FastAPI()
api = APIRouter(prefix="/api")
logger = logging.getLogger("creatorlive")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CACHE_DIR = Path("/tmp/creatorlive_videos")
CACHE_DIR.mkdir(exist_ok=True)
MAX_UPLOAD = 1024 * 1024 * 1024
DEFAULT_URLS = {"youtube": "rtmp://a.rtmp.youtube.com/live2", "facebook": "rtmps://live-api-s.facebook.com:443/rtmp"}


def now():
    return datetime.now(timezone.utc).isoformat()


class Destination(BaseModel):
    enabled: bool = False
    url: str = ""
    key: str = ""


class DestinationsIn(BaseModel):
    youtube: Destination
    facebook: Destination


class VideoStartIn(BaseModel):
    video_id: str
    loop: bool = True
    quality: Literal["720p", "1080p"] = "720p"
    fps: Literal[30, 60] = 30


@api.get("/")
async def root():
    return {"app": "CreatorLive24/7"}


@api.get("/destinations")
async def get_destinations(user=Depends(require_user)):
    doc = await db.destinations.find_one({"user_id": user["user_id"]}, {"_id": 0, "user_id": 0})
    out = {}
    for p in ("youtube", "facebook"):
        d = (doc or {}).get(p) or {}
        out[p] = {"enabled": d.get("enabled", False), "url": d.get("url") or DEFAULT_URLS[p], "key": d.get("key", "")}
    return out


@api.put("/destinations")
async def save_destinations(body: DestinationsIn, user=Depends(require_user)):
    data = body.model_dump()
    for p, d in data.items():
        d["url"] = d["url"].strip() or DEFAULT_URLS[p]
        d["key"] = d["key"].strip()
        if d["enabled"] and not d["key"]:
            raise HTTPException(400, f"Stream key required for {p}")
        if not d["url"].startswith(("rtmp://", "rtmps://")):
            raise HTTPException(400, f"Server URL for {p} must start with rtmp:// or rtmps://")
    await db.destinations.update_one({"user_id": user["user_id"]}, {"$set": {**data, "updated_at": now()}}, upsert=True)
    return data


async def enabled_outputs(user_id: str):
    doc = await db.destinations.find_one({"user_id": user_id}, {"_id": 0}) or {}
    outs = [{"platform": p, "url": doc[p]["url"], "key": doc[p]["key"]}
            for p in ("youtube", "facebook") if (doc.get(p) or {}).get("enabled") and doc[p].get("key")]
    if not outs:
        raise HTTPException(400, "Add and enable at least one stream key in Step 1")
    return outs


@api.post("/videos")
async def upload_video(file: UploadFile = File(...), user=Depends(require_user)):
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(400, "Only video files are allowed")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "mp4"
    vid = str(uuid.uuid4())
    local = CACHE_DIR / f"{vid}.{ext}"
    size = 0
    with open(local, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD:
                f.close()
                local.unlink(missing_ok=True)
                raise HTTPException(413, "Video must be under 1 GB")
            await run_in_threadpool(f.write, chunk)
    path = f"{storage.APP_NAME}/videos/{user['user_id']}/{vid}.{ext}"
    result = await run_in_threadpool(storage.put_file, path, str(local), file.content_type)
    doc = {"id": vid, "user_id": user["user_id"], "storage_path": result["path"], "title": file.filename,
           "content_type": file.content_type, "size": size, "is_deleted": False, "created_at": now()}
    await db.videos.insert_one(doc.copy())
    doc.pop("storage_path")
    return doc


@api.get("/videos")
async def list_videos(user=Depends(require_user)):
    return await db.videos.find({"user_id": user["user_id"], "is_deleted": False},
                                {"_id": 0, "storage_path": 0}).sort("created_at", -1).to_list(500)


@api.delete("/videos/{vid}")
async def delete_video(vid: str, user=Depends(require_user)):
    r = await db.videos.update_one({"id": vid, "user_id": user["user_id"], "is_deleted": False},
                                   {"$set": {"is_deleted": True}})
    if r.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@api.get("/videos/{vid}/file")
async def video_file(vid: str, user=Depends(require_user)):
    rec = await db.videos.find_one({"id": vid, "user_id": user["user_id"], "is_deleted": False})
    if not rec:
        raise HTTPException(404, "Not found")
    local = await cached_file(rec)
    return FileResponse(local, media_type=rec["content_type"])


async def cached_file(rec) -> Path:
    local = CACHE_DIR / f"{rec['id']}.{rec['storage_path'].rsplit('.', 1)[-1]}"
    if not local.exists():
        await run_in_threadpool(storage.download_to_file, rec["storage_path"], str(local))
    return local


async def log_history(session, user_id):
    await db.streams.insert_one({"id": str(uuid.uuid4()), "user_id": user_id, "kind": session.kind,
                                 "title": session.title, "platforms": [o["platform"] for o in session.outputs],
                                 "started_at": session.started_at, "ended_at": now()})


@api.post("/streams/video")
async def start_video_stream(body: VideoStartIn, user=Depends(require_user)):
    uid = user["user_id"]
    if streamer.status(uid)["live"]:
        raise HTTPException(409, "A stream is already live. End it first.")
    rec = await db.videos.find_one({"id": body.video_id, "user_id": uid, "is_deleted": False})
    if not rec:
        raise HTTPException(404, "Video not found")
    outs = await enabled_outputs(uid)
    local = await cached_file(rec)
    session = streamer.Session(uid, "video", rec["title"], outs)
    session.on_exit = lambda s: log_history(s, uid)
    loop = ["-stream_loop", "-1"] if body.loop else []
    await streamer.start_process(session, ["-re", *loop, "-i", str(local)], body.quality, body.fps)
    await asyncio.sleep(3)
    if session.proc.returncode is not None:
        streamer.sessions.pop(uid, None)
        raise HTTPException(422, streamer.friendly_error(session.log))
    session.confirmed = True
    return streamer.status(uid)


@api.post("/streams/stop")
async def stop_stream(user=Depends(require_user)):
    session = await streamer.stop(user["user_id"])
    if session:
        await log_history(session, user["user_id"])
    return {"live": False}


@api.get("/streams/status")
async def stream_status(user=Depends(require_user)):
    return streamer.status(user["user_id"])


@api.get("/streams/history")
async def stream_history(user=Depends(require_user)):
    return await db.streams.find({"user_id": user["user_id"]}, {"_id": 0}).sort("started_at", -1).to_list(20)


@app.websocket("/api/ws/live")
async def live_ws(ws: WebSocket, token: str = Query(...), kind: str = Query("camera"),
                  quality: str = Query("720p"), fps: int = Query(30)):
    await ws.accept()
    try:
        uid = verify_session_token(token)["sub"]
    except HTTPException:
        await ws.close(code=4401)
        return
    if streamer.status(uid)["live"]:
        await ws.send_json({"error": "A stream is already live. End it first."})
        await ws.close()
        return
    try:
        outs = await enabled_outputs(uid)
    except HTTPException as e:
        await ws.send_json({"error": e.detail})
        await ws.close()
        return
    session = streamer.Session(uid, kind, "Camera" if kind == "camera" else "Screen Broadcast", outs)
    session.on_exit = lambda s: log_history(s, uid)
    session.confirmed = True
    await streamer.start_process(session, ["-fflags", "+genpts", "-i", "pipe:0"], quality,
                                 30 if fps not in (30, 60) else fps, stdin=True)
    await ws.send_json({"ok": True})
    try:
        while True:
            chunk = await ws.receive_bytes()
            if session.proc.returncode is not None:
                await ws.send_json({"error": streamer.friendly_error(session.log)})
                break
            session.proc.stdin.write(chunk)
            await session.proc.stdin.drain()
    except (WebSocketDisconnect, ConnectionResetError, BrokenPipeError, RuntimeError):
        pass
    finally:
        if streamer.sessions.get(uid) is session:
            await streamer.stop(uid)
            await log_history(session, uid)


@app.on_event("startup")
async def startup():
    try:
        await run_in_threadpool(storage.init_storage)
        logger.info("Storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    for uid in list(streamer.sessions):
        await streamer.stop(uid)
    client.close()


app.include_router(api)
app.include_router(clerk_router)
app.add_middleware(CORSMiddleware, allow_credentials=True,
                   allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
                   allow_methods=["*"], allow_headers=["*"])
