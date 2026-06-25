"""
Google Docs API v1 — full coverage.
3 REST endpoints, ~25 batchUpdate request types exposed as individual MCP tools.
"""

from mcp import types
from auth import docs

# =============================================================================
# Tool definitions
# =============================================================================

TOOLS = [
    # --- Document CRUD ---
    types.Tool(
        name="docs_create",
        description="Create a new empty Google Doc. Returns document ID and link.",
        inputSchema={"type": "object", "required": ["title"], "properties": {
            "title": {"type": "string", "description": "Document title"},
        }},
    ),
    types.Tool(
        name="docs_get",
        description="Get a Google Doc's full content as structured JSON (paragraphs, tables, lists, headers, footers, images). Use for reading document structure.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string", "description": "Document ID or URL"},
        }},
    ),
    types.Tool(
        name="docs_get_text",
        description="Get a Google Doc's content as plain text (all paragraphs concatenated). Simpler than docs_get for just reading text.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string", "description": "Document ID or URL"},
            "max_chars": {"type": "integer", "description": "Max characters (default 50000)", "default": 50000},
        }},
    ),

    # --- Text operations ---
    types.Tool(
        name="docs_insert_text",
        description="Insert text at a specific index in a Google Doc.",
        inputSchema={"type": "object", "required": ["document_id", "text"], "properties": {
            "document_id": {"type": "string"},
            "text": {"type": "string", "description": "Text to insert"},
            "index": {"type": "integer", "description": "Character index to insert at (1 = start of body). Default: end of document.", "default": -1},
            "segment_id": {"type": "string", "description": "Segment ID (for headers/footers). Omit for body."},
        }},
    ),
    types.Tool(
        name="docs_delete_content",
        description="Delete content in a range of character indices.",
        inputSchema={"type": "object", "required": ["document_id", "start_index", "end_index"], "properties": {
            "document_id": {"type": "string"},
            "start_index": {"type": "integer"},
            "end_index": {"type": "integer"},
            "segment_id": {"type": "string"},
        }},
    ),
    types.Tool(
        name="docs_replace_all_text",
        description="Find and replace all occurrences of text in the document.",
        inputSchema={"type": "object", "required": ["document_id", "find", "replace"], "properties": {
            "document_id": {"type": "string"},
            "find": {"type": "string", "description": "Text to find"},
            "replace": {"type": "string", "description": "Replacement text"},
            "match_case": {"type": "boolean", "description": "Case-sensitive match", "default": True},
        }},
    ),

    # --- Formatting ---
    types.Tool(
        name="docs_update_text_style",
        description="Apply text formatting (bold, italic, underline, font, size, color, link) to a range.",
        inputSchema={"type": "object", "required": ["document_id", "start_index", "end_index"], "properties": {
            "document_id": {"type": "string"},
            "start_index": {"type": "integer"},
            "end_index": {"type": "integer"},
            "bold": {"type": "boolean"},
            "italic": {"type": "boolean"},
            "underline": {"type": "boolean"},
            "strikethrough": {"type": "boolean"},
            "font_family": {"type": "string", "description": "Font name (e.g. 'Arial', 'Courier New')"},
            "font_size": {"type": "number", "description": "Font size in points"},
            "foreground_color": {"type": "string", "description": "Text color hex (#RRGGBB)"},
            "background_color": {"type": "string", "description": "Highlight color hex (#RRGGBB)"},
            "link_url": {"type": "string", "description": "URL to link the text to"},
            "segment_id": {"type": "string"},
        }},
    ),
    types.Tool(
        name="docs_update_paragraph_style",
        description="Update paragraph formatting: alignment, spacing, indentation, heading level, named style.",
        inputSchema={"type": "object", "required": ["document_id", "start_index", "end_index"], "properties": {
            "document_id": {"type": "string"},
            "start_index": {"type": "integer"},
            "end_index": {"type": "integer"},
            "alignment": {"type": "string", "enum": ["START", "CENTER", "END", "JUSTIFIED"]},
            "named_style": {"type": "string", "enum": ["NORMAL_TEXT", "TITLE", "SUBTITLE", "HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6"]},
            "line_spacing": {"type": "number", "description": "Line spacing (100 = single, 200 = double)"},
            "space_above": {"type": "number", "description": "Space above paragraph in points"},
            "space_below": {"type": "number", "description": "Space below paragraph in points"},
            "indent_first_line": {"type": "number", "description": "First line indent in points"},
            "indent_start": {"type": "number", "description": "Left indent in points"},
            "indent_end": {"type": "number", "description": "Right indent in points"},
            "direction": {"type": "string", "enum": ["LEFT_TO_RIGHT", "RIGHT_TO_LEFT"]},
            "segment_id": {"type": "string"},
        }},
    ),

    # --- Lists / Bullets ---
    types.Tool(
        name="docs_create_bullets",
        description="Create a bulleted or numbered list from a range of paragraphs.",
        inputSchema={"type": "object", "required": ["document_id", "start_index", "end_index"], "properties": {
            "document_id": {"type": "string"},
            "start_index": {"type": "integer"},
            "end_index": {"type": "integer"},
            "bullet_preset": {"type": "string", "description": "Preset: BULLET_DISC_CIRCLE_SQUARE, NUMBERED_DECIMAL_ALPHA_ROMAN, etc.", "default": "BULLET_DISC_CIRCLE_SQUARE"},
            "segment_id": {"type": "string"},
        }},
    ),
    types.Tool(
        name="docs_delete_bullets",
        description="Remove bullets/numbering from a range of paragraphs.",
        inputSchema={"type": "object", "required": ["document_id", "start_index", "end_index"], "properties": {
            "document_id": {"type": "string"},
            "start_index": {"type": "integer"},
            "end_index": {"type": "integer"},
            "segment_id": {"type": "string"},
        }},
    ),

    # --- Tables ---
    types.Tool(
        name="docs_insert_table",
        description="Insert a table at a specific index.",
        inputSchema={"type": "object", "required": ["document_id", "rows", "columns"], "properties": {
            "document_id": {"type": "string"},
            "rows": {"type": "integer"},
            "columns": {"type": "integer"},
            "index": {"type": "integer", "description": "Insert position (default: end)", "default": -1},
            "segment_id": {"type": "string"},
        }},
    ),
    types.Tool(
        name="docs_insert_table_row",
        description="Insert a row into a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "row_index"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer", "description": "Start index of the table element"},
            "row_index": {"type": "integer", "description": "Row index to insert below"},
            "insert_below": {"type": "boolean", "default": True},
        }},
    ),
    types.Tool(
        name="docs_insert_table_column",
        description="Insert a column into a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "column_index"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "column_index": {"type": "integer"},
            "insert_right": {"type": "boolean", "default": True},
        }},
    ),
    types.Tool(
        name="docs_delete_table_row",
        description="Delete a row from a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "row_index"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "row_index": {"type": "integer"},
        }},
    ),
    types.Tool(
        name="docs_delete_table_column",
        description="Delete a column from a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "column_index"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "column_index": {"type": "integer"},
        }},
    ),
    types.Tool(
        name="docs_merge_table_cells",
        description="Merge cells in a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "row_start", "row_end", "col_start", "col_end"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "row_start": {"type": "integer"},
            "row_end": {"type": "integer"},
            "col_start": {"type": "integer"},
            "col_end": {"type": "integer"},
        }},
    ),
    types.Tool(
        name="docs_unmerge_table_cells",
        description="Unmerge previously merged cells in a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "row_start", "row_end", "col_start", "col_end"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "row_start": {"type": "integer"},
            "row_end": {"type": "integer"},
            "col_start": {"type": "integer"},
            "col_end": {"type": "integer"},
        }},
    ),
    types.Tool(
        name="docs_update_table_column_properties",
        description="Set column width in a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "column_index", "width_pts"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "column_index": {"type": "integer"},
            "width_pts": {"type": "number", "description": "Column width in points"},
        }},
    ),
    types.Tool(
        name="docs_update_table_row_style",
        description="Set row height and header properties in a table.",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "row_index"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "row_index": {"type": "integer"},
            "min_height_pts": {"type": "number", "description": "Minimum row height in points"},
            "prevent_overflow": {"type": "boolean"},
        }},
    ),
    types.Tool(
        name="docs_pin_table_header_rows",
        description="Pin rows as table header (repeat on each page).",
        inputSchema={"type": "object", "required": ["document_id", "table_start_index", "pinned_count"], "properties": {
            "document_id": {"type": "string"},
            "table_start_index": {"type": "integer"},
            "pinned_count": {"type": "integer", "description": "Number of rows to pin as headers"},
        }},
    ),

    # --- Images ---
    types.Tool(
        name="docs_insert_inline_image",
        description="Insert an image from a URL into the document.",
        inputSchema={"type": "object", "required": ["document_id", "uri"], "properties": {
            "document_id": {"type": "string"},
            "uri": {"type": "string", "description": "Image URL (must be publicly accessible)"},
            "index": {"type": "integer", "description": "Insert position (default: end)", "default": -1},
            "width_pts": {"type": "number", "description": "Image width in points"},
            "height_pts": {"type": "number", "description": "Image height in points"},
            "segment_id": {"type": "string"},
        }},
    ),

    # --- Breaks ---
    types.Tool(
        name="docs_insert_page_break",
        description="Insert a page break at a specific index.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string"},
            "index": {"type": "integer", "default": -1},
            "segment_id": {"type": "string"},
        }},
    ),
    types.Tool(
        name="docs_insert_section_break",
        description="Insert a section break (new page or continuous).",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string"},
            "index": {"type": "integer", "default": -1},
            "break_type": {"type": "string", "enum": ["NEXT_PAGE", "CONTINUOUS"], "default": "NEXT_PAGE"},
            "segment_id": {"type": "string"},
        }},
    ),

    # --- Named ranges ---
    types.Tool(
        name="docs_create_named_range",
        description="Create a named range in the document for later reference.",
        inputSchema={"type": "object", "required": ["document_id", "name", "start_index", "end_index"], "properties": {
            "document_id": {"type": "string"},
            "name": {"type": "string"},
            "start_index": {"type": "integer"},
            "end_index": {"type": "integer"},
            "segment_id": {"type": "string"},
        }},
    ),
    types.Tool(
        name="docs_delete_named_range",
        description="Delete a named range by name or ID.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string"},
            "name": {"type": "string", "description": "Named range name (use this OR named_range_id)"},
            "named_range_id": {"type": "string", "description": "Named range ID"},
        }},
    ),
    types.Tool(
        name="docs_replace_named_range_content",
        description="Replace all content in a named range with new text.",
        inputSchema={"type": "object", "required": ["document_id", "text"], "properties": {
            "document_id": {"type": "string"},
            "text": {"type": "string", "description": "New text content"},
            "name": {"type": "string"},
            "named_range_id": {"type": "string"},
        }},
    ),

    # --- Headers / Footers ---
    types.Tool(
        name="docs_create_header",
        description="Create a header for a section of the document.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string"},
            "section_break_index": {"type": "integer", "description": "Index of section break. Omit for default section."},
        }},
    ),
    types.Tool(
        name="docs_create_footer",
        description="Create a footer for a section of the document.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string"},
            "section_break_index": {"type": "integer"},
        }},
    ),
    types.Tool(
        name="docs_delete_header",
        description="Delete a header by its ID.",
        inputSchema={"type": "object", "required": ["document_id", "header_id"], "properties": {
            "document_id": {"type": "string"},
            "header_id": {"type": "string"},
        }},
    ),
    types.Tool(
        name="docs_delete_footer",
        description="Delete a footer by its ID.",
        inputSchema={"type": "object", "required": ["document_id", "footer_id"], "properties": {
            "document_id": {"type": "string"},
            "footer_id": {"type": "string"},
        }},
    ),

    # --- Document-level style ---
    types.Tool(
        name="docs_update_document_style",
        description="Update document-level properties: margins, page size, orientation.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string"},
            "margin_top_pts": {"type": "number"},
            "margin_bottom_pts": {"type": "number"},
            "margin_left_pts": {"type": "number"},
            "margin_right_pts": {"type": "number"},
            "page_width_pts": {"type": "number"},
            "page_height_pts": {"type": "number"},
            "use_first_page_header_footer": {"type": "boolean"},
        }},
    ),

    # --- Table of Contents ---
    types.Tool(
        name="docs_insert_toc",
        description="Insert a table of contents at a specific index.",
        inputSchema={"type": "object", "required": ["document_id"], "properties": {
            "document_id": {"type": "string"},
            "index": {"type": "integer", "default": -1},
            "segment_id": {"type": "string"},
        }},
    ),
]


