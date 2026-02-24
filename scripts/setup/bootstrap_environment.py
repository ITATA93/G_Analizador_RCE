#!/usr/bin/env python3
"""
Antigravity Environment Setup - Interactive Step-by-Step
========================================================

Run after cloning G_Plantilla on a new machine:
    python scripts/setup/bootstrap_environment.py

Requires: git, python, 7z (for secrets)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows console
if sys.platform == "win32":
    os.system("")  # Enable ANSI colors
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---- Colors ----
class C:
    OK = "\033[92m"    # green
    WARN = "\033[93m"  # yellow
    ERR = "\033[91m"   # red
    INFO = "\033[96m"  # cyan
    DIM = "\033[90m"   # gray
    BOLD = "\033[1m"
    END = "\033[0m"


def ok(msg):    print(f"    {C.OK}[OK]{C.END} {msg}")
def warn(msg):  print(f"    {C.WARN}[!]{C.END} {msg}")
def err(msg):   print(f"    {C.ERR}[X]{C.END} {msg}")
def info(msg):  print(f"    {C.INFO}[+]{C.END} {msg}")
def dim(msg):   print(f"    {C.DIM}{msg}{C.END}")
def step(n, total, title):
    print(f"\n  {C.INFO}[{n}/{total}] {title}{C.END}")
    print(f"  {C.DIM}{'-' * 50}{C.END}")


def ask_yn(question):
    r = input(f"    {question} (s/n): ").strip().lower()
    return r in ("s", "y", "si", "yes")


def cmd_exists(name):
    return shutil.which(name) is not None


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


# ---- Detect paths ----
def detect_paths():
    script_dir = Path(__file__).resolve().parent  # scripts/setup/
    plantilla = script_dir.parent.parent           # G_Plantilla/
    base = plantilla.parent                        # C:\_Repositorio/
    return plantilla, base


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print(f"  {C.INFO}====================================={C.END}")
    print(f"  {C.INFO}  Antigravity Environment Setup{C.END}")
    print(f"  {C.INFO}====================================={C.END}")
    print()

    plantilla, base = detect_paths()
    print(f"  G_Plantilla: {C.OK}{plantilla}{C.END}")
    print(f"  Base:         {C.OK}{base}{C.END}")
    print()

    total = 6

    # ==========================================================
    # STEP 1: Check tools
    # ==========================================================
    step(1, total, "Verificar herramientas")

    tools = {
        "git": "Git",
        "python": "Python",
        "node": "Node.js",
        "7z": "7-Zip",
        "gh": "GitHub CLI",
    }

    # Try adding 7-Zip to PATH if not found
    if not cmd_exists("7z"):
        sz_path = r"C:\Program Files\7-Zip"
        if os.path.exists(os.path.join(sz_path, "7z.exe")):
            os.environ["PATH"] += f";{sz_path}"

    missing = []
    for cmd, name in tools.items():
        if cmd_exists(cmd):
            ok(name)
        else:
            err(f"{name} - NO ENCONTRADO")
            missing.append((cmd, name))

    if missing and cmd_exists("winget"):
        if ask_yn(f"Instalar {len(missing)} herramientas faltantes via winget?"):
            winget_ids = {
                "git": "Git.Git",
                "python": "Python.Python.3.12",
                "node": "OpenJS.NodeJS.LTS",
                "7z": "7zip.7zip",
                "gh": "GitHub.cli",
            }
            for cmd, name in missing:
                wid = winget_ids.get(cmd)
                if wid:
                    info(f"Instalando {name}...")
                    r = run(["winget", "install", wid,
                             "--accept-package-agreements",
                             "--accept-source-agreements", "--silent"])
                    if r.returncode == 0:
                        ok(f"{name} instalado")
                    else:
                        warn(f"{name} puede necesitar instalacion manual")
    elif missing:
        names = ", ".join(n for _, n in missing)
        warn(f"Instala manualmente: {names}")

    # ==========================================================
    # STEP 2: Register environment
    # ==========================================================
    step(2, total, "Registrar entorno")

    env_file = plantilla / "config" / "environments.json"
    if env_file.exists():
        env_config = json.loads(env_file.read_text(encoding="utf-8"))
        env_id = input("    Nombre de este PC (ej: desktop, notebook, oficina): ").strip()
        if not env_id:
            env_id = "default"

        envs = env_config.get("environments", {})
        if env_id not in envs:
            envs[env_id] = {
                "base_path": str(base),
                "projects_dir": "G_Proyectos",
                "plantilla_dir": "G_Plantilla",
                "capabilities": ["git", "python"],
            }
            env_config["environments"] = envs
            env_config["active_environment"] = env_id
            env_file.write_text(json.dumps(env_config, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
            ok(f"Registrado como '{env_id}'")
        else:
            ok(f"'{env_id}' ya existe")
    else:
        warn("environments.json no encontrado")

    # ==========================================================
    # STEP 3: Clone projects
    # ==========================================================
    step(3, total, "Clonar proyectos")

    reg_file = plantilla / "config" / "project_registry.json"

    if not cmd_exists("git"):
        err("Git no disponible, no puedo clonar")
    elif reg_file.exists():
        registry = json.loads(reg_file.read_text(encoding="utf-8"))
        projects = registry.get("projects", [])

        existing = 0
        to_clone = []
        for proj in projects:
            abs_path = base / proj["path_relative"]
            if abs_path.exists():
                existing += 1
            elif proj.get("github_repo"):
                to_clone.append(proj)

        ok(f"{existing} proyectos ya existen")
        if to_clone:
            warn(f"{len(to_clone)} por clonar:")
            for p in to_clone:
                dim(f"  - {p['name']} ({p.get('category', '?')})")
            print()

            if ask_yn(f"Clonar los {len(to_clone)} proyectos faltantes?"):
                cloned = 0
                for proj in to_clone:
                    abs_path = base / proj["path_relative"]
                    repo_url = f"https://github.com/{proj['github_repo']}.git"
                    abs_path.parent.mkdir(parents=True, exist_ok=True)

                    print(f"      {C.INFO}[+]{C.END} {proj['name']}...", end="", flush=True)
                    r = run(["git", "clone", repo_url, str(abs_path)])
                    if r.returncode == 0:
                        print(f" {C.OK}OK{C.END}")
                        cloned += 1
                    else:
                        print(f" {C.ERR}ERROR{C.END}")
                ok(f"{cloned} repos clonados")
            else:
                dim("Saltado")
        else:
            ok("Todos los proyectos presentes")
    else:
        warn("project_registry.json no encontrado")

    # ==========================================================
    # STEP 4: Restore secrets
    # ==========================================================
    step(4, total, "Restaurar secretos (.env, credentials)")

    secrets_file = plantilla / "data" / "secure" / "secrets.7z"
    if not secrets_file.exists():
        secrets_file = plantilla / "data" / "secure" / "agent_configs.7z"

    if secrets_file.exists():
        ok(f"Archivo: {secrets_file.name}")
        if ask_yn("Restaurar secretos?"):
            sync_script = plantilla / "scripts" / "setup" / "agent_config_sync.py"
            if sync_script.exists():
                subprocess.run([sys.executable, str(sync_script), "unpack"])
            else:
                err("agent_config_sync.py no encontrado")
    else:
        warn("No hay archivo secrets.7z")
        print()
        dim("Para migrar secretos desde otro PC:")
        dim("  1. En el PC origen: python agent_config_sync.py pack")
        dim(f"  2. Copiar secrets.7z a: {plantilla / 'data' / 'secure'}")
        dim("  3. Volver a ejecutar este script")

    # ==========================================================
    # STEP 5: Agent profile
    # ==========================================================
    step(5, total, "Instalar perfil de agentes")

    install_script = plantilla / "_global-profile" / "install-global.ps1"
    if install_script.exists():
        if ask_yn("Instalar perfil global de agentes?"):
            subprocess.run(["powershell", "-NoProfile", "-File", str(install_script)])
            ok("Perfil instalado")
    else:
        dim("install-global.ps1 no encontrado, saltando")

    # ==========================================================
    # STEP 6: Health check
    # ==========================================================
    step(6, total, "Verificacion final")

    dashboard = plantilla / "scripts" / "ecosystem_dashboard.py"
    if dashboard.exists():
        subprocess.run([sys.executable, str(dashboard)])
    else:
        # Quick manual check
        for cmd, name in [("git", "git"), ("python", "python"), ("gh", "gh")]:
            if cmd_exists(cmd):
                ok(name)
            else:
                err(name)

        proj_dir = base / "G_Proyectos"
        if proj_dir.exists():
            count = len([d for d in proj_dir.iterdir() if d.is_dir() and d.name.startswith("G_")])
            ok(f"Proyectos: {count}")

    # Done
    print()
    print(f"  {C.OK}====================================={C.END}")
    print(f"  {C.OK}  Setup completo!{C.END}")
    print(f"  {C.OK}====================================={C.END}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Cancelado.")
    except Exception as e:
        print(f"\n  Error: {e}")
    sys.exit(0)
