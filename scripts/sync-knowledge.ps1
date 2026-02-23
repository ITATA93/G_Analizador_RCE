# sync-knowledge.ps1 - Promote deep research to global Knowledge Items
# Windows PowerShell version

$ErrorActionPreference = "Stop"

$RESEARCH_DIR = "docs\research"
$KNOWLEDGE_DIR = "$env:USERPROFILE\.gemini\antigravity\knowledge"

Write-Host "🔍 Antigravity Knowledge Sync" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Check if research directory exists
if (-not (Test-Path $RESEARCH_DIR)) {
    Write-Host "❌ Error: $RESEARCH_DIR not found" -ForegroundColor Red
    exit 1
}

# List recent research files (last 30 days)
Write-Host "📚 Recent research files:" -ForegroundColor Yellow
$recentFiles = Get-ChildItem -Path $RESEARCH_DIR -Filter "*.md" -Recurse -File |
    Where-Object { $_.FullName -notlike "*_templates*" -and $_.LastWriteTime -gt (Get-Date).AddDays(-30) } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10

$recentFiles | ForEach-Object { Write-Host "  - $($_.FullName)" }

Write-Host ""
$research_file = Read-Host "Enter the path to the research file to promote (or 'q' to quit)"

if ($research_file -eq 'q') {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $research_file)) {
    Write-Host "❌ File not found: $research_file" -ForegroundColor Red
    exit 1
}

# Extract title and tags
$content = Get-Content $research_file -Raw
$title = ($content -split "`n" | Where-Object { $_ -match "^# " } | Select-Object -First 1) -replace "^# ", ""
$tagsLine = ($content -split "`n" | Where-Object { $_ -match "^\*\*Tags:\*\*" } | Select-Object -First 1)
$tags = if ($tagsLine) { $tagsLine -replace "^\*\*Tags:\*\* ", "" } else { "" }

Write-Host ""
Write-Host "📄 Research: $title" -ForegroundColor Green
Write-Host "🏷️  Tags: $tags" -ForegroundColor Green
Write-Host ""
$ki_name = Read-Host "Enter Knowledge Item name (snake_case, e.g., 'nocobase_api_patterns')"

if ([string]::IsNullOrWhiteSpace($ki_name)) {
    Write-Host "❌ Name cannot be empty" -ForegroundColor Red
    exit 1
}

$ki_path = Join-Path $KNOWLEDGE_DIR $ki_name

# Check if KI already exists
if (Test-Path $ki_path) {
    Write-Host "⚠️  Knowledge Item '$ki_name' already exists" -ForegroundColor Yellow
    $add_to_existing = Read-Host "Do you want to add to it? (y/n)"

    if ($add_to_existing -ne 'y') {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
} else {
    # Create new KI structure
    New-Item -ItemType Directory -Force -Path "$ki_path\artifacts" | Out-Null

    # Create metadata.json
    $metadata = @{
        title = $title
        created = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        updated = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        tags = $tags
        source = $research_file
    } | ConvertTo-Json -Depth 10

    $metadata | Out-File -FilePath "$ki_path\metadata.json" -Encoding UTF8

    Write-Host "✅ Created new Knowledge Item: $ki_name" -ForegroundColor Green
}

# Copy research to artifacts
$artifact_name = Split-Path $research_file -Leaf
Copy-Item $research_file "$ki_path\artifacts\$artifact_name" -Force

Write-Host "✅ Copied research to KI artifacts" -ForegroundColor Green
Write-Host ""
Write-Host "Knowledge Item location: $ki_path" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review and organize artifacts in $ki_path\artifacts\"
Write-Host "2. Create overview.md if needed"
Write-Host "3. Update metadata.json with additional info"
Write-Host ""
Write-Host "✨ Done!" -ForegroundColor Green