# =============================================================================
# Helpers
# =============================================================================

def _parse_doc_id(document_id: str) -> str:
    if "/" in document_id:
        import re
        match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", document_id)
        if match:
            return match.group(1)
        raise ValueError(f"Cannot extract document ID from URL: {document_id}")
    return document_id.strip()


def _make_location(index: int, segment_id: str = None) -> dict:
    loc = {"index": index}
    if segment_id:
        loc["segmentId"] = segment_id
    return loc


def _make_range(start: int, end: int, segment_id: str = None) -> dict:
    r = {"startIndex": start, "endIndex": end}
    if segment_id:
        r["segmentId"] = segment_id
    return r


def _hex_to_color(hex_color: str) -> dict:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return {"red": r / 255, "green": g / 255, "blue": b / 255}


def _pts(value: float) -> dict:
    return {"magnitude": value, "unit": "PT"}


def _get_end_index(doc: dict) -> int:
    body = doc.get("body", {})
    content = body.get("content", [])
    if content:
        last = content[-1]
        return last.get("endIndex", 1) - 1
    return 1


def _batch_update(document_id: str, requests: list) -> dict:
    return docs().documents().batchUpdate(
        documentId=document_id, body={"requests": requests}
    ).execute()


# =============================================================================
# Handler
# =============================================================================

