# MCP Pack

**566 MCP tools for Claude Desktop — install in one command.**

Trello (171 tools) · Google Workspace (167 tools) · Telegram (218 tools) · Fathom (10 tools)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/m0rvayne/mcp-pack/main/install.sh | bash
```

That's it. The installer will:

1. Install Node.js and Python if needed (no Homebrew, no sudo)
2. Download all 4 connectors
3. Install dependencies
4. Ask for your API keys
5. Configure Claude Desktop automatically
6. You restart Claude Desktop — done

## What's included

| Connector | Tools | What it does |
|-----------|-------|-------------|
| **Trello** | 171 | Boards, lists, cards, labels, checklists, members, search |
| **Google Workspace** | 167 | Calendar, Drive, Docs, Sheets |
| **Telegram** | 218 | Messages, chats, media, stickers, payments, forums, bots |
| **Fathom** | 10 | Meeting recordings, transcripts, summaries, team management |

## API Keys

Each connector needs its own API key:

- **Trello** — [trello.com/power-ups/admin](https://trello.com/power-ups/admin)
- **Fathom** — [fathom.video/settings/api](https://fathom.video/settings/api)
- **Telegram** — [@BotFather](https://t.me/BotFather) on Telegram
- **Google Workspace** — Requires OAuth setup (instructions shown after install)

## Requirements

- macOS 13+ (Ventura or later)
- Claude Desktop ([download](https://claude.ai/download))

Node.js and Python are installed automatically if not present.

## Uninstall

```bash
rm -rf ~/.mcp-pack ~/.nodejs
```

Then remove the connector entries from `~/Library/Application Support/Claude/claude_desktop_config.json`.

## License

MIT

---

by [m0rvayne](https://github.com/m0rvayne)
