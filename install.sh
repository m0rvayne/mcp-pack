#!/bin/bash
# MCP Pack Installer — 566 tools across 4 connectors
# One command: curl -fsSL https://raw.githubusercontent.com/m0rvayne/mcp-pack/main/install.sh | bash

main() {
set -euo pipefail

REPO="https://github.com/m0rvayne/mcp-pack"
INSTALL_DIR="$HOME/.mcp-pack"
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
NODE_VERSION="20.18.3"
NODE_DIR="$HOME/.nodejs"

# ─── Colors ───────────────────────────────────────────────────────────────────

if [ -t 1 ]; then
    GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'
    BLUE='\033[1;34m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
else
    GREEN=''; RED=''; YELLOW=''; BLUE=''; BOLD=''; DIM=''; RESET=''
fi

say()  { printf "${GREEN}==>${RESET}${BOLD} %s${RESET}\n" "$1"; }
info() { printf "    %s\n" "$1"; }
warn() { printf "${YELLOW}warn:${RESET} %s\n" "$1" >&2; }
err()  { printf "${RED}error:${RESET} %s\n" "$1" >&2; exit 1; }

# ─── Cleanup ──────────────────────────────────────────────────────────────────

TMPDIR_INSTALL="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_INSTALL"' EXIT

# ─── Banner ───────────────────────────────────────────────────────────────────

printf "\n"
printf "${BOLD}MCP Pack Installer${RESET}\n"
printf "${DIM}566 tools across 4 connectors for Claude Desktop${RESET}\n"
printf "${DIM}Trello (171) · Google Workspace (167) · Telegram (218) · Fathom (10)${RESET}\n"
printf "\n"

# ─── Detect Architecture ─────────────────────────────────────────────────────

detect_arch() {
    local arch
    arch="$(uname -m)"
    if [ "$arch" = "x86_64" ]; then
        if sysctl hw.optional.arm64 2>/dev/null | grep -q ': 1'; then
            arch="arm64"
        fi
    fi
    echo "$arch"
}

# ─── Check macOS ──────────────────────────────────────────────────────────────

if [ "$(uname)" != "Darwin" ]; then
    err "This installer only works on macOS"
fi

say "Checking system..."
ARCH="$(detect_arch)"
info "macOS $(sw_vers -productVersion) ($ARCH)"

# ─── Check Claude Desktop ────────────────────────────────────────────────────

if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    if mdfind "kMDItemCFBundleIdentifier == 'com.anthropic.claude'" 2>/dev/null | grep -q .; then
        mkdir -p "$CLAUDE_CONFIG_DIR"
    else
        err "Claude Desktop not found. Install it from https://claude.ai/download"
    fi
fi

info "Claude Desktop detected"

# ─── Install Node.js (if needed) ─────────────────────────────────────────────

install_node() {
    local node_arch
    if [ "$ARCH" = "arm64" ]; then
        node_arch="arm64"
    else
        node_arch="x64"
    fi

    say "Installing Node.js $NODE_VERSION..."
    mkdir -p "$NODE_DIR"
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-${node_arch}.tar.gz" \
        | tar xz -C "$NODE_DIR" --strip-components=1
    info "Installed to $NODE_DIR"
}

NODE_BIN=""
NPM_BIN=""

if command -v node >/dev/null 2>&1; then
    NODE_MAJOR=$(node --version | sed 's/v\([0-9]*\).*/\1/')
    if [ "$NODE_MAJOR" -ge 18 ]; then
        info "Node.js $(node --version) already installed"
        NODE_BIN="$(command -v node)"
        NPM_BIN="$(command -v npm)"
    else
        install_node
        NODE_BIN="$NODE_DIR/bin/node"
        NPM_BIN="$NODE_DIR/bin/npm"
    fi
else
    install_node
    NODE_BIN="$NODE_DIR/bin/node"
    NPM_BIN="$NODE_DIR/bin/npm"
fi

export PATH="$NODE_DIR/bin:$PATH"

# ─── Install uv + Python (if needed) ─────────────────────────────────────────

if ! command -v uv >/dev/null 2>&1; then
    say "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
    export PATH="$HOME/.local/bin:$PATH"
    info "uv installed"
else
    info "uv already installed"
fi

if ! uv python find 3.12 >/dev/null 2>&1; then
    say "Installing Python 3.12 via uv..."
    uv python install 3.12 2>/dev/null
    info "Python 3.12 installed"
else
    info "Python 3.12 already available"
fi

# ─── Install Claude CLI ──────────────────────────────────────────────────────

say "Installing Claude CLI..."
if command -v claude >/dev/null 2>&1; then
    info "Claude CLI already installed ($(claude --version 2>/dev/null || echo 'unknown version'))"
else
    "$NPM_BIN" install -g @anthropic-ai/claude-code 2>/dev/null || \
        npm install -g @anthropic-ai/claude-code 2>/dev/null || \
        { warn "Could not install globally, using npx"; }
    info "Claude CLI installed"
fi

# ─── Download connectors ─────────────────────────────────────────────────────

say "Downloading MCP connectors..."

if command -v git >/dev/null 2>&1; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Updating existing installation..."
        git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
    else
        rm -rf "$INSTALL_DIR"
        git clone --depth 1 "$REPO.git" "$INSTALL_DIR" 2>/dev/null
    fi
else
    info "git not found, downloading archive..."
    curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" \
        | tar xz -C "$(dirname "$INSTALL_DIR")"
    rm -rf "$INSTALL_DIR"
    mv "$(dirname "$INSTALL_DIR")/mcp-pack-main" "$INSTALL_DIR"
fi

info "Connectors downloaded to $INSTALL_DIR"

# ─── Install dependencies ────────────────────────────────────────────────────

say "Installing connector dependencies..."

# Trello (Python)
info "Trello..."
cd "$INSTALL_DIR/connectors/MCP_Trello"
uv venv --python 3.12 .venv 2>/dev/null
uv pip install -r requirements.txt --quiet 2>/dev/null

# Fathom (Python)
info "Fathom..."
cd "$INSTALL_DIR/connectors/MCP_Fathom"
uv venv --python 3.12 .venv 2>/dev/null
uv pip install -r requirements.txt --quiet 2>/dev/null

# Google Workspace (Python)
info "Google Workspace..."
cd "$INSTALL_DIR/connectors/MCP_Google_Workspace"
uv venv --python 3.12 .venv 2>/dev/null
if [ -f requirements.txt ]; then
    uv pip install -r requirements.txt --quiet 2>/dev/null
fi

# Telegram (Node.js)
info "Telegram..."
cd "$INSTALL_DIR/connectors/MCP_Telegram"
"$NPM_BIN" install --silent 2>/dev/null || "$NPM_BIN" install 2>/dev/null

# ─── Configure Claude Desktop (with placeholders) ────────────────────────────

say "Configuring Claude Desktop..."

# Backup existing config
if [ -f "$CLAUDE_CONFIG" ]; then
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    info "Backed up existing config"
fi

UV_BIN="$HOME/.local/bin/uv"

SERVERS_JSON=$(cat <<JSONEOF
{
    "trello": {
        "command": "$INSTALL_DIR/connectors/MCP_Trello/.venv/bin/python3",
        "args": ["$INSTALL_DIR/connectors/MCP_Trello/server.py"],
        "env": {
            "TRELLO_API_KEY": "CONFIGURE_ME",
            "TRELLO_API_TOKEN": "CONFIGURE_ME"
        }
    },
    "fathom": {
        "command": "$UV_BIN",
        "args": ["--directory", "$INSTALL_DIR/connectors/MCP_Fathom", "run", "fastmcp", "run", "server.py"],
        "env": {
            "FATHOM_API_KEY": "CONFIGURE_ME",
            "FATHOM_WEBHOOK_SECRET": "CONFIGURE_ME"
        }
    },
    "google-workspace": {
        "command": "$INSTALL_DIR/connectors/MCP_Google_Workspace/.venv/bin/python3",
        "args": ["$INSTALL_DIR/connectors/MCP_Google_Workspace/server.py"]
    },
    "telegram": {
        "command": "$NODE_BIN",
        "args": ["$INSTALL_DIR/connectors/MCP_Telegram/build/index.js"],
        "env": {
            "TELEGRAM_BOT_TOKEN": "CONFIGURE_ME"
        }
    }
}
JSONEOF
)

# Merge into Claude Desktop config
if [ ! -s "$CLAUDE_CONFIG" ]; then
    echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
fi

/usr/bin/python3 -c "
import json, sys

config_path = sys.argv[1]
new_servers = json.loads(sys.argv[2])

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    config = {'mcpServers': {}}

existing = config.setdefault('mcpServers', {})
added = 0
for key, val in new_servers.items():
    if key not in existing:
        existing[key] = val
        added += 1
    else:
        print(f'  skip: \"{key}\" already configured', file=sys.stderr)

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f'  Added {added} connector(s) to Claude Desktop config')
" "$CLAUDE_CONFIG" "$SERVERS_JSON"

