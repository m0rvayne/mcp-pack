"""
Google Calendar API v3 — full coverage.
37 REST methods: events, calendars, calendarList, acl, freebusy, colors, settings, channels.
"""

from datetime import datetime, timedelta, timezone
from mcp import types
from auth import calendar

# =============================================================================
# Tool definitions
# =============================================================================

TOOLS = [
    # ── events ──
    types.Tool(name="cal_list_events", description="List events from a calendar. Defaults to primary, next 30 days.", inputSchema={"type": "object", "properties": {
        "calendar_id": {"type": "string", "default": "primary"}, "time_min": {"type": "string", "description": "ISO 8601 start"},
        "time_max": {"type": "string", "description": "ISO 8601 end"}, "max_results": {"type": "integer", "default": 50},
        "query": {"type": "string", "description": "Free-text search"}, "show_deleted": {"type": "boolean", "default": False},
        "single_events": {"type": "boolean", "description": "Expand recurring events", "default": True},
        "order_by": {"type": "string", "enum": ["startTime", "updated"], "default": "startTime"},
    }}),
    types.Tool(name="cal_get_event", description="Get full details of a single event.", inputSchema={"type": "object", "required": ["event_id"], "properties": {
        "event_id": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
    }}),
    types.Tool(name="cal_create_event", description="Create a calendar event. Supports attendees, Zoom, reminders, recurrence (RRULE), all-day, location, color.\n\nRRULE examples:\n- RRULE:FREQ=WEEKLY;BYDAY=TU,TH,FR\n- RRULE:FREQ=DAILY;COUNT=10\n- RRULE:FREQ=MONTHLY;BYMONTHDAY=1",
        inputSchema={"type": "object", "required": ["summary", "start", "end"], "properties": {
        "calendar_id": {"type": "string", "default": "primary"},
        "summary": {"type": "string"}, "description": {"type": "string"}, "location": {"type": "string"},
        "start": {"type": "string", "description": "ISO 8601 datetime or date"}, "end": {"type": "string"},
        "time_zone": {"type": "string"}, "attendees": {"type": "string", "description": "Comma-separated emails"},
        "recurrence": {"type": "string"}, "zoom_link": {"type": "string"},
        "reminders_minutes": {"type": "string", "description": "Comma-separated minutes"},
        "color_id": {"type": "string"}, "visibility": {"type": "string", "enum": ["default", "public", "private", "confidential"]},
        "send_updates": {"type": "string", "enum": ["all", "externalOnly", "none"], "default": "none"},
        "transparency": {"type": "string", "enum": ["opaque", "transparent"]},
        "guests_can_modify": {"type": "boolean"}, "guests_can_invite_others": {"type": "boolean"},
    }}),
    types.Tool(name="cal_update_event", description="Update any field of an existing event.", inputSchema={"type": "object", "required": ["event_id"], "properties": {
        "event_id": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
        "summary": {"type": "string"}, "description": {"type": "string"}, "location": {"type": "string"},
        "start": {"type": "string"}, "end": {"type": "string"}, "time_zone": {"type": "string"},
        "attendees": {"type": "string"}, "zoom_link": {"type": "string"}, "recurrence": {"type": "string"},
        "color_id": {"type": "string"}, "status": {"type": "string", "enum": ["confirmed", "tentative", "cancelled"]},
        "send_updates": {"type": "string", "enum": ["all", "externalOnly", "none"], "default": "none"},
    }}),
    types.Tool(name="cal_patch_event", description="Patch (partial update) an event — only sends changed fields.", inputSchema={"type": "object", "required": ["event_id"], "properties": {
        "event_id": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
        "summary": {"type": "string"}, "description": {"type": "string"}, "location": {"type": "string"},
        "start": {"type": "string"}, "end": {"type": "string"}, "color_id": {"type": "string"},
        "status": {"type": "string"}, "send_updates": {"type": "string", "default": "none"},
    }}),
    types.Tool(name="cal_delete_event", description="Delete a calendar event.", inputSchema={"type": "object", "required": ["event_id"], "properties": {
        "event_id": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
        "send_updates": {"type": "string", "enum": ["all", "externalOnly", "none"], "default": "none"},
    }}),
    types.Tool(name="cal_move_event", description="Move an event to another calendar.", inputSchema={"type": "object", "required": ["event_id", "destination_calendar_id"], "properties": {
        "event_id": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
        "destination_calendar_id": {"type": "string"}, "send_updates": {"type": "string", "default": "none"},
    }}),
    types.Tool(name="cal_quick_add", description="Create event from natural language ('Meeting with Bob tomorrow at 3pm').", inputSchema={"type": "object", "required": ["text"], "properties": {
        "text": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
        "send_updates": {"type": "string", "default": "none"},
    }}),
    types.Tool(name="cal_import_event", description="Import an event (preserves original iCalendar UID). Use for syncing external calendars.", inputSchema={"type": "object", "required": ["calendar_id", "event_body"], "properties": {
        "calendar_id": {"type": "string"}, "event_body": {"type": "object", "description": "Full event resource per Calendar API spec"},
    }}),
    types.Tool(name="cal_list_instances", description="List all instances of a recurring event.", inputSchema={"type": "object", "required": ["event_id"], "properties": {
        "event_id": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
        "time_min": {"type": "string"}, "time_max": {"type": "string"}, "max_results": {"type": "integer", "default": 50},
    }}),
    types.Tool(name="cal_respond", description="Set your RSVP response to an event.", inputSchema={"type": "object", "required": ["event_id", "response"], "properties": {
        "event_id": {"type": "string"}, "calendar_id": {"type": "string", "default": "primary"},
        "response": {"type": "string", "enum": ["accepted", "declined", "tentative"]},
    }}),
    types.Tool(name="cal_watch_events", description="Subscribe to push notifications for event changes.", inputSchema={"type": "object", "required": ["calendar_id", "channel_id", "webhook_url"], "properties": {
        "calendar_id": {"type": "string"}, "channel_id": {"type": "string"},
        "webhook_url": {"type": "string"}, "expiration": {"type": "string"},
    }}),

    # ── calendars ──
    types.Tool(name="cal_get_calendar", description="Get metadata of a calendar (summary, timezone, description).", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {"calendar_id": {"type": "string"}}}),
    types.Tool(name="cal_create_calendar", description="Create a new secondary calendar.", inputSchema={"type": "object", "required": ["summary"], "properties": {
        "summary": {"type": "string"}, "description": {"type": "string"}, "time_zone": {"type": "string"}, "location": {"type": "string"},
    }}),
    types.Tool(name="cal_update_calendar", description="Update calendar metadata.", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {
        "calendar_id": {"type": "string"}, "summary": {"type": "string"}, "description": {"type": "string"}, "time_zone": {"type": "string"}, "location": {"type": "string"},
    }}),
    types.Tool(name="cal_delete_calendar", description="Delete a secondary calendar.", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {"calendar_id": {"type": "string"}}}),
    types.Tool(name="cal_clear_calendar", description="Clear all events from a primary calendar (cannot clear secondary).", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {"calendar_id": {"type": "string"}}}),

    # ── calendarList ──
    types.Tool(name="cal_list_calendars", description="List all calendars (own + subscribed) with colors and access roles.", inputSchema={"type": "object", "properties": {"show_hidden": {"type": "boolean", "default": False}}}),
    types.Tool(name="cal_get_calendar_list_entry", description="Get a specific calendar's list entry (color, notifications, access).", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {"calendar_id": {"type": "string"}}}),
    types.Tool(name="cal_add_calendar", description="Add an existing calendar to the user's calendar list (subscribe).", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {
        "calendar_id": {"type": "string"}, "color_id": {"type": "string"}, "hidden": {"type": "boolean"},
    }}),
    types.Tool(name="cal_update_calendar_list_entry", description="Update calendar list entry (color, visibility, notifications).", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {
        "calendar_id": {"type": "string"}, "color_id": {"type": "string"}, "hidden": {"type": "boolean"},
        "summary_override": {"type": "string", "description": "Custom display name"},
        "default_reminders": {"type": "array", "items": {"type": "object", "properties": {"method": {"type": "string"}, "minutes": {"type": "integer"}}}},
    }}),
    types.Tool(name="cal_remove_calendar", description="Remove a calendar from the user's calendar list (unsubscribe).", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {"calendar_id": {"type": "string"}}}),
    types.Tool(name="cal_watch_calendar_list", description="Watch for changes to calendar list.", inputSchema={"type": "object", "required": ["channel_id", "webhook_url"], "properties": {
        "channel_id": {"type": "string"}, "webhook_url": {"type": "string"}, "expiration": {"type": "string"},
    }}),

    # ── acl ──
    types.Tool(name="cal_list_acl", description="List access control rules for a calendar (who has what access).", inputSchema={"type": "object", "required": ["calendar_id"], "properties": {"calendar_id": {"type": "string"}}}),
    types.Tool(name="cal_get_acl", description="Get a specific ACL rule.", inputSchema={"type": "object", "required": ["calendar_id", "rule_id"], "properties": {"calendar_id": {"type": "string"}, "rule_id": {"type": "string"}}}),
    types.Tool(name="cal_insert_acl", description="Share a calendar with a user/group. Roles: none, freeBusyReader, reader, writer, owner.", inputSchema={"type": "object", "required": ["calendar_id", "role", "scope_type", "scope_value"], "properties": {
        "calendar_id": {"type": "string"}, "role": {"type": "string", "enum": ["none", "freeBusyReader", "reader", "writer", "owner"]},
        "scope_type": {"type": "string", "enum": ["default", "user", "group", "domain"]}, "scope_value": {"type": "string", "description": "Email or domain"},
        "send_notifications": {"type": "boolean", "default": True},
    }}),
    types.Tool(name="cal_update_acl", description="Update an ACL rule's role.", inputSchema={"type": "object", "required": ["calendar_id", "rule_id", "role"], "properties": {
        "calendar_id": {"type": "string"}, "rule_id": {"type": "string"},
        "role": {"type": "string", "enum": ["none", "freeBusyReader", "reader", "writer", "owner"]},
    }}),
    types.Tool(name="cal_delete_acl", description="Delete an ACL rule (revoke access).", inputSchema={"type": "object", "required": ["calendar_id", "rule_id"], "properties": {"calendar_id": {"type": "string"}, "rule_id": {"type": "string"}}}),
    types.Tool(name="cal_watch_acl", description="Watch for ACL changes on a calendar.", inputSchema={"type": "object", "required": ["calendar_id", "channel_id", "webhook_url"], "properties": {
        "calendar_id": {"type": "string"}, "channel_id": {"type": "string"}, "webhook_url": {"type": "string"},
    }}),

    # ── freebusy ──
    types.Tool(name="cal_freebusy", description="Check free/busy status for one or more calendars.", inputSchema={"type": "object", "required": ["time_min", "time_max"], "properties": {
        "time_min": {"type": "string"}, "time_max": {"type": "string"},
        "calendar_ids": {"type": "string", "description": "Comma-separated calendar IDs (default: primary)"},
    }}),

    # ── colors ──
    types.Tool(name="cal_get_colors", description="Get all available calendar and event color definitions.", inputSchema={"type": "object", "properties": {}}),

    # ── settings ──
    types.Tool(name="cal_list_settings", description="List all user calendar settings.", inputSchema={"type": "object", "properties": {}}),
    types.Tool(name="cal_get_setting", description="Get a specific calendar setting by ID.", inputSchema={"type": "object", "required": ["setting_id"], "properties": {"setting_id": {"type": "string"}}}),
    types.Tool(name="cal_watch_settings", description="Watch for changes to user settings.", inputSchema={"type": "object", "required": ["channel_id", "webhook_url"], "properties": {
        "channel_id": {"type": "string"}, "webhook_url": {"type": "string"},
    }}),

    # ── channels ──
    types.Tool(name="cal_stop_channel", description="Stop a push notification channel.", inputSchema={"type": "object", "required": ["channel_id", "resource_id"], "properties": {
        "channel_id": {"type": "string"}, "resource_id": {"type": "string"},
    }}),
]


