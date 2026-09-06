from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

# 👈 uvicorn এই 'app' নামটাই খুঁজছে!
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
        payload = {"url": target_url}
        requests.post(
            GOOGLE_SHEET_API, 
            json=payload, 
            headers={"Content-Type": "application/json"},
            allow_redirects=True,
            timeout=10
        )
    except Exception:
        pass

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
