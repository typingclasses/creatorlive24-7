import os
import requests

STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
APP_NAME = "creatorlive247"
storage_key = None


def init_storage(force: bool = False):
    global storage_key
    if storage_key and not force:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    for attempt in range(2):
        resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": init_storage(force=attempt > 0), "Content-Type": content_type},
                            data=data, timeout=600)
        if resp.status_code != 404:
            break
    resp.raise_for_status()
    return resp.json()


def put_file(path: str, local: str, content_type: str) -> dict:
    for attempt in range(2):
        with open(local, "rb") as f:
            resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                                headers={"X-Storage-Key": init_storage(force=attempt > 0), "Content-Type": content_type},
                                data=f, timeout=900)
        if resp.status_code != 404:
            break
    resp.raise_for_status()
    return resp.json()


def download_to_file(path: str, dest: str):
    for attempt in range(2):
        with requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": init_storage(force=attempt > 0)},
                          stream=True, timeout=600) as resp:
            if resp.status_code == 404 and attempt == 0:
                continue
            resp.raise_for_status()
            with open(dest + ".part", "wb") as f:
                for chunk in resp.iter_content(1024 * 1024):
                    f.write(chunk)
            os.replace(dest + ".part", dest)
            return


def download_parts(paths, dest: str):
    with open(dest + ".part", "wb") as f:
        for p in paths:
            for attempt in range(2):
                resp = requests.get(f"{STORAGE_URL}/objects/{p}", headers={"X-Storage-Key": init_storage(force=attempt > 0)}, timeout=600)
                if resp.status_code != 404:
                    break
            resp.raise_for_status()
            f.write(resp.content)
    os.replace(dest + ".part", dest)


def iter_parts(paths):
    for p in paths:
        for attempt in range(2):
            resp = requests.get(f"{STORAGE_URL}/objects/{p}", headers={"X-Storage-Key": init_storage(force=attempt > 0)}, timeout=600)
            if resp.status_code != 404:
                break
        resp.raise_for_status()
        yield resp.content


def get_object(path: str):
    resp = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": init_storage()}, timeout=600)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
