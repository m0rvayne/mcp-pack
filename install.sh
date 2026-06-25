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
USED_SCRIPT_NODE=false

# ─── Colors ───────────────────────────────────────────────────────────────────

if [ -t 1 ]; then
    GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'
    BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
else
    GREEN=''; RED=''; YELLOW=''; BOLD=''; DIM=''; RESET=''
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

# ─── Shell profile detection ─────────────────────────────────────────────────

detect_profile() {
    case "${SHELL:-}" in
        */zsh)  echo "${ZDOTDIR:-$HOME}/.zshrc" ;;
        */bash) echo "$HOME/.bash_profile" ;;
        *)      echo "$HOME/.profile" ;;
    esac
}

add_to_path() {
    local dir="$1"
    local profile
    profile="$(detect_profile)"

    if [ -f "$profile" ] && grep -qF "$dir" "$profile" 2>/dev/null; then
        return 0
    fi

    printf '\n# Added by MCP Pack installer\nexport PATH="%s:$PATH"\n' "$dir" >> "$profile"
}

# ─── Check if git actually works (not just Xcode CLT shim) ───────────────────

git_works() {
    command -v git >/dev/null 2>&1 || return 1
    # On fresh Mac, /usr/bin/git is a shim that triggers Xcode CLT dialog
    # Test if git actually works without triggering the dialog
    git --version >/dev/null 2>&1
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
    # Check both Spotlight and common paths
    if mdfind "kMDItemCFBundleIdentifier == 'com.anthropic.claude'" 2>/dev/null | grep -q . \
       || [ -d "/Applications/Claude.app" ]; then
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
    local tarball="$TMPDIR_INSTALL/node.tar.gz"
    curl -fsSL -o "$tarball" \
        "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-${node_arch}.tar.gz" \
        || err "Failed to download Node.js. Check your internet connection."

    rm -rf "$NODE_DIR"
    mkdir -p "$NODE_DIR"
    tar xzf "$tarball" -C "$NODE_DIR" --strip-components=1 \
        || err "Failed to extract Node.js."

    USED_SCRIPT_NODE=true
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

# Only add to PATH if we installed Node ourselves
if [ "$USED_SCRIPT_NODE" = true ]; then
    export PATH="$NODE_DIR/bin:$PATH"
    add_to_path "$NODE_DIR/bin"
fi

# ─── Install uv + Python (if needed) ─────────────────────────────────────────

if ! command -v uv >/dev/null 2>&1; then
    say "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh \
        || err "Failed to install uv. Check your internet connection."
    export PATH="$HOME/.local/bin:$PATH"
    info "uv installed"
else
    info "uv already installed"
fi

if ! uv python find 3.12 >/dev/null 2>&1; then
    say "Installing Python 3.12 via uv..."
    uv python install 3.12 \
        || err "Failed to install Python 3.12."
    info "Python 3.12 installed"
else
    info "Python 3.12 already available"
fi

# ─── Download connectors (BEFORE Claude CLI to avoid $INSTALL_DIR conflict) ──

say "Downloading MCP connectors..."

if git_works; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Updating existing installation..."
        git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
    else
        if [ -d "$INSTALL_DIR" ]; then
            # Preserve user data (OAuth tokens etc)
            if [ -d "$INSTALL_DIR/connectors" ]; then
                mv "$INSTALL_DIR/connectors" "$TMPDIR_INSTALL/connectors_backup" 2>/dev/null || true
            fi
            rm -rf "$INSTALL_DIR"
        fi
        git clone --depth 1 "$REPO.git" "$INSTALL_DIR" \
            || err "Failed to download connectors. Check your internet connection."
        # Restore user data
        if [ -d "$TMPDIR_INSTALL/connectors_backup" ]; then
            find "$TMPDIR_INSTALL/connectors_backup" \( -name "token.json" -o -name "credentials.json" -o -name ".env" \) 2>/dev/null | while read -r f; do
                local rel="${f#$TMPDIR_INSTALL/connectors_backup/}"
                local dest="$INSTALL_DIR/connectors/$rel"
                mkdir -p "$(dirname "$dest")"
                cp "$f" "$dest"
            done
        fi
    fi
else
    info "git not available, downloading archive..."
    local tarball="$TMPDIR_INSTALL/mcp-pack.tar.gz"
    curl -fsSL -o "$tarball" "$REPO/archive/refs/heads/main.tar.gz" \
        || err "Failed to download connectors. Check your internet connection."

    if [ -d "$INSTALL_DIR" ]; then
        if [ -d "$INSTALL_DIR/connectors" ]; then
            mv "$INSTALL_DIR/connectors" "$TMPDIR_INSTALL/connectors_backup" 2>/dev/null || true
        fi
        rm -rf "$INSTALL_DIR"
    fi

    tar xzf "$tarball" -C "$(dirname "$INSTALL_DIR")" \
        || err "Failed to extract connectors."
    mv "$(dirname "$INSTALL_DIR")/mcp-pack-main" "$INSTALL_DIR"
fi

info "Connectors at $INSTALL_DIR"

# ─── Install Claude CLI (AFTER connectors so $INSTALL_DIR exists) ─────────────

say "Installing Claude CLI..."
if command -v claude >/dev/null 2>&1; then
    info "Claude CLI already installed"
else
    if [ "$USED_SCRIPT_NODE" = true ]; then
        # Script-installed Node: global prefix is ~/.nodejs (user-writable)
        "$NPM_BIN" install -g @anthropic-ai/claude-code \
            || err "Failed to install Claude CLI"
    else
        # System Node: try global, fall back to local in a SAFE location
        "$NPM_BIN" install -g @anthropic-ai/claude-code 2>/dev/null || {
            warn "Global npm install failed (may need sudo). Installing locally..."
            local cli_dir="$HOME/.claude-cli"
            mkdir -p "$cli_dir"
            cd "$cli_dir"
            "$NPM_BIN" init -y >/dev/null 2>&1
            "$NPM_BIN" install @anthropic-ai/claude-code \
                || err "Failed to install Claude CLI"
            export PATH="$cli_dir/node_modules/.bin:$PATH"
            add_to_path "$cli_dir/node_modules/.bin"
        }
    fi
    info "Claude CLI installed"
fi

# ─── Install dependencies ────────────────────────────────────────────────────

say "Installing connector dependencies..."

# Trello (Python)
info "Trello..."
cd "$INSTALL_DIR/connectors/MCP_Trello"
uv venv --python 3.12 .venv 2>&1 | tail -1 || err "Failed to create Trello venv"
uv pip install -r requirements.txt -p .venv 2>&1 | tail -1 || warn "Trello dependencies may be incomplete"

# Fathom (Python)
info "Fathom..."
cd "$INSTALL_DIR/connectors/MCP_Fathom"
uv venv --python 3.12 .venv 2>&1 | tail -1 || err "Failed to create Fathom venv"
uv pip install -r requirements.txt -p .venv 2>&1 | tail -1 || warn "Fathom dependencies may be incomplete"

# Google Workspace (Python)
info "Google Workspace..."
cd "$INSTALL_DIR/connectors/MCP_Google_Workspace"
uv venv --python 3.12 .venv 2>&1 | tail -1 || err "Failed to create Google Workspace venv"
if [ -f requirements.txt ]; then
    uv pip install -r requirements.txt -p .venv 2>&1 | tail -1 || warn "Google Workspace dependencies may be incomplete"
fi

# Telegram (Node.js)
info "Telegram..."
cd "$INSTALL_DIR/connectors/MCP_Telegram"
"$NPM_BIN" install 2>&1 | tail -3 || warn "Telegram dependencies may be incomplete"

# ─── Configure Claude Desktop (with placeholders) ────────────────────────────

say "Configuring Claude Desktop..."

if [ -f "$CLAUDE_CONFIG" ]; then
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    info "Backed up existing config"
fi

UV_BIN="$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")"

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

