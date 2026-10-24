# Admin panel tests: auth gating, public settings/plans, plans CRUD+offers, users activate/plan, UPI payments, settings
import asyncio
import json
import os
import uuid

import pytest
import requests
import websockets
from pymongo import MongoClient

from conftest import API, BASE_URL, make_user, token_for

ADMIN_EMAIL = "admin+clerk_test@example.com"


@pytest.fixture(scope="module")
def admin_h():
    _, sess = make_user(ADMIN_EMAIL)
    return {"Authorization": f"Bearer {token_for(sess)}"}


@pytest.fixture(scope="module")
def user_d():
    # dedicated user for deactivation tests (deactivating user_a would kill its streams in other workers)
    u, sess = make_user("deact+clerk_test@example.com")
    return {"user": u, "headers": {"Authorization": f"Bearer {token_for(sess)}"}}


@pytest.fixture(scope="class")
def mongo():
    # class-scoped so cleanup can't race tests running in the other xdist worker
    c = MongoClient(os.environ["MONGO_URL"])
    yield c[os.environ["DB_NAME"]]
    c.close()


@pytest.fixture(scope="class")
def cleanup_payments(mongo):
    yield
    mongo.payments.delete_many({"utr": {"$regex": "^TEST"}})


@pytest.fixture(scope="module", autouse=True)
def restore(admin_h, user_a):
    s = requests.get(f"{API}/settings").json()
    yield
    s["address"] = "Tripoliya, Patna, Bihar"
    requests.put(f"{API}/admin/settings", json=s, headers=admin_h)
    requests.patch(f"{API}/admin/users/{user_a['user']['id']}", json={"active": True}, headers=admin_h)


# --- auth gating ---
class TestAdminAuth:
    def test_no_token_401(self):
        for p in ["stats", "users", "plans", "payments"]:
            assert requests.get(f"{API}/admin/{p}").status_code == 401, p

    def test_normal_user_403(self, user_a):
        r = requests.get(f"{API}/admin/stats", headers=user_a["headers"])
        assert r.status_code == 403

    def test_admin_200(self, admin_h):
        r = requests.get(f"{API}/admin/stats", headers=admin_h)
        assert r.status_code == 200
        assert {"users", "active_users", "pending_payments"} <= set(r.json())

    def test_me_fields(self, user_a, admin_h):
        m = requests.get(f"{API}/me", headers=user_a["headers"]).json()
        assert m["email"] == "creator+clerk_test@example.com" and m["is_admin"] is False
        for k in ["active", "plan_id", "plan_expires_at", "plan_valid"]:
            assert k in m
        assert "_id" not in m
        a = requests.get(f"{API}/me", headers=admin_h).json()
        assert a["is_admin"] is True and a["email"] == ADMIN_EMAIL


# --- public ---
class TestPublic:
    def test_settings(self):
        r = requests.get(f"{API}/settings")
        assert r.status_code == 200
        d = r.json()
        assert "social" in d and "site_name" in d and "_id" not in d

    def test_seeded_plans(self):
        plans = requests.get(f"{API}/plans").json()
        by = {p["name"]: p for p in plans}
        assert by["Starter"]["price"] == 199 and by["Starter"]["duration_days"] == 30
        assert by["Pro"]["price"] == 499 and by["Pro Yearly"]["duration_days"] == 365
        assert all(p["active"] for p in plans)


# --- plans CRUD ---
class TestPlans:
    def test_crud_and_offer(self, admin_h, user_a):
        body = {"name": "TEST_Plan", "price": 99, "duration_days": 7, "features": ["a"], "sort": 9}
        assert requests.post(f"{API}/admin/plans", json=body, headers=user_a["headers"]).status_code == 403
        r = requests.post(f"{API}/admin/plans", json=body, headers=admin_h)
        assert r.status_code == 200
        pid = r.json()["id"]
        pub = {p["id"]: p for p in requests.get(f"{API}/plans").json()}
        assert pid in pub and pub[pid]["price"] == 99
        body.update(offer_active=True, offer_price=49, offer_label="Diwali")
        r = requests.put(f"{API}/admin/plans/{pid}", json=body, headers=admin_h)
        assert r.status_code == 200
        pub = {p["id"]: p for p in requests.get(f"{API}/plans").json()}
        assert pub[pid]["offer_active"] and pub[pid]["offer_price"] == 49 and pub[pid]["offer_label"] == "Diwali"
        body["active"] = False
        requests.put(f"{API}/admin/plans/{pid}", json=body, headers=admin_h)
        assert pid not in [p["id"] for p in requests.get(f"{API}/plans").json()]
        assert pid in [p["id"] for p in requests.get(f"{API}/admin/plans", headers=admin_h).json()]
        assert requests.delete(f"{API}/admin/plans/{pid}", headers=admin_h).status_code == 200
        assert requests.delete(f"{API}/admin/plans/{pid}", headers=admin_h).status_code == 404
        assert requests.put(f"{API}/admin/plans/{pid}", json=body, headers=admin_h).status_code == 404

    def test_validation(self, admin_h):
        r = requests.post(f"{API}/admin/plans", json={"name": "", "price": -1, "duration_days": 0}, headers=admin_h)
        assert r.status_code == 422