# =============================================================================
# Helpers
# =============================================================================

def _fmt_event(e: dict) -> dict:
    start = e.get("start", {})
    end = e.get("end", {})
    return {
        "id": e.get("id"),
        "summary": e.get("summary", "(no title)"),
        "start": start.get("dateTime", start.get("date", "")),
        "end": end.get("dateTime", end.get("date", "")),
        "location": e.get("location"),
        "status": e.get("status"),
        "organizer": e.get("organizer", {}).get("email"),
        "attendees": [{"email": a.get("email"), "status": a.get("responseStatus")} for a in e.get("attendees", [])],
        "hangoutLink": e.get("hangoutLink"),
        "htmlLink": e.get("htmlLink"),
        "recurrence": e.get("recurrence"),
        "colorId": e.get("colorId"),
    }


def _build_event_body(a: dict) -> dict:
    body = {}
    if "summary" in a: body["summary"] = a["summary"]
    if "description" in a: body["description"] = a["description"]
    if "location" in a: body["location"] = a["location"]
    if "color_id" in a: body["colorId"] = a["color_id"]
    if "status" in a: body["status"] = a["status"]
    if "visibility" in a: body["visibility"] = a["visibility"]
    if "transparency" in a: body["transparency"] = a["transparency"]
    if "guests_can_modify" in a: body["guestsCanModify"] = a["guests_can_modify"]
    if "guests_can_invite_others" in a: body["guestsCanInviteOthers"] = a["guests_can_invite_others"]

    tz = a.get("time_zone")
    if "start" in a:
        s = a["start"]
        if "T" in s: body["start"] = {"dateTime": s, **({"timeZone": tz} if tz else {})}
        else: body["start"] = {"date": s}
    if "end" in a:
        e = a["end"]
        if "T" in e: body["end"] = {"dateTime": e, **({"timeZone": tz} if tz else {})}
        else: body["end"] = {"date": e}

    if "attendees" in a:
        body["attendees"] = [{"email": e.strip()} for e in a["attendees"].split(",") if e.strip()]
    if "recurrence" in a:
        body["recurrence"] = [a["recurrence"]] if not isinstance(a["recurrence"], list) else a["recurrence"]
    if "zoom_link" in a:
        body.setdefault("conferenceData", {})
        body["description"] = body.get("description", "") + f"\n\nZoom: {a['zoom_link']}"
    if "reminders_minutes" in a:
        mins = [int(m.strip()) for m in a["reminders_minutes"].split(",") if m.strip()]
        body["reminders"] = {"useDefault": False, "overrides": [{"method": "popup", "minutes": m} for m in mins]}
    return body


