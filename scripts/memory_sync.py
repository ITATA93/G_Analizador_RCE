#!/usr/bin/env python3
"""
Transversal Memory System — Antigravity Ecosystem
===================================================

Collects project status (DEVLOG, TASKS) across all AG projects and generates
a unified ecosystem dashboard at docs/ecosystem-status.md.

Also syncs individual project session data into episodic memory.

Usage:
    python scripts/memory_sync.py sync      # Sync current project memory
    python scripts/memory_sync.py dashboard  # Generate ecosystem status dashboard
    python scripts/memory_sync.py full       # Sync + dashboard
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

# -- Configuration -------------------------------------------------------------

REPO_ROOT = Path(r"C:\_Repositorio")
PROJECTS_DIR = REPO_ROOT / "G_Proyectos"
PLANTILLA_DIR = REPO_ROOT / "G_Plantilla"

BRAIN_PATH = PLANTILLA_DIR / ".gemini" / "brain"
EPISODES_PATH = BRAIN_PATH / "episodes"
DASHBOARD_PATH = PLANTILLA_DIR / "docs" / "ecosystem-status.md"


# -- Helpers -------------------------------------------------------------------


def get_all_projects() -> list[tuple[str, Path]]:
    """Return all AG projects as (name, path) tuples."""
    projects = [("G_Plantilla", PLANTILLA_DIR)]
    if PROJECTS_DIR.is_dir():
        for d in sorted(PROJECTS_DIR.iterdir()):
            if d.is_dir() and d.name.startswith("G_"):
                projects.append((d.name, d))
    return projects


def extract_last_session(devlog_path: Path) -> dict | None:
    """Extract the most recent session entry from DEVLOG.md."""
    if not devlog_path.is_file():
        return None

    content = devlog_path.read_text(encoding="utf-8", errors="replace")
    # Find last ## header (session entry)
    sessions = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    sessions = [s.strip() for s in sessions if s.strip().startswith("## ")]

    if not sessions:
        return None

    last = sessions[-1]
    lines = last.splitlines()
    title = lines[0].replace("## ", "").strip() if lines else "Unknown"

    # Extract date from title (YYYY-MM-DD pattern)
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", title)
    date = date_match.group(1) if date_match else "unknown"

    # Summary = first 3 non-empty content lines
    content_lines = [l.strip() for l in lines[1:] if l.strip() and not l.startswith("#")]
    summary = " ".join(content_lines[:3])[:200]

    return {"title": title, "date": date, "summary": summary}


def extract_pending_tasks(tasks_path: Path) -> list[str]:
    """Extract pending tasks from TASKS.md (local + incoming)."""
    if not tasks_path.is_file():
        return []

    content = tasks_path.read_text(encoding="utf-8", errors="replace")
    pending = []

    for line in content.splitlines():
        line_stripped = line.strip()
        # Local tasks: - [ ] items
        if line_stripped.startswith("- [ ]") or line_stripped.startswith("- [/]"):
            pending.append(line_stripped)
        # Incoming cross-project tasks with PENDING status
        elif "PENDING" in line_stripped and line_stripped.startswith("- "):
            pending.append(line_stripped)

    return pending[:10]  # Cap at 10


def extract_blockers(tasks_path: Path) -> list[str]:
    """Extract blocker items from TASKS.md."""
    if not tasks_path.is_file():
        return []

    content = tasks_path.read_text(encoding="utf-8", errors="replace")
    blockers = []
    in_blocker = False

    for line in content.splitlines():
        if "Blocker" in line and line.strip().startswith("###"):
            in_blocker = True
            continue
        if in_blocker and line.strip().startswith("###"):
            break
        if in_blocker and line.strip().startswith("- "):
            if "(none)" not in line.lower():
                blockers.append(line.strip())

    return blockers


# -- Commands ------------------------------------------------------------------


def cmd_sync(_args: argparse.Namespace) -> None:
    """Sync current session data to episodic memory."""
    EPISODES_PATH.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    episode_file = EPISODES_PATH / f"session_{today}.md"

    projects = get_all_projects()
    entries = []

    for name, path in projects:
        devlog = path / "docs" / "DEVLOG.md"
        session = extract_last_session(devlog)
        if session and session["date"] == today:
            entries.append(f"## {name}\n\n{session['summary']}\n")

    if entries:
        content = f"# Ecosystem Session — {today}\n\n" + "\n".join(entries)
        episode_file.write_text(content, encoding="utf-8")
        print(f"✅ Synced {len(entries)} project sessions → {episode_file}")
    else:
        print(f"ℹ️  No sessions found for today ({today})")


def cmd_dashboard(_args: argparse.Namespace) -> None:
    """Generate transversal ecosystem status dashboard."""
    projects = get_all_projects()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Ecosystem Status — {now}",
        "",
        "> Auto-generated by `scripts/memory_sync.py dashboard`",
        "> DO NOT EDIT MANUALLY — will be overwritten on next sync",
        "",
        "## Project Activity",
        "",
        "| Project | Last Session | Pending | Blockers |",
        "|---------|-------------|---------|----------|",
    ]

    total_pending = 0
    total_blockers = 0

    for name, path in projects:
        devlog = path / "docs" / "DEVLOG.md"
        tasks = path / "docs" / "TASKS.md"

        session = extract_last_session(devlog)
        last_date = session["date"] if session else "—"

        pending = extract_pending_tasks(tasks)
        blockers = extract_blockers(tasks)

        total_pending += len(pending)
        total_blockers += len(blockers)

        blocker_text = f"🔴 {len(blockers)}" if blockers else "—"
        pending_text = str(len(pending)) if pending else "0"

        lines.append(f"| {name} | {last_date} | {pending_text} | {blocker_text} |")

    lines.extend([
        "",
        "## Summary",
        "",
        f"- **Projects**: {len(projects)}",
        f"- **Total pending tasks**: {total_pending}",
        f"- **Total blockers**: {total_blockers}",
        "",
    ])

    # Active blockers detail
    if total_blockers > 0:
        lines.extend(["## 🔴 Active Blockers", ""])
        for name, path in projects:
            blockers = extract_blockers(path / "docs" / "TASKS.md")
            if blockers:
                lines.append(f"### {name}")
                for b in blockers:
                    lines.append(f"  {b}")
                lines.append("")

    lines.extend(["---", f"*Generated: {now}*", ""])

    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Dashboard generated: {DASHBOARD_PATH}")
    print(f"   {len(projects)} projects | {total_pending} pending | {total_blockers} blockers")


def cmd_full(args: argparse.Namespace) -> None:
    """Run sync + dashboard."""
    cmd_sync(args)
    cmd_dashboard(args)


# -- CLI -----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transversal Memory System — Antigravity Ecosystem"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("sync", help="Sync session data to episodic memory")
    sub.add_parser("dashboard", help="Generate ecosystem status dashboard")
    sub.add_parser("full", help="Sync + dashboard")

    args = parser.parse_args()

    commands = {
        "sync": cmd_sync,
        "dashboard": cmd_dashboard,
        "full": cmd_full,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
