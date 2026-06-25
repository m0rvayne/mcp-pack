"""
Google Workspace MCP — shared OAuth authentication.
All API modules import credentials and service builders from here.
"""

import os
import threading
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]

_creds_cache = None
_creds_lock = threading.Lock()
_services: dict = {}


def get_creds() -> Credentials:
    global _creds_cache
    with _creds_lock:
        if _creds_cache and _creds_cache.valid:
            return _creds_cache
        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    raise RuntimeError(
                        f"Google authentication required. Place credentials.json in {BASE_DIR} and run setup_auth.py first."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=8085, prompt="consent", access_type="offline")
            TOKEN_FILE.write_text(creds.to_json())
            os.chmod(TOKEN_FILE, 0o600)
            _services.clear()
        _creds_cache = creds
        return creds


def get_service(api: str, version: str):
    key = f"{api}:{version}"
    if key not in _services:
        _services[key] = build(api, version, credentials=get_creds())
    return _services[key]


def drive():
    return get_service("drive", "v3")


def calendar():
    return get_service("calendar", "v3")


def sheets():
    return get_service("sheets", "v4")


def docs():
    return get_service("docs", "v1")