if [ ! -s "$CLAUDE_CONFIG" ]; then
    echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
fi

# Use uv's Python (not /usr/bin/python3 which may trigger Xcode CLT dialog)
UV_PYTHON="$(uv python find 3.12 2>/dev/null || echo "/usr/bin/python3")"

"$UV_PYTHON" -c "
import json, sys

config_path = sys.argv[1]
new_servers = json.loads(sys.argv[2])

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    config = {'mcpServers': {}}

# Ensure config is a dict with mcpServers
if not isinstance(config, dict):
    config = {'mcpServers': {}}
if 'mcpServers' not in config or not isinstance(config.get('mcpServers'), dict):
    config['mcpServers'] = {}

existing = config['mcpServers']
added = 0
for key, val in new_servers.items():
    if key not in existing:
        existing[key] = val
        added += 1

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f'  Added {added} connector(s)')
" "$CLAUDE_CONFIG" "$SERVERS_JSON" || err "Failed to update Claude Desktop config"

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
CLAUDEMD

# ─── Done ─────────────────────────────────────────────────────────────────────

printf "\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${GREEN}${BOLD}  ✓ MCP Pack installed!${RESET}\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "\n"
printf "  ${BOLD}566 tools installed:${RESET}\n"
printf "    • Trello           — 171 tools\n"
printf "    • Google Workspace — 167 tools\n"
printf "    • Telegram         — 218 tools\n"
printf "    • Fathom           — 10 tools\n"
printf "\n"
printf "  ${BOLD}Next steps:${RESET}\n"
printf "\n"
printf "    ${BOLD}1.${RESET} Configure your API keys. Run:\n"
printf "\n"
printf "       ${BOLD}cd ~/.mcp-pack && claude${RESET}\n"
printf "\n"
printf "    ${BOLD}2.${RESET} Tell Claude your keys:\n"
printf "\n"
printf "       ${DIM}\"Here are my API keys:${RESET}\n"
printf "       ${DIM} Trello: key=xxx, token=yyy${RESET}\n"
printf "       ${DIM} Fathom: key=zzz, secret=www${RESET}\n"
printf "       ${DIM} Telegram: token=ttt${RESET}\n"
printf "       ${DIM} Configure them in Claude Desktop.\"${RESET}\n"
printf "\n"
printf "    ${BOLD}3.${RESET} Restart Claude Desktop — done!\n"
printf "\n"
printf "  ${DIM}Google Workspace: cd ~/.mcp-pack/connectors/MCP_Google_Workspace && python3 setup_auth.py${RESET}\n"
printf "  ${DIM}by m0rvayne · github.com/m0rvayne/mcp-pack${RESET}\n"
printf "\n"

}

main "$@"
