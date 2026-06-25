#!/bin/bash
# MCP Pack Installer — 566 tools across 4 connectors
# curl -fsSL https://raw.githubusercontent.com/m0rvayne/mcp-pack/main/install.sh | bash
#
# Patterns stolen from: nvm, Volta, fnm, n, uv, rustup

{ # ensure entire script is downloaded before execution (nvm pattern)

set -euo pipefail

REPO="https://github.com/m0rvayne/mcp-pack"
INSTALL_DIR="$HOME/.mcp-pack"
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
NODE_VERSION="20.18.3"
NODE_DIR="$HOME/.nodejs"
MAX_BACKUPS=3
USED_SCRIPT_NODE=false

# ═══════════════════════════════════════════════════════════════════════════════
# Output helpers (Volta pattern)
# ═══════════════════════════════════════════════════════════════════════════════

if [ -t 1 ]; then
    GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'
    BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
else
    GREEN=''; RED=''; YELLOW=''; BOLD=''; DIM=''; RESET=''
fi

say()  { command printf "${GREEN}==>${RESET}${BOLD} %s${RESET}\n" "$1"; }
info() { command printf "    %s\n" "$1"; }
warn() { command printf "${YELLOW}warn:${RESET} %s\n" "$1" 1>&2; }
err()  { command printf "${RED}error:${RESET} %s\n" "$1" 1>&2; exit 1; }

# ═══════════════════════════════════════════════════════════════════════════════
# Cleanup
# ═══════════════════════════════════════════════════════════════════════════════

TMPDIR_INSTALL="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_INSTALL"' EXIT

# ═══════════════════════════════════════════════════════════════════════════════
# Banner
# ═══════════════════════════════════════════════════════════════════════════════

printf "\n"
printf "${BOLD}MCP Pack Installer${RESET}\n"
printf "${DIM}566 tools · Trello (171) · Google Workspace (167) · Telegram (218) · Fathom (10)${RESET}\n"
printf "\n"

# ═══════════════════════════════════════════════════════════════════════════════
# Architecture detection (n pattern — handles Rosetta)
# ═══════════════════════════════════════════════════════════════════════════════

detect_arch() {
    case "$(uname -m)" in
        x86_64)        echo "x64" ;;
        arm64|aarch64) echo "arm64" ;;
        *)             err "Unsupported architecture: $(uname -m)" ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════════
# Shell profile detection (nvm pattern — cascade with fallback)
# ═══════════════════════════════════════════════════════════════════════════════

detect_profile() {
    if [ -n "${PROFILE-}" ] && [ -f "$PROFILE" ]; then
        echo "$PROFILE"
        return
    fi
    case "$(basename "${SHELL:-}")" in
        zsh)
            for f in "${ZDOTDIR:-$HOME}/.zshrc" "${ZDOTDIR:-$HOME}/.zprofile"; do
                [ -f "$f" ] && echo "$f" && return
            done
            # Create .zshrc if nothing exists (macOS default shell is zsh)
            echo "${ZDOTDIR:-$HOME}/.zshrc"
            ;;
        bash)
            for f in "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
                [ -f "$f" ] && echo "$f" && return
            done
            echo "$HOME/.bash_profile"
            ;;
        fish)
            echo "${XDG_CONFIG_HOME:-$HOME/.config}/fish/conf.d/mcp-pack.fish"
            ;;
        *)
            for f in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
                [ -f "$f" ] && echo "$f" && return
            done
            echo "$HOME/.profile"
            ;;
    esac
}

# Idempotent PATH addition (nvm + fnm guard pattern)
add_to_profile() {
    local dir="$1"
    local profile
    profile="$(detect_profile)"

    # Already on PATH — skip
    case ":${PATH}:" in
        *":${dir}:"*) return 0 ;;
    esac

    # Already in profile file — skip
    if [ -f "$profile" ] && grep -qF "$dir" "$profile" 2>/dev/null; then
        return 0
    fi

    # Add with guard (fnm pattern — harmless if dir doesn't exist)
    printf '\n# MCP Pack\nif [ -d "%s" ]; then export PATH="%s:$PATH"; fi\n' "$dir" "$dir" >> "$profile"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Git detection (nvm pattern — detects Xcode CLT shim)
