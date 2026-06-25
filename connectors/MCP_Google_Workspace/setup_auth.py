"""
Run this once to authenticate with Google and save token.json.
Usage: python3 setup_auth.py
"""
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    # TODO: Uncomment to enable Gmail, Docs, Tasks:
    # "https://www.googleapis.com/auth/gmail.modify",
    # "https://www.googleapis.com/auth/documents",
    # "https://www.googleapis.com/auth/tasks",
]


def main():
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: {CREDENTIALS_FILE} not found.")
        print()
        print("Steps to get credentials.json:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create/select a project")
        print("  3. Enable Google Drive, Calendar, Sheets APIs")
        print("  4. APIs & Services -> Credentials -> Create OAuth 2.0 Client ID")
        print("  5. Application type: Desktop app")
        print("  6. Download JSON -> save as credentials.json in this folder")
        return

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Token refreshed.")
        else:
            with open(CREDENTIALS_FILE) as f:
                cred_data = json.load(f)
            if "installed" in cred_data:
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            else:
                flow = InstalledAppFlow.from_client_config(
                    {"installed": cred_data["web"]}, SCOPES
                )
            creds = flow.run_local_server(port=8085, prompt='consent', access_type='offline')
            print("Authentication successful!")

        TOKEN_FILE.write_text(creds.to_json())
        import os
        os.chmod(TOKEN_FILE, 0o600)
        print(f"Token saved to {TOKEN_FILE}")
    else:
        print("Already authenticated. token.json is valid.")


if __name__ == "__main__":
    main()
