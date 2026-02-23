<#
.SYNOPSIS
    Checks the health of Antigravity installation and configuration.

.DESCRIPTION
    Verifies that all required tools, files, and configurations are
    properly installed and configured for Antigravity development.

.EXAMPLE
    .\health-check.ps1
#>

$ErrorActionPreference = "Continue"

# Colors
function Write-Pass { param($msg) Write-Host "[PASS] $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  ANTIGRAVITY HEALTH CHECK" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

$totalChecks = 0
$passedChecks = 0

function Test-Check {
    param($name, $condition, $fixHint)
    $script:totalChecks++
    if ($condition) {
        Write-Pass $name
        $script:passedChecks++
        return $true
    } else {
        Write-Fail $name
        if ($fixHint) { Write-Info "  Fix: $fixHint" }
        return $false
    }
}

# ============================================
# TOOLS
# ============================================
Write-Host "--- Tools ---" -ForegroundColor Yellow

# Git
$gitVersion = git --version 2>$null
Test-Check "Git installed" ($LASTEXITCODE -eq 0) "Install Git from https://git-scm.com/"

# GitHub CLI
$ghVersion = gh --version 2>$null
Test-Check "GitHub CLI (gh) installed" ($LASTEXITCODE -eq 0) "Install from https://cli.github.com/"

# Node.js
$nodeVersion = node --version 2>$null
Test-Check "Node.js installed" ($LASTEXITCODE -eq 0) "Install from https://nodejs.org/"

# Check gh auth
$ghAuth = gh auth status 2>&1
Test-Check "GitHub CLI authenticated" ($LASTEXITCODE -eq 0) "Run: gh auth login"

# ============================================
# WORKSPACE STRUCTURE
# ============================================
Write-Host ""
Write-Host "--- Workspace Structure ---" -ForegroundColor Yellow

$workspaceRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$requiredDirs = @(
    ".gemini",
    ".gemini\agents",
    ".gemini\commands",
    ".gemini\rules",
    ".claude",
    ".subagents",
    "_template",
    "_global-profile",
    "docs"
)

foreach ($dir in $requiredDirs) {
    $path = Join-Path $workspaceRoot $dir
    Test-Check "Directory: $dir" (Test-Path $path) "Create directory or re-run setup"
}

# ============================================
# CONFIGURATION FILES
# ============================================
Write-Host ""
Write-Host "--- Configuration Files ---" -ForegroundColor Yellow

$requiredFiles = @(
    @{ Path = ".gemini\settings.json"; Name = "Gemini settings" }
    @{ Path = ".subagents\manifest.json"; Name = "Sub-agents manifest" }
    @{ Path = "GEMINI.md"; Name = "GEMINI.md" }
    @{ Path = "CLAUDE.md"; Name = "CLAUDE.md" }
)

foreach ($file in $requiredFiles) {
    $path = Join-Path $workspaceRoot $file.Path
    Test-Check $file.Name (Test-Path $path) "File missing: $($file.Path)"
}

# ============================================
# GLOBAL PROFILE
# ============================================
Write-Host ""
Write-Host "--- Global Profile ---" -ForegroundColor Yellow

$homeGemini = Join-Path $env:USERPROFILE ".gemini"
$homeClaude = Join-Path $env:USERPROFILE ".claude"

Test-Check "~/.gemini exists" (Test-Path $homeGemini) "Run: _global-profile\install-global.ps1"
Test-Check "~/.gemini/settings.json" (Test-Path "$homeGemini\settings.json") "Run: _global-profile\install-global.ps1"
Test-Check "~/.gemini/agents/" (Test-Path "$homeGemini\agents") "Run: _global-profile\install-global.ps1"

# ============================================
# AGENTS
# ============================================
Write-Host ""
Write-Host "--- Agents ---" -ForegroundColor Yellow

$agentsDir = Join-Path $workspaceRoot ".gemini\agents"
if (Test-Path $agentsDir) {
    $agents = Get-ChildItem "$agentsDir\*.toml" -ErrorAction SilentlyContinue
    $agentCount = ($agents | Measure-Object).Count
    Test-Check "Agents defined ($agentCount found)" ($agentCount -gt 0) "Add agents to .gemini/agents/"

    $expectedAgents = @("code-analyst", "doc-writer", "code-reviewer", "test-writer", "db-analyst", "deployer")
    foreach ($agent in $expectedAgents) {
        $agentFile = Join-Path $agentsDir "$agent.toml"
        if (Test-Path $agentFile) {
            Write-Pass "  Agent: $agent"
            $passedChecks++
        } else {
            Write-Warn "  Agent missing: $agent"
        }
        $totalChecks++
    }
}

# ============================================
# MIGRATION TOOLS
# ============================================
Write-Host ""
Write-Host "--- Migration Tools ---" -ForegroundColor Yellow

$templateDir = Join-Path $workspaceRoot "_template"
Test-Check "migrate-project.ps1" (Test-Path "$templateDir\migrate-project.ps1") "Missing PowerShell migration script"
Test-Check "migrate-project.sh" (Test-Path "$templateDir\migrate-project.sh") "Missing Bash migration script"
Test-Check "MIGRATION-CHECKLIST.md" (Test-Path "$templateDir\MIGRATION-CHECKLIST.md") "Missing migration checklist"

# ============================================
# SUMMARY
# ============================================
Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
$percentage = [math]::Round(($passedChecks / $totalChecks) * 100)
$color = if ($percentage -ge 90) { "Green" } elseif ($percentage -ge 70) { "Yellow" } else { "Red" }
Write-Host "  Health Score: $passedChecks/$totalChecks ($percentage%)" -ForegroundColor $color
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

if ($percentage -ge 90) {
    Write-Host "System is healthy and ready for development!" -ForegroundColor Green
} elseif ($percentage -ge 70) {
    Write-Host "System has some issues. Review warnings above." -ForegroundColor Yellow
} else {
    Write-Host "System needs attention. Review failures above." -ForegroundColor Red
}
Write-Host ""