# --- users ---
class TestUsers:
    def test_list_has_emails(self, admin_h, user_a):
        users = requests.get(f"{API}/admin/users", headers=admin_h).json()
        emails = [u["email"] for u in users]
        assert "creator+clerk_test@example.com" in emails and ADMIN_EMAIL in emails
        assert all("_id" not in u for u in users)

    def test_self_deactivate_400(self, admin_h):
        me = requests.get(f"{API}/me", headers=admin_h).json()
        r = requests.patch(f"{API}/admin/users/{me['user_id']}", json={"active": False}, headers=admin_h)
        assert r.status_code == 400

    def test_unknown_user_404(self, admin_h):
        assert requests.patch(f"{API}/admin/users/nope", json={"active": True}, headers=admin_h).status_code == 404

    def test_deactivate_blocks_writes(self, admin_h, user_d):
        uid = user_d["user"]["id"]
        h = user_d["headers"]
        requests.get(f"{API}/admin/users", headers=admin_h)  # sync new Clerk user into db
        dest = requests.get(f"{API}/destinations", headers=h)
        assert dest.status_code == 200
        r = requests.patch(f"{API}/admin/users/{uid}", json={"active": False}, headers=admin_h)
        assert r.status_code == 200 and r.json()["active"] is False
        try:
            r = requests.put(f"{API}/destinations", json=dest.json(), headers=h)
            assert r.status_code == 403 and "deactivated" in r.json()["detail"]
            r = requests.post(f"{API}/uploads", files={"file": ("x.mp4", b"0" * 10, "video/mp4")}, headers=h)
            assert r.status_code == 403
            r = requests.post(f"{API}/streams/video", json={"video_id": "x"}, headers=h)
            assert r.status_code == 403
            assert requests.get(f"{API}/destinations", headers=h).status_code == 200
            assert requests.get(f"{API}/me", headers=h).json()["active"] is False

            async def ws():
                tok = h["Authorization"].split()[1]
                url = BASE_URL.replace("https", "wss") + f"/api/ws/live?token={tok}"
                async with websockets.connect(url) as c:
                    return json.loads(await asyncio.wait_for(c.recv(), 15))
            msg = asyncio.run(ws())
            assert "deactivated" in msg.get("error", "")
        finally:
            r = requests.patch(f"{API}/admin/users/{uid}", json={"active": True}, headers=admin_h)
            assert r.json()["active"] is True
        assert requests.put(f"{API}/destinations", json=dest.json(), headers=h).status_code == 200

