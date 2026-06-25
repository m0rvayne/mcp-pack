"""
Google Sheets API v4 — full coverage.
Wraps all existing sheets functions + adds missing ones.
Imports existing implementation functions from the old server.py helpers.
"""

# This module re-exports the existing Sheets tools and handlers.
# The actual implementation functions are in utils.py (helpers) and
# the tool definitions + dispatch are carried over from the original server.py.
#
# For now, we define TOOLS list and handle() that delegates to the original code.
# This allows the new server.py to import uniformly from all api_* modules.

from mcp import types
from auth import sheets as get_sheets_svc, drive as get_drive_svc
from utils import (
    validate_spreadsheet_id, make_color, make_text_format, make_cell_format,
    a1_to_grid_range, rows_to_table, col_letter_to_index, col_index_to_letter,
    parse_a1_range, fmt_file, fmt_size, DOWNLOAD_DIR,
)

# We'll define TOOLS inline — same as old server.py but prefixed with sheets_
# to avoid collision with drive tools

TOOLS = [
    # File ops
    types.Tool(name="sheets_create", description="Create a new Google Sheets spreadsheet.", inputSchema={"type": "object", "required": ["title"], "properties": {"title": {"type": "string"}, "sheet_names": {"type": "array", "items": {"type": "string"}}, "folder_id": {"type": "string"}}}),
    types.Tool(name="sheets_copy", description="Copy an existing spreadsheet.", inputSchema={"type": "object", "required": ["spreadsheet_id", "new_title"], "properties": {"spreadsheet_id": {"type": "string"}, "new_title": {"type": "string"}, "folder_id": {"type": "string"}}}),
    types.Tool(name="sheets_get_info", description="Get spreadsheet metadata: title, locale, timezone, all sheets with sizes.", inputSchema={"type": "object", "required": ["spreadsheet_id"], "properties": {"spreadsheet_id": {"type": "string"}}}),
    types.Tool(name="sheets_list", description="Search for spreadsheets on Drive.", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "folder_id": {"type": "string"}, "max_results": {"type": "integer", "default": 20}}}),
    types.Tool(name="sheets_share", description="Share a spreadsheet.", inputSchema={"type": "object", "required": ["spreadsheet_id", "email", "role"], "properties": {"spreadsheet_id": {"type": "string"}, "email": {"type": "string"}, "role": {"type": "string", "enum": ["reader", "commenter", "writer", "owner"]}}}),
    types.Tool(name="sheets_get_permissions", description="List who has access.", inputSchema={"type": "object", "required": ["spreadsheet_id"], "properties": {"spreadsheet_id": {"type": "string"}}}),

    # Sheet tabs
    types.Tool(name="sheets_list_sheets", description="List all sheets (tabs).", inputSchema={"type": "object", "required": ["spreadsheet_id"], "properties": {"spreadsheet_id": {"type": "string"}}}),
    types.Tool(name="sheets_add_sheet", description="Add a new sheet tab.", inputSchema={"type": "object", "required": ["spreadsheet_id", "title"], "properties": {"spreadsheet_id": {"type": "string"}, "title": {"type": "string"}, "rows": {"type": "integer", "default": 1000}, "columns": {"type": "integer", "default": 26}, "tab_color": {"type": "string"}}}),
    types.Tool(name="sheets_delete_sheet", description="Delete a sheet tab.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}}}),
    types.Tool(name="sheets_rename_sheet", description="Rename a sheet tab.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "new_title"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "new_title": {"type": "string"}}}),
    types.Tool(name="sheets_copy_sheet", description="Copy a sheet to same or another spreadsheet.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "destination_spreadsheet_id": {"type": "string"}}}),
    types.Tool(name="sheets_reorder", description="Change sheet tab order.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_order"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_order": {"type": "array", "items": {"type": "object"}}}}),

    # Read
    types.Tool(name="sheets_read_range", description="Read data from a range (A1 notation).", inputSchema={"type": "object", "required": ["spreadsheet_id", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "range": {"type": "string"}, "value_render": {"type": "string", "enum": ["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"]}}}),
    types.Tool(name="sheets_batch_read", description="Read multiple ranges at once.", inputSchema={"type": "object", "required": ["spreadsheet_id", "ranges"], "properties": {"spreadsheet_id": {"type": "string"}, "ranges": {"type": "array", "items": {"type": "string"}}, "value_render": {"type": "string"}}}),
    types.Tool(name="sheets_get_cell", description="Get single cell value, formula, format.", inputSchema={"type": "object", "required": ["spreadsheet_id", "cell"], "properties": {"spreadsheet_id": {"type": "string"}, "cell": {"type": "string"}}}),
    types.Tool(name="sheets_search", description="Search for text across sheets.", inputSchema={"type": "object", "required": ["spreadsheet_id", "query"], "properties": {"spreadsheet_id": {"type": "string"}, "query": {"type": "string"}, "sheet_name": {"type": "string"}}}),
    types.Tool(name="sheets_get_table", description="Get sheet as structured table with headers.", inputSchema={"type": "object", "required": ["spreadsheet_id"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_name": {"type": "string"}, "has_header": {"type": "boolean", "default": True}, "max_rows": {"type": "integer", "default": 0}}}),
    types.Tool(name="sheets_get_formulas", description="Show all formulas in a range.", inputSchema={"type": "object", "required": ["spreadsheet_id", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "range": {"type": "string"}}}),

    # Write
    types.Tool(name="sheets_write_range", description="Write data to a range.", inputSchema={"type": "object", "required": ["spreadsheet_id", "range", "values"], "properties": {"spreadsheet_id": {"type": "string"}, "range": {"type": "string"}, "values": {"type": "array", "items": {"type": "array"}}, "value_input": {"type": "string", "enum": ["USER_ENTERED", "RAW"]}}}),
    types.Tool(name="sheets_append_rows", description="Append rows after last data row.", inputSchema={"type": "object", "required": ["spreadsheet_id", "range", "values"], "properties": {"spreadsheet_id": {"type": "string"}, "range": {"type": "string"}, "values": {"type": "array", "items": {"type": "array"}}, "value_input": {"type": "string", "default": "USER_ENTERED"}}}),
    types.Tool(name="sheets_batch_write", description="Write to multiple ranges.", inputSchema={"type": "object", "required": ["spreadsheet_id", "data"], "properties": {"spreadsheet_id": {"type": "string"}, "data": {"type": "array", "items": {"type": "object"}}, "value_input": {"type": "string", "default": "USER_ENTERED"}}}),
    types.Tool(name="sheets_update_cell", description="Update single cell.", inputSchema={"type": "object", "required": ["spreadsheet_id", "cell", "value"], "properties": {"spreadsheet_id": {"type": "string"}, "cell": {"type": "string"}, "value": {}}}),
    types.Tool(name="sheets_clear_range", description="Clear values (keep formatting).", inputSchema={"type": "object", "required": ["spreadsheet_id", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "range": {"type": "string"}}}),
    types.Tool(name="sheets_batch_clear", description="Clear multiple ranges at once.", inputSchema={"type": "object", "required": ["spreadsheet_id", "ranges"], "properties": {"spreadsheet_id": {"type": "string"}, "ranges": {"type": "array", "items": {"type": "string"}}}}),

    # Structure
    types.Tool(name="sheets_insert_rows_cols", description="Insert rows or columns.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "dimension", "start_index", "end_index"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "dimension": {"type": "string", "enum": ["ROWS", "COLUMNS"]}, "start_index": {"type": "integer"}, "end_index": {"type": "integer"}, "inherit_from_before": {"type": "boolean", "default": False}}}),
    types.Tool(name="sheets_delete_rows_cols", description="Delete rows or columns.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "dimension", "start_index", "end_index"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "dimension": {"type": "string", "enum": ["ROWS", "COLUMNS"]}, "start_index": {"type": "integer"}, "end_index": {"type": "integer"}}}),
    types.Tool(name="sheets_sort_range", description="Sort data by columns.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "range", "sort_specs"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}, "sort_specs": {"type": "array", "items": {"type": "object"}}}}),

    # Formatting
    types.Tool(name="sheets_format_cells", description="Format cells: font, color, bold, alignment, number format, background.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "range"], "properties": {
        "spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"},
        "bg_color": {"type": "string"}, "font_color": {"type": "string"}, "bold": {"type": "boolean"}, "italic": {"type": "boolean"},
        "underline": {"type": "boolean"}, "strikethrough": {"type": "boolean"}, "font_size": {"type": "integer"}, "font_family": {"type": "string"},
        "h_align": {"type": "string", "enum": ["LEFT", "CENTER", "RIGHT"]}, "v_align": {"type": "string", "enum": ["TOP", "MIDDLE", "BOTTOM"]},
        "wrap_strategy": {"type": "string", "enum": ["OVERFLOW_CELL", "CLIP", "WRAP"]},
        "number_format": {"type": "string"}, "number_format_type": {"type": "string"},
    }}),
    types.Tool(name="sheets_merge_cells", description="Merge cells.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}, "merge_type": {"type": "string", "enum": ["MERGE_ALL", "MERGE_COLUMNS", "MERGE_ROWS"]}}}),
    types.Tool(name="sheets_unmerge_cells", description="Unmerge cells.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}}}),
    types.Tool(name="sheets_set_column_width", description="Set column width.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "start_col", "end_col", "width"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "start_col": {"type": "integer"}, "end_col": {"type": "integer"}, "width": {"type": "integer"}}}),
    types.Tool(name="sheets_set_row_height", description="Set row height.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "start_row", "end_row", "height"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "start_row": {"type": "integer"}, "end_row": {"type": "integer"}, "height": {"type": "integer"}}}),
    types.Tool(name="sheets_auto_resize", description="Auto-resize columns or rows.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "dimension"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "dimension": {"type": "string", "enum": ["COLUMNS", "ROWS"]}, "start_index": {"type": "integer", "default": 0}, "end_index": {"type": "integer", "default": 26}}}),
    types.Tool(name="sheets_set_borders", description="Set borders on cells.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}, "style": {"type": "string", "enum": ["SOLID", "SOLID_MEDIUM", "SOLID_THICK", "DASHED", "DOTTED", "DOUBLE", "NONE"]}, "color": {"type": "string"}, "top": {"type": "boolean", "default": True}, "bottom": {"type": "boolean", "default": True}, "left": {"type": "boolean", "default": True}, "right": {"type": "boolean", "default": True}, "inner_horizontal": {"type": "boolean", "default": False}, "inner_vertical": {"type": "boolean", "default": False}}}),

    # Advanced
    types.Tool(name="sheets_conditional_format", description="Add conditional formatting rule.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "range", "rule_type"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}, "rule_type": {"type": "string", "enum": ["NUMBER_GREATER", "NUMBER_LESS", "NUMBER_BETWEEN", "TEXT_CONTAINS", "TEXT_NOT_CONTAINS", "CUSTOM_FORMULA", "NOT_BLANK", "BLANK", "COLOR_SCALE"]}, "values": {"type": "array", "items": {"type": "string"}}, "bg_color": {"type": "string"}, "text_color": {"type": "string"}, "bold": {"type": "boolean"}, "min_color": {"type": "string"}, "mid_color": {"type": "string"}, "max_color": {"type": "string"}}}),
    types.Tool(name="sheets_data_validation", description="Set data validation (dropdowns, checkboxes, etc).", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "range", "validation_type"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}, "validation_type": {"type": "string", "enum": ["ONE_OF_LIST", "NUMBER_BETWEEN", "NUMBER_GREATER", "NUMBER_LESS", "DATE_AFTER", "DATE_BEFORE", "CUSTOM_FORMULA", "BOOLEAN"]}, "values": {"type": "array", "items": {"type": "string"}}, "strict": {"type": "boolean", "default": True}, "input_message": {"type": "string"}}}),
    types.Tool(name="sheets_named_range", description="Create a named range.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "name", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "name": {"type": "string"}, "range": {"type": "string"}}}),
    types.Tool(name="sheets_filter_view", description="Create a saved filter view.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "title", "range"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "title": {"type": "string"}, "range": {"type": "string"}, "sort_column": {"type": "integer"}, "sort_order": {"type": "string", "enum": ["ASCENDING", "DESCENDING"]}, "filter_column": {"type": "integer"}, "hidden_values": {"type": "array", "items": {"type": "string"}}}}),
    types.Tool(name="sheets_basic_filter", description="Set or clear basic auto-filter.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}}}),
    types.Tool(name="sheets_pivot_table", description="Create a pivot table.", inputSchema={"type": "object", "required": ["spreadsheet_id", "source_sheet_id", "source_range", "target_sheet_id", "row_fields", "value_fields"], "properties": {"spreadsheet_id": {"type": "string"}, "source_sheet_id": {"type": "integer"}, "source_range": {"type": "string"}, "target_sheet_id": {"type": "integer"}, "target_row": {"type": "integer", "default": 0}, "target_col": {"type": "integer", "default": 0}, "row_fields": {"type": "array", "items": {"type": "integer"}}, "value_fields": {"type": "array", "items": {"type": "object"}}, "column_fields": {"type": "array", "items": {"type": "integer"}}}}),
    types.Tool(name="sheets_protect_range", description="Protect a range or sheet from editing.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range": {"type": "string"}, "description": {"type": "string"}, "warning_only": {"type": "boolean", "default": False}, "editors": {"type": "array", "items": {"type": "string"}}}}),
    types.Tool(name="sheets_set_note", description="Add/update/clear a note on a cell.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_id", "cell", "note"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "cell": {"type": "string"}, "note": {"type": "string"}}}),
    types.Tool(name="sheets_get_notes", description="Get all notes from a sheet.", inputSchema={"type": "object", "required": ["spreadsheet_id", "sheet_name"], "properties": {"spreadsheet_id": {"type": "string"}, "sheet_name": {"type": "string"}}}),
    types.Tool(name="sheets_export", description="Export spreadsheet as XLSX, CSV, PDF, etc.", inputSchema={"type": "object", "required": ["spreadsheet_id", "format"], "properties": {"spreadsheet_id": {"type": "string"}, "format": {"type": "string", "enum": ["xlsx", "csv", "pdf", "ods", "tsv", "html"]}, "sheet_id": {"type": "integer"}, "download_dir": {"type": "string"}}}),
    types.Tool(name="sheets_duplicate_template", description="Copy spreadsheet as template (clear data, keep formatting).", inputSchema={"type": "object", "required": ["spreadsheet_id", "new_title"], "properties": {"spreadsheet_id": {"type": "string"}, "new_title": {"type": "string"}, "folder_id": {"type": "string"}, "clear_data": {"type": "boolean", "default": True}}}),

    # Developer metadata
    types.Tool(name="sheets_get_developer_metadata", description="Get developer metadata by ID.", inputSchema={"type": "object", "required": ["spreadsheet_id", "metadata_id"], "properties": {"spreadsheet_id": {"type": "string"}, "metadata_id": {"type": "integer"}}}),
    types.Tool(name="sheets_search_developer_metadata", description="Search developer metadata by key or location.", inputSchema={"type": "object", "required": ["spreadsheet_id", "data_filters"], "properties": {"spreadsheet_id": {"type": "string"}, "data_filters": {"type": "array", "items": {"type": "object"}}}}),
]


# =============================================================================
# Handler — delegates to existing implementation functions
# =============================================================================

def _svc():
    return get_sheets_svc().spreadsheets()

def _vid(sid):
    return validate_spreadsheet_id(sid)

def _bu(sid, requests):
    """Execute batchUpdate."""
    return _svc().batchUpdate(spreadsheetId=_vid(sid), body={"requests": requests}).execute()


def handle(name: str, a: dict):
    svc = _svc()

    # ── File ops ──
    if name == "sheets_create":
        body = {"properties": {"title": a["title"]}}
        if "sheet_names" in a and a["sheet_names"]:
            body["sheets"] = [{"properties": {"title": n}} for n in a["sheet_names"]]
        result = svc.create(body=body).execute()
        sid = result["spreadsheetId"]
        if "folder_id" in a and a["folder_id"]:
            get_drive_svc().files().update(fileId=sid, addParents=a["folder_id"], removeParents="root", fields="id").execute()
        return {"spreadsheetId": sid, "title": a["title"], "link": f"https://docs.google.com/spreadsheets/d/{sid}/edit"}

    if name == "sheets_copy":
        sid = _vid(a["spreadsheet_id"])
        copy = get_drive_svc().files().copy(fileId=sid, body={"name": a["new_title"]}, supportsAllDrives=True).execute()
        new_id = copy["id"]
        if "folder_id" in a and a["folder_id"]:
            get_drive_svc().files().update(fileId=new_id, addParents=a["folder_id"], removeParents="root", fields="id").execute()
        return {"spreadsheetId": new_id, "title": a["new_title"], "link": f"https://docs.google.com/spreadsheets/d/{new_id}/edit"}

    if name == "sheets_get_info":
        sid = _vid(a["spreadsheet_id"])
        ss = svc.get(spreadsheetId=sid, fields="properties,sheets.properties,namedRanges").execute()
        props = ss.get("properties", {})
        sheets_info = []
        for sh in ss.get("sheets", []):
            sp = sh["properties"]
            sheets_info.append({"sheetId": sp["sheetId"], "title": sp["title"],
                               "rows": sp.get("gridProperties", {}).get("rowCount"),
                               "columns": sp.get("gridProperties", {}).get("columnCount"),
                               "hidden": sp.get("hidden", False)})
        return {"title": props.get("title"), "locale": props.get("locale"), "timeZone": props.get("timeZone"),
                "sheets": sheets_info, "namedRanges": ss.get("namedRanges", [])}

    if name == "sheets_list":
        q = "mimeType='application/vnd.google-apps.spreadsheet'"
        if "query" in a and a["query"]: q += f" and name contains '{a['query']}'"
        if "folder_id" in a and a["folder_id"]: q += f" and '{a['folder_id']}' in parents"
        r = get_drive_svc().files().list(q=q, pageSize=a.get("max_results", 20), fields="files(id,name,modifiedTime,owners)",
                                         supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        return {"spreadsheets": [{"id": f["id"], "name": f["name"], "modified": f.get("modifiedTime", "")[:10],
                                  "link": f"https://docs.google.com/spreadsheets/d/{f['id']}/edit"} for f in r.get("files", [])]}

    if name == "sheets_share":
        sid = _vid(a["spreadsheet_id"])
        perm = {"role": a["role"], "type": "user", "emailAddress": a["email"]}
        return get_drive_svc().permissions().create(fileId=sid, body=perm, supportsAllDrives=True).execute()

    if name == "sheets_get_permissions":
        sid = _vid(a["spreadsheet_id"])
        return get_drive_svc().permissions().list(fileId=sid, supportsAllDrives=True, fields="permissions(id,type,role,emailAddress,displayName)").execute()

    # ── Sheet tabs ──
    if name == "sheets_list_sheets":
        sid = _vid(a["spreadsheet_id"])
        ss = svc.get(spreadsheetId=sid, fields="sheets.properties").execute()
        return [{"sheetId": s["properties"]["sheetId"], "title": s["properties"]["title"],
                 "rows": s["properties"].get("gridProperties", {}).get("rowCount"),
                 "columns": s["properties"].get("gridProperties", {}).get("columnCount")} for s in ss.get("sheets", [])]

    if name == "sheets_add_sheet":
        sid = _vid(a["spreadsheet_id"])
        props = {"title": a["title"], "gridProperties": {"rowCount": a.get("rows", 1000), "columnCount": a.get("columns", 26)}}
        if "tab_color" in a: props["tabColorStyle"] = {"rgbColor": make_color(a["tab_color"])}
        r = _bu(sid, [{"addSheet": {"properties": props}}])
        return r["replies"][0]["addSheet"]["properties"]

    if name == "sheets_delete_sheet":
        return _bu(_vid(a["spreadsheet_id"]), [{"deleteSheet": {"sheetId": a["sheet_id"]}}])

    if name == "sheets_rename_sheet":
        return _bu(_vid(a["spreadsheet_id"]), [{"updateSheetProperties": {"properties": {"sheetId": a["sheet_id"], "title": a["new_title"]}, "fields": "title"}}])

    if name == "sheets_copy_sheet":
        sid = _vid(a["spreadsheet_id"])
        dest = _vid(a["destination_spreadsheet_id"]) if "destination_spreadsheet_id" in a else sid
        return svc.sheets().copyTo(spreadsheetId=sid, sheetId=a["sheet_id"], body={"destinationSpreadsheetId": dest}).execute()

    if name == "sheets_reorder":
        sid = _vid(a["spreadsheet_id"])
        reqs = [{"updateSheetProperties": {"properties": {"sheetId": s["sheetId"], "index": s["index"]}, "fields": "index"}} for s in a["sheet_order"]]
        return _bu(sid, reqs)

    # ── Read ──
    if name == "sheets_read_range":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().get(spreadsheetId=sid, range=a["range"], valueRenderOption=a.get("value_render", "FORMATTED_VALUE")).execute()

    if name == "sheets_batch_read":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().batchGet(spreadsheetId=sid, ranges=a["ranges"], valueRenderOption=a.get("value_render", "FORMATTED_VALUE")).execute()

    if name == "sheets_get_cell":
        sid = _vid(a["spreadsheet_id"])
        vals = svc.values().get(spreadsheetId=sid, range=a["cell"], valueRenderOption="FORMATTED_VALUE").execute()
        formula = svc.values().get(spreadsheetId=sid, range=a["cell"], valueRenderOption="FORMULA").execute()
        v = vals.get("values", [[""]])[0][0] if vals.get("values") else ""
        f = formula.get("values", [[""]])[0][0] if formula.get("values") else ""
        return {"cell": a["cell"], "value": v, "formula": f if f != v else None}

    if name == "sheets_search":
        sid = _vid(a["spreadsheet_id"])
        ss = svc.get(spreadsheetId=sid, fields="sheets.properties.title").execute()
        sheets = [s["properties"]["title"] for s in ss.get("sheets", [])]
        if "sheet_name" in a and a["sheet_name"]: sheets = [a["sheet_name"]]
        results = []
        for sheet in sheets:
            vals = svc.values().get(spreadsheetId=sid, range=f"'{sheet}'").execute().get("values", [])
            for r, row in enumerate(vals):
                for c, cell in enumerate(row):
                    if a["query"].lower() in str(cell).lower():
                        results.append({"sheet": sheet, "cell": f"{col_index_to_letter(c)}{r+1}", "value": cell})
        return {"matches": results}

    if name == "sheets_get_table":
        sid = _vid(a["spreadsheet_id"])
        sheet = a.get("sheet_name")
        if not sheet:
            ss = svc.get(spreadsheetId=sid, fields="sheets.properties.title").execute()
            sheet = ss["sheets"][0]["properties"]["title"]
        vals = svc.values().get(spreadsheetId=sid, range=f"'{sheet}'").execute().get("values", [])
        if a.get("max_rows", 0) > 0: vals = vals[:a["max_rows"] + (1 if a.get("has_header", True) else 0)]
        return rows_to_table(vals, has_header=a.get("has_header", True))

    if name == "sheets_get_formulas":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().get(spreadsheetId=sid, range=a["range"], valueRenderOption="FORMULA").execute()

    # ── Write ──
    if name == "sheets_write_range":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().update(spreadsheetId=sid, range=a["range"], valueInputOption=a.get("value_input", "USER_ENTERED"), body={"values": a["values"]}).execute()

    if name == "sheets_append_rows":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().append(spreadsheetId=sid, range=a["range"], valueInputOption=a.get("value_input", "USER_ENTERED"), body={"values": a["values"]}).execute()

    if name == "sheets_batch_write":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().batchUpdate(spreadsheetId=sid, body={"valueInputOption": a.get("value_input", "USER_ENTERED"), "data": a["data"]}).execute()

    if name == "sheets_update_cell":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().update(spreadsheetId=sid, range=a["cell"], valueInputOption="USER_ENTERED", body={"values": [[a["value"]]]}).execute()

    if name == "sheets_clear_range":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().clear(spreadsheetId=sid, range=a["range"], body={}).execute()

    if name == "sheets_batch_clear":
        sid = _vid(a["spreadsheet_id"])
        return svc.values().batchClear(spreadsheetId=sid, body={"ranges": a["ranges"]}).execute()

    # ── Structure ──
    if name == "sheets_insert_rows_cols":
        return _bu(_vid(a["spreadsheet_id"]), [{"insertDimension": {"range": {"sheetId": a["sheet_id"], "dimension": a["dimension"], "startIndex": a["start_index"], "endIndex": a["end_index"]}, "inheritFromBefore": a.get("inherit_from_before", False)}}])

    if name == "sheets_delete_rows_cols":
        return _bu(_vid(a["spreadsheet_id"]), [{"deleteDimension": {"range": {"sheetId": a["sheet_id"], "dimension": a["dimension"], "startIndex": a["start_index"], "endIndex": a["end_index"]}}}])

    if name == "sheets_sort_range":
        sid = _vid(a["spreadsheet_id"])
        gr = a1_to_grid_range(a["range"], a["sheet_id"])
        return _bu(sid, [{"sortRange": {"range": gr, "sortSpecs": a["sort_specs"]}}])

    # ── Formatting ──
    if name == "sheets_format_cells":
        sid = _vid(a["spreadsheet_id"])
        fmt_args = {k: v for k, v in a.items() if k not in ("spreadsheet_id", "sheet_id", "range")}
        cell_fmt, fields_str = make_cell_format(**fmt_args)
        gr = a1_to_grid_range(a["range"], a["sheet_id"])
        return _bu(sid, [{"repeatCell": {"range": gr, "cell": {"userEnteredFormat": cell_fmt}, "fields": fields_str}}])

    if name == "sheets_merge_cells":
        return _bu(_vid(a["spreadsheet_id"]), [{"mergeCells": {"range": a1_to_grid_range(a["range"], a["sheet_id"]), "mergeType": a.get("merge_type", "MERGE_ALL")}}])

    if name == "sheets_unmerge_cells":
        return _bu(_vid(a["spreadsheet_id"]), [{"unmergeCells": {"range": a1_to_grid_range(a["range"], a["sheet_id"])}}])

    if name == "sheets_set_column_width":
        return _bu(_vid(a["spreadsheet_id"]), [{"updateDimensionProperties": {"range": {"sheetId": a["sheet_id"], "dimension": "COLUMNS", "startIndex": a["start_col"], "endIndex": a["end_col"]}, "properties": {"pixelSize": a["width"]}, "fields": "pixelSize"}}])

    if name == "sheets_set_row_height":
        return _bu(_vid(a["spreadsheet_id"]), [{"updateDimensionProperties": {"range": {"sheetId": a["sheet_id"], "dimension": "ROWS", "startIndex": a["start_row"], "endIndex": a["end_row"]}, "properties": {"pixelSize": a["height"]}, "fields": "pixelSize"}}])

    if name == "sheets_auto_resize":
        return _bu(_vid(a["spreadsheet_id"]), [{"autoResizeDimensions": {"dimensions": {"sheetId": a["sheet_id"], "dimension": a["dimension"], "startIndex": a.get("start_index", 0), "endIndex": a.get("end_index", 26)}}}])

    if name == "sheets_set_borders":
        sid = _vid(a["spreadsheet_id"])
        gr = a1_to_grid_range(a["range"], a["sheet_id"])
        color = make_color(a.get("color", "#000000"))
        style = a.get("style", "SOLID")
        border = {"style": style, "colorStyle": {"rgbColor": color}}
        borders = {}
        if a.get("top", True): borders["top"] = border
        if a.get("bottom", True): borders["bottom"] = border
        if a.get("left", True): borders["left"] = border
        if a.get("right", True): borders["right"] = border
        if a.get("inner_horizontal"): borders["innerHorizontal"] = border
        if a.get("inner_vertical"): borders["innerVertical"] = border
        return _bu(sid, [{"updateBorders": {"range": gr, **borders}}])

    # ── Advanced ──
    if name == "sheets_conditional_format":
        sid = _vid(a["spreadsheet_id"])
        gr = a1_to_grid_range(a["range"], a["sheet_id"])
        if a["rule_type"] == "COLOR_SCALE":
            rule = {"addConditionalFormatRule": {"rule": {"ranges": [gr], "gradientRule": {
                "minpoint": {"color": make_color(a.get("min_color", "#FF0000")), "type": "MIN"},
                "maxpoint": {"color": make_color(a.get("max_color", "#00FF00")), "type": "MAX"},
                **({"midpoint": {"color": make_color(a["mid_color"]), "type": "PERCENTILE", "value": "50"}} if "mid_color" in a else {}),
            }}}}
        else:
            fmt = {}
            if "bg_color" in a: fmt["backgroundColor"] = make_color(a["bg_color"])
            if "text_color" in a: fmt["textFormat"] = {"foregroundColor": make_color(a["text_color"])}
            if "bold" in a: fmt.setdefault("textFormat", {})["bold"] = a["bold"]
            cond = {"type": a["rule_type"]}
            if "values" in a: cond["values"] = [{"userEnteredValue": v} for v in a["values"]]
            rule = {"addConditionalFormatRule": {"rule": {"ranges": [gr], "booleanRule": {"condition": cond, "format": fmt}}}}
        return _bu(sid, [rule])

    if name == "sheets_data_validation":
        sid = _vid(a["spreadsheet_id"])
        gr = a1_to_grid_range(a["range"], a["sheet_id"])
        cond = {"type": a["validation_type"]}
        if "values" in a: cond["values"] = [{"userEnteredValue": v} for v in a["values"]]
        rule = {"condition": cond, "strict": a.get("strict", True), "showCustomUi": True}
        if "input_message" in a: rule["inputMessage"] = a["input_message"]
        return _bu(sid, [{"setDataValidation": {"range": gr, "rule": rule}}])

    if name == "sheets_named_range":
        sid = _vid(a["spreadsheet_id"])
        gr = a1_to_grid_range(a["range"], a["sheet_id"])
        return _bu(sid, [{"addNamedRange": {"namedRange": {"name": a["name"], "range": gr}}}])

    if name == "sheets_filter_view":
        sid = _vid(a["spreadsheet_id"])
        gr = a1_to_grid_range(a["range"], a["sheet_id"])
        fv = {"title": a["title"], "range": gr}
        if "sort_column" in a:
            fv["sortSpecs"] = [{"dimensionIndex": a["sort_column"], "sortOrder": a.get("sort_order", "ASCENDING")}]
        if "filter_column" in a and "hidden_values" in a:
            fv["criteria"] = {str(a["filter_column"]): {"hiddenValues": a["hidden_values"]}}
        return _bu(sid, [{"addFilterView": {"filter": fv}}])

    if name == "sheets_basic_filter":
        sid = _vid(a["spreadsheet_id"])
        if "range" in a and a["range"]:
            gr = a1_to_grid_range(a["range"], a["sheet_id"])
            return _bu(sid, [{"setBasicFilter": {"filter": {"range": gr}}}])
        else:
            return _bu(sid, [{"clearBasicFilter": {"sheetId": a["sheet_id"]}}])

    if name == "sheets_pivot_table":
        sid = _vid(a["spreadsheet_id"])
        src_gr = a1_to_grid_range(a["source_range"], a["source_sheet_id"])
        pivot = {"source": src_gr,
                 "rows": [{"sourceColumnOffset": f, "sortOrder": "ASCENDING", "showTotals": True} for f in a["row_fields"]],
                 "values": a["value_fields"]}
        if "column_fields" in a:
            pivot["columns"] = [{"sourceColumnOffset": f, "sortOrder": "ASCENDING"} for f in a["column_fields"]]
        return _bu(sid, [{"updateCells": {"rows": [{"values": [{"pivotTable": pivot}]}],
                                          "start": {"sheetId": a["target_sheet_id"], "rowIndex": a.get("target_row", 0), "columnIndex": a.get("target_col", 0)},
                                          "fields": "pivotTable"}}])

    if name == "sheets_protect_range":
        sid = _vid(a["spreadsheet_id"])
        prot = {"description": a.get("description", ""), "warningOnly": a.get("warning_only", False)}
        if "range" in a and a["range"]:
            prot["range"] = a1_to_grid_range(a["range"], a["sheet_id"])
        else:
            prot["sheetId"] = a["sheet_id"]
        if "editors" in a: prot["editors"] = {"users": a["editors"]}
        return _bu(sid, [{"addProtectedRange": {"protectedRange": prot}}])

    if name == "sheets_set_note":
        sid = _vid(a["spreadsheet_id"])
        parsed = parse_a1_range(a["cell"])
        row = (parsed.get("start_row") or 1) - 1
        col = col_letter_to_index(parsed.get("start_col") or "A")
        return _bu(sid, [{"updateCells": {"rows": [{"values": [{"note": a["note"]}]}],
                                          "start": {"sheetId": a["sheet_id"], "rowIndex": row, "columnIndex": col},
                                          "fields": "note"}}])

    if name == "sheets_get_notes":
        sid = _vid(a["spreadsheet_id"])
        ss = svc.get(spreadsheetId=sid, ranges=f"'{a['sheet_name']}'", fields="sheets.data.rowData.values.note", includeGridData=True).execute()
        notes = []
        for sh in ss.get("sheets", []):
            for ri, row in enumerate(sh.get("data", [{}])[0].get("rowData", [])):
                for ci, cell in enumerate(row.get("values", [])):
                    if cell.get("note"):
                        notes.append({"cell": f"{col_index_to_letter(ci)}{ri+1}", "note": cell["note"]})
        return {"notes": notes}

    if name == "sheets_export":
        sid = _vid(a["spreadsheet_id"])
        fmt_map = {"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   "csv": "text/csv", "pdf": "application/pdf", "ods": "application/vnd.oasis.opendocument.spreadsheet",
                   "tsv": "text/tab-separated-values", "html": "text/html"}
        mime = fmt_map.get(a["format"], "application/pdf")
        from utils import export_bytes
        data = export_bytes(get_drive_svc(), sid, mime)
        dl_dir = Path(a.get("download_dir") or DOWNLOAD_DIR)
        dl_dir.mkdir(exist_ok=True)
        info = svc.get(spreadsheetId=sid, fields="properties.title").execute()
        fname = f"{info['properties']['title']}.{a['format']}"
        path = dl_dir / fname
        path.write_bytes(data)
        return {"saved": str(path), "size": fmt_size(len(data))}

    if name == "sheets_duplicate_template":
        sid = _vid(a["spreadsheet_id"])
        copy = get_drive_svc().files().copy(fileId=sid, body={"name": a["new_title"]}, supportsAllDrives=True).execute()
        new_id = copy["id"]
        if "folder_id" in a: get_drive_svc().files().update(fileId=new_id, addParents=a["folder_id"], removeParents="root").execute()
        if a.get("clear_data", True):
            ss = svc.get(spreadsheetId=new_id, fields="sheets.properties").execute()
            for sh in ss.get("sheets", []):
                title = sh["properties"]["title"]
                svc.values().clear(spreadsheetId=new_id, range=f"'{title}'", body={}).execute()
        return {"spreadsheetId": new_id, "link": f"https://docs.google.com/spreadsheets/d/{new_id}/edit"}

    # ── Developer metadata ──
    if name == "sheets_get_developer_metadata":
        sid = _vid(a["spreadsheet_id"])
        return svc.developerMetadata().get(spreadsheetId=sid, metadataId=a["metadata_id"]).execute()

    if name == "sheets_search_developer_metadata":
        sid = _vid(a["spreadsheet_id"])
        return svc.developerMetadata().search(spreadsheetId=sid, body={"dataFilters": a["data_filters"]}).execute()

    raise ValueError(f"Unknown sheets tool: {name}")
