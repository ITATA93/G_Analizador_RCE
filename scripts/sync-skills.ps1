<#
.SYNOPSIS
    Sync Skills
.DESCRIPTION
    Consolidates and synchronizes Antigravity skills across all vendor directories
    (.gemini, .claude, .codex) from the universal repository (.subagents/skills).
#>

$WorkspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$UniversalRepo = Join-Path $WorkspaceRoot ".subagents\skills"
$Vendors = @(".gemini\skills", ".claude\skills", ".codex\skills")

Write-Host "Syncing Antigravity Skills..." -ForegroundColor Cyan

# 1. Create Universal Repo if missing
if (!(Test-Path $UniversalRepo)) {
    New-Item -ItemType Directory -Path $UniversalRepo -Force | Out-Null
}

# 2. Migrate existing fragmented skills to Universal Repo
foreach ($vendor in $Vendors) {
    $VendorDir = Join-Path $WorkspaceRoot $vendor
    if (Test-Path $VendorDir) {
        $Files = Get-ChildItem -Path $VendorDir -File
        foreach ($file in $Files) {
            $TargetFile = Join-Path $UniversalRepo $file.Name
            if (!(Test-Path $TargetFile)) {
                Write-Host "Migrating $($file.Name) from $vendor to Universal Repo" -ForegroundColor Yellow
                Move-Item -Path $file.FullName -Destination $TargetFile -Force
            }
        }
    }
}

# 3. Broadcast Universal Skills back to all vendors (Parity)
$UniversalFiles = Get-ChildItem -Path $UniversalRepo -File
if ($UniversalFiles.Count -gt 0) {
    foreach ($vendor in $Vendors) {
        $VendorDir = Join-Path $WorkspaceRoot $vendor
        if (!(Test-Path $VendorDir)) {
            New-Item -ItemType Directory -Path $VendorDir -Force | Out-Null
        }
        foreach ($file in $UniversalFiles) {
            $TargetFile = Join-Path $VendorDir $file.Name
            Copy-Item -Path $file.FullName -Destination $TargetFile -Force
        }
        Write-Host "Synced $($UniversalFiles.Count) skills to $vendor" -ForegroundColor Green
    }
} else {
    Write-Host "No skills found in Universal Repo to sync." -ForegroundColor Yellow
}

Write-Host "Skill sync complete." -ForegroundColor Cyan