# ─── Create helper script for Claude CLI to configure keys ────────────────────

HELPER_SCRIPT="$INSTALL_DIR/configure-keys.sh"
cat > "$HELPER_SCRIPT" << 'HELPEREOF'
#!/bin/bash
# Helper: configure API keys in Claude Desktop config
# Usage: called by Claude CLI when user provides keys

CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <connector> <key>=<value> [<key>=<value> ...]"
    echo "Connectors: trello, fathom, telegram"
    exit 1
fi

CONNECTOR="$1"
shift

/usr/bin/python3 -c "
import json, sys

config_path = '$CONFIG'
connector = sys.argv[1]
pairs = sys.argv[2:]

with open(config_path, 'r') as f:
    config = json.load(f)

server = config.get('mcpServers', {}).get(connector)
if not server:
    print(f'Connector \"{connector}\" not found in config')
    sys.exit(1)

env = server.setdefault('env', {})
for pair in pairs:
    key, _, value = pair.partition('=')
    env[key] = value
    print(f'  Set {key} for {connector}')

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f'Keys configured for {connector}. Restart Claude Desktop.')
" "$CONNECTOR" "$@"
HELPEREOF
chmod +x "$HELPER_SCRIPT"

# ─── Create CLAUDE.md for Claude CLI context ──────────────────────────────────

