<#
.SYNOPSIS
    Antigravity Ecosystem Migrator
.DESCRIPTION
    Migrates the flat workspace (W:\G_Plantilla, W:\G_Proyectos) into the
    Star Topology domain architecture (W:\Antigravity_OS).
#>

$SourceRoot = "W:\G_Proyectos" # Where most projects currently live
$SourcePlantilla = "W:\G_Plantilla"
$TargetRoot = "W:\Antigravity_OS"

Write-Host "Initializing Antigravity Domain Migration..." -ForegroundColor Cyan

# Define the dictionary of movement
$MigrationMap = @{
    "00_CORE" = @(
        "G_Notebook",
        "G_SV_Agent"
    )
    "01_HOSPITAL_PRIVADO" = @(
        "G_Analizador_RCE",
        "G_Consultas",
        "G_DeepResearch_Salud_Chile",
        "G_Hospital",
        "G_Hospital_Organizador",
        "G_Informatica_Medica",
        "G_Lists_Agent",
        "G_TrakCare_Explorer"
    )
    "02_HOSPITAL_PUBLICO" = @(
        "G_NB_Apps",
        "G_SD_Plantilla"
    )
}

# 1. Create Target Root if missing
if (!(Test-Path $TargetRoot)) {
    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
    Write-Host "Created new OS root: $TargetRoot" -ForegroundColor Green
}

# 2. Iterate through domains and move projects
foreach ($Domain in $MigrationMap.Keys) {
    $DomainPath = Join-Path $TargetRoot $Domain
    if (!(Test-Path $DomainPath)) {
        New-Item -ItemType Directory -Path $DomainPath -Force | Out-Null
        Write-Host "Created domain zone: $DomainPath" -ForegroundColor Green
    }

    foreach ($Project in $MigrationMap[$Domain]) {
        $SourceProjectPath = Join-Path $SourceRoot $Project
        $TargetProjectPath = Join-Path $DomainPath $Project

        if (Test-Path $SourceProjectPath) {
            Write-Host "Moving $Project --> $Domain" -ForegroundColor Yellow
            try {
                Move-Item -Path $SourceProjectPath -Destination $TargetProjectPath -Force
            } catch {
                Write-Host "Failed to move $Project. Error: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "Project $Project not found in $SourceRoot. Skipping." -ForegroundColor DarkGray
        }
    }
}

# 3. Handle G_Plantilla globally
$CorePath = Join-Path $TargetRoot "00_CORE"
if (!(Test-Path $CorePath)) { New-Item -ItemType Directory -Path $CorePath | Out-Null }

if (Test-Path $SourcePlantilla) {
    $TargetPlantilla = Join-Path $CorePath "G_Plantilla"
    Write-Host "Moving G_Plantilla --> 00_CORE" -ForegroundColor Yellow
    try {
        Move-Item -Path $SourcePlantilla -Destination $TargetPlantilla -Force
    } catch {
        Write-Host "Failed to move G_Plantilla. Error: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Migration Complete!" -ForegroundColor Cyan
Write-Host "Please close this Editor window and reopen your global workspace at: $TargetRoot" -ForegroundColor Yellow
