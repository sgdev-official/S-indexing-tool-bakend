from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI(title="S-Indexer Core Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KV_URL = os.getenv("KV_REST_API_URL")
KV_TOKEN = os.getenv("KV_REST_API_TOKEN")

class IndexRequest(BaseModel):
    url: str

def push_to_vercel_kv(target_url: str):
    try:
        headers = {"Authorization": f"Bearer {KV_TOKEN}"}
        url = f"{KV_URL}/lpush/urls/{target_url}"
        response = requests.get(url, headers=headers, timeout=5)
        print(f"KV Push Response: {response.status_code}")
    except Exception as e:
        print(f"KV Push Error: {e}")

@app.get("/")
def root_check():
    return {"status": "online", "system": "S-Indexer Vercel KV Active"}

@app.get("/feed")
def get_feed_urls():
    try:
        headers = {"Authorization": f"Bearer {KV_TOKEN}"}
        url = f"{KV_URL}/lrange/urls/0/99"
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        return {"urls": data.get("result", [])}
    except Exception as e:
        return {"urls": [], "error": str(e)}

@app.post("/index")
async def handle_indexing(req: IndexRequest, background_tasks: BackgroundTasks):
    if not req.url or not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    background_tasks.add_task(push_to_vercel_kv, req.url)

    return {
        "success": True,
        "message": "URL successfully queued in Vercel KV",
        "target_url": req.url
    }
