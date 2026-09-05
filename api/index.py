import os
import json
import random
import logging
import urllib.request

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("s-indexer")

APP_VERSION = "1.0.0"
DEVELOPER = "Sgdev"

FEED_NODES = [
    "https://1.sindex.duckdns.org",
    "https://2.sindex.duckdns.org",
    "https://3.sindex.duckdns.org",
    "https://4.sindex.duckdns.org",
    "https://5.sindex.duckdns.org",
]

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_HOST = "sindex.duckdns.org"
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "sindex-auth-key-1234")
INDEXNOW_KEY_LOCATION = os.environ.get("INDEXNOW_KEY_LOCATION", "https://sindex.duckdns.org/indexnow_key.txt")
GOOGLE_SHEET_WEBAPP_URL = os.environ.get(
    "GOOGLE_SHEET_WEBAPP_URL",
    "https://script.google.com/macros/s/AKfycbzG1fAg6CKkbsOLaNgGRsuqvYoyg8tva6VwPQusEfzsISyJXmVchP_72Vjj9_jY3zATEQ/exec"
)

# Vercel-এর জন্য 'app' অবজেক্ট
app = FastAPI(title="S-Indexer API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLSubmission(BaseModel):
    url: str

def send_post_request(url: str, data: dict) -> bool:
    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=json_data, 
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status in (200, 202)
    except Exception as exc:
        logger.error("HTTP Request failed: %s", exc)
        return False

def process_background_tasks(target_url: str, assigned_node: str) -> None:
    indexnow_status = "Failed"
    payload = {
        "host": INDEXNOW_HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": INDEXNOW_KEY_LOCATION,
        "urlList": [target_url],
    }
    if send_post_request(INDEXNOW_ENDPOINT, payload):
        indexnow_status = "Dispatched"

    if GOOGLE_SHEET_WEBAPP_URL:
        sheet_payload = {
            "url": target_url,
            "node": assigned_node,
            "indexnow": indexnow_status
        }
        send_post_request(GOOGLE_SHEET_WEBAPP_URL, sheet_payload)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "S-Indexer",
        "version": APP_VERSION,
        "developer": DEVELOPER,
    }

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/submit")
def submit_url(payload: URLSubmission, background_tasks: BackgroundTasks):
    try:
        target_url = payload.url
        assigned_node = random.choice(FEED_NODES)
        background_tasks.add_task(process_background_tasks, target_url, assigned_node)

        return {
            "success": True,
            "message": "URL received and queued.",
            "target_url": target_url,
            "assigned_feed_node": assigned_node,
            "indexnow_dispatched": True,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
