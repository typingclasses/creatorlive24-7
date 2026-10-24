import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

try:
    from backend.clerk_auth import require_user
except ModuleNotFoundError:
    from clerk_auth import require_user

db = None
public = APIRouter(prefix="/api")
admin = APIRouter(prefix="/api/admin")

DEFAULT_SETTINGS = {
    "site_name": "CreatorLive24/7", "tagline": "Your Content. Always On.",
    "address": "Tripoliya, Patna, Bihar", "support_email": "", "mobile": "", "whatsapp": "",
    "support_text": "Need help with streaming? Call or WhatsApp us.",
    "social": {"youtube": "", "facebook": "", "instagram": "", "twitter": ""},
    "upi_id": "", "upi_name": "CreatorLive24/7",
}
SEED_PLANS = [
    {"name": "Starter", "price": 199, "duration_days": 30, "features": ["Live to YouTube & Facebook", "Video Library", "720p streaming"], "sort": 1},
    {"name": "Pro", "price": 499, "duration_days": 30, "features": ["Everything in Starter", "1080p @ 60fps", "Loop videos 24/7"], "sort": 2},
    {"name": "Pro Yearly", "price": 4999, "duration_days": 365, "features": ["Everything in Pro", "Priority support"], "sort": 3},
]


def now():
    return datetime.now(timezone.utc).isoformat()


def admin_emails():
    return {e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()}


def _clerk(path: str):
    r = requests.get(f"https://api.clerk.com/v1{path}", timeout=15,
                     headers={"Authorization": f"Bearer {os.environ['CLERK_SECRET_KEY']}", "User-Agent": "creatorlive"})
    r.raise_for_status()
    return r.json()


def _primary_email(u: dict) -> str:
    pid = u.get("primary_email_address_id")
    return next((e["email_address"] for e in u.get("email_addresses", []) if e.get("id") == pid), "").lower()


def _profile_from_clerk(u: dict) -> dict:
    name = " ".join(x for x in (u.get("first_name"), u.get("last_name")) if x)
    return {"email": _primary_email(u), "name": name, "image_url": u.get("image_url", "")}


async def init(database):
    global db
    db = database
    await db.users.create_index("user_id", unique=True)
    if not await db.settings.find_one({"key": "site"}):
        await db.settings.insert_one({"key": "site", **DEFAULT_SETTINGS})
    if await db.plans.count_documents({}) == 0:
        for p in SEED_PLANS:
            await db.plans.insert_one({"id": str(uuid.uuid4()), "active": True, "offer_active": False,
                                       "offer_price": None, "offer_label": "", **p, "created_at": now()})


async def get_profile(user=Depends(require_user)) -> dict:
    uid = user["user_id"]
    prof = await db.users.find_one({"user_id": uid}, {"_id": 0})
    if not prof or not prof.get("email"):
        info = _profile_from_clerk(await run_in_threadpool(_clerk, f"/users/{uid}"))
        await db.users.update_one({"user_id": uid}, {"$set": info, "$setOnInsert": {
            "user_id": uid, "active": True, "plan_id": None, "plan_name": None, "plan_expires_at": None,
            "created_at": now()}}, upsert=True)
        prof = await db.users.find_one({"user_id": uid}, {"_id": 0})
    return prof


async def require_active(prof=Depends(get_profile)) -> dict:
    if not prof.get("active", True):
        raise HTTPException(403, "Your account is deactivated. Please contact support.")
    return {"user_id": prof["user_id"]}


async def require_admin(prof=Depends(get_profile)) -> dict:
    if (prof.get("email") or "").lower() not in admin_emails():
        raise HTTPException(403, "Admin access required")
    return prof


def _plan_valid(prof):
    exp = prof.get("plan_expires_at")
    return bool(exp and exp > now())


@public.get("/me")
async def me(prof=Depends(get_profile)):
    return {**prof, "is_admin": (prof.get("email") or "").lower() in admin_emails(), "plan_valid": _plan_valid(prof)}


