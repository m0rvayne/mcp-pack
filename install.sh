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

# Ensure Python 3.12
if ! uv python find 3.12 >/dev/null 2>&1; then
    say "Installing Python 3.12 via uv..."
    uv python install 3.12 2>/dev/null
    info "Python 3.12 installed"
else
    info "Python 3.12 already available"
fi

# ─── Download connectors ─────────────────────────────────────────────────────

say "Downloading MCP connectors..."

if command -v git >/dev/null 2>&1; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Updating existing installation..."
        git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
    else
        git clone --depth 1 "$REPO.git" "$INSTALL_DIR" 2>/dev/null
    fi
else
    # Fallback: download tarball
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
TRELLO_PYTHON="$INSTALL_DIR/connectors/MCP_Trello/.venv/bin/python3"

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

# ─── Collect API keys ────────────────────────────────────────────────────────

say "Configuring API keys..."
printf "\n"
printf "  ${DIM}Each connector needs API keys to work.${RESET}\n"
printf "  ${DIM}Press Enter to skip — you can configure later.${RESET}\n"
printf "\n"

# Trello
printf "  ${BOLD}Trello${RESET}\n"
printf "    API Key (from https://trello.com/power-ups/admin): "
read -r TRELLO_API_KEY
printf "    API Token: "
read -r TRELLO_API_TOKEN

# Fathom
printf "\n  ${BOLD}Fathom${RESET}\n"
printf "    API Key (from https://fathom.video/settings/api): "
read -r FATHOM_API_KEY
printf "    Webhook Secret: "
read -r FATHOM_WEBHOOK_SECRET

# Google Workspace
printf "\n  ${BOLD}Google Workspace${RESET}\n"
printf "    ${DIM}Requires OAuth setup. Run after install:${RESET}\n"
printf "    ${DIM}cd $INSTALL_DIR/connectors/MCP_Google_Workspace && python3 setup_auth.py${RESET}\n"

# Telegram
printf "\n  ${BOLD}Telegram${RESET}\n"
printf "    Bot Token (from @BotFather): "
read -r TELEGRAM_BOT_TOKEN

printf "\n"

# ─── Build Claude Desktop config ─────────────────────────────────────────────

say "Configuring Claude Desktop..."

# Backup existing config
if [ -f "$CLAUDE_CONFIG" ]; then
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    info "Backed up existing config"
fi

# Build servers JSON
UV_BIN="$HOME/.local/bin/uv"
SERVERS_JSON=$(cat <<JSONEOF
{
    "trello": {
        "command": "$INSTALL_DIR/connectors/MCP_Trello/.venv/bin/python3",
        "args": ["$INSTALL_DIR/connectors/MCP_Trello/server.py"],
        "env": {
            "TRELLO_API_KEY": "${TRELLO_API_KEY:-CONFIGURE_ME}",
            "TRELLO_API_TOKEN": "${TRELLO_API_TOKEN:-CONFIGURE_ME}"
        }
    },
    "fathom": {
        "command": "$UV_BIN",
        "args": ["--directory", "$INSTALL_DIR/connectors/MCP_Fathom", "run", "fastmcp", "run", "server.py"],
        "env": {
            "FATHOM_API_KEY": "${FATHOM_API_KEY:-CONFIGURE_ME}",
            "FATHOM_WEBHOOK_SECRET": "${FATHOM_WEBHOOK_SECRET:-CONFIGURE_ME}"
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
            "TELEGRAM_BOT_TOKEN": "${TELEGRAM_BOT_TOKEN:-CONFIGURE_ME}"
        }
    }
}
JSONEOF
)

# Merge into Claude Desktop config
if [ ! -s "$CLAUDE_CONFIG" ]; then
    echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
fi

# Use python3 for JSON merge (always available on macOS)
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

# ─── Done ─────────────────────────────────────────────────────────────────────

printf "\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${GREEN}${BOLD}  ✓ MCP Pack installed successfully!${RESET}\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "\n"
printf "  ${BOLD}Connectors installed:${RESET}\n"
printf "    • Trello        — 171 tools\n"
printf "    • Google Workspace — 167 tools (Calendar, Drive, Docs, Sheets)\n"
printf "    • Telegram      — 218 tools\n"
printf "    • Fathom        — 10 tools\n"
printf "    ${DIM}Total: 566 tools${RESET}\n"
printf "\n"
printf "  ${BOLD}Next steps:${RESET}\n"
printf "    1. Restart Claude Desktop\n"
printf "    2. Start chatting — your connectors are ready!\n"
printf "\n"

if [ "${TRELLO_API_KEY:-}" = "" ] || [ "${FATHOM_API_KEY:-}" = "" ] || [ "${TELEGRAM_BOT_TOKEN:-}" = "" ]; then
    printf "  ${YELLOW}Some API keys were skipped.${RESET}\n"
    printf "  Edit: ${DIM}~/Library/Application Support/Claude/claude_desktop_config.json${RESET}\n"
    printf "  Replace ${DIM}CONFIGURE_ME${RESET} with your actual keys.\n"
    printf "\n"
fi

printf "  ${DIM}Google Workspace requires OAuth setup:${RESET}\n"
printf "  ${DIM}cd $INSTALL_DIR/connectors/MCP_Google_Workspace && python3 setup_auth.py${RESET}\n"
printf "\n"
printf "  ${DIM}Installed to: $INSTALL_DIR${RESET}\n"
printf "  ${DIM}by m0rvayne · github.com/m0rvayne/mcp-pack${RESET}\n"
printf "\n"

}

main "$@"
