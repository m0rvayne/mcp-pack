# Fathom MCP Server - Usage Guide

## Quick Start

### 1. Installation

Install dependencies:

```bash
uv sync
uv run python -c "from server import mcp; print('Server ready!')"
```

### 2. Running the Server

#### Option A: Direct Python Execution

```bash
python server.py
```

#### Option B: Using fastmcp CLI

```bash
fastmcp run server.py
```

#### Option C: Using uv (recommended)

```bash
uv run --with fastmcp fastmcp run server.py
```

If you created a `.env` file with `FATHOM_API_KEY=...`, it is auto-loaded by `server.py`.

### 3. Claude Desktop Integration

Add this configuration to your Claude Desktop config file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "fathom": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/fathom-mcp",
        "run",
        "fastmcp",
        "run",
        "server.py"
      ],
      "env": {
        "FATHOM_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

After adding the configuration, restart Claude Desktop.

## Available Tools

### 1. list_meetings

List meetings with advanced filtering options.

**Example prompts for Claude:**
- "Show me all meetings from the past week"
- "List meetings with alice@acme.com as a participant"
- "Find meetings with external participants"
- "Show me meetings recorded by bob@acme.com with transcripts"

**Parameters:**
- `cursor`: For pagination
- `calendar_invitees`: Filter by participant emails
- `calendar_invitees_domains`: Filter by company domains
- `calendar_invitees_domains_type`: Filter by internal/external
- `created_after` / `created_before`: Date range filtering
- `recorded_by`: Filter by recording user
- `teams`: Filter by team names
- `include_action_items`: Include action items in response
- `include_crm_matches`: Include CRM data
- `include_summary`: Include meeting summary
- `include_transcript`: Include full transcript

### 2. get_summary

Get the summary for a specific meeting recording.

**Example prompts:**
- "Get the summary for recording 93339249"
- "Show me what was discussed in meeting 93339249"

**Parameters:**
- `recording_id`: The meeting recording ID (required)
- `destination_url`: Optional URL for async delivery

### 3. get_transcript

Get the transcript for a meeting with speaker information and timestamps.

**Example prompts:**
- "Get the transcript for recording 93339249"
- "Show me the full transcript with timestamps for meeting 93339249"

**Parameters:**
- `recording_id`: The meeting recording ID (required)
- `destination_url`: Optional URL for async delivery

### 4. list_teams

List all teams you have access to.

**Example prompts:**
- "List all my teams"
- "Show me available teams"

**Parameters:**
- `cursor`: For pagination

### 5. list_team_members

List members of a specific team or all team members.

**Example prompts:**
- "List all members of the Sales team"
- "Show me who is on my teams"

**Parameters:**
- `cursor`: For pagination
- `team`: Filter by specific team name

### 6. create_webhook

Create a webhook for receiving meeting notifications.

**Example prompts:**
- "Create a webhook for my recordings at https://myapp.com/webhook"
- "Set up a webhook that includes transcripts and summaries"

**Parameters:**
- `destination_url`: Where to send webhook events (required)
- `triggered_for`: Array of recording types (required)
  - Options: `my_recordings`, `shared_external_recordings`, `my_shared_with_team_recordings`, `shared_team_recordings`
- `include_action_items`: Include action items (boolean)
- `include_crm_matches`: Include CRM matches (boolean)
- `include_summary`: Include summary (boolean)
- `include_transcript`: Include transcript (boolean)

**Note:** At least one `include_*` flag must be true.

### 7. delete_webhook

Delete a webhook by its ID.

**Example prompts:**
- "Delete webhook abc123"
- "Remove the webhook with ID abc123"

**Parameters:**
- `webhook_id`: The webhook ID (required)

## Available Resources

### 1. fathom://api/info

Get information about the Fathom API, available endpoints, and authentication.

**Example prompts:**
- "Show me info about the Fathom API"
- "What endpoints are available?"

### 2. fathom://api/rate-limits

Get information about API rate limits and best practices.

**Example prompts:**
- "What are the rate limits for Fathom API?"
- "How many requests can I make?"

## Example Workflows

### Workflow 1: Find and Summarize Recent Meetings

1. "List my meetings from the past 7 days with summaries"
2. Claude will call `list_meetings` with `created_after` parameter
3. Review the summaries directly in the response

### Workflow 2: Get Full Details of a Specific Meeting

1. "List my recent meetings"
2. Note the `recording_id` of interest
3. "Get the full transcript for recording 93339249"
4. "Get the summary for recording 93339249"

### Workflow 3: Set Up Meeting Notifications

1. "Create a webhook at https://myapp.com/fathom-webhook that includes transcripts and summaries for my recordings"
2. Claude will call `create_webhook` with appropriate parameters
3. Note the returned `webhook_id` and `secret` for signature verification

### Workflow 4: Team Analysis

1. "List all my teams"
2. "Show me members of the Sales team"
3. "List all meetings with the Sales team in the past month"

## Testing the Server

You can test the server directly with Python:

```python
import asyncio
import os
from server import make_request

async def test():
    # List meetings
    meetings = await make_request("GET", "/meetings", params={"limit": 5})
    print(f"Found {len(meetings['items'])} meetings")

    # Get a summary
    if meetings['items']:
        recording_id = meetings['items'][0]['recording_id']
        summary = await make_request("GET", f"/recordings/{recording_id}/summary")
        print(f"Summary: {summary}")

asyncio.run(test())
```

## Troubleshooting

### Server won't start

**Error:** "FATHOM_API_KEY environment variable is required"
**Solution:** Make sure the API key is set in your environment or `.env` file

### Rate Limit Errors

**Error:** "Rate limit exceeded. Reset in X seconds."
**Solution:** The API allows 60 requests per 60 seconds. Wait for the reset time or implement exponential backoff.

### Authentication Errors

**Error:** "Authentication failed. Please check your FATHOM_API_KEY."
**Solution:** Verify your API key is correct and hasn't been revoked. Get a new key from [Fathom Settings](https://app.fathom.video/settings/integrations).

### Resource Not Found

**Error:** "Resource not found."
**Solution:** Check that the recording ID or webhook ID exists and you have permission to access it.

## API Limitations

- **Rate Limit:** 60 requests per 60 seconds
- **Access Scope:** API keys can only access meetings you recorded or meetings shared with your team
- **Admin Keys:** Admin API keys do NOT automatically grant access to all users' meetings

## Support

For issues with:
- **This MCP server:** Check the README.md or open an issue on GitHub
- **Fathom API:** Visit [Fathom Developer Documentation](https://developers.fathom.ai) or contact Fathom support

## Additional Resources

- [Fathom API Quickstart](https://developers.fathom.ai/quickstart)
- [Fathom API Reference](https://developers.fathom.ai/api-overview)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://gofastmcp.com/)