@public.get("/settings")
async def public_settings():
    s = await db.settings.find_one({"key": "site"}, {"_id": 0, "key": 0}) or {}
    return {**DEFAULT_SETTINGS, **s}


@public.get("/plans")
async def public_plans():
    return await db.plans.find({"active": True}, {"_id": 0}).sort("sort", 1).to_list(50)


class PaymentIn(BaseModel):
    plan_id: str
    utr: str = Field(min_length=6, max_length=40, pattern=r"^[A-Za-z0-9]+$")

    @field_validator("utr", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


def plan_amount(plan) -> float:
    return plan["offer_price"] if plan.get("offer_active") and plan.get("offer_price") is not None else plan["price"]


@public.post("/payments")
async def create_payment(body: PaymentIn, prof=Depends(get_profile)):
    plan = await db.plans.find_one({"id": body.plan_id, "active": True})
    if not plan:
        raise HTTPException(404, "Plan not found")
    utr = body.utr.strip().upper()
    if await db.payments.find_one({"utr": utr, "status": {"$ne": "rejected"}}):
        raise HTTPException(409, "This UPI transaction ID was already submitted")
    doc = {"id": str(uuid.uuid4()), "user_id": prof["user_id"], "email": prof.get("email"), "plan_id": plan["id"],
           "plan_name": plan["name"], "amount": plan_amount(plan), "duration_days": plan["duration_days"],
           "utr": utr, "status": "pending", "created_at": now()}
    await db.payments.insert_one(doc.copy())
    return doc


@public.get("/payments/mine")
async def my_payments(prof=Depends(get_profile)):
    return await db.payments.find({"user_id": prof["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)


# ---------- admin ----------

class Social(BaseModel):
    youtube: str = ""
    facebook: str = ""
    instagram: str = ""
    twitter: str = ""


class SettingsIn(BaseModel):
    site_name: str = Field(min_length=1, max_length=60)
    tagline: str = ""
    address: str = ""
    support_email: str = ""
    mobile: str = ""
    whatsapp: str = ""
    support_text: str = ""
    social: Social
    upi_id: str = ""
    upi_name: str = ""


class PlanIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    price: float = Field(ge=0)
    duration_days: int = Field(gt=0, le=3660)
    features: List[str] = []
    active: bool = True
    offer_active: bool = False
    offer_price: Optional[float] = Field(default=None, ge=0)
    offer_label: str = ""
    sort: int = 0


class UserPatch(BaseModel):
    active: Optional[bool] = None
    plan_id: Optional[str] = None  # "" removes plan


@admin.get("/stats")
async def stats(_=Depends(require_admin)):
    return {"users": await db.users.count_documents({}),
            "active_users": await db.users.count_documents({"active": True}),
            "paid_users": await db.users.count_documents({"plan_expires_at": {"$gt": now()}}),
            "pending_payments": await db.payments.count_documents({"status": "pending"}),
            "videos": await db.videos.count_documents({"is_deleted": False}),
            "streams": await db.streams.count_documents({})}


@admin.put("/settings")
async def save_settings(body: SettingsIn, _=Depends(require_admin)):
    await db.settings.update_one({"key": "site"}, {"$set": body.model_dump()}, upsert=True)
    return body.model_dump()


@admin.get("/plans")
async def all_plans(_=Depends(require_admin)):
    return await db.plans.find({}, {"_id": 0}).sort("sort", 1).to_list(100)


@admin.post("/plans")
async def create_plan(body: PlanIn, _=Depends(require_admin)):
    doc = {"id": str(uuid.uuid4()), **body.model_dump(), "created_at": now()}
    await db.plans.insert_one(doc.copy())
    return doc


@admin.put("/plans/{pid}")
async def update_plan(pid: str, body: PlanIn, _=Depends(require_admin)):
    r = await db.plans.update_one({"id": pid}, {"$set": body.model_dump()})
    if r.matched_count == 0:
        raise HTTPException(404, "Plan not found")
    return {"id": pid, **body.model_dump()}


@admin.delete("/plans/{pid}")
async def delete_plan(pid: str, _=Depends(require_admin)):
    r = await db.plans.delete_one({"id": pid})
    if r.deleted_count == 0:
        raise HTTPException(404, "Plan not found")
    return {"ok": True}


async def _sync_clerk_users():
    offset = 0
    while True:
        batch = await run_in_threadpool(_clerk, f"/users?limit=100&offset={offset}&order_by=-created_at")
        for u in batch:
            await db.users.update_one({"user_id": u["id"]}, {"$set": _profile_from_clerk(u), "$setOnInsert": {
                "user_id": u["id"], "active": True, "plan_id": None, "plan_name": None, "plan_expires_at": None,
                "created_at": datetime.fromtimestamp(u["created_at"] / 1000, timezone.utc).isoformat()}}, upsert=True)
        if len(batch) < 100:
            break
        offset += 100


@admin.get("/users")
async def list_users(_=Depends(require_admin)):
    try:
        await _sync_clerk_users()
    except requests.RequestException:
        pass
    users = await db.users.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)
    admins = admin_emails()
    return [{**u, "is_admin": (u.get("email") or "").lower() in admins, "plan_valid": _plan_valid(u)} for u in users]


@admin.patch("/users/{uid}")
async def update_user(uid: str, body: UserPatch, prof=Depends(require_admin)):
    target = await db.users.find_one({"user_id": uid})
    if not target:
        raise HTTPException(404, "User not found")
    update = {}
    if body.active is not None:
        if uid == prof["user_id"] and not body.active:
            raise HTTPException(400, "You cannot deactivate your own admin account")
        update["active"] = body.active
    if body.plan_id is not None:
        if body.plan_id == "":
            update.update(plan_id=None, plan_name=None, plan_expires_at=None)
        else:
            plan = await db.plans.find_one({"id": body.plan_id})
            if not plan:
                raise HTTPException(404, "Plan not found")
            update.update(plan_id=plan["id"], plan_name=plan["name"],
                          plan_expires_at=(datetime.now(timezone.utc) + timedelta(days=plan["duration_days"])).isoformat())
    if update:
        await db.users.update_one({"user_id": uid}, {"$set": update})
    if body.active is False:
        try:
            from backend import streamer
        except ModuleNotFoundError:
            import streamer
        await streamer.stop(uid)
    return await db.users.find_one({"user_id": uid}, {"_id": 0})


@admin.get("/payments")
async def list_payments(status: Optional[Literal["pending", "approved", "rejected"]] = None, _=Depends(require_admin)):
    q = {"status": status} if status else {}
    return await db.payments.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)


@admin.post("/payments/{pay_id}/{action}")
async def decide_payment(pay_id: str, action: Literal["approve", "reject"], _=Depends(require_admin)):
    pay = await db.payments.find_one_and_update({"id": pay_id, "status": "pending"},
                                                {"$set": {"status": "approved" if action == "approve" else "rejected",
                                                          "decided_at": now()}})
    if not pay:
        raise HTTPException(404, "Pending payment not found")
    if action == "approve":
        user = await db.users.find_one({"user_id": pay["user_id"]}) or {}
        start = datetime.now(timezone.utc)
        if user.get("plan_id") == pay["plan_id"] and _plan_valid(user):
            start = datetime.fromisoformat(user["plan_expires_at"])
        await db.users.update_one({"user_id": pay["user_id"]}, {"$set": {
            "plan_id": pay["plan_id"], "plan_name": pay["plan_name"],
            "plan_expires_at": (start + timedelta(days=pay["duration_days"])).isoformat()}})
    return {"id": pay_id, "status": "approved" if action == "approve" else "rejected"}
