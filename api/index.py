from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json

app = FastAPI(title="S-Indexer Core Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzG1fAg6CKkbsOLaNgGRsuqvYoyg8tva6VwPQusEfzsISyJXmVchP_72Vjj9_jY3zATEQ/exec"

class IndexRequest(BaseModel):
    url: str

def push_to_google_sheet(target_url: str):
    try:
        payload = json.dumps({"url": target_url})
        headers = {"Content-Type": "text/plain;charset=utf-8"}
        response = requests.post(
            GOOGLE_SHEET_API, 
            data=payload, 
            headers=headers,
            allow_redirects=True,
            timeout=10
        )
        print(f"Sheet Sync Status: {response.status_code}")
    except Exception as e:
        print(f"Sheet Sync Error: {e}")

@app.get("/")
def root_check():
    return {"status": "online", "system": "S-Indexer Active"}

@app.post("/api/v1/index")
async def handle_indexing(req: IndexRequest, background_tasks: BackgroundTasks):
    if not req.url or not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    background_tasks.add_task(push_to_google_sheet, req.url)

    return {
        "success": True,
        "message": "URL successfully queued",
        "target_url": req.url
    }
