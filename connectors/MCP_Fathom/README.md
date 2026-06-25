# Fathom AI MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0-green.svg)](https://gofastmcp.com/)

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for interacting with the [Fathom AI API](https://developers.fathom.ai). This server provides tools for accessing meeting recordings, summaries, transcripts, teams, and webhooks.

## Quick Start

```bash
git clone https://github.com/Dot-Fun/fathom-mcp.git
cd fathom-mcp
uv pip install fastmcp httpx pydantic
export FATHOM_API_KEY="your_api_key_here"
fastmcp run server.py
```

## Features

### Tools

- **list_meetings**: List meetings with advanced filtering (by participants, date ranges, teams) and optional inclusion of transcripts, summaries, action items, and CRM matches
- **get_summary**: Retrieve meeting summaries (supports async delivery)
- **get_transcript**: Retrieve meeting transcripts with speaker information and timestamps (supports async delivery)
- **list_teams**: List all accessible teams
- **list_team_members**: List team members with optional team filtering
- **create_webhook**: Create webhooks for meeting notifications with customizable triggers and content inclusion
- **delete_webhook**: Delete webhooks by ID

### Resources

- **fathom://api/info**: API information and available endpoints
- **fathom://api/rate-limits**: Rate limiting information and best practices

## Installation

1. Clone this repository or copy the files to your local machine

2. Install dependencies using uv (recommended) or pip:

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

3. Set up your Fathom API key:

Create a `.env` file in the project root:

```bash
FATHOM_API_KEY=your_api_key_here
```

The server auto-loads `.env` for local usage.

Get your API key from the [Fathom settings page](https://app.fathom.video/settings/integrations).

## Usage

### Running the Server

#### Local Development (stdio)

```bash
# Using fastmcp CLI
fastmcp run server.py

# Or directly with Python
python server.py
```

#### HTTP Server

```python
# Modify server.py to run as HTTP server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

### Integrating with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

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

### Integrating with Codex (alternative)

Add this block to your Codex config (`~/.codex/config.toml`):

```toml
[mcp_servers.fathom]
command = "uv"
args = ["--directory", "/path/to/fathom-mcp", "run", "fastmcp", "run", "server.py"]
```

Then restart Codex (or reload MCP servers) and verify:

```bash
codex mcp list
```

## API Reference

### Authentication

All requests require the `FATHOM_API_KEY` environment variable. API keys are user-level and can access:
- Meetings recorded by the user
- Meetings shared to the user's team

### Rate Limits

- **Global limit**: 60 API calls per 60-second window
- Rate-limited requests return HTTP 429
- Monitor rate limit headers: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`

### Tool Examples

#### List Recent Meetings

```python
# List meetings with transcripts from the last week
result = await list_meetings(
    created_after="2024-01-01T00:00:00Z",
    include_transcript=True,
    include_summary=True
)
```

#### Get Meeting Summary

```python
# Get summary for a specific recording
summary = await get_summary(recording_id=123456789)
```

#### Create a Webhook

```python
# Create webhook for team recordings with all content
webhook = await create_webhook(
    destination_url="https://your-app.com/webhook",
    triggered_for=["my_recordings", "shared_team_recordings"],
    include_transcript=True,
    include_summary=True,
    include_action_items=True,
    include_crm_matches=True
)
# Returns webhook ID, URL, and secret for signature verification
```

#### Filter Meetings by Participants

```python
# Find meetings with specific participants
meetings = await list_meetings(
    calendar_invitees=["alice@acme.com", "bob@acme.com"],
    include_action_items=True
)
```

#### List Team Members

```python
# Get all members of the Sales team
members = await list_team_members(team="Sales")
```

## Error Handling

The server handles common API errors:

- **401 Unauthorized**: Invalid or missing API key
- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Resource doesn't exist
- **429 Rate Limited**: Too many requests (includes reset time)

## Development

### Project Structure

```
fathom-mcp/
├── server.py           # Main MCP server implementation
├── pyproject.toml      # Project configuration and dependencies
├── Dockerfile          # Container configuration for deployment
├── package.json        # Package metadata
├── README.md           # This file
├── .env                # Environment variables (API key)
└── .dockerignore       # Docker build exclusions
```

### Code Quality

The project uses Ruff for linting and formatting:

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Testing

The server has been tested with real Fathom API data. See [TEST_RESULTS.md](./TEST_RESULTS.md) for detailed test results.

To test manually:

```bash
# Set your API key
export FATHOM_API_KEY="your_api_key_here"

# Test server loads
python -c "from server import mcp; print('✓ Server ready')"

# Test API connectivity
python -c "
import asyncio
from server import make_request
asyncio.run(make_request('GET', '/meetings'))
"
```

## API Documentation

For complete API documentation, visit:
- [Fathom API Quickstart](https://developers.fathom.ai/quickstart)
- [Fathom API Reference](https://developers.fathom.ai/api-overview)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- **Issues**: [GitHub Issues](https://github.com/Dot-Fun/fathom-mcp/issues)
- **Fathom API**: [Fathom Support](https://fathom.video/support)
- **MCP Protocol**: [MCP Documentation](https://modelcontextprotocol.io)

## Acknowledgments

Built with [FastMCP](https://gofastmcp.com/) - The fast, Pythonic way to build MCP servers.

## Repository

**GitHub**: [https://github.com/Dot-Fun/fathom-mcp](https://github.com/Dot-Fun/fathom-mcp)