cat > "$INSTALL_DIR/CLAUDE.md" << 'CLAUDEMD'
# MCP Pack — Key Configuration

When the user provides API keys for their MCP connectors, update the Claude Desktop config file.

## Config file location
`~/Library/Application Support/Claude/claude_desktop_config.json`

## How to configure keys

When the user says something like "here are my keys" or "configure Trello with key XXX":

1. Read the config file
2. Find the connector in `mcpServers`
3. Replace `CONFIGURE_ME` values in the `env` section with the actual keys
4. Write back the file
5. Tell the user to restart Claude Desktop

## Connectors and their keys

### Trello
- `TRELLO_API_KEY` — from https://trello.com/power-ups/admin
- `TRELLO_API_TOKEN` — from Trello authorization

### Fathom
- `FATHOM_API_KEY` — from https://fathom.video/settings/api
- `FATHOM_WEBHOOK_SECRET` — from Fathom webhook settings

### Telegram
- `TELEGRAM_BOT_TOKEN` — from @BotFather on Telegram

### Google Workspace
No API keys needed in config — requires OAuth setup:
```
cd ~/.mcp-pack/connectors/MCP_Google_Workspace && python3 setup_auth.py
```

## Example

User: "My Trello API key is abc123 and token is xyz789"

You should:
1. Read ~/Library/Application Support/Claude/claude_desktop_config.json
2. Set mcpServers.trello.env.TRELLO_API_KEY = "abc123"
3. Set mcpServers.trello.env.TRELLO_API_TOKEN = "xyz789"
4. Save the file
5. Tell user: "Keys configured! Restart Claude Desktop."

## Helper script

You can also use the helper:
```bash
~/.mcp-pack/configure-keys.sh trello TRELLO_API_KEY=abc123 TRELLO_API_TOKEN=xyz789
~/.mcp-pack/configure-keys.sh fathom FATHOM_API_KEY=xxx FATHOM_WEBHOOK_SECRET=yyy
~/.mcp-pack/configure-keys.sh telegram TELEGRAM_BOT_TOKEN=zzz
```
CLAUDEMD

# ─── Done ─────────────────────────────────────────────────────────────────────

printf "\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${GREEN}${BOLD}  ✓ MCP Pack installed successfully!${RESET}\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "\n"
printf "  ${BOLD}Installed:${RESET}\n"
printf "    • Trello           — 171 tools\n"
printf "    • Google Workspace — 167 tools (Calendar, Drive, Docs, Sheets)\n"
printf "    • Telegram         — 218 tools\n"
printf "    • Fathom           — 10 tools\n"
printf "    ${DIM}Total: 566 tools${RESET}\n"
printf "\n"
printf "  ${BOLD}Next steps:${RESET}\n"
printf "\n"
printf "    ${BOLD}1.${RESET} Open terminal and run:\n"
printf "\n"
printf "       ${BLUE}cd ~/.mcp-pack && claude${RESET}\n"
printf "\n"
printf "    ${BOLD}2.${RESET} Tell Claude your API keys:\n"
printf "\n"
printf "       ${DIM}\"Here are my keys:${RESET}\n"
printf "       ${DIM} Trello API key: xxx, token: yyy${RESET}\n"
printf "       ${DIM} Fathom API key: zzz, webhook secret: www${RESET}\n"
printf "       ${DIM} Telegram bot token: ttt${RESET}\n"
printf "       ${DIM} Please configure them in Claude Desktop.\"${RESET}\n"
printf "\n"
printf "    ${BOLD}3.${RESET} Restart Claude Desktop\n"
printf "\n"
printf "    ${BOLD}4.${RESET} Done! Start chatting with your 566 tools.\n"
printf "\n"
printf "  ${DIM}Google Workspace requires additional OAuth setup:${RESET}\n"
printf "  ${DIM}cd ~/.mcp-pack/connectors/MCP_Google_Workspace && python3 setup_auth.py${RESET}\n"
printf "\n"
printf "  ${DIM}Installed to: $INSTALL_DIR${RESET}\n"
printf "  ${DIM}by m0rvayne · github.com/m0rvayne/mcp-pack${RESET}\n"
printf "\n"

}

main "$@"