# --- UPI payments ---
class TestPayments:
    def test_flow(self, admin_h, user_a, cleanup_payments):
        from datetime import datetime
        uid = user_a["user"]["id"]
        h = user_a["headers"]
        requests.patch(f"{API}/admin/users/{uid}", json={"plan_id": ""}, headers=admin_h)
        pro = next(p for p in requests.get(f"{API}/plans").json() if p["name"] == "Pro")
        assert requests.post(f"{API}/payments", json={"plan_id": pro["id"], "utr": "123"}, headers=h).status_code == 422
        assert requests.post(f"{API}/payments", json={"plan_id": "bad", "utr": "TEST123456"}, headers=h).status_code == 404
        assert requests.post(f"{API}/payments", json={"plan_id": pro["id"], "utr": "TEST1"}).status_code == 401
        u1 = "TEST" + uuid.uuid4().hex[:10].upper()
        r = requests.post(f"{API}/payments", json={"plan_id": pro["id"], "utr": u1}, headers=h)
        assert r.status_code == 200 and r.json()["status"] == "pending" and r.json()["amount"] == pro["price"]
        p1 = r.json()["id"]
        assert requests.post(f"{API}/payments", json={"plan_id": pro["id"], "utr": u1.lower()}, headers=h).status_code == 409
        assert p1 in [p["id"] for p in requests.get(f"{API}/payments/mine", headers=h).json()]
        pend = requests.get(f"{API}/admin/payments?status=pending", headers=admin_h).json()
        assert p1 in [p["id"] for p in pend] and all(p["status"] == "pending" for p in pend)
        assert requests.get(f"{API}/admin/payments?status=bogus", headers=admin_h).status_code == 422
        assert requests.post(f"{API}/admin/payments/{p1}/approve", headers=h).status_code == 403
        r = requests.post(f"{API}/admin/payments/{p1}/approve", headers=admin_h)
        assert r.status_code == 200 and r.json()["status"] == "approved"
        assert requests.post(f"{API}/admin/payments/{p1}/approve", headers=admin_h).status_code == 404
        me = requests.get(f"{API}/me", headers=h).json()
        assert me["plan_id"] == pro["id"] and me["plan_valid"]
        exp1 = datetime.fromisoformat(me["plan_expires_at"])
        # renewal extends
        u2 = "TEST" + uuid.uuid4().hex[:10].upper()
        p2 = requests.post(f"{API}/payments", json={"plan_id": pro["id"], "utr": u2}, headers=h).json()["id"]
        requests.post(f"{API}/admin/payments/{p2}/approve", headers=admin_h)
        exp2 = datetime.fromisoformat(requests.get(f"{API}/me", headers=h).json()["plan_expires_at"])
        assert (exp2 - exp1).days == pro["duration_days"]
        # reject
        u3 = "TEST" + uuid.uuid4().hex[:10].upper()
        p3 = requests.post(f"{API}/payments", json={"plan_id": pro["id"], "utr": u3}, headers=h).json()["id"]
        r = requests.post(f"{API}/admin/payments/{p3}/reject", headers=admin_h)
        assert r.json()["status"] == "rejected"
        assert requests.post(f"{API}/admin/payments/{p3}/approve", headers=admin_h).status_code == 404
        mine = {p["id"]: p for p in requests.get(f"{API}/payments/mine", headers=h).json()}
        assert mine[p3]["status"] == "rejected" and mine[p1]["status"] == "approved"
        # rejected UTR can be resubmitted
        assert requests.post(f"{API}/payments", json={"plan_id": pro["id"], "utr": u3}, headers=h).status_code == 200


    def test_assign_and_remove_plan(self, admin_h, user_a):
        uid = user_a["user"]["id"]
        starter = next(p for p in requests.get(f"{API}/plans").json() if p["name"] == "Starter")
        r = requests.patch(f"{API}/admin/users/{uid}", json={"plan_id": starter["id"]}, headers=admin_h)
        assert r.status_code == 200 and r.json()["plan_name"] == "Starter" and r.json()["plan_expires_at"]
        assert requests.get(f"{API}/me", headers=user_a["headers"]).json()["plan_valid"] is True
        r = requests.patch(f"{API}/admin/users/{uid}", json={"plan_id": ""}, headers=admin_h)
        assert r.json()["plan_id"] is None and r.json()["plan_expires_at"] is None
        assert requests.patch(f"{API}/admin/users/{uid}", json={"plan_id": "bad"}, headers=admin_h).status_code == 404


# --- settings ---
class TestSettings:
    def test_update(self, admin_h, user_a):
        s = requests.get(f"{API}/settings").json()
        s.update(mobile="+91 9000000001", whatsapp="+91 9000000002", support_email="help@example.com",
                 site_name="CreatorLive24/7", upi_id="test@upi")
        s["social"] = {"youtube": "https://youtube.com/@t", "facebook": "https://facebook.com/t",
                       "instagram": "https://instagram.com/t", "twitter": "https://x.com/t"}
        assert requests.put(f"{API}/admin/settings", json=s, headers=user_a["headers"]).status_code == 403
        r = requests.put(f"{API}/admin/settings", json=s, headers=admin_h)
        assert r.status_code == 200
        g = requests.get(f"{API}/settings").json()
        assert g["mobile"] == "+91 9000000001" and g["upi_id"] == "test@upi"
        assert g["social"]["instagram"] == "https://instagram.com/t"
        bad = dict(s, site_name="")
        assert requests.put(f"{API}/admin/settings", json=bad, headers=admin_h).status_code == 422