# ═══════════════════════════════════════════════════════════════════════════════

git_is_available() {
    command -v git >/dev/null 2>&1 || return 1
    # On fresh macOS, /usr/bin/git is a shim that triggers Xcode CLT install dialog
    # nvm pattern: check if xcode-select reports CLT not installed
    if command -v xcode-select >/dev/null 2>&1; then
        if ! xcode-select -p >/dev/null 2>&1; then
            # CLT not installed — git is just a shim
            return 1
        fi
    fi
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# Download helper (n pattern — curl with PIPESTATUS checking)
# ═══════════════════════════════════════════════════════════════════════════════

download() {
    local url="$1" dest="$2"
    curl --fail --location --silent --show-error \
        --proto '=https' --tlsv1.2 \
        --retry 3 --retry-delay 2 \
        -o "$dest" "$url"
}

download_and_extract() {
    local url="$1" dest="$2"
    local tarball="$TMPDIR_INSTALL/download_$$.tar.gz"
    download "$url" "$tarball" || return 1
    mkdir -p "$dest"
    tar xzf "$tarball" -C "$dest" --strip-components=1 || {
        rm -rf "$dest"
        return 1
    }
    rm -f "$tarball"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Dependency check (fnm pattern — check all, report all, then exit)
# ═══════════════════════════════════════════════════════════════════════════════

say "Checking system..."

if [ "$(uname -s)" != "Darwin" ]; then
    err "This installer only works on macOS"
fi

ARCH="$(detect_arch)"
info "macOS $(sw_vers -productVersion) ($ARCH)"

missing_deps=()
for cmd in curl tar; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        missing_deps+=("$cmd")
    fi
done
if [ ${#missing_deps[@]} -gt 0 ]; then
    err "Missing required tools: ${missing_deps[*]}"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Check Claude Desktop
# ═══════════════════════════════════════════════════════════════════════════════

if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    # Check both Spotlight and filesystem (nvm pattern — multiple detection methods)
    if [ -d "/Applications/Claude.app" ] || \
       mdfind "kMDItemCFBundleIdentifier == 'com.anthropic.claude'" 2>/dev/null | grep -q .; then
        mkdir -p "$CLAUDE_CONFIG_DIR"
    else
        err "Claude Desktop not found. Install it from https://claude.ai/download"
    fi
fi
info "Claude Desktop detected"

# ═══════════════════════════════════════════════════════════════════════════════
# Install Node.js (Volta pattern — user-space, no sudo)
# ═══════════════════════════════════════════════════════════════════════════════

NODE_BIN=""
NPM_BIN=""

if command -v node >/dev/null 2>&1; then
    NODE_MAJOR=$(node --version 2>/dev/null | sed 's/v\([0-9]*\).*/\1/' || echo "0")
    if [ "$NODE_MAJOR" -ge 18 ] 2>/dev/null; then
        info "Node.js $(node --version) found"
        NODE_BIN="$(command -v node)"
        NPM_BIN="$(command -v npm)"
    fi
fi

if [ -z "$NODE_BIN" ]; then
    say "Installing Node.js $NODE_VERSION..."
    rm -rf "$NODE_DIR"
    download_and_extract \
        "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-${ARCH}.tar.gz" \
        "$NODE_DIR" \
        || err "Failed to install Node.js. Check your internet connection."

    # Verify binary works (n pattern)
    if ! "$NODE_DIR/bin/node" --version >/dev/null 2>&1; then
        rm -rf "$NODE_DIR"
        err "Node.js binary verification failed"
    fi

    NODE_BIN="$NODE_DIR/bin/node"
    NPM_BIN="$NODE_DIR/bin/npm"
    USED_SCRIPT_NODE=true
    export PATH="$NODE_DIR/bin:$PATH"
    add_to_profile "$NODE_DIR/bin"
    info "Installed Node.js $NODE_VERSION"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Install uv + Python (uv pattern — idempotent, no sudo)
# ═══════════════════════════════════════════════════════════════════════════════

if ! command -v uv >/dev/null 2>&1; then
    say "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh \
        || err "Failed to install uv. Check your internet connection."
    export PATH="$HOME/.local/bin:$PATH"
    # uv installer adds to profile itself, but verify
    if ! command -v uv >/dev/null 2>&1; then
        err "uv installed but not found on PATH"
    fi
    info "uv installed"
else
    info "uv found"
fi

# uv python install is idempotent — safe to re-run
say "Ensuring Python 3.12..."
uv python install 3.12 2>&1 | grep -v "^$" | tail -1 || err "Failed to install Python 3.12"
info "Python 3.12 ready"

# ═══════════════════════════════════════════════════════════════════════════════
# Download connectors (BEFORE Claude CLI — avoids $INSTALL_DIR conflict)
# ═══════════════════════════════════════════════════════════════════════════════

say "Downloading connectors..."

if git_is_available; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Updating existing installation..."
        git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || warn "git pull failed, using existing version"
    else
        # Backup user data before fresh clone (Volta pattern — preserve user state)
        if [ -d "$INSTALL_DIR/connectors" ]; then
            mv "$INSTALL_DIR/connectors" "$TMPDIR_INSTALL/connectors_backup" 2>/dev/null || true
        fi
        rm -rf "$INSTALL_DIR"
        git clone --depth 1 "$REPO.git" "$INSTALL_DIR" \
            || err "Failed to download connectors. Check your internet connection."
        # Restore user data (tokens, credentials)
        if [ -d "$TMPDIR_INSTALL/connectors_backup" ]; then
            find "$TMPDIR_INSTALL/connectors_backup" \( -name "token.json" -o -name "credentials.json" -o -name ".env" \) 2>/dev/null | while IFS= read -r f; do
                rel="${f#$TMPDIR_INSTALL/connectors_backup/}"
                dest="$INSTALL_DIR/connectors/$rel"
                mkdir -p "$(dirname "$dest")"
                cp "$f" "$dest"
            done
        fi
    fi
else
    info "git not available, downloading archive..."
    if [ -d "$INSTALL_DIR/connectors" ]; then
        mv "$INSTALL_DIR/connectors" "$TMPDIR_INSTALL/connectors_backup" 2>/dev/null || true
    fi
    rm -rf "$INSTALL_DIR"
    download "$REPO/archive/refs/heads/main.tar.gz" "$TMPDIR_INSTALL/mcp-pack.tar.gz" \
        || err "Failed to download connectors. Check your internet connection."
    mkdir -p "$(dirname "$INSTALL_DIR")"
    tar xzf "$TMPDIR_INSTALL/mcp-pack.tar.gz" -C "$(dirname "$INSTALL_DIR")" \
        || err "Failed to extract connectors."
    mv "$(dirname "$INSTALL_DIR")/mcp-pack-main" "$INSTALL_DIR"
fi

info "Connectors at $INSTALL_DIR"

# ═══════════════════════════════════════════════════════════════════════════════
# Install Claude CLI (npm research pattern — NPM_CONFIG_PREFIX for zero-sudo)
# AFTER connectors so $INSTALL_DIR exists
# ═══════════════════════════════════════════════════════════════════════════════

say "Installing Claude CLI..."

if command -v claude >/dev/null 2>&1; then
    info "Claude CLI already installed"
else
    # Determine writable npm prefix (npm research pattern)
    npm_prefix="$("$NPM_BIN" prefix -g 2>/dev/null || echo "")"

    if [ -n "$npm_prefix" ] && [ -w "$npm_prefix" ] 2>/dev/null; then
        # Prefix is writable (script-installed node, nvm, volta)
        "$NPM_BIN" install -g --no-audit --no-fund --loglevel=error \
            @anthropic-ai/claude-code \
            || err "Failed to install Claude CLI"
    else
        # System node or non-writable prefix — use custom prefix (npm research pattern)
        local_prefix="$HOME/.npm-global"
        mkdir -p "$local_prefix"
        NPM_CONFIG_PREFIX="$local_prefix" "$NPM_BIN" install -g \
            --no-audit --no-fund --loglevel=error \
            @anthropic-ai/claude-code \
            || err "Failed to install Claude CLI"
        export PATH="$local_prefix/bin:$PATH"
        add_to_profile "$local_prefix/bin"
    fi

    # Verify binary exists (post-install verification — npm research pattern)
    if ! command -v claude >/dev/null 2>&1; then
        err "Claude CLI installed but 'claude' command not found on PATH"
    fi
    info "Claude CLI installed"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Install connector dependencies (uv research — explicit -p for targeting)
# ═══════════════════════════════════════════════════════════════════════════════

say "Installing dependencies..."

install_python_connector() {
    local name="$1" dir="$2"
    info "$name..."
    # Use subshell to avoid cd leak (code review finding)
    (
        cd "$dir" || exit 1
        uv venv .venv -p 3.12 --quiet 2>&1 || { echo "warn: $name: failed to create venv" >&2; exit 1; }
        if [ -f requirements.txt ]; then
            uv pip install -p .venv -r requirements.txt --quiet 2>&1 || { echo "warn: $name: dependencies incomplete" >&2; exit 1; }
        fi
        .venv/bin/python3 -c "import sys" 2>/dev/null || { echo "warn: $name: venv Python broken" >&2; exit 1; }
    ) || warn "$name: setup failed, connector may not work"
}

install_python_connector "Trello" "$INSTALL_DIR/connectors/MCP_Trello"
install_python_connector "Fathom" "$INSTALL_DIR/connectors/MCP_Fathom"
install_python_connector "Google Workspace" "$INSTALL_DIR/connectors/MCP_Google_Workspace"

info "Telegram..."
(
    cd "$INSTALL_DIR/connectors/MCP_Telegram" || exit 1
    "$NPM_BIN" install --no-audit --no-fund --loglevel=error 2>&1 | tail -1
) || warn "Telegram dependencies incomplete"

# ═══════════════════════════════════════════════════════════════════════════════
# Configure Claude Desktop (atomic write — config research pattern)
# ═══════════════════════════════════════════════════════════════════════════════

say "Configuring Claude Desktop..."

UV_BIN="$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")"

SERVERS_JSON=$(cat <<JSONEOF
{
    "mcpServers": {
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
}
JSONEOF
)

# Use uv's Python (not /usr/bin/python3 which is a CLT shim on fresh Mac)
# BOM-safe, deep merge, backup with pruning (config research pattern)
uv run --python 3.12 python3 - "$CLAUDE_CONFIG" "$SERVERS_JSON" "$MAX_BACKUPS" <<'PYEOF'
import sys, os, json, tempfile, shutil, glob, time

config_path = sys.argv[1]
fragment_str = sys.argv[2]
max_backups = int(sys.argv[3])

def deep_merge(base, override):
    """Merge override into base. Existing values win over CONFIGURE_ME placeholders."""
    result = base.copy()
    for k, v in override.items():
        if k not in result:
            # New key — add it
            result[k] = v
        elif isinstance(result[k], dict) and isinstance(v, dict):
            # Both dicts — recurse
            result[k] = deep_merge(result[k], v)
        elif isinstance(v, str) and v == "CONFIGURE_ME":
            # Placeholder — never overwrite existing value
            pass
        else:
            # Non-placeholder override (e.g. updated paths) — update
            result[k] = v
    return result

try:
    fragment = json.loads(fragment_str)
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON fragment: {e}", file=sys.stderr)
    sys.exit(1)

config_dir = os.path.dirname(config_path)
if config_dir:
    os.makedirs(config_dir, exist_ok=True)

existing = {}
if os.path.exists(config_path) and os.path.getsize(config_path) > 0:
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            existing = json.load(f)
    except json.JSONDecodeError:
        print("  warn: existing config is malformed, starting fresh", file=sys.stderr)
        existing = {}

if not isinstance(existing, dict):
    existing = {}

# Deep merge — existing values win over CONFIGURE_ME placeholders
merged = deep_merge(existing, fragment)

# Backup with pruning
if os.path.exists(config_path):
    ts = time.strftime("%Y%m%dT%H%M%S")
    backup = f"{config_path}.backup.{ts}"
    try:
        shutil.copy2(config_path, backup)
    except OSError:
        pass
    for old in sorted(glob.glob(f"{config_path}.backup.*"))[:-max_backups]:
        try: os.unlink(old)
        except OSError: pass

# Atomic write: temp file → fsync → rename
try:
    fd, tmp = tempfile.mkstemp(dir=config_dir or '.', prefix='.config_', suffix='.json')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    if os.path.exists(config_path):
        os.chmod(tmp, os.stat(config_path).st_mode)
    else:
        os.chmod(tmp, 0o600)
    os.rename(tmp, config_path)
except OSError as e:
    try: os.unlink(tmp)
    except: pass
    print(f"ERROR: Failed to write config: {e}", file=sys.stderr)
    sys.exit(1)

# Count what was added
servers = merged.get('mcpServers', {})
new_count = sum(1 for s in servers.values()
                if isinstance(s, dict) and
                any(v == "CONFIGURE_ME" for v in s.get('env', {}).values()))
print(f"  {len(servers)} connector(s) configured ({new_count} need API keys)")
PYEOF

# set -e handles non-zero exit from Python above

# ═══════════════════════════════════════════════════════════════════════════════
# Create CLAUDE.md for Claude CLI key configuration
# ═══════════════════════════════════════════════════════════════════════════════

cat > "$INSTALL_DIR/CLAUDE.md" << 'CLAUDEMD'
# MCP Pack — Key Configuration

When the user provides API keys, update Claude Desktop config.

## Config file
`~/Library/Application Support/Claude/claude_desktop_config.json`

## What to do
1. Read the config file
2. Find the connector in `mcpServers`
3. Replace `CONFIGURE_ME` values with actual keys
4. Write back the file (use json.dump with indent=2)
5. Tell user to restart Claude Desktop

## Keys needed

**Trello:** `TRELLO_API_KEY` + `TRELLO_API_TOKEN` (from https://trello.com/power-ups/admin)
**Fathom:** `FATHOM_API_KEY` + `FATHOM_WEBHOOK_SECRET` (from https://fathom.video/settings/api)
**Telegram:** `TELEGRAM_BOT_TOKEN` (from @BotFather)
**Google Workspace:** No keys — run: `cd ~/.mcp-pack/connectors/MCP_Google_Workspace && python3 setup_auth.py`
CLAUDEMD

# ═══════════════════════════════════════════════════════════════════════════════
# Done
# ═══════════════════════════════════════════════════════════════════════════════

printf "\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${GREEN}${BOLD}  ✓ MCP Pack installed!${RESET}\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "\n"
printf "  ${BOLD}566 tools ready:${RESET}\n"
printf "    • Trello           — 171 tools\n"
printf "    • Google Workspace — 167 tools\n"
printf "    • Telegram         — 218 tools\n"
printf "    • Fathom           — 10 tools\n"
printf "\n"
printf "  ${BOLD}Next:${RESET}\n"
printf "    ${BOLD}1.${RESET} Run: ${BOLD}cd ~/.mcp-pack && claude${RESET}\n"
printf "    ${BOLD}2.${RESET} Tell Claude your API keys\n"
printf "    ${BOLD}3.${RESET} Restart Claude Desktop\n"
printf "\n"
printf "  ${DIM}Google Workspace: cd ~/.mcp-pack/connectors/MCP_Google_Workspace && python3 setup_auth.py${RESET}\n"
printf "  ${DIM}by m0rvayne · github.com/m0rvayne/mcp-pack${RESET}\n"
printf "\n"

} # end of script integrity wrapper (nvm pattern)
