<#
.SYNOPSIS
    Synchronizes workspace configuration with global profile.

.DESCRIPTION
    Copies updated configuration from workspace to the global profile
    (_global-profile/) and optionally installs to ~/.gemini/.

.PARAMETER InstallGlobal
    Also install to ~/.gemini/ after syncing.

.EXAMPLE
    .\sync-global.ps1
    .\sync-global.ps1 -InstallGlobal
#>

param(
    [switch]$InstallGlobal = $false
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[..] $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "[!!] $msg" -ForegroundColor Yellow }

Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  ANTIGRAVITY SYNC GLOBAL PROFILE" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

# Paths
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$globalProfile = Join-Path $workspaceRoot "_global-profile"

# Items to sync (workspace -> global profile)
$syncItems = @(
    @{ Source = ".gemini\agents"; Dest = ".gemini\agents" }
    @{ Source = ".gemini\commands"; Dest = ".gemini\commands" }
    @{ Source = ".gemini\rules"; Dest = ".gemini\rules" }
    @{ Source = ".gemini\skills"; Dest = ".gemini\skills" }
    @{ Source = ".gemini\workflows"; Dest = ".gemini\workflows" }
    @{ Source = ".gemini\settings.json"; Dest = ".gemini\settings.json" }
    @{ Source = "GEMINI.md"; Dest = "GEMINI.md" }
)

Write-Info "Syncing workspace -> _global-profile..."
Write-Host ""

foreach ($item in $syncItems) {
    $sourcePath = Join-Path $workspaceRoot $item.Source
    $destPath = Join-Path $globalProfile $item.Dest

    if (Test-Path $sourcePath) {
        # Create destination directory if needed
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }

        # Copy
        if ((Get-Item $sourcePath).PSIsContainer) {
            # Remove existing and copy fresh
            if (Test-Path $destPath) {
                Remove-Item -Recurse -Force $destPath
            }
            Copy-Item -Recurse $sourcePath $destPath
        } else {
            Copy-Item -Force $sourcePath $destPath
        }
        Write-Success "Synced: $($item.Source)"
    } else {
        Write-Warning "Skipped (not found): $($item.Source)"
    }
}

# Update timestamp
$timestampFile = Join-Path $globalProfile ".last-sync"
Get-Date -Format "yyyy-MM-dd HH:mm:ss" | Set-Content $timestampFile
Write-Success "Updated sync timestamp"

Write-Host ""
Write-Host "Global profile updated: $globalProfile" -ForegroundColor Cyan

# Install to global if requested
if ($InstallGlobal) {
    Write-Host ""
    Write-Info "Installing to ~/.gemini/..."
    $installScript = Join-Path $globalProfile "install-global.ps1"
    if (Test-Path $installScript) {
        & $installScript -Force
    } else {
        Write-Warning "install-global.ps1 not found"
    }
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  SYNC COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
