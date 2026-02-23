<#
.SYNOPSIS
    Antigravity Environment Setup - Interactive Step-by-Step Guide
.DESCRIPTION
    Run this after cloning AG_Plantilla on a new machine.
    It guides you through setting up everything step by step.
.EXAMPLE
    .\bootstrap_environment.ps1
    .\bootstrap_environment.ps1 -DryRun
#>
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

function Ask-YesNo {
    param([string]$Question)
    $r = Read-Host "$Question (s/n)"
    return ($r -eq "s" -or $r -eq "S" -or $r -eq "y" -or $r -eq "Y")
}

function Show-Step {
    param([int]$Num, [int]$Total, [string]$Title)
    Write-Host ""
    Write-Host "  [$Num/$Total] $Title" -ForegroundColor Cyan
    Write-Host "  $('-' * 50)" -ForegroundColor DarkGray
}

# ---- Banner ----
Write-Host ""
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host "  Antigravity Environment Setup" -ForegroundColor Cyan
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "  MODO: DRY RUN (sin cambios reales)" -ForegroundColor Yellow
    Write-Host ""
}

# ---- Detect where we are ----
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }

# script is at scripts/setup/ so PlantillaDir is 2 levels up
try {
    $PlantillaDir = (Resolve-Path "$ScriptDir\..\..").Path
    $BasePath = (Resolve-Path "$PlantillaDir\..").Path
} catch {
    Write-Host "  No pude detectar la ubicacion automaticamente." -ForegroundColor Yellow
    $PlantillaDir = Read-Host "  Ruta a AG_Plantilla (ej: C:\_Repositorio\AG_Plantilla)"
    $BasePath = Split-Path $PlantillaDir -Parent
}

Write-Host "  AG_Plantilla: $PlantillaDir" -ForegroundColor Green
Write-Host "  Base:         $BasePath" -ForegroundColor Green
Write-Host ""

$TotalSteps = 6

# ============================================================
# STEP 1: Check Dev Tools
# ============================================================
Show-Step 1 $TotalSteps "Verificar herramientas"

$toolsInfo = @(
    @{ Name = "git";     Cmd = "git" },
    @{ Name = "python";  Cmd = "python" },
    @{ Name = "node";    Cmd = "node" },
    @{ Name = "7z";      Cmd = "7z" },
    @{ Name = "gh";      Cmd = "gh" }
)

$missing = @()
foreach ($t in $toolsInfo) {
    $found = $null -ne (Get-Command $t.Cmd -ErrorAction SilentlyContinue)
    if ($found) {
        Write-Host "    [OK] $($t.Name)" -ForegroundColor Green
    } else {
        Write-Host "    [X] $($t.Name) - NO ENCONTRADO" -ForegroundColor Red
        $missing += $t
    }
}

# Add 7-Zip to PATH if not found but exists
if (-not (Get-Command "7z" -ErrorAction SilentlyContinue)) {
    if (Test-Path "C:\Program Files\7-Zip\7z.exe") {
        $env:PATH += ";C:\Program Files\7-Zip"
        Write-Host "    [OK] 7z (agregado al PATH)" -ForegroundColor Green
        $missing = $missing | Where-Object { $_.Name -ne "7z" }
    }
}

if ($missing.Count -gt 0) {
    $wingetOk = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
    if ($wingetOk) {
        $doInstall = Ask-YesNo "    Instalar herramientas faltantes via winget?"
        if ($doInstall -and -not $DryRun) {
            $wingetIds = @{
                "git" = "Git.Git"
                "python" = "Python.Python.3.12"
                "node" = "OpenJS.NodeJS.LTS"
                "7z" = "7zip.7zip"
                "gh" = "GitHub.cli"
            }
            foreach ($m in $missing) {
                $id = $wingetIds[$m.Name]
                if ($id) {
                    Write-Host "    [+] Instalando $($m.Name)..." -ForegroundColor Cyan
                    $null = & winget install $id --accept-package-agreements --accept-source-agreements --silent 2>&1
                    Write-Host "    [OK] $($m.Name)" -ForegroundColor Green
                }
            }
            # Refresh PATH
            $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [Environment]::GetEnvironmentVariable("PATH", "User") + ";C:\Program Files\7-Zip"
        }
    } else {
        $names = @(); foreach ($mm in $missing) { $names += $mm.Name }; $nameList = $names -join ', '
        Write-Host "    Instala manualmente: $nameList" -ForegroundColor Yellow
    }
}