def handle(name: str, a: dict):
    if name == "docs_create":
        result = docs().documents().create(body={"title": a["title"]}).execute()
        doc_id = result["documentId"]
        return {"documentId": doc_id, "title": a["title"], "link": f"https://docs.google.com/document/d/{doc_id}/edit"}

    if name == "docs_get":
        doc_id = _parse_doc_id(a["document_id"])
        return docs().documents().get(documentId=doc_id).execute()

    if name == "docs_get_text":
        doc_id = _parse_doc_id(a["document_id"])
        doc = docs().documents().get(documentId=doc_id).execute()
        parts = []
        for elem in doc.get("body", {}).get("content", []):
            if "paragraph" in elem:
                for e in elem["paragraph"].get("elements", []):
                    if "textRun" in e:
                        parts.append(e["textRun"]["content"])
            elif "table" in elem:
                for row in elem["table"].get("tableRows", []):
                    cells = []
                    for cell in row.get("tableCells", []):
                        cell_text = ""
                        for content in cell.get("content", []):
                            if "paragraph" in content:
                                for e in content["paragraph"].get("elements", []):
                                    if "textRun" in e:
                                        cell_text += e["textRun"]["content"]
                        cells.append(cell_text.strip())
                    parts.append(" | ".join(cells))
        text = "".join(parts)
        max_chars = a.get("max_chars", 50000)
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... [truncated — {len(text) - max_chars} more chars]"
        return {"title": doc.get("title", ""), "documentId": doc.get("documentId", ""), "text": text, "chars": len(text)}

    if name == "docs_insert_text":
        doc_id = _parse_doc_id(a["document_id"])
        idx = a.get("index", -1)
        if idx == -1:
            doc = docs().documents().get(documentId=doc_id).execute()
            idx = _get_end_index(doc)
        req = {"insertText": {"text": a["text"], "location": _make_location(idx, a.get("segment_id"))}}
        return _batch_update(doc_id, [req])

    if name == "docs_delete_content":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"deleteContentRange": {"range": _make_range(a["start_index"], a["end_index"], a.get("segment_id"))}}
        return _batch_update(doc_id, [req])

    if name == "docs_replace_all_text":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"replaceAllText": {
            "containsText": {"text": a["find"], "matchCase": a.get("match_case", True)},
            "replaceText": a["replace"],
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_update_text_style":
        doc_id = _parse_doc_id(a["document_id"])
        style = {}
        fields = []
        if "bold" in a: style["bold"] = a["bold"]; fields.append("bold")
        if "italic" in a: style["italic"] = a["italic"]; fields.append("italic")
        if "underline" in a: style["underline"] = a["underline"]; fields.append("underline")
        if "strikethrough" in a: style["strikethrough"] = a["strikethrough"]; fields.append("strikethrough")
        if "font_family" in a: style["weightedFontFamily"] = {"fontFamily": a["font_family"]}; fields.append("weightedFontFamily")
        if "font_size" in a: style["fontSize"] = _pts(a["font_size"]); fields.append("fontSize")
        if "foreground_color" in a: style["foregroundColor"] = {"color": {"rgbColor": _hex_to_color(a["foreground_color"])}}; fields.append("foregroundColor")
        if "background_color" in a: style["backgroundColor"] = {"color": {"rgbColor": _hex_to_color(a["background_color"])}}; fields.append("backgroundColor")
        if "link_url" in a: style["link"] = {"url": a["link_url"]}; fields.append("link")
        req = {"updateTextStyle": {
            "textStyle": style,
            "range": _make_range(a["start_index"], a["end_index"], a.get("segment_id")),
            "fields": ",".join(fields),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_update_paragraph_style":
        doc_id = _parse_doc_id(a["document_id"])
        style = {}
        fields = []
        if "alignment" in a: style["alignment"] = a["alignment"]; fields.append("alignment")
        if "named_style" in a: style["namedStyleType"] = a["named_style"]; fields.append("namedStyleType")
        if "line_spacing" in a: style["lineSpacing"] = a["line_spacing"]; fields.append("lineSpacing")
        if "space_above" in a: style["spaceAbove"] = _pts(a["space_above"]); fields.append("spaceAbove")
        if "space_below" in a: style["spaceBelow"] = _pts(a["space_below"]); fields.append("spaceBelow")
        if "indent_first_line" in a: style["indentFirstLine"] = _pts(a["indent_first_line"]); fields.append("indentFirstLine")
        if "indent_start" in a: style["indentStart"] = _pts(a["indent_start"]); fields.append("indentStart")
        if "indent_end" in a: style["indentEnd"] = _pts(a["indent_end"]); fields.append("indentEnd")
        if "direction" in a: style["direction"] = a["direction"]; fields.append("direction")
        req = {"updateParagraphStyle": {
            "paragraphStyle": style,
            "range": _make_range(a["start_index"], a["end_index"], a.get("segment_id")),
            "fields": ",".join(fields),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_create_bullets":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"createParagraphBullets": {
            "range": _make_range(a["start_index"], a["end_index"], a.get("segment_id")),
            "bulletPreset": a.get("bullet_preset", "BULLET_DISC_CIRCLE_SQUARE"),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_delete_bullets":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"deleteParagraphBullets": {
            "range": _make_range(a["start_index"], a["end_index"], a.get("segment_id")),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_insert_table":
        doc_id = _parse_doc_id(a["document_id"])
        idx = a.get("index", -1)
        if idx == -1:
            doc = docs().documents().get(documentId=doc_id).execute()
            idx = _get_end_index(doc)
        req = {"insertTable": {
            "rows": a["rows"], "columns": a["columns"],
            "location": _make_location(idx, a.get("segment_id")),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_insert_table_row":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"insertTableRow": {
            "tableCellLocation": {"tableStartLocation": {"index": a["table_start_index"]}, "rowIndex": a["row_index"], "columnIndex": 0},
            "insertBelow": a.get("insert_below", True),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_insert_table_column":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"insertTableColumn": {
            "tableCellLocation": {"tableStartLocation": {"index": a["table_start_index"]}, "rowIndex": 0, "columnIndex": a["column_index"]},
            "insertRight": a.get("insert_right", True),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_delete_table_row":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"deleteTableRow": {
            "tableCellLocation": {"tableStartLocation": {"index": a["table_start_index"]}, "rowIndex": a["row_index"], "columnIndex": 0},
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_delete_table_column":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"deleteTableColumn": {
            "tableCellLocation": {"tableStartLocation": {"index": a["table_start_index"]}, "rowIndex": 0, "columnIndex": a["column_index"]},
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_merge_table_cells":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"mergeTableCells": {"tableRange": {
            "tableCellLocation": {"tableStartLocation": {"index": a["table_start_index"]}, "rowIndex": a["row_start"], "columnIndex": a["col_start"]},
            "rowSpan": a["row_end"] - a["row_start"], "columnSpan": a["col_end"] - a["col_start"],
        }}}
        return _batch_update(doc_id, [req])

    if name == "docs_unmerge_table_cells":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"unmergeTableCells": {"tableRange": {
            "tableCellLocation": {"tableStartLocation": {"index": a["table_start_index"]}, "rowIndex": a["row_start"], "columnIndex": a["col_start"]},
            "rowSpan": a["row_end"] - a["row_start"], "columnSpan": a["col_end"] - a["col_start"],
        }}}
        return _batch_update(doc_id, [req])

    if name == "docs_update_table_column_properties":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"updateTableColumnProperties": {
            "tableStartLocation": {"index": a["table_start_index"]},
            "columnIndices": [a["column_index"]],
            "tableColumnProperties": {"width": _pts(a["width_pts"]), "widthType": "FIXED_WIDTH"},
            "fields": "width,widthType",
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_update_table_row_style":
        doc_id = _parse_doc_id(a["document_id"])
        style = {}
        fields = []
        if "min_height_pts" in a:
            style["minRowHeight"] = _pts(a["min_height_pts"])
            fields.append("minRowHeight")
        if "prevent_overflow" in a:
            style["preventOverflow"] = a["prevent_overflow"]
            fields.append("preventOverflow")
        req = {"updateTableRowStyle": {
            "tableStartLocation": {"index": a["table_start_index"]},
            "rowIndices": [a["row_index"]],
            "tableRowStyle": style,
            "fields": ",".join(fields),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_pin_table_header_rows":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"pinTableHeaderRows": {
            "tableStartLocation": {"index": a["table_start_index"]},
            "pinnedHeaderRowsCount": a["pinned_count"],
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_insert_inline_image":
        doc_id = _parse_doc_id(a["document_id"])
        idx = a.get("index", -1)
        if idx == -1:
            doc = docs().documents().get(documentId=doc_id).execute()
            idx = _get_end_index(doc)
        img = {"uri": a["uri"], "location": _make_location(idx, a.get("segment_id"))}
        size = {}
        if "width_pts" in a: size["width"] = _pts(a["width_pts"])
        if "height_pts" in a: size["height"] = _pts(a["height_pts"])
        if size: img["objectSize"] = size
        req = {"insertInlineImage": img}
        return _batch_update(doc_id, [req])

    if name == "docs_insert_page_break":
        doc_id = _parse_doc_id(a["document_id"])
        idx = a.get("index", -1)
        if idx == -1:
            doc = docs().documents().get(documentId=doc_id).execute()
            idx = _get_end_index(doc)
        req = {"insertPageBreak": {"location": _make_location(idx, a.get("segment_id"))}}
        return _batch_update(doc_id, [req])

    if name == "docs_insert_section_break":
        doc_id = _parse_doc_id(a["document_id"])
        idx = a.get("index", -1)
        if idx == -1:
            doc = docs().documents().get(documentId=doc_id).execute()
            idx = _get_end_index(doc)
        req = {"insertSectionBreak": {
            "location": _make_location(idx, a.get("segment_id")),
            "sectionType": a.get("break_type", "NEXT_PAGE"),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_create_named_range":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"createNamedRange": {
            "name": a["name"],
            "range": _make_range(a["start_index"], a["end_index"], a.get("segment_id")),
        }}
        return _batch_update(doc_id, [req])

    if name == "docs_delete_named_range":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"deleteNamedRange": {}}
        if "name" in a: req["deleteNamedRange"]["name"] = a["name"]
        elif "named_range_id" in a: req["deleteNamedRange"]["namedRangeId"] = a["named_range_id"]
        return _batch_update(doc_id, [req])

    if name == "docs_replace_named_range_content":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"replaceNamedRangeContent": {"text": a["text"]}}
        if "name" in a: req["replaceNamedRangeContent"]["namedRangeName"] = a["name"]
        elif "named_range_id" in a: req["replaceNamedRangeContent"]["namedRangeId"] = a["named_range_id"]
        return _batch_update(doc_id, [req])

    if name == "docs_create_header":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"createHeader": {"type": "DEFAULT"}}
        if "section_break_index" in a:
            req["createHeader"]["sectionBreakLocation"] = {"index": a["section_break_index"]}
        return _batch_update(doc_id, [req])

    if name == "docs_create_footer":
        doc_id = _parse_doc_id(a["document_id"])
        req = {"createFooter": {"type": "DEFAULT"}}
        if "section_break_index" in a:
            req["createFooter"]["sectionBreakLocation"] = {"index": a["section_break_index"]}
        return _batch_update(doc_id, [req])

    if name == "docs_delete_header":
        doc_id = _parse_doc_id(a["document_id"])
        return _batch_update(doc_id, [{"deleteHeader": {"headerId": a["header_id"]}}])

    if name == "docs_delete_footer":
        doc_id = _parse_doc_id(a["document_id"])
        return _batch_update(doc_id, [{"deleteFooter": {"footerId": a["footer_id"]}}])

    if name == "docs_update_document_style":
        doc_id = _parse_doc_id(a["document_id"])
        style = {}
        fields = []
        if "margin_top_pts" in a: style["marginTop"] = _pts(a["margin_top_pts"]); fields.append("marginTop")
        if "margin_bottom_pts" in a: style["marginBottom"] = _pts(a["margin_bottom_pts"]); fields.append("marginBottom")
        if "margin_left_pts" in a: style["marginLeft"] = _pts(a["margin_left_pts"]); fields.append("marginLeft")
        if "margin_right_pts" in a: style["marginRight"] = _pts(a["margin_right_pts"]); fields.append("marginRight")
        if "page_width_pts" in a or "page_height_pts" in a:
            ps = {}
            if "page_width_pts" in a: ps["width"] = _pts(a["page_width_pts"])
            if "page_height_pts" in a: ps["height"] = _pts(a["page_height_pts"])
            style["pageSize"] = ps
            fields.append("pageSize")
        if "use_first_page_header_footer" in a:
            style["useFirstPageHeaderFooter"] = a["use_first_page_header_footer"]
            fields.append("useFirstPageHeaderFooter")
        req = {"updateDocumentStyle": {"documentStyle": style, "fields": ",".join(fields)}}
        return _batch_update(doc_id, [req])

    if name == "docs_insert_toc":
        doc_id = _parse_doc_id(a["document_id"])
        idx = a.get("index", -1)
        if idx == -1:
            doc = docs().documents().get(documentId=doc_id).execute()
            idx = _get_end_index(doc)
        req = {"insertTableOfContents": {"location": _make_location(idx, a.get("segment_id"))}}
        return _batch_update(doc_id, [req])

    raise ValueError(f"Unknown docs tool: {name}")
