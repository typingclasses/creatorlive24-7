import asyncio
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import (APIRouter, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, WebSocket,
                     WebSocketDisconnect)
from fastapi.responses import FileResponse, Response, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
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
MAX_UPLOAD = 5 * 1024 * 1024 * 1024
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


CHUNK_SIZE = 20 * 1024 * 1024


class UploadInit(BaseModel):
    filename: str
    size: int = Field(gt=0)
    content_type: str


class VideoPatch(BaseModel):
    format: Literal["long", "short"]


async def probe(local: Path) -> dict:
    proc = await asyncio.create_subprocess_exec(streamer.FFMPEG, "-hide_banner", "-i", str(local),
                                                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    _, err = await proc.communicate()
    text = err.decode(errors="ignore")
    info = {"duration": None, "width": None, "height": None}
    if m := re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", text):
        info["duration"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    if m := re.search(r"Video: .*?, (\d{2,5})x(\d{2,5})", text):
        w, h = int(m[1]), int(m[2])
        if re.search(r"rotation of -?90|rotate\s*:\s*-?(90|270)", text):
            w, h = h, w
        info["width"], info["height"] = w, h
    return info


def detect_format(info: dict) -> str:
    vertical = info["width"] and info["height"] and info["height"] > info["width"]
    short = info["duration"] is not None and info["duration"] <= 180
    return "short" if vertical or short else "long"


async def save_video_doc(user_id, vid, title, content_type, size, local, storage_fields):
    info = await probe(local)
    doc = {"id": vid, "user_id": user_id, "title": title, "content_type": content_type, "size": size,
           **info, "format": detect_format(info), "is_deleted": False, "created_at": now(), **storage_fields}
    await db.videos.insert_one(doc.copy())
    return {k: v for k, v in doc.items() if k not in ("storage_path", "storage_parts", "user_id")}


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
                raise HTTPException(413, "Video must be under 5 GB")
            await run_in_threadpool(f.write, chunk)
    path = f"{storage.APP_NAME}/videos/{user['user_id']}/{vid}.{ext}"
    result = await run_in_threadpool(storage.put_file, path, str(local), file.content_type)
    return await save_video_doc(user["user_id"], vid, file.filename, file.content_type, size, local,
                                {"storage_path": result["path"]})


@api.post("/uploads")
async def upload_init(body: UploadInit, user=Depends(require_user)):
    if not body.content_type.startswith("video/"):
        raise HTTPException(400, "Only video files are allowed")
    if body.size > MAX_UPLOAD:
        raise HTTPException(413, "Video must be under 5 GB")
    ext = body.filename.rsplit(".", 1)[-1].lower() if "." in body.filename else "mp4"
    up = {"id": str(uuid.uuid4()), "user_id": user["user_id"], "filename": body.filename, "ext": ext,
          "content_type": body.content_type, "size": body.size, "received": 0, "claimed": 0, "parts": [], "created_at": now()}
    await db.uploads.insert_one(up.copy())
    return {"upload_id": up["id"], "chunk_size": CHUNK_SIZE}


@api.put("/uploads/{upload_id}/chunks/{index}")
async def upload_chunk(upload_id: str, index: int, request: Request, user=Depends(require_user)):
    up = await db.uploads.find_one({"id": upload_id, "user_id": user["user_id"]})
    if not up:
        raise HTTPException(404, "Upload not found")
    if index < len(up["parts"]):
        return {"received": up["received"]}  # already stored (client retry)
    if index > len(up["parts"]):
        raise HTTPException(409, f"Expected chunk {len(up['parts'])}")
    data = await request.body()
    if not data or len(data) > CHUNK_SIZE or up["received"] + len(data) > up["size"]:
        raise HTTPException(400, "Invalid chunk")
    claimed = await db.uploads.find_one_and_update({"id": upload_id, "claimed": index, "parts": {"$size": index}},
                                                   {"$inc": {"claimed": 1}})
    if not claimed:
        raise HTTPException(409, "Chunk in progress, retry" if index < up.get("claimed", 0) else f"Expected chunk {len(up['parts'])}")
    try:
        path = f"{storage.APP_NAME}/videos/{user['user_id']}/{upload_id}/part{index:05d}"
        result = await run_in_threadpool(storage.put_object, path, data, "application/octet-stream")
        local = CACHE_DIR / f"{upload_id}.{up['ext']}"
        with open(local, "r+b" if local.exists() else "wb") as f:
            f.seek(claimed["received"])
            await run_in_threadpool(f.write, data)
    except Exception:
        await db.uploads.update_one({"id": upload_id, "claimed": index + 1}, {"$set": {"claimed": index}})
        raise
    up = await db.uploads.find_one_and_update({"id": upload_id}, {"$push": {"parts": result["path"]}, "$inc": {"received": len(data)}},
                                              return_document=ReturnDocument.AFTER)
    return {"received": up["received"]}


@api.post("/uploads/{upload_id}/complete")
async def upload_complete(upload_id: str, user=Depends(require_user)):
    up = await db.uploads.find_one({"id": upload_id, "user_id": user["user_id"]})
    if not up:
        raise HTTPException(404, "Upload not found")
    if up["received"] != up["size"]:
        raise HTTPException(400, "Upload is incomplete")
    local = CACHE_DIR / f"{upload_id}.{up['ext']}"
    if not local.exists() or local.stat().st_size != up["size"]:
        local.unlink(missing_ok=True)
        await run_in_threadpool(storage.download_parts, up["parts"], str(local))
    doc = await save_video_doc(user["user_id"], upload_id, up["filename"], up["content_type"], up["size"], local,
                               {"storage_parts": up["parts"], "ext": up["ext"]})
    await db.uploads.delete_one({"id": upload_id})
    return doc


@api.patch("/videos/{vid}")
async def update_video(vid: str, body: VideoPatch, user=Depends(require_user)):
    r = await db.videos.update_one({"id": vid, "user_id": user["user_id"], "is_deleted": False},
                                   {"$set": {"format": body.format}})
    if r.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"id": vid, "format": body.format}


@api.get("/videos")
async def list_videos(user=Depends(require_user)):
    return await db.videos.find({"user_id": user["user_id"], "is_deleted": False},
                                {"_id": 0, "storage_path": 0, "storage_parts": 0, "user_id": 0}).sort("created_at", -1).to_list(500)


@api.delete("/videos/{vid}")
async def delete_video(vid: str, user=Depends(require_user)):
    r = await db.videos.update_one({"id": vid, "user_id": user["user_id"], "is_deleted": False},
                                   {"$set": {"is_deleted": True}})
    if r.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@api.get("/videos/{vid}/file")
async def video_file(vid: str, request: Request, auth: Optional[str] = Query(None)):
    user = {"user_id": verify_session_token(auth)["sub"]} if auth else require_user(request)
    rec = await db.videos.find_one({"id": vid, "user_id": user["user_id"], "is_deleted": False})
    if not rec:
        raise HTTPException(404, "Not found")
    local = local_path(rec)
    if not local.exists():
        prepare(rec)
        if rec.get("storage_parts"):
            return StreamingResponse(storage.iter_parts(rec["storage_parts"]), media_type=rec["content_type"])
        local = await cached_file(rec)
    return ranged_file(local, rec["content_type"], request.headers.get("range"))


def ranged_file(local: Path, media_type: str, range_header: Optional[str]):
    size = local.stat().st_size
    m = re.match(r"bytes=(\d*)-(\d*)", range_header or "")
    if not m or (not m[1] and not m[2]):
        return FileResponse(local, media_type=media_type, headers={"Accept-Ranges": "bytes"})
    start, end = (int(m[1]), int(m[2]) if m[2] else size - 1) if m[1] else (size - int(m[2]), size - 1)
    end = min(end, size - 1)
    if start > end:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})

    def body():
        with open(local, "rb") as f:
            f.seek(start)
            left = end - start + 1
            while left > 0 and (chunk := f.read(min(1024 * 1024, left))):
                left -= len(chunk)
                yield chunk
    return StreamingResponse(body(), status_code=206, media_type=media_type, headers={
        "Accept-Ranges": "bytes", "Content-Range": f"bytes {start}-{end}/{size}", "Content-Length": str(end - start + 1)})


def local_path(rec) -> Path:
    return CACHE_DIR / f"{rec['id']}.{rec.get('ext') or rec['storage_path'].rsplit('.', 1)[-1]}"


preparing: dict = {}


def prepare(rec) -> asyncio.Task:
    """Rebuild the local copy from cloud storage once, in the background."""
    if rec["id"] not in preparing:
        local = local_path(rec)
        fn = storage.download_parts if rec.get("storage_parts") else storage.download_to_file
        src = rec.get("storage_parts") or rec["storage_path"]
        task = asyncio.create_task(run_in_threadpool(fn, src, str(local)))
        task.add_done_callback(lambda _: preparing.pop(rec["id"], None))
        preparing[rec["id"]] = task
    return preparing[rec["id"]]


async def cached_file(rec, wait: float = 600) -> Path:
    local = local_path(rec)
    if not local.exists():
        try:
            await asyncio.wait_for(asyncio.shield(prepare(rec)), timeout=wait)
        except asyncio.TimeoutError:
            raise HTTPException(422, "Your video is being prepared from cloud storage. Try Go Live again in a minute.")
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
    local = await cached_file(rec, wait=45)
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