# ============================================================
# STEP 2: Register Environment
# ============================================================
Show-Step 2 $TotalSteps "Registrar entorno"

$envFile = "$PlantillaDir\config\environments.json"
if (Test-Path $envFile) {
    $envConfig = Get-Content $envFile -Raw | ConvertFrom-Json
    $EnvId = Read-Host "    Nombre de este PC (ej: desktop, notebook, oficina)"
    if (-not $EnvId) { $EnvId = "default" }

    $existing = $envConfig.environments.PSObject.Properties | Where-Object { $_.Name -eq $EnvId }

    if (-not $existing) {
        if (-not $DryRun) {
            $newEnv = @{
                base_path     = $BasePath
                projects_dir  = "AG_Proyectos"
                plantilla_dir = "AG_Plantilla"
                capabilities  = @("git", "python")
                description   = "Registered $(Get-Date -Format 'yyyy-MM-dd')"
            }
            $envConfig.environments | Add-Member -NotePropertyName $EnvId -NotePropertyValue $newEnv
            $envConfig.active_environment = $EnvId
            $envConfig | ConvertTo-Json -Depth 10 | Set-Content $envFile -Encoding UTF8
        }
        Write-Host "    [OK] Registrado como '$EnvId'" -ForegroundColor Green
    } else {
        Write-Host "    [OK] '$EnvId' ya existe" -ForegroundColor Green
    }
} else {
    Write-Host "    [!] environments.json no encontrado" -ForegroundColor Yellow
}

# ============================================================
# STEP 3: Clone All Projects
# ============================================================
Show-Step 3 $TotalSteps "Clonar proyectos"

$regFile = "$PlantillaDir\config\project_registry.json"

