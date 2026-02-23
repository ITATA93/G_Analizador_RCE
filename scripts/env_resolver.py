#!/usr/bin/env python3
"""
Antigravity Environment Resolver
=================================

Central module that replaces all hardcoded paths across the ecosystem.
Auto-detects the current environment by probing filesystem paths or
reading the AG_ENV environment variable.

Usage (as import):
    from env_resolver import get_repo_root, get_projects_dir, get_plantilla_dir

Usage (standalone):
    python env_resolver.py              # Show detected environment
    python env_resolver.py --register   # Register this machine as a new environment
"""

import json
import os
import sys
from pathlib import Path

# -- Locate config -------------------------------------------------------------

# The config file lives relative to this script: ../config/environments.json
_SCRIPT_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _SCRIPT_DIR.parent / "config" / "environments.json"


def _load_config() -> dict:
    """Load the environments config file."""
    if not _CONFIG_PATH.exists():
        print(f"[WARN] environments.json not found at {_CONFIG_PATH}", file=sys.stderr)
        return {"environments": {}}
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def _save_config(config: dict) -> None:
    """Save the environments config file."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# -- Environment Detection ----------------------------------------------------


def detect_environment() -> tuple[str, dict]:
    """
    Detect the current environment.

    Resolution order:
    1. AG_ENV environment variable
    2. config['active_environment'] if set
    3. Auto-detect by probing base_path existence

    Returns:
        (env_id, env_config) tuple

    Raises:
        RuntimeError: if no environment can be detected
    """
    config = _load_config()
    envs = config.get("environments", {})

    if not envs:
        raise RuntimeError(
            "No environments defined in environments.json. "
            "Run: python env_resolver.py --register"
        )

    # 1. Check AG_ENV env var
    env_var = config.get("env_var_override", "AG_ENV")
    env_from_var = os.environ.get(env_var)
    if env_from_var and env_from_var in envs:
        return env_from_var, envs[env_from_var]

    # 2. Check active_environment in config
    active = config.get("active_environment")
    if active and active in envs:
        return active, envs[active]

    # 3. Auto-detect by probing filesystem
    for env_id, env_cfg in envs.items():
        base = Path(env_cfg["base_path"])
        if base.exists():
            return env_id, env_cfg

    # 4. Fall back to default
    for env_id, env_cfg in envs.items():
        if env_cfg.get("is_default"):
            return env_id, env_cfg

    raise RuntimeError(
        f"Cannot detect environment. Known envs: {list(envs.keys())}. "
        f"Set {env_var} or run: python env_resolver.py --register"
    )


# -- Public API ----------------------------------------------------------------


def get_environment_id() -> str:
    """Return the current environment identifier (e.g., 'notebook', 'hetzner')."""
    env_id, _ = detect_environment()
    return env_id


def get_repo_root() -> Path:
    """Return the base repository root for the current environment."""
    _, env_cfg = detect_environment()
    return Path(env_cfg["base_path"])


def get_projects_dirs() -> list[Path]:
    """Return the list of project directories for the current environment."""
    _, env_cfg = detect_environment()
    base = Path(env_cfg["base_path"])
    if "projects_dirs" in env_cfg:
        return [base / p for p in env_cfg["projects_dirs"]]
    if "projects_dir" in env_cfg:
        return [base / env_cfg["projects_dir"]]
    return []


def get_plantilla_dir() -> Path:
    """Return the AG_Plantilla directory for the current environment."""
    _, env_cfg = detect_environment()
    return Path(env_cfg["base_path"]) / env_cfg["plantilla_dir"]


def get_template_dir() -> Path:
    """Return the _template/workspace directory."""
    return get_plantilla_dir() / "_template" / "workspace"


def list_ag_projects() -> list[Path]:
    """List all AG_* project directories in the current environment."""
    projects = []
    for p_dir in get_projects_dirs():
        if p_dir.exists():
            projects.extend(
                d for d in p_dir.iterdir() if d.is_dir() and d.name.startswith("AG_")
            )
    return sorted(projects)


def resolve_project_path(relative_path: str) -> Path:
    """
    Resolve a relative project path (e.g., 'AG_Proyectos/AG_Hospital')
    to an absolute path in the current environment.
    """
    return get_repo_root() / relative_path


def get_capabilities() -> list[str]:
    """Return the capabilities of the current environment."""
    _, env_cfg = detect_environment()
    return env_cfg.get("capabilities", [])


# -- Registration CLI ----------------------------------------------------------


def register_environment(env_id: str, base_path: str, description: str = "") -> None:
    """Register a new environment in the config."""
    config = _load_config()
    envs = config.setdefault("environments", {})

    if env_id in envs:
        print(f"[WARN] Environment '{env_id}' already exists. Updating.")

    envs[env_id] = {
        "base_path": base_path,
        "projects_dir": "AG_Proyectos",
        "plantilla_dir": "AG_Plantilla",
        "capabilities": ["git", "python"],
        "description": description or f"Environment on {base_path}",
    }

    # Set as active
    config["active_environment"] = env_id
    _save_config(config)
    print(f"[+] Registered environment '{env_id}' at {base_path}")


# -- CLI -----------------------------------------------------------------------


def main() -> None:
    """CLI entry point for environment management."""
    import argparse

    parser = argparse.ArgumentParser(description="Antigravity Environment Resolver")
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register this machine as a new environment",
    )
    parser.add_argument("--id", help="Environment ID (for --register)")
    parser.add_argument("--base-path", help="Base path (for --register)")
    parser.add_argument(
        "--description", default="", help="Description (for --register)"
    )
    parser.add_argument("--list", action="store_true", help="List all environments")
    args = parser.parse_args()

    if args.register:
        env_id = (
            args.id
            or input("Environment ID (e.g., notebook, hetzner, desktop3): ").strip()
        )
        base_path = (
            args.base_path or input("Base path (e.g., C:\\_Repositorio): ").strip()
        )
        register_environment(env_id, base_path, args.description)
        return

    if args.list:
        config = _load_config()
        envs = config.get("environments", {})
        print(f"\nAntigravity Environments ({len(envs)}):\n")
        for eid, ecfg in envs.items():
            exists = "✓" if Path(ecfg["base_path"]).exists() else "✗"
            default = " (default)" if ecfg.get("is_default") else ""
            print(f"  [{exists}] {eid}{default}")
            print(f"      Path: {ecfg['base_path']}")
            print(f"      Caps: {', '.join(ecfg.get('capabilities', []))}")
            desc = ecfg.get("description", "")
            if desc:
                print(f"      Desc: {desc}")
            print()
        return

    # Default: show detected environment
    try:
        env_id, env_cfg = detect_environment()
        print(f"\n  Environment: {env_id}")
        print(f"  Base Path:   {env_cfg['base_path']}")
        print(f"  Projects:    {[d.name for d in get_projects_dirs()]}")
        print(f"  Plantilla:   {get_plantilla_dir()}")
        print(f"  Caps:        {', '.join(env_cfg.get('capabilities', []))}")

        projects = list_ag_projects()
        print(f"  Projects:    {len(projects)} found")
        for p in projects:
            print(f"    - {p.name}")
        print()
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
