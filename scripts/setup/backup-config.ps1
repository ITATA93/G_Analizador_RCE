<#
.SYNOPSIS
    Creates a backup of Antigravity configuration.

.DESCRIPTION
    Backs up .gemini/, .claude/, and instruction files to a timestamped
    archive for safe keeping before major changes.

.PARAMETER OutputPath
    Where to save the backup. Defaults to current directory.

.EXAMPLE
    .\backup-config.ps1
    .\backup-config.ps1 -OutputPath "D:\Backups"
#>

param(
    [string]$OutputPath = "."
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  ANTIGRAVITY CONFIGURATION BACKUP" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

# Determine workspace root
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupName = "antigravity-backup-$timestamp"
$backupDir = Join-Path $OutputPath $backupName

Write-Host "[..] Creating backup directory..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Items to backup
$itemsToBackup = @(
    ".gemini",
    ".claude",
    ".subagents",
    ".agent",
    "GEMINI.md",
    "CLAUDE.md",
    "CHANGELOG.md"
)

Write-Host "[..] Backing up configuration..." -ForegroundColor Cyan

foreach ($item in $itemsToBackup) {
    $sourcePath = Join-Path $workspaceRoot $item
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $backupDir $item
        if ((Get-Item $sourcePath).PSIsContainer) {
            Copy-Item -Recurse $sourcePath $destPath
        } else {
            Copy-Item $sourcePath $destPath
        }
        Write-Host "[OK] Backed up: $item" -ForegroundColor Green
    } else {
        Write-Host "[!!] Skipped (not found): $item" -ForegroundColor Yellow
    }
}

# Also backup global profile if it exists
$homeGemini = Join-Path $env:USERPROFILE ".gemini"
if (Test-Path $homeGemini) {
    $globalBackup = Join-Path $backupDir "_home-.gemini"
    Copy-Item -Recurse $homeGemini $globalBackup
    Write-Host "[OK] Backed up: ~/.gemini (global)" -ForegroundColor Green
}

# Create info file
$infoContent = @"
Antigravity Backup
==================
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Source: $workspaceRoot
User: $env:USERNAME
Computer: $env:COMPUTERNAME

Contents:
- .gemini/      Gemini CLI configuration
- .claude/      Claude Code configuration
- .subagents/   Sub-agent manifest
- .agent/       Agent rules
- GEMINI.md     Gemini instructions
- CLAUDE.md     Claude instructions
- CHANGELOG.md  Version history
- _home-.gemini/ Global profile backup

To restore:
1. Extract to workspace root
2. Or use restore-config.ps1
"@
$infoContent | Set-Content (Join-Path $backupDir "BACKUP-INFO.txt") -Encoding UTF8

# Create zip archive
$zipPath = "$backupDir.zip"
Write-Host "[..] Creating archive..." -ForegroundColor Cyan
Compress-Archive -Path $backupDir -DestinationPath $zipPath -Force
Remove-Item -Recurse -Force $backupDir

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  BACKUP COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Archive: $zipPath" -ForegroundColor Cyan
Write-Host "Size: $([math]::Round((Get-Item $zipPath).Length / 1KB, 2)) KB" -ForegroundColor Cyan
Write-Host ""