if (Test-Path $regFile) {
    $registry = Get-Content $regFile -Raw | ConvertFrom-Json
    $projects = $registry.projects

    # Count existing vs missing
    $existCount = 0
    $missingProjects = @()
    foreach ($proj in $projects) {
        $absPath = "$BasePath\$($proj.path_relative)"
        if (Test-Path $absPath) {
            $existCount++
        } elseif ($proj.github_repo) {
            $missingProjects += $proj
        }
    }

    Write-Host "    $existCount proyectos ya existen" -ForegroundColor Green
    Write-Host "    $($missingProjects.Count) por clonar" -ForegroundColor Yellow

    if ($missingProjects.Count -gt 0) {
        Write-Host ""
        foreach ($p in $missingProjects) {
            Write-Host "      - $($p.name) ($($p.category))" -ForegroundColor DarkGray
        }
        Write-Host ""

        $doClone = Ask-YesNo "    Clonar los $($missingProjects.Count) proyectos faltantes?"

        if ($doClone) {
            $cloned = 0
            foreach ($proj in $missingProjects) {
                $absPath = "$BasePath\$($proj.path_relative)"
                $repoUrl = "https://github.com/$($proj.github_repo).git"

                if (-not $DryRun) {
                    Write-Host "      [+] $($proj.name)..." -ForegroundColor Cyan -NoNewline
                    $parentDir = Split-Path $absPath -Parent
                    if (-not (Test-Path $parentDir)) {
                        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
                    }
                    git clone $repoUrl $absPath 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host " OK" -ForegroundColor Green
                        $cloned++
                    } else {
                        Write-Host " ERROR" -ForegroundColor Red
                    }
                } else {
                    Write-Host "      [DRY] $($proj.name)" -ForegroundColor Yellow
                    $cloned++
                }
            }
            Write-Host "    $cloned repos clonados" -ForegroundColor Green
        } else {
            Write-Host "    Saltado" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "    [!] project_registry.json no encontrado" -ForegroundColor Yellow
}

# ============================================================
# STEP 4: Restore Secrets (.env, credentials)
# ============================================================
Show-Step 4 $TotalSteps "Restaurar secretos (.env, credentials)"

$secretsFile = "$PlantillaDir\data\secure\secrets.7z"
if (-not (Test-Path $secretsFile)) {
    $secretsFile = "$PlantillaDir\data\secure\agent_configs.7z"
}

if (Test-Path $secretsFile) {
    Write-Host "    Archivo encontrado: $secretsFile" -ForegroundColor Green

    $doSecrets = Ask-YesNo "    Restaurar secretos?"

    if ($doSecrets -and -not $DryRun) {
        $syncScript = "$PlantillaDir\scripts\setup\agent_config_sync.py"
        if (Test-Path $syncScript) {
            python $syncScript unpack
        } else {
            Write-Host "    [!] agent_config_sync.py no encontrado" -ForegroundColor Red
        }
    } elseif ($DryRun) {
        Write-Host "    [DRY] Restauraria secretos" -ForegroundColor Yellow
    }
} else {
    Write-Host "    [!] No hay archivo secrets.7z" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    Para migrar secretos desde otro PC:" -ForegroundColor DarkGray
    Write-Host "      1. En el PC origen: python agent_config_sync.py pack" -ForegroundColor DarkGray
    Write-Host "      2. Copiar secrets.7z a: $PlantillaDir\data\secure" -ForegroundColor DarkGray
    Write-Host "      3. Volver a ejecutar este script" -ForegroundColor DarkGray
}

# ============================================================
# STEP 5: Install Agent Profile
# ============================================================
Show-Step 5 $TotalSteps "Instalar perfil de agentes"

$installScript = "$PlantillaDir\_global-profile\install-global.ps1"
if (Test-Path $installScript) {
    $doProfile = Ask-YesNo "    Instalar perfil global de agentes?"
    if ($doProfile -and -not $DryRun) {
        & $installScript
        Write-Host "    [OK] Perfil instalado" -ForegroundColor Green
    }
} else {
    Write-Host "    [i] install-global.ps1 no encontrado, saltando" -ForegroundColor DarkGray
}

# ============================================================
# STEP 6: Health Check
# ============================================================
Show-Step 6 $TotalSteps "Verificacion final"

$dashboard = "$PlantillaDir\scripts\ecosystem_dashboard.py"
if ((Test-Path $dashboard) -and -not $DryRun) {
    python $dashboard
} else {
    # Manual quick check
    $gitOk = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
    $pyOk  = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
    $ghOk  = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

    if ($gitOk) { Write-Host "    git:    OK" -ForegroundColor Green } else { Write-Host "    git:    FALTA" -ForegroundColor Red }
    if ($pyOk)  { Write-Host "    python: OK" -ForegroundColor Green } else { Write-Host "    python: FALTA" -ForegroundColor Red }
    if ($ghOk)  { Write-Host "    gh:     OK" -ForegroundColor Green } else { Write-Host "    gh:     FALTA" -ForegroundColor Red }

    $projCount = 0
    $projDir = "$BasePath\AG_Proyectos"
    if (Test-Path $projDir) {
        $projCount = @(Get-ChildItem $projDir -Directory | Where-Object { $_.Name -match "^AG_" }).Count
    }
    Write-Host "    Proyectos: $projCount" -ForegroundColor Green
}

# ---- Done ----
Write-Host ""
Write-Host "  =====================================" -ForegroundColor Green
Write-Host "  Setup completo!" -ForegroundColor Green
Write-Host "  =====================================" -ForegroundColor Green
Write-Host ""
