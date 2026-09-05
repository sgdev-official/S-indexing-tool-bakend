"""
S-Indexer API
=============
Developer: Sgdev

A lightweight, serverless-ready FastAPI backend that accepts a target URL,
dispatches it to IndexNow protocol, and logs submission data into Google Sheets Queue DB.
"""

import random
import logging
from typing import List

import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("s-indexer")

# ---------------------------------------------------------------------------
# App metadata & constants
# ---------------------------------------------------------------------------
APP_VERSION = "1.0.0"
DEVELOPER = "Sgdev"

FEED_NODES: List[str] = [
    "https://1.sindex.duckdns.org",
    "https://2.sindex.duckdns.org",
    "https://3.sindex.duckdns.org",
    "https://4.sindex.duckdns.org",
    "https://5.sindex.duckdns.org",
]

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_HOST = "sindex.duckdns.org"
INDEXNOW_KEY = "sindex-auth-key-1234"
INDEXNOW_KEY_LOCATION = "https://sindex.duckdns.org/indexnow_key.txt"

# Google Apps Script Web App URL
GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzG1fAg6CKkbsOLaNgGRsuqvYoyg8tva6VwPQusEfzsISyJXmVchP_72Vjj9_jY3zATEQ/exec"

OUTBOUND_TIMEOUT = 10.0

# ---------------------------------------------------------------------------
# FastAPI app instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="S-Indexer API",
    description="Automated URL indexing platform (IndexNow dispatcher & Google Sheets Queue Logger).",
    version=APP_VERSION,
)

# ---------------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class URLSubmission(BaseModel):
    url: HttpUrl


class SubmissionResponse(BaseModel):
    success: bool
    message: str
    target_url: str
    assigned_feed_node: str
    indexnow_dispatched: bool


# ---------------------------------------------------------------------------
# Background task: dispatch to IndexNow & Log to Google Sheet
# ---------------------------------------------------------------------------
async def process_background_tasks(target_url: str, assigned_node: str) -> None:
    """
    1. Dispatch to IndexNow API
    2. Post submission record to Google Sheets Apps Script Web App DB
    """
    indexnow_status = "Failed"

    # Step 1: Dispatch IndexNow Ping
    payload = {
        "host": INDEXNOW_HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": INDEXNOW_KEY_LOCATION,
        "urlList": [target_url],
    }

    try:
        async with httpx.AsyncClient(timeout=OUTBOUND_TIMEOUT, follow_redirects=True) as client:
            response = await client.post(
                INDEXNOW_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            if response.status_code in (200, 202):
                indexnow_status = "Dispatched"
                logger.info("IndexNow accepted submission for %s", target_url)
            else:
                logger.warning("IndexNow status %s for %s", response.status_code, target_url)
    except Exception as exc:
        logger.error("IndexNow dispatch failed for %s: %s", target_url, exc)

    # Step 2: Save Log to Google Sheet Queue DB
    if GOOGLE_SHEET_WEBAPP_URL:
        sheet_payload = {
            "url": target_url,
            "node": assigned_node,
            "indexnow": indexnow_status
        }
        try:
            async with httpx.AsyncClient(timeout=OUTBOUND_TIMEOUT, follow_redirects=True) as client:
                await client.post(GOOGLE_SHEET_WEBAPP_URL, json=sheet_payload)
                logger.info("Successfully logged %s to Google Sheet DB", target_url)
        except Exception as exc:
            logger.error("Failed to log to Google Sheet: %s", exc)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "S-Indexer",
        "version": APP_VERSION,
        "developer": DEVELOPER,
    }


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/submit", response_model=SubmissionResponse)
async def submit_url(payload: URLSubmission, background_tasks: BackgroundTasks):
    try:
        target_url = str(payload.url)
        assigned_node = random.choice(FEED_NODES)

        # Background task processing (IndexNow + Google Sheets logging)
        background_tasks.add_task(process_background_tasks, target_url, assigned_node)

        return SubmissionResponse(
            success=True,
            message="URL received, queued for IndexNow dispatch and logged to Sheet.",
            target_url=target_url,
            assigned_feed_node=assigned_node,
            indexnow_dispatched=True,
        )
    except Exception as exc:
        logger.exception("Failed to process submission")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process URL submission: {exc}",
        )
    app=app
