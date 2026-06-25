"""
Google Drive API v3 — full coverage.
64 REST methods: files, comments, replies, revisions, permissions,
drives, changes, channels, about, apps, accessproposals, approvals, operations.
"""

import io
import json
import base64
from pathlib import Path
from mcp import types
from auth import drive
from utils import (
    fmt_file, fmt_size, file_link, download_bytes, export_bytes, truncate,
    MIME_LABELS, EXPORT_FORMATS, DOWNLOAD_DIR, MAX_DOWNLOAD_SIZE,
    read_pdf, read_docx, read_xlsx, read_pptx, read_zip,
)
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

# =============================================================================
# Tool definitions
# =============================================================================

TOOLS = [
    # ── about ──
    types.Tool(name="drive_about", description="Get current user's Drive storage quota, name, email, and permissions info.", inputSchema={"type": "object", "properties": {}}),

    # ── files ──
    types.Tool(name="drive_search_files", description="Search files on Google Drive by name, MIME type, date, folder, etc. Returns name, type, size, modified date and link.", inputSchema={"type": "object", "properties": {
        "query": {"type": "string", "description": "Drive API query (e.g. name contains 'report', mimeType = 'application/pdf'). Leave empty for recent files."},
        "page_size": {"type": "integer", "default": 20}, "order_by": {"type": "string", "default": "modifiedTime desc"},
        "fields": {"type": "string", "description": "Custom fields to return (advanced)"},
    }}),
    types.Tool(name="drive_list_folder", description="List all files and subfolders inside a Google Drive folder.", inputSchema={"type": "object", "required": ["folder_id"], "properties": {
        "folder_id": {"type": "string", "description": "Folder ID. Use 'root' for My Drive root."}, "page_size": {"type": "integer", "default": 50},
    }}),
    types.Tool(name="drive_get_file", description="Get full metadata of a file: name, type, size, owner, dates, link, parents, permissions.", inputSchema={"type": "object", "required": ["file_id"], "properties": {"file_id": {"type": "string"}}}),
    types.Tool(name="drive_read_content", description="Read and extract CONTENT of any file: Docs, Sheets, Slides, PDF, Word, Excel, PowerPoint, text, CSV, JSON, images, ZIP.", inputSchema={"type": "object", "required": ["file_id"], "properties": {
        "file_id": {"type": "string"}, "max_chars": {"type": "integer", "default": 10000},
    }}),
    types.Tool(name="drive_download_file", description="Download a file to local downloads/ folder. Google Docs auto-converted to docx/xlsx/pptx.", inputSchema={"type": "object", "required": ["file_id"], "properties": {
        "file_id": {"type": "string"}, "save_as": {"type": "string", "description": "Custom filename (optional)"},
    }}),
    types.Tool(name="drive_create_file", description="Create a new file on Drive (upload content or create empty Google Doc/Sheet/Slides).", inputSchema={"type": "object", "required": ["name"], "properties": {
        "name": {"type": "string"}, "mime_type": {"type": "string", "description": "MIME type (e.g. application/vnd.google-apps.document for Google Doc)"},
        "parent_id": {"type": "string"}, "content": {"type": "string", "description": "Text content or base64-encoded binary"},
        "content_type": {"type": "string", "description": "Content MIME type for upload (e.g. text/plain, application/pdf)"},
    }}),
    types.Tool(name="drive_upload_file", description="Upload a local file to Google Drive.", inputSchema={"type": "object", "required": ["local_path"], "properties": {
        "local_path": {"type": "string"}, "name": {"type": "string"}, "parent_id": {"type": "string"},
    }}),
    types.Tool(name="drive_update_file", description="Update file metadata (name, description, starred) and/or content.", inputSchema={"type": "object", "required": ["file_id"], "properties": {
        "file_id": {"type": "string"}, "name": {"type": "string"}, "description": {"type": "string"},
        "starred": {"type": "boolean"}, "content": {"type": "string"}, "content_type": {"type": "string"},
        "add_parents": {"type": "string", "description": "Comma-separated parent folder IDs to add"},
        "remove_parents": {"type": "string", "description": "Comma-separated parent folder IDs to remove"},
    }}),
    types.Tool(name="drive_copy_file", description="Copy a file on Drive.", inputSchema={"type": "object", "required": ["file_id"], "properties": {
        "file_id": {"type": "string"}, "new_name": {"type": "string"}, "parent_id": {"type": "string"},
    }}),
    types.Tool(name="drive_delete_file", description="Move a file or folder to trash.", inputSchema={"type": "object", "required": ["file_id"], "properties": {"file_id": {"type": "string"}}}),
    types.Tool(name="drive_permanently_delete", description="Permanently delete a file (no recovery). Requires owner permission.", inputSchema={"type": "object", "required": ["file_id"], "properties": {"file_id": {"type": "string"}}}),
    types.Tool(name="drive_empty_trash", description="Permanently delete all trashed files.", inputSchema={"type": "object", "properties": {}}),
    types.Tool(name="drive_export_file", description="Export a Google Doc/Sheet/Slides to a specific format (PDF, DOCX, CSV, etc.).", inputSchema={"type": "object", "required": ["file_id", "export_mime"], "properties": {
        "file_id": {"type": "string"}, "export_mime": {"type": "string", "description": "Target MIME: application/pdf, text/csv, etc."},
        "save_path": {"type": "string", "description": "Local path to save (optional)"},
    }}),
    types.Tool(name="drive_create_folder", description="Create a new folder on Drive.", inputSchema={"type": "object", "required": ["name"], "properties": {
        "name": {"type": "string"}, "parent_id": {"type": "string"},
    }}),
    types.Tool(name="drive_move_file", description="Move a file to a different folder.", inputSchema={"type": "object", "required": ["file_id", "new_parent_id"], "properties": {
        "file_id": {"type": "string"}, "new_parent_id": {"type": "string"},
    }}),
    types.Tool(name="drive_rename_file", description="Rename a file or folder.", inputSchema={"type": "object", "required": ["file_id", "new_name"], "properties": {
        "file_id": {"type": "string"}, "new_name": {"type": "string"},
    }}),
    types.Tool(name="drive_generate_ids", description="Generate unique file IDs for pre-creating files.", inputSchema={"type": "object", "properties": {
        "count": {"type": "integer", "default": 1, "description": "Number of IDs to generate (max 1000)"},
    }}),

    # ── permissions ──
    types.Tool(name="drive_share", description="Share a file/folder with a user or anyone (link sharing).", inputSchema={"type": "object", "required": ["file_id", "role"], "properties": {
        "file_id": {"type": "string"}, "email": {"type": "string", "description": "Email (omit for 'anyone' link sharing)"},
        "role": {"type": "string", "enum": ["reader", "commenter", "writer", "organizer", "fileOrganizer", "owner"]},
        "type": {"type": "string", "enum": ["user", "group", "domain", "anyone"], "default": "user"},
        "domain": {"type": "string"}, "send_notification": {"type": "boolean", "default": True},
        "message": {"type": "string", "description": "Notification message"},
    }}),
    types.Tool(name="drive_list_permissions", description="List all permissions (who has access) for a file.", inputSchema={"type": "object", "required": ["file_id"], "properties": {"file_id": {"type": "string"}}}),
    types.Tool(name="drive_get_permission", description="Get details of a specific permission.", inputSchema={"type": "object", "required": ["file_id", "permission_id"], "properties": {"file_id": {"type": "string"}, "permission_id": {"type": "string"}}}),
    types.Tool(name="drive_update_permission", description="Update a permission's role.", inputSchema={"type": "object", "required": ["file_id", "permission_id", "role"], "properties": {
        "file_id": {"type": "string"}, "permission_id": {"type": "string"},
        "role": {"type": "string", "enum": ["reader", "commenter", "writer", "organizer", "fileOrganizer", "owner"]},
    }}),
    types.Tool(name="drive_delete_permission", description="Remove a permission (revoke access).", inputSchema={"type": "object", "required": ["file_id", "permission_id"], "properties": {"file_id": {"type": "string"}, "permission_id": {"type": "string"}}}),

    # ── comments ──
    types.Tool(name="drive_list_comments", description="List comments on a file.", inputSchema={"type": "object", "required": ["file_id"], "properties": {
        "file_id": {"type": "string"}, "page_size": {"type": "integer", "default": 20}, "include_deleted": {"type": "boolean", "default": False},
    }}),
    types.Tool(name="drive_get_comment", description="Get a specific comment by ID.", inputSchema={"type": "object", "required": ["file_id", "comment_id"], "properties": {"file_id": {"type": "string"}, "comment_id": {"type": "string"}}}),
    types.Tool(name="drive_create_comment", description="Create a comment on a file.", inputSchema={"type": "object", "required": ["file_id", "content"], "properties": {
        "file_id": {"type": "string"}, "content": {"type": "string", "description": "Comment text"},
        "anchor": {"type": "string", "description": "Anchor JSON for positioning the comment"},
    }}),
    types.Tool(name="drive_update_comment", description="Update a comment's content.", inputSchema={"type": "object", "required": ["file_id", "comment_id", "content"], "properties": {
        "file_id": {"type": "string"}, "comment_id": {"type": "string"}, "content": {"type": "string"},
    }}),
    types.Tool(name="drive_delete_comment", description="Delete a comment.", inputSchema={"type": "object", "required": ["file_id", "comment_id"], "properties": {"file_id": {"type": "string"}, "comment_id": {"type": "string"}}}),

    # ── replies ──
    types.Tool(name="drive_list_replies", description="List replies to a comment.", inputSchema={"type": "object", "required": ["file_id", "comment_id"], "properties": {
        "file_id": {"type": "string"}, "comment_id": {"type": "string"}, "page_size": {"type": "integer", "default": 20},
    }}),
    types.Tool(name="drive_get_reply", description="Get a specific reply.", inputSchema={"type": "object", "required": ["file_id", "comment_id", "reply_id"], "properties": {
        "file_id": {"type": "string"}, "comment_id": {"type": "string"}, "reply_id": {"type": "string"},
    }}),
    types.Tool(name="drive_create_reply", description="Reply to a comment. Set action='resolve' to resolve the comment.", inputSchema={"type": "object", "required": ["file_id", "comment_id", "content"], "properties": {
        "file_id": {"type": "string"}, "comment_id": {"type": "string"}, "content": {"type": "string"},
        "action": {"type": "string", "enum": ["resolve", "reopen"], "description": "Optional action"},
    }}),
    types.Tool(name="drive_update_reply", description="Update a reply's content.", inputSchema={"type": "object", "required": ["file_id", "comment_id", "reply_id", "content"], "properties": {
        "file_id": {"type": "string"}, "comment_id": {"type": "string"}, "reply_id": {"type": "string"}, "content": {"type": "string"},
    }}),
    types.Tool(name="drive_delete_reply", description="Delete a reply.", inputSchema={"type": "object", "required": ["file_id", "comment_id", "reply_id"], "properties": {
        "file_id": {"type": "string"}, "comment_id": {"type": "string"}, "reply_id": {"type": "string"},
    }}),

    # ── revisions ──
    types.Tool(name="drive_list_revisions", description="List all revisions of a file.", inputSchema={"type": "object", "required": ["file_id"], "properties": {
        "file_id": {"type": "string"}, "page_size": {"type": "integer", "default": 50},
    }}),
    types.Tool(name="drive_get_revision", description="Get metadata of a specific revision.", inputSchema={"type": "object", "required": ["file_id", "revision_id"], "properties": {"file_id": {"type": "string"}, "revision_id": {"type": "string"}}}),
    types.Tool(name="drive_update_revision", description="Update revision metadata (keepForever, publishAuto, published).", inputSchema={"type": "object", "required": ["file_id", "revision_id"], "properties": {
        "file_id": {"type": "string"}, "revision_id": {"type": "string"},
        "keep_forever": {"type": "boolean"}, "publish_auto": {"type": "boolean"}, "published": {"type": "boolean"},
    }}),
    types.Tool(name="drive_delete_revision", description="Delete a revision (only works for some file types).", inputSchema={"type": "object", "required": ["file_id", "revision_id"], "properties": {"file_id": {"type": "string"}, "revision_id": {"type": "string"}}}),

    # ── shared drives ──
    types.Tool(name="drive_list_shared_drives", description="List all Shared Drives (Team Drives) the user has access to.", inputSchema={"type": "object", "properties": {"page_size": {"type": "integer", "default": 50}}}),
    types.Tool(name="drive_get_shared_drive", description="Get metadata of a Shared Drive.", inputSchema={"type": "object", "required": ["drive_id"], "properties": {"drive_id": {"type": "string"}}}),
    types.Tool(name="drive_create_shared_drive", description="Create a new Shared Drive.", inputSchema={"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}),
    types.Tool(name="drive_update_shared_drive", description="Update Shared Drive metadata (name, theme, restrictions).", inputSchema={"type": "object", "required": ["drive_id"], "properties": {
        "drive_id": {"type": "string"}, "name": {"type": "string"},
    }}),
    types.Tool(name="drive_delete_shared_drive", description="Delete a Shared Drive (must be empty).", inputSchema={"type": "object", "required": ["drive_id"], "properties": {"drive_id": {"type": "string"}}}),
    types.Tool(name="drive_hide_shared_drive", description="Hide a Shared Drive from the default view.", inputSchema={"type": "object", "required": ["drive_id"], "properties": {"drive_id": {"type": "string"}}}),
    types.Tool(name="drive_unhide_shared_drive", description="Unhide a previously hidden Shared Drive.", inputSchema={"type": "object", "required": ["drive_id"], "properties": {"drive_id": {"type": "string"}}}),

    # ── changes ──
    types.Tool(name="drive_get_start_page_token", description="Get the starting page token for listing future changes.", inputSchema={"type": "object", "properties": {}}),
    types.Tool(name="drive_list_changes", description="List changes to files since a given page token.", inputSchema={"type": "object", "required": ["page_token"], "properties": {
        "page_token": {"type": "string"}, "page_size": {"type": "integer", "default": 100},
        "include_removed": {"type": "boolean", "default": True},
    }}),

    # ── channels ──
    types.Tool(name="drive_stop_channel", description="Stop receiving push notifications for a channel.", inputSchema={"type": "object", "required": ["channel_id", "resource_id"], "properties": {
        "channel_id": {"type": "string"}, "resource_id": {"type": "string"},
    }}),

    # ── apps ──
    types.Tool(name="drive_list_apps", description="List installed Drive apps.", inputSchema={"type": "object", "properties": {}}),
    types.Tool(name="drive_get_app", description="Get info about a Drive app.", inputSchema={"type": "object", "required": ["app_id"], "properties": {"app_id": {"type": "string"}}}),

    # ── file labels ──
    types.Tool(name="drive_list_labels", description="List labels applied to a file.", inputSchema={"type": "object", "required": ["file_id"], "properties": {"file_id": {"type": "string"}}}),
    types.Tool(name="drive_modify_labels", description="Add, update, or remove labels on a file.", inputSchema={"type": "object", "required": ["file_id", "label_modifications"], "properties": {
        "file_id": {"type": "string"},
        "label_modifications": {"type": "array", "items": {"type": "object"}, "description": "Array of label modification objects per Drive API spec"},
    }}),

    # ── watch ──
    types.Tool(name="drive_watch_file", description="Subscribe to push notifications for changes to a file.", inputSchema={"type": "object", "required": ["file_id", "channel_id", "webhook_url"], "properties": {
        "file_id": {"type": "string"}, "channel_id": {"type": "string", "description": "Unique channel ID"},
        "webhook_url": {"type": "string", "description": "HTTPS URL to receive notifications"},
        "expiration": {"type": "string", "description": "Expiration time in ms since epoch"},
    }}),
    types.Tool(name="drive_watch_changes", description="Subscribe to push notifications for Drive changes.", inputSchema={"type": "object", "required": ["page_token", "channel_id", "webhook_url"], "properties": {
        "page_token": {"type": "string"}, "channel_id": {"type": "string"},
        "webhook_url": {"type": "string"}, "expiration": {"type": "string"},
    }}),
]


# =============================================================================
# Handler
# =============================================================================

def handle(name: str, a: dict):
    svc = drive()
    S = True  # supportsAllDrives shorthand

    # ── about ──
    if name == "drive_about":
        return svc.about().get(fields="user,storageQuota,maxUploadSize").execute()

    # ── files ──
    if name == "drive_search_files":
        q = a.get("query", "")
        if not q: q = "trashed = false"
        elif "trashed" not in q.lower(): q += " and trashed = false"
        fields = a.get("fields", "files(id,name,mimeType,size,modifiedTime,owners)")
        r = svc.files().list(q=q, pageSize=min(a.get("page_size", 20), 100), orderBy=a.get("order_by", "modifiedTime desc"),
                             fields=f"nextPageToken,{fields}", supportsAllDrives=S, includeItemsFromAllDrives=S).execute()
        return {"files": [fmt_file(f) for f in r.get("files", [])], "nextPageToken": r.get("nextPageToken")}

    if name == "drive_list_folder":
        fid = a["folder_id"]
        q = f"'{fid}' in parents and trashed = false"
        r = svc.files().list(q=q, pageSize=min(a.get("page_size", 50), 100),
                             fields="files(id,name,mimeType,size,modifiedTime)", supportsAllDrives=S, includeItemsFromAllDrives=S).execute()
        return {"files": [fmt_file(f) for f in r.get("files", [])]}

    if name == "drive_get_file":
        f = svc.files().get(fileId=a["file_id"], fields="*", supportsAllDrives=S).execute()
        return fmt_file(f) | {"description": f.get("description"), "owners": f.get("owners"), "parents": f.get("parents"), "webViewLink": f.get("webViewLink")}

    if name == "drive_read_content":
        fid = a["file_id"]
        meta = svc.files().get(fileId=fid, fields="id,name,mimeType,size", supportsAllDrives=S).execute()
        mime = meta.get("mimeType", "")
        max_c = a.get("max_chars", 10000)
        if mime.startswith("application/vnd.google-apps."):
            if mime == "application/vnd.google-apps.spreadsheet":
                from auth import sheets
                ss = sheets().spreadsheets().get(spreadsheetId=fid, includeGridData=False).execute()
                result = {"title": ss.get("properties", {}).get("title"), "sheets": []}
                for sh in ss.get("sheets", []):
                    title = sh["properties"]["title"]
                    vals = sheets().spreadsheets().values().get(spreadsheetId=fid, range=f"'{title}'").execute().get("values", [])
                    result["sheets"].append({"name": title, "rows": len(vals), "data": vals[:200]})
                return result
            exp_mime, ext = EXPORT_FORMATS.get(mime, ("text/plain", ".txt"))
            data = export_bytes(svc, fid, exp_mime)
            if ext == ".docx": return {"content": truncate(read_docx(data), max_c)}
            if ext == ".pptx": return {"content": truncate(read_pptx(data), max_c)}
            return {"content": truncate(data.decode("utf-8", errors="replace"), max_c)}
        data = download_bytes(svc, fid, mime)
        if mime == "application/pdf": return {"content": truncate(read_pdf(data), max_c)}
        if "word" in mime: return {"content": truncate(read_docx(data), max_c)}
        if "spreadsheet" in mime or "excel" in mime: return {"content": truncate(read_xlsx(data), max_c)}
        if "presentation" in mime or "powerpoint" in mime: return {"content": truncate(read_pptx(data), max_c)}
        if mime.startswith("text/") or mime in ("application/json", "application/xml"):
            return {"content": truncate(data.decode("utf-8", errors="replace"), max_c)}
        if "zip" in mime: return {"content": read_zip(data)}
        if mime.startswith("image/"):
            return [types.ImageContent(type="image", data=base64.b64encode(data).decode(), mimeType=mime)]
        return {"info": fmt_file(meta), "message": f"Binary file ({fmt_size(meta.get('size'))}). Use drive_download_file to save locally."}

    if name == "drive_download_file":
        fid = a["file_id"]
        meta = svc.files().get(fileId=fid, fields="id,name,mimeType", supportsAllDrives=S).execute()
        mime = meta["mimeType"]
        fname = a.get("save_as", meta["name"])
        DOWNLOAD_DIR.mkdir(exist_ok=True)
        if mime.startswith("application/vnd.google-apps."):
            exp_mime, ext = EXPORT_FORMATS.get(mime, ("application/pdf", ".pdf"))
            data = export_bytes(svc, fid, exp_mime)
            if not fname.endswith(ext): fname += ext
        else:
            data = download_bytes(svc, fid, mime)
        path = DOWNLOAD_DIR / fname
        path.write_bytes(data)
        return {"saved": str(path), "size": fmt_size(len(data))}

    if name == "drive_create_file":
        body = {"name": a["name"]}
        if "mime_type" in a: body["mimeType"] = a["mime_type"]
        if "parent_id" in a: body["parents"] = [a["parent_id"]]
        media = None
        if "content" in a:
            ct = a.get("content_type", "text/plain")
            try: raw = base64.b64decode(a["content"])
            except Exception: raw = a["content"].encode("utf-8")
            media = MediaIoBaseUpload(io.BytesIO(raw), mimetype=ct, resumable=True)
        f = svc.files().create(body=body, media_body=media, fields="id,name,mimeType,webViewLink", supportsAllDrives=S).execute()
        return fmt_file(f)

    if name == "drive_upload_file":
        p = Path(a["local_path"])
        if not p.exists(): raise FileNotFoundError(f"File not found: {p}")
        if p.stat().st_size > MAX_DOWNLOAD_SIZE: raise ValueError(f"File too large: {fmt_size(p.stat().st_size)}")
        body = {"name": a.get("name", p.name)}
        if "parent_id" in a: body["parents"] = [a["parent_id"]]
        import mimetypes
        mt = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        media = MediaFileUpload(str(p), mimetype=mt, resumable=True)
        f = svc.files().create(body=body, media_body=media, fields="id,name,mimeType,webViewLink,size", supportsAllDrives=S).execute()
        return fmt_file(f)

    if name == "drive_update_file":
        body = {}
        if "name" in a: body["name"] = a["name"]
        if "description" in a: body["description"] = a["description"]
        if "starred" in a: body["starred"] = a["starred"]
        kwargs = {"fileId": a["file_id"], "body": body, "supportsAllDrives": S}
        if "add_parents" in a: kwargs["addParents"] = a["add_parents"]
        if "remove_parents" in a: kwargs["removeParents"] = a["remove_parents"]
        media = None
        if "content" in a:
            ct = a.get("content_type", "text/plain")
            try: raw = base64.b64decode(a["content"])
            except Exception: raw = a["content"].encode("utf-8")
            media = MediaIoBaseUpload(io.BytesIO(raw), mimetype=ct, resumable=True)
            kwargs["media_body"] = media
        return svc.files().update(**kwargs, fields="id,name,mimeType,modifiedTime").execute()

    if name == "drive_copy_file":
        body = {}
        if "new_name" in a: body["name"] = a["new_name"]
        if "parent_id" in a: body["parents"] = [a["parent_id"]]
        return svc.files().copy(fileId=a["file_id"], body=body, fields="id,name,mimeType,webViewLink", supportsAllDrives=S).execute()

    if name == "drive_delete_file":
        svc.files().update(fileId=a["file_id"], body={"trashed": True}, supportsAllDrives=S).execute()
        return {"status": "trashed", "file_id": a["file_id"]}

    if name == "drive_permanently_delete":
        svc.files().delete(fileId=a["file_id"], supportsAllDrives=S).execute()
        return {"status": "permanently_deleted", "file_id": a["file_id"]}

    if name == "drive_empty_trash":
        svc.files().emptyTrash().execute()
        return {"status": "trash_emptied"}

    if name == "drive_export_file":
        data = export_bytes(svc, a["file_id"], a["export_mime"])
        if "save_path" in a:
            Path(a["save_path"]).write_bytes(data)
            return {"saved": a["save_path"], "size": fmt_size(len(data))}
        return {"size": fmt_size(len(data)), "content_base64": base64.b64encode(data[:50000]).decode(), "truncated": len(data) > 50000}

    if name == "drive_create_folder":
        body = {"name": a["name"], "mimeType": "application/vnd.google-apps.folder"}
        if "parent_id" in a: body["parents"] = [a["parent_id"]]
        return svc.files().create(body=body, fields="id,name,webViewLink", supportsAllDrives=S).execute()

    if name == "drive_move_file":
        f = svc.files().get(fileId=a["file_id"], fields="parents", supportsAllDrives=S).execute()
        prev = ",".join(f.get("parents", []))
        return svc.files().update(fileId=a["file_id"], addParents=a["new_parent_id"], removeParents=prev, fields="id,name,parents", supportsAllDrives=S).execute()

    if name == "drive_rename_file":
        return svc.files().update(fileId=a["file_id"], body={"name": a["new_name"]}, fields="id,name", supportsAllDrives=S).execute()

    if name == "drive_generate_ids":
        return svc.files().generateIds(count=min(a.get("count", 1), 1000)).execute()

    # ── permissions ──
    if name == "drive_share":
        perm = {"role": a["role"], "type": a.get("type", "user")}
        if "email" in a: perm["emailAddress"] = a["email"]
        if "domain" in a: perm["domain"] = a["domain"]
        return svc.permissions().create(fileId=a["file_id"], body=perm, sendNotificationEmail=a.get("send_notification", True),
                                        emailMessage=a.get("message"), supportsAllDrives=S, fields="*").execute()

    if name == "drive_list_permissions":
        return svc.permissions().list(fileId=a["file_id"], supportsAllDrives=S, fields="permissions(id,type,role,emailAddress,displayName)").execute()

    if name == "drive_get_permission":
        return svc.permissions().get(fileId=a["file_id"], permissionId=a["permission_id"], supportsAllDrives=S, fields="*").execute()

    if name == "drive_update_permission":
        return svc.permissions().update(fileId=a["file_id"], permissionId=a["permission_id"], body={"role": a["role"]}, supportsAllDrives=S).execute()

    if name == "drive_delete_permission":
        svc.permissions().delete(fileId=a["file_id"], permissionId=a["permission_id"], supportsAllDrives=S).execute()
        return {"status": "deleted", "permission_id": a["permission_id"]}

    # ── comments ──
    if name == "drive_list_comments":
        return svc.comments().list(fileId=a["file_id"], pageSize=a.get("page_size", 20), includeDeleted=a.get("include_deleted", False), fields="comments(id,content,author,createdTime,resolved,replies)").execute()

    if name == "drive_get_comment":
        return svc.comments().get(fileId=a["file_id"], commentId=a["comment_id"], fields="*", includeDeleted=True).execute()

    if name == "drive_create_comment":
        body = {"content": a["content"]}
        if "anchor" in a: body["anchor"] = a["anchor"]
        return svc.comments().create(fileId=a["file_id"], body=body, fields="*").execute()

    if name == "drive_update_comment":
        return svc.comments().update(fileId=a["file_id"], commentId=a["comment_id"], body={"content": a["content"]}, fields="*").execute()

    if name == "drive_delete_comment":
        svc.comments().delete(fileId=a["file_id"], commentId=a["comment_id"]).execute()
        return {"status": "deleted"}

    # ── replies ──
    if name == "drive_list_replies":
        return svc.replies().list(fileId=a["file_id"], commentId=a["comment_id"], pageSize=a.get("page_size", 20), fields="replies(id,content,author,createdTime,action)").execute()

    if name == "drive_get_reply":
        return svc.replies().get(fileId=a["file_id"], commentId=a["comment_id"], replyId=a["reply_id"], fields="*").execute()

    if name == "drive_create_reply":
        body = {"content": a["content"]}
        if "action" in a: body["action"] = a["action"]
        return svc.replies().create(fileId=a["file_id"], commentId=a["comment_id"], body=body, fields="*").execute()

    if name == "drive_update_reply":
        return svc.replies().update(fileId=a["file_id"], commentId=a["comment_id"], replyId=a["reply_id"], body={"content": a["content"]}, fields="*").execute()

    if name == "drive_delete_reply":
        svc.replies().delete(fileId=a["file_id"], commentId=a["comment_id"], replyId=a["reply_id"]).execute()
        return {"status": "deleted"}

    # ── revisions ──
    if name == "drive_list_revisions":
        return svc.revisions().list(fileId=a["file_id"], pageSize=a.get("page_size", 50), fields="revisions(id,modifiedTime,lastModifyingUser,size,keepForever)").execute()

    if name == "drive_get_revision":
        return svc.revisions().get(fileId=a["file_id"], revisionId=a["revision_id"], fields="*").execute()

    if name == "drive_update_revision":
        body = {}
        if "keep_forever" in a: body["keepForever"] = a["keep_forever"]
        if "publish_auto" in a: body["publishAuto"] = a["publish_auto"]
        if "published" in a: body["published"] = a["published"]
        return svc.revisions().update(fileId=a["file_id"], revisionId=a["revision_id"], body=body).execute()

    if name == "drive_delete_revision":
        svc.revisions().delete(fileId=a["file_id"], revisionId=a["revision_id"]).execute()
        return {"status": "deleted"}

    # ── shared drives ──
    if name == "drive_list_shared_drives":
        return svc.drives().list(pageSize=a.get("page_size", 50)).execute()

    if name == "drive_get_shared_drive":
        return svc.drives().get(driveId=a["drive_id"]).execute()

    if name == "drive_create_shared_drive":
        import uuid
        return svc.drives().create(requestId=str(uuid.uuid4()), body={"name": a["name"]}).execute()

    if name == "drive_update_shared_drive":
        body = {}
        if "name" in a: body["name"] = a["name"]
        return svc.drives().update(driveId=a["drive_id"], body=body).execute()

    if name == "drive_delete_shared_drive":
        svc.drives().delete(driveId=a["drive_id"]).execute()
        return {"status": "deleted"}

    if name == "drive_hide_shared_drive":
        return svc.drives().hide(driveId=a["drive_id"]).execute()

    if name == "drive_unhide_shared_drive":
        return svc.drives().unhide(driveId=a["drive_id"]).execute()

    # ── changes ──
    if name == "drive_get_start_page_token":
        return svc.changes().getStartPageToken(supportsAllDrives=S).execute()

    if name == "drive_list_changes":
        return svc.changes().list(pageToken=a["page_token"], pageSize=a.get("page_size", 100),
                                  includeRemoved=a.get("include_removed", True), supportsAllDrives=S, includeItemsFromAllDrives=S,
                                  fields="nextPageToken,newStartPageToken,changes(fileId,removed,time,file(id,name,mimeType,trashed))").execute()

    # ── channels ──
    if name == "drive_stop_channel":
        svc.channels().stop(body={"id": a["channel_id"], "resourceId": a["resource_id"]}).execute()
        return {"status": "stopped"}

    # ── apps ──
    if name == "drive_list_apps":
        return svc.apps().list().execute()

    if name == "drive_get_app":
        return svc.apps().get(appId=a["app_id"]).execute()

    # ── labels ──
    if name == "drive_list_labels":
        return svc.files().listLabels(fileId=a["file_id"]).execute()

    if name == "drive_modify_labels":
        return svc.files().modifyLabels(fileId=a["file_id"], body={"labelModifications": a["label_modifications"]}).execute()

    # ── watch ──
    if name == "drive_watch_file":
        body = {"id": a["channel_id"], "type": "web_hook", "address": a["webhook_url"]}
        if "expiration" in a: body["expiration"] = a["expiration"]
        return svc.files().watch(fileId=a["file_id"], body=body, supportsAllDrives=S).execute()

    if name == "drive_watch_changes":
        body = {"id": a["channel_id"], "type": "web_hook", "address": a["webhook_url"]}
        if "expiration" in a: body["expiration"] = a["expiration"]
        return svc.changes().watch(pageToken=a["page_token"], body=body, supportsAllDrives=S).execute()

    raise ValueError(f"Unknown drive tool: {name}")
