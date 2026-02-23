#!/usr/bin/env python3
"""
Template Propagation Engine — Antigravity Ecosystem
=====================================================

Detects "template drift" between _template/workspace/ and project files.
Can preview diffs and apply approved changes across all AG projects.

Usage:
    python scripts/propagate.py status              # Show drift summary
    python scripts/propagate.py diff AG_Hospital     # Show diffs for one project
    python scripts/propagate.py apply --file GEMINI.md  # Propagate a specific file
    python scripts/propagate.py apply --all          # Propagate all drifted files
"""

import argparse
import difflib
import subprocess
import sys
from pathlib import Path

# -- Configuration -------------------------------------------------------------

REPO_ROOT = Path(r"C:\_Repositorio")
PROJECTS_DIR = REPO_ROOT / "AG_Proyectos"
PLANTILLA_DIR = REPO_ROOT / "AG_Plantilla"
TEMPLATE_DIR = PLANTILLA_DIR / "_template" / "workspace"

# Files tracked for propagation (relative to project root)
PROPAGATED_FILES = [
    "GEMINI.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".gitignore",
    "docs/standards/output_governance.md",
]

# Files that use {{PROJECT_NAME}} placeholder
TEMPLATED_FILES = {"GEMINI.md", "CLAUDE.md", "AGENTS.md", "docs/TASKS.md"}


# -- Helpers -------------------------------------------------------------------


def get_all_projects() -> list[tuple[str, Path]]:
    """Return list of (name, path) for all AG projects."""
    projects = []
    if PROJECTS_DIR.is_dir():
        for d in sorted(PROJECTS_DIR.iterdir()):
            if d.is_dir() and d.name.startswith("AG_"):
                projects.append((d.name, d))
    return projects


def get_template_content(file_path: str, project_name: str = "") -> str | None:
    """Read template file and replace placeholders."""
    template = TEMPLATE_DIR / file_path
    if not template.is_file():
        return None
    content = template.read_text(encoding="utf-8", errors="replace")
    if file_path in TEMPLATED_FILES and project_name:
        content = content.replace("{{PROJECT_NAME}}", project_name)
    return content


def compute_drift(project_name: str, project_dir: Path) -> list[dict]:
    """Compare project files against template. Return list of drifted files."""
    drifted = []
    for f in PROPAGATED_FILES:
        template_content = get_template_content(f, project_name)
        if template_content is None:
            continue

        project_file = project_dir / f
        if not project_file.is_file():
            drifted.append({"file": f, "status": "MISSING", "diff": None})
            continue

        project_content = project_file.read_text(encoding="utf-8", errors="replace")
        if project_content.strip() != template_content.strip():
            diff = list(difflib.unified_diff(
                project_content.splitlines(keepends=True),
                template_content.splitlines(keepends=True),
                fromfile=f"project/{f}",
                tofile=f"template/{f}",
                n=3,
            ))
            if diff:
                drifted.append({"file": f, "status": "DRIFTED", "diff": "".join(diff)})
    return drifted


# -- Commands ------------------------------------------------------------------


def cmd_status(_args: argparse.Namespace) -> None:
    """Show drift summary for all projects."""
    projects = get_all_projects()
    if not projects:
        print("No AG projects found.")
        return

    print(f"\n{'=' * 60}")
    print("  Template Drift Report")
    print(f"  Template: {TEMPLATE_DIR}")
    print(f"  {len(projects)} projects | {len(PROPAGATED_FILES)} tracked files")
    print(f"{'=' * 60}")

    total_drifted = 0
    for name, path in projects:
        drifts = compute_drift(name, path)
        if drifts:
            total_drifted += len(drifts)
            status_parts = []
            for d in drifts:
                icon = "❌" if d["status"] == "MISSING" else "⚠️"
                status_parts.append(f"{icon} {d['file']}")
            print(f"\n  {name}:")
            for s in status_parts:
                print(f"    {s}")
        else:
            print(f"\n  {name}: ✅ in sync")

    print(f"\n  Total drifted: {total_drifted}")
    if total_drifted == 0:
        print("  🎯 ALL PROJECTS IN SYNC")
    print()


def cmd_diff(args: argparse.Namespace) -> None:
    """Show diff for a specific project."""
    project_name = args.project
    project_dir = PROJECTS_DIR / project_name
    if not project_dir.is_dir():
        print(f"Project not found: {project_name}")
        sys.exit(1)

    drifts = compute_drift(project_name, project_dir)
    if not drifts:
        print(f"✅ {project_name} is in sync with template")
        return

    for d in drifts:
        print(f"\n--- {d['file']} [{d['status']}] ---")
        if d["diff"]:
            print(d["diff"])
        else:
            print("  (file missing — would create from template)")


def cmd_apply(args: argparse.Namespace) -> None:
    """Apply template changes to projects."""
    projects = get_all_projects()
    target_file = args.file
    apply_all = args.all

    if not target_file and not apply_all:
        print("Specify --file <name> or --all")
        sys.exit(1)

    applied = 0
    for name, path in projects:
        drifts = compute_drift(name, path)
        for d in drifts:
            if not apply_all and d["file"] != target_file:
                continue

            template_content = get_template_content(d["file"], name)
            if template_content is None:
                continue

            target = path / d["file"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(template_content, encoding="utf-8")
            print(f"  [SYNC] {name}/{d['file']}")
            applied += 1

        # Auto-commit if changes were applied
        if applied > 0 and (path / ".git").is_dir():
            try:
                subprocess.run(
                    ["git", "add", "."],
                    cwd=path, capture_output=True, timeout=10,
                )
                subprocess.run(
                    ["git", "commit", "--no-verify", "-m",
                     f"chore: sync from template ({target_file or 'all'})"],
                    cwd=path, capture_output=True, timeout=10,
                )
            except Exception:
                pass

    print(f"\n  Applied: {applied} file(s)")


# -- CLI -----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Template Propagation Engine — Antigravity Ecosystem"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show drift summary")

    p_diff = sub.add_parser("diff", help="Show diffs for a project")
    p_diff.add_argument("project", help="Project name (e.g., AG_Hospital)")

    p_apply = sub.add_parser("apply", help="Apply template to projects")
    p_apply.add_argument("--file", help="Specific file to propagate")
    p_apply.add_argument("--all", action="store_true", help="Propagate all drifted files")

    args = parser.parse_args()

    commands = {
        "status": cmd_status,
        "diff": cmd_diff,
        "apply": cmd_apply,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
