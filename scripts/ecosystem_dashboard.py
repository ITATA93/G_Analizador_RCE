#!/usr/bin/env python3
"""
Antigravity Ecosystem Dashboard
================================

Category-aware dashboard for the full AG ecosystem.
Groups projects by category, shows health indicators, and supports
environment-specific views.

Usage:
    python ecosystem_dashboard.py                          # Full dashboard
    python ecosystem_dashboard.py --category hospital-personal  # Filter by category
    python ecosystem_dashboard.py --env hetzner            # Show what's installed in env
    python ecosystem_dashboard.py --json                   # JSON output for automation
"""

import json
import sys
from pathlib import Path

# -- Configuration (env-aware) -------------------------------------------------

try:
    from env_resolver import get_plantilla_dir, get_repo_root

    REPO_ROOT = get_repo_root()
    PLANTILLA_DIR = get_plantilla_dir()
except ImportError:
    REPO_ROOT = Path(r"C:\_Repositorio")
    PLANTILLA_DIR = REPO_ROOT / "AG_Plantilla"

REGISTRY_PATH = PLANTILLA_DIR / "config" / "project_registry.json"


# -- Registry Loading ---------------------------------------------------------


def load_registry() -> dict:
    """Load the project registry."""
    if not REGISTRY_PATH.exists():
        print(f"[ERROR] Registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def resolve_project_path(project: dict) -> Path:
    """Resolve a project's absolute path from its relative path."""
    rel = project.get("path_relative", "")
    if rel:
        # Path() automatically normalizes separators for the current OS
        return REPO_ROOT / Path(rel)
    # Legacy support: absolute path
    return Path(project.get("path", ""))


# -- Health Checks ------------------------------------------------------------


def check_project_health(project_path: Path) -> dict:
    """Quick health check for a project directory."""
    exists = project_path.exists()
    checks = {
        "exists": exists,
        "has_git": (project_path / ".git").is_dir() if exists else False,
        "has_gemini": (project_path / "GEMINI.md").is_file() if exists else False,
        "has_changelog": (project_path / "CHANGELOG.md").is_file() if exists else False,
        "has_tasks": (
            (project_path / "docs" / "TASKS.md").is_file() if exists else False
        ),
        "has_agents": (
            (project_path / ".subagents" / "manifest.json").is_file()
            if exists
            else False
        ),
    }
    # Score is computed AFTER building the dict to avoid counting itself
    score = sum(1 for v in checks.values() if v)
    max_score = len(checks)
    return {**checks, "score": score, "max_score": max_score}


# -- Dashboard Output ---------------------------------------------------------


def print_category_header(category_id: str, category_info: dict) -> None:
    """Print a category header."""
    icon = category_info.get("icon", "📁")
    desc = category_info.get("description", "")
    print(f"\n  {icon} {category_id.upper()}")
    if desc:
        print(f"     {desc}")
    print(f"  {'─' * 60}")


def print_project_row(project: dict, health: dict) -> None:
    """Print a single project row."""
    name = project["name"]
    ptype = project.get("type", "?")

    if not health["exists"]:
        indicator = "✗ NOT INSTALLED"
        score_str = "—"
    else:
        score = health["score"]
        max_score = health["max_score"]
        pct = score * 100 // max_score if max_score else 0
        if pct >= 80:
            indicator = "●"
        elif pct >= 50:
            indicator = "◐"
        else:
            indicator = "○"
        score_str = f"{score}/{max_score}"

    checks = []
    if health["exists"]:
        checks.append("GIT" if health["has_git"] else "no-git")
        checks.append("AGENTS" if health["has_agents"] else "no-agents")
        checks.append("TASKS" if health["has_tasks"] else "no-tasks")

    checks_str = " | ".join(checks) if checks else ""
    print(f"    {indicator} {name:<35} [{ptype:<14}] {score_str}")
    if checks_str:
        print(f"      {checks_str}")


def print_dashboard(
    registry: dict,
    category_filter: str | None = None,
) -> None:
    """Print the full ecosystem dashboard."""
    projects = registry.get("projects", [])
    categories = registry.get("categories", {})

    # Group by category
    grouped: dict[str, list[dict]] = {}
    for proj in projects:
        cat = proj.get("category", "uncategorized")
        grouped.setdefault(cat, []).append(proj)

    # Print header
    print("\n" + "=" * 66)
    print("  🌐 ANTIGRAVITY ECOSYSTEM DASHBOARD")
    print(
        f"  Registry v{registry.get('registry_version', '?')}"
        f" | {len(projects)} projects"
        f" | {len(categories)} categories"
    )
    print("=" * 66)

    # Stats
    total_installed = 0
    total_healthy = 0

    # Determine category order
    category_order = list(categories.keys())
    for cat in grouped:
        if cat not in category_order:
            category_order.append(cat)

    for cat_id in category_order:
        if category_filter and cat_id != category_filter:
            continue

        cat_projects = grouped.get(cat_id, [])
        if not cat_projects:
            continue

        cat_info = categories.get(cat_id, {"icon": "📁", "description": ""})
        print_category_header(cat_id, cat_info)

        for proj in cat_projects:
            proj_path = resolve_project_path(proj)
            health = check_project_health(proj_path)
            print_project_row(proj, health)

            if health["exists"]:
                total_installed += 1
                if health["score"] >= health["max_score"] - 1:
                    total_healthy += 1

    # Summary
    print(f"\n{'=' * 66}")
    print(
        f"  Summary: {total_installed}/{len(projects)} installed"
        f" | {total_healthy} healthy"
    )

    from env_resolver import get_environment_id

    try:
        env_id = get_environment_id()
        print(f"  Environment: {env_id}")
    except (ImportError, RuntimeError):
        pass

    print("=" * 66)
    print()


def print_json_output(registry: dict, category_filter: str | None = None) -> None:
    """Print JSON output for automation."""
    projects = registry.get("projects", [])
    output = []

    for proj in projects:
        if category_filter and proj.get("category") != category_filter:
            continue

        proj_path = resolve_project_path(proj)
        health = check_project_health(proj_path)

        output.append(
            {
                "id": proj["id"],
                "name": proj["name"],
                "category": proj.get("category", "uncategorized"),
                "type": proj.get("type", "unknown"),
                "path": str(proj_path),
                "installed": health["exists"],
                "health_score": health["score"],
                "health_max": health["max_score"],
                "health_details": health,
            }
        )

    print(json.dumps(output, indent=2, ensure_ascii=False))


# -- CLI -----------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Antigravity Ecosystem Dashboard")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--env", help="Show projects for a specific environment (future)"
    )
    args = parser.parse_args()

    registry = load_registry()

    if args.json:
        print_json_output(registry, args.category)
    else:
        print_dashboard(registry, args.category)


if __name__ == "__main__":
    main()
