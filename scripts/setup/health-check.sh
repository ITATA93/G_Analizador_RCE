#!/bin/bash
#
# health-check.sh
# Checks the health of Antigravity installation and configuration.
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }

echo ""
echo -e "${MAGENTA}=============================================${NC}"
echo -e "${MAGENTA}  ANTIGRAVITY HEALTH CHECK${NC}"
echo -e "${MAGENTA}=============================================${NC}"
echo ""

TOTAL_CHECKS=0
PASSED_CHECKS=0

check() {
    local name="$1"
    local condition="$2"
    local fix_hint="$3"

    ((TOTAL_CHECKS++))

    if bash -c "$condition" > /dev/null 2>&1; then
        pass "$name"
        ((PASSED_CHECKS++))
        return 0
    else
        fail "$name"
        [ -n "$fix_hint" ] && info "  Fix: $fix_hint"
        return 1
    fi
}

# Get workspace root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# ============================================
# TOOLS
# ============================================
echo -e "${YELLOW}--- Tools ---${NC}"

check "Git installed" "command -v git" "Install Git"
check "GitHub CLI (gh) installed" "command -v gh" "Install from https://cli.github.com/"
check "Node.js installed" "command -v node" "Install from https://nodejs.org/"
check "GitHub CLI authenticated" "gh auth status" "Run: gh auth login"

# ============================================
# WORKSPACE STRUCTURE
# ============================================
echo ""
echo -e "${YELLOW}--- Workspace Structure ---${NC}"

REQUIRED_DIRS=(
    ".gemini"
    ".gemini/agents"
    ".gemini/commands"
    ".gemini/rules"
    ".claude"
    ".subagents"
    "_template"
    "_global-profile"
    "docs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    check "Directory: $dir" "[ -d '$WORKSPACE_ROOT/$dir' ]" "Create directory or re-run setup"
done

# ============================================
# CONFIGURATION FILES
# ============================================
echo ""
echo -e "${YELLOW}--- Configuration Files ---${NC}"

check "Gemini settings" "[ -f '$WORKSPACE_ROOT/.gemini/settings.json' ]" "File missing"
check "Sub-agents manifest" "[ -f '$WORKSPACE_ROOT/.subagents/manifest.json' ]" "File missing"
check "GEMINI.md" "[ -f '$WORKSPACE_ROOT/GEMINI.md' ]" "File missing"
check "CLAUDE.md" "[ -f '$WORKSPACE_ROOT/CLAUDE.md' ]" "File missing"

# ============================================
# GLOBAL PROFILE
# ============================================
echo ""
echo -e "${YELLOW}--- Global Profile ---${NC}"

check "~/.gemini exists" "[ -d '$HOME/.gemini' ]" "Run: _global-profile/install-global.sh"
check "~/.gemini/settings.json" "[ -f '$HOME/.gemini/settings.json' ]" "Run: _global-profile/install-global.sh"
check "~/.gemini/agents/" "[ -d '$HOME/.gemini/agents' ]" "Run: _global-profile/install-global.sh"

# ============================================
# AGENTS
# ============================================
echo ""
echo -e "${YELLOW}--- Agents ---${NC}"

AGENTS_DIR="$WORKSPACE_ROOT/.gemini/agents"
if [ -d "$AGENTS_DIR" ]; then
    AGENT_COUNT=$(find "$AGENTS_DIR" -name "*.toml" 2>/dev/null | wc -l)
    check "Agents defined ($AGENT_COUNT found)" "[ $AGENT_COUNT -gt 0 ]" "Add agents to .gemini/agents/"

    EXPECTED_AGENTS=("code-analyst" "doc-writer" "code-reviewer" "test-writer" "db-analyst" "deployer")
    for agent in "${EXPECTED_AGENTS[@]}"; do
        ((TOTAL_CHECKS++))
        if [ -f "$AGENTS_DIR/$agent.toml" ]; then
            pass "  Agent: $agent"
            ((PASSED_CHECKS++))
        else
            warn "  Agent missing: $agent"
        fi
    done
fi

# ============================================
# MIGRATION TOOLS
# ============================================
echo ""
echo -e "${YELLOW}--- Migration Tools ---${NC}"

TEMPLATE_DIR="$WORKSPACE_ROOT/_template"
check "migrate-project.ps1" "[ -f '$TEMPLATE_DIR/migrate-project.ps1' ]" "Missing PowerShell migration script"
check "migrate-project.sh" "[ -f '$TEMPLATE_DIR/migrate-project.sh' ]" "Missing Bash migration script"
check "MIGRATION-CHECKLIST.md" "[ -f '$TEMPLATE_DIR/MIGRATION-CHECKLIST.md' ]" "Missing migration checklist"

# ============================================
# SUMMARY
# ============================================
echo ""
echo -e "${MAGENTA}=============================================${NC}"
PERCENTAGE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

if [ $PERCENTAGE -ge 90 ]; then
    COLOR=$GREEN
elif [ $PERCENTAGE -ge 70 ]; then
    COLOR=$YELLOW
else
    COLOR=$RED
fi

echo -e "  Health Score: ${COLOR}$PASSED_CHECKS/$TOTAL_CHECKS ($PERCENTAGE%)${NC}"
echo -e "${MAGENTA}=============================================${NC}"
echo ""

if [ $PERCENTAGE -ge 90 ]; then
    echo -e "${GREEN}System is healthy and ready for development!${NC}"
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "${YELLOW}System has some issues. Review warnings above.${NC}"
else
    echo -e "${RED}System needs attention. Review failures above.${NC}"
fi
echo ""