# =============================================================================
# Handler
# =============================================================================

def handle(name: str, a: dict):
    svc = calendar()
    cid = a.get("calendar_id", "primary")

    # ── events ──
    if name == "cal_list_events":
        now = datetime.now(timezone.utc)
        tmin = a.get("time_min", now.isoformat())
        tmax = a.get("time_max", (now + timedelta(days=30)).isoformat())
        kwargs = {"calendarId": cid, "timeMin": tmin, "timeMax": tmax,
                  "maxResults": min(a.get("max_results", 50), 2500),
                  "singleEvents": a.get("single_events", True), "orderBy": a.get("order_by", "startTime")}
        if "query" in a: kwargs["q"] = a["query"]
        if a.get("show_deleted"): kwargs["showDeleted"] = True
        r = svc.events().list(**kwargs).execute()
        return {"events": [_fmt_event(e) for e in r.get("items", [])], "nextPageToken": r.get("nextPageToken")}

    if name == "cal_get_event":
        return _fmt_event(svc.events().get(calendarId=cid, eventId=a["event_id"]).execute())

    if name == "cal_create_event":
        body = _build_event_body(a)
        return _fmt_event(svc.events().insert(calendarId=cid, body=body, sendUpdates=a.get("send_updates", "none")).execute())

    if name == "cal_update_event":
        existing = svc.events().get(calendarId=cid, eventId=a["event_id"]).execute()
        updates = _build_event_body(a)
        existing.update(updates)
        return _fmt_event(svc.events().update(calendarId=cid, eventId=a["event_id"], body=existing, sendUpdates=a.get("send_updates", "none")).execute())

    if name == "cal_patch_event":
        body = _build_event_body(a)
        return _fmt_event(svc.events().patch(calendarId=cid, eventId=a["event_id"], body=body, sendUpdates=a.get("send_updates", "none")).execute())

    if name == "cal_delete_event":
        svc.events().delete(calendarId=cid, eventId=a["event_id"], sendUpdates=a.get("send_updates", "none")).execute()
        return {"status": "deleted", "event_id": a["event_id"]}

    if name == "cal_move_event":
        return _fmt_event(svc.events().move(calendarId=cid, eventId=a["event_id"], destination=a["destination_calendar_id"], sendUpdates=a.get("send_updates", "none")).execute())

    if name == "cal_quick_add":
        return _fmt_event(svc.events().quickAdd(calendarId=cid, text=a["text"], sendUpdates=a.get("send_updates", "none")).execute())

    if name == "cal_import_event":
        return _fmt_event(svc.events().import_(calendarId=a["calendar_id"], body=a["event_body"]).execute())

    if name == "cal_list_instances":
        kwargs = {"calendarId": cid, "eventId": a["event_id"], "maxResults": a.get("max_results", 50)}
        if "time_min" in a: kwargs["timeMin"] = a["time_min"]
        if "time_max" in a: kwargs["timeMax"] = a["time_max"]
        r = svc.events().instances(**kwargs).execute()
        return {"events": [_fmt_event(e) for e in r.get("items", [])]}

    if name == "cal_respond":
        event = svc.events().get(calendarId=cid, eventId=a["event_id"]).execute()
        # Find self in attendees
        me = svc.calendarList().get(calendarId="primary").execute().get("id", "")
        for att in event.get("attendees", []):
            if att.get("email", "").lower() == me.lower() or att.get("self"):
                att["responseStatus"] = a["response"]
                break
        else:
            event.setdefault("attendees", []).append({"email": me, "responseStatus": a["response"]})
        return _fmt_event(svc.events().update(calendarId=cid, eventId=a["event_id"], body=event).execute())

    if name == "cal_watch_events":
        body = {"id": a["channel_id"], "type": "web_hook", "address": a["webhook_url"]}
        if "expiration" in a: body["expiration"] = a["expiration"]
        return svc.events().watch(calendarId=a["calendar_id"], body=body).execute()

    # ── calendars ──
    if name == "cal_get_calendar":
        return svc.calendars().get(calendarId=a["calendar_id"]).execute()

    if name == "cal_create_calendar":
        body = {"summary": a["summary"]}
        if "description" in a: body["description"] = a["description"]
        if "time_zone" in a: body["timeZone"] = a["time_zone"]
        if "location" in a: body["location"] = a["location"]
        return svc.calendars().insert(body=body).execute()

    if name == "cal_update_calendar":
        existing = svc.calendars().get(calendarId=a["calendar_id"]).execute()
        if "summary" in a: existing["summary"] = a["summary"]
        if "description" in a: existing["description"] = a["description"]
        if "time_zone" in a: existing["timeZone"] = a["time_zone"]
        if "location" in a: existing["location"] = a["location"]
        return svc.calendars().update(calendarId=a["calendar_id"], body=existing).execute()

    if name == "cal_delete_calendar":
        svc.calendars().delete(calendarId=a["calendar_id"]).execute()
        return {"status": "deleted"}

    if name == "cal_clear_calendar":
        svc.calendars().clear(calendarId=a["calendar_id"]).execute()
        return {"status": "cleared"}

    # ── calendarList ──
    if name == "cal_list_calendars":
        r = svc.calendarList().list(showHidden=a.get("show_hidden", False)).execute()
        return {"calendars": [{"id": c["id"], "summary": c.get("summary"), "primary": c.get("primary", False),
                               "accessRole": c.get("accessRole"), "backgroundColor": c.get("backgroundColor")}
                              for c in r.get("items", [])]}

    if name == "cal_get_calendar_list_entry":
        return svc.calendarList().get(calendarId=a["calendar_id"]).execute()

    if name == "cal_add_calendar":
        body = {"id": a["calendar_id"]}
        if "color_id" in a: body["colorId"] = a["color_id"]
        if "hidden" in a: body["hidden"] = a["hidden"]
        return svc.calendarList().insert(body=body).execute()

    if name == "cal_update_calendar_list_entry":
        existing = svc.calendarList().get(calendarId=a["calendar_id"]).execute()
        if "color_id" in a: existing["colorId"] = a["color_id"]
        if "hidden" in a: existing["hidden"] = a["hidden"]
        if "summary_override" in a: existing["summaryOverride"] = a["summary_override"]
        if "default_reminders" in a: existing["defaultReminders"] = a["default_reminders"]
        return svc.calendarList().update(calendarId=a["calendar_id"], body=existing).execute()

    if name == "cal_remove_calendar":
        svc.calendarList().delete(calendarId=a["calendar_id"]).execute()
        return {"status": "removed"}

    if name == "cal_watch_calendar_list":
        body = {"id": a["channel_id"], "type": "web_hook", "address": a["webhook_url"]}
        if "expiration" in a: body["expiration"] = a["expiration"]
        return svc.calendarList().watch(body=body).execute()

    # ── acl ──
    if name == "cal_list_acl":
        return svc.acl().list(calendarId=a["calendar_id"]).execute()

    if name == "cal_get_acl":
        return svc.acl().get(calendarId=a["calendar_id"], ruleId=a["rule_id"]).execute()

    if name == "cal_insert_acl":
        body = {"role": a["role"], "scope": {"type": a["scope_type"], "value": a.get("scope_value", "")}}
        return svc.acl().insert(calendarId=a["calendar_id"], body=body, sendNotifications=a.get("send_notifications", True)).execute()

    if name == "cal_update_acl":
        body = {"role": a["role"], "scope": svc.acl().get(calendarId=a["calendar_id"], ruleId=a["rule_id"]).execute().get("scope", {})}
        return svc.acl().update(calendarId=a["calendar_id"], ruleId=a["rule_id"], body=body).execute()

    if name == "cal_delete_acl":
        svc.acl().delete(calendarId=a["calendar_id"], ruleId=a["rule_id"]).execute()
        return {"status": "deleted"}

    if name == "cal_watch_acl":
        body = {"id": a["channel_id"], "type": "web_hook", "address": a["webhook_url"]}
        return svc.acl().watch(calendarId=a["calendar_id"], body=body).execute()

    # ── freebusy ──
    if name == "cal_freebusy":
        ids = [i.strip() for i in a.get("calendar_ids", "primary").split(",")]
        body = {"timeMin": a["time_min"], "timeMax": a["time_max"], "items": [{"id": i} for i in ids]}
        return svc.freebusy().query(body=body).execute()

    # ── colors ──
    if name == "cal_get_colors":
        return svc.colors().get().execute()

    # ── settings ──
    if name == "cal_list_settings":
        return svc.settings().list().execute()

    if name == "cal_get_setting":
        return svc.settings().get(setting=a["setting_id"]).execute()

    if name == "cal_watch_settings":
        body = {"id": a["channel_id"], "type": "web_hook", "address": a["webhook_url"]}
        return svc.settings().watch(body=body).execute()

    # ── channels ──
    if name == "cal_stop_channel":
        svc.channels().stop(body={"id": a["channel_id"], "resourceId": a["resource_id"]}).execute()
        return {"status": "stopped"}

    raise ValueError(f"Unknown calendar tool: {name}")
