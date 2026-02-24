#!/usr/bin/env python3
"""
Cross-Workspace Task Delegation System — Antigravity Ecosystem
==============================================================

Creates, lists, updates, and tracks tasks that span multiple AG projects.
Each task is dual-written to both source (outgoing) and target (incoming) TASKS.md.

Usage:
    python cross_task.py create --from G_NB_Apps --to G_Consultas --title "..." --description "..."
    python cross_task.py list [--project G_Consultas] [--status pending]
    python cross_task.py update TASK-2026-0001 --status done [--notes "Completed query"]
    python cross_task.py dashboard
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# -- Configuration ------------------------------------------------------------

try:
    from env_resolver import (
        get_plantilla_dir,
        get_projects_dirs,
        get_repo_root,
        list_ag_projects,
    )

    REPO_ROOT = get_repo_root()
    PLANTILLA_DIR = get_plantilla_dir()
except ImportError:
    # Fallback for standalone execution without env_resolver in sys.path
    REPO_ROOT = Path(r"C:\_Repositorio")
    PLANTILLA_DIR = REPO_ROOT / "G_Plantilla"

    def get_projects_dirs():
        return [REPO_ROOT / "G_Proyectos"]

    def list_ag_projects():
        d = get_projects_dirs()[0]
        return (
            sorted([p for p in d.iterdir() if p.is_dir() and p.name.startswith("G_")])
            if d.exists()
            else []
        )


INDEX_PATH = PLANTILLA_DIR / "docs" / "TASKS_INDEX.md"
COUNTER_PATH = PLANTILLA_DIR / "data" / "task_counter.json"

PRIORITY_MAP = {
    "critical": "P0-Critical",
    "high": "P1-High",
    "medium": "P2-Medium",
    "low": "P3-Low",
}

STATUS_MAP = {
    "pending": "PENDING",
    "in-progress": "IN-PROGRESS",
    "done": "DONE",
    "rejected": "REJECTED",
}

# Standard normalization checklist -- each item becomes a TASK
NORMALIZATION_CHECKLIST = [
    {
        "title": "Create/verify docs/TASKS.md (unified)",
        "description": "Ensure docs/TASKS.md exists with unified format: Local (Blocker/InProgress/Backlog) + Incoming/Outgoing/Completed",
        "priority": "high",
    },
    {
        "title": "Create/verify docs/DEVLOG.md",
        "description": "Ensure docs/DEVLOG.md exists with session entry format per output_governance.md",
        "priority": "high",
    },
    {
        "title": "Create/verify CHANGELOG.md",
        "description": "Ensure CHANGELOG.md exists in project root following Keep a Changelog format",
        "priority": "high",
    },
    {
        "title": "Create/verify GEMINI.md",
        "description": "Ensure GEMINI.md exists with project-specific agent instructions, complexity classifier, and sub-agent dispatch",
        "priority": "high",
    },
    {
        "title": "Create/verify .gitignore",
        "description": "Ensure .gitignore exists covering: .env, __pycache__, node_modules, *.db, .DS_Store, knowledge_vault.db",
        "priority": "medium",
    },
    {
        "title": "Create/verify docs/standards/output_governance.md",
        "description": "Ensure output governance standard is present with file creation rules, output routing table, and forbidden outputs",
        "priority": "medium",
    },
    {
        "title": "Security: verify no hardcoded credentials",
        "description": "Scan for hardcoded passwords, API keys, tokens. Replace with env vars or config references",
        "priority": "critical",
    },
    {
        "title": "Security: verify .env.example exists",
        "description": "Ensure .env.example lists all required env vars with placeholder values (never real credentials)",
        "priority": "medium",
    },
    {
        "title": "Git: initialize repo if missing",
        "description": "Ensure git repository is initialized. Run git init if needed, create initial commit",
        "priority": "high",
    },
    {
        "title": "Config: verify config/ directory structure",
        "description": "Ensure config/ directory exists for YAML/JSON configuration files. No config in project root",
        "priority": "low",
    },
    {
        "title": "README.md: verify project documentation",
        "description": "Ensure README.md exists with: project purpose, setup instructions, usage examples, architecture overview",
        "priority": "medium",
    },
]


# -- Helpers -------------------------------------------------------------------


def find_project_root(name: str) -> Path | None:
    """Find an AG project root by name."""
    if name == "G_Plantilla":
        return PLANTILLA_DIR

    for p_dir in get_projects_dirs():
        candidate = p_dir / name
        if candidate.is_dir():
            return candidate

    # Fuzzy match (case-insensitive)
    for p_dir in get_projects_dirs():
        if p_dir.is_dir():
            for d in p_dir.iterdir():
                if d.is_dir() and d.name.lower() == name.lower():
                    return d

    return None


def get_tasks_path(project_root: Path) -> Path:
    """Return the TASKS.md path for a project."""
    return project_root / "docs" / "TASKS.md"


def get_next_task_id() -> str:
    """Generate next sequential task ID for the current year."""
    year = datetime.now().year
    COUNTER_PATH.parent.mkdir(parents=True, exist_ok=True)

    if COUNTER_PATH.exists():
        data = json.loads(COUNTER_PATH.read_text(encoding="utf-8"))
    else:
        data = {}

    year_key = str(year)
    counter = data.get(year_key, 0) + 1
    data[year_key] = counter
    COUNTER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return f"TASK-{year}-{counter:04d}"


def ensure_tasks_file(tasks_path: Path, project_name: str) -> None:
    """Create TASKS.md if it doesn't exist (unified format)."""
    if tasks_path.exists():
        return

    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# Tasks -- {project_name}

> Unified task board: local work + cross-project delegation.
> Managed by `G_Plantilla/scripts/cross_task.py`.
>
> **Agents**: Check this file on session start for pending tasks.

## Local

### \U0001f534 Blocker

(none)

### \U0001f7e1 In Progress

(none)

### \U0001f4cb Backlog

(none)

## Incoming (tasks requested to this project)

(none)

## Outgoing (tasks delegated to other projects)

(none)

## Completed

(none)
"""
    tasks_path.write_text(content, encoding="utf-8")
    print(f"  [+] Created {tasks_path}")


def format_task_entry(
    task_id: str,
    title: str,
    from_project: str,
    to_project: str,
    priority: str,
    description: str,
    direction: str,
) -> str:
    """Format a task entry for TASKS.md."""
    now = datetime.now().strftime("%Y-%m-%d")
    priority_display = PRIORITY_MAP.get(priority, priority)

    lines = [f"### {task_id}: {title}"]
    if direction == "incoming":
        lines.append(f"- **From**: {from_project}")
    else:
        lines.append(f"- **To**: {to_project}")
    lines.append(f"- **Priority**: {priority_display}")
    lines.append("- **Status**: PENDING")
    lines.append(f"- **Created**: {now}")
    lines.append(f"- **Description**: {description}")
    lines.append("")

    return "\n".join(lines)


def insert_task(tasks_path: Path, task_entry: str, section: str) -> None:
    """Insert a task entry into the correct section of TASKS.md."""
    content = tasks_path.read_text(encoding="utf-8")

    if section == "incoming":
        marker_keywords = ["Incoming", "incoming"]
    else:
        marker_keywords = ["Outgoing", "outgoing"]

    lines = content.split("\n")
    insert_idx = None
    in_section = False

    for i, line in enumerate(lines):
        if line.startswith("##") and any(kw in line for kw in marker_keywords):
            in_section = True
            continue
        if in_section:
            if line.strip() == "(none)":
                lines[i] = task_entry
                tasks_path.write_text("\n".join(lines), encoding="utf-8")
                return
            if line.startswith("## "):
                insert_idx = i
                break

    if insert_idx is not None:
        lines.insert(insert_idx, task_entry)
        tasks_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        content += "\n" + task_entry
        tasks_path.write_text(content, encoding="utf-8")


def parse_tasks_from_file(tasks_path: Path) -> list[dict]:
    """Parse all tasks from a TASKS.md file."""
    if not tasks_path.exists():
        return []

    content = tasks_path.read_text(encoding="utf-8")
    tasks = []
    current_task = None
    current_section = None

    for line in content.split("\n"):
        stripped = line.strip().lower()
        if line.startswith("##") and "incoming" in stripped:
            current_section = "incoming"
        elif line.startswith("##") and "outgoing" in stripped:
            current_section = "outgoing"
        elif line.startswith("##") and "completed" in stripped:
            current_section = "completed"
        elif line.startswith("### TASK-"):
            if current_task:
                tasks.append(current_task)
            match = re.match(r"### (TASK-\d{4}-\d{4}): (.+)", line)
            if match:
                current_task = {
                    "id": match.group(1),
                    "title": match.group(2),
                    "section": current_section,
                    "project": tasks_path.parent.parent.name,
                    "fields": {},
                }
        elif current_task and line.startswith("- **"):
            match = re.match(r"- \*\*(.+?)\*\*: (.+)", line)
            if match:
                current_task["fields"][match.group(1).lower()] = match.group(2)

    if current_task:
        tasks.append(current_task)

    return tasks


# -- Commands ------------------------------------------------------------------


def cmd_create(args: argparse.Namespace) -> None:
    """Create a cross-project task."""
    from_root = find_project_root(args.from_project)
    to_root = find_project_root(args.to_project)

    if not from_root:
        print(f"[ERROR] Project not found: {args.from_project}")
        sys.exit(1)
    if not to_root:
        print(f"[ERROR] Project not found: {args.to_project}")
        sys.exit(1)
    if args.from_project == args.to_project:
        print("[ERROR] Source and target must be different projects")
        sys.exit(1)

    task_id = get_next_task_id()

    from_tasks = get_tasks_path(from_root)
    to_tasks = get_tasks_path(to_root)
    ensure_tasks_file(from_tasks, args.from_project)
    ensure_tasks_file(to_tasks, args.to_project)

    priority = args.priority or "medium"

    outgoing_entry = format_task_entry(
        task_id,
        args.title,
        args.from_project,
        args.to_project,
        priority,
        args.description,
        "outgoing",
    )
    incoming_entry = format_task_entry(
        task_id,
        args.title,
        args.from_project,
        args.to_project,
        priority,
        args.description,
        "incoming",
    )

    insert_task(from_tasks, outgoing_entry, "outgoing")
    print(f"  [+] Written to {from_tasks} (outgoing)")

    insert_task(to_tasks, incoming_entry, "incoming")
    print(f"  [+] Written to {to_tasks} (incoming)")

    update_index(task_id, args.title, args.from_project, args.to_project, priority)

    print(f"\n  Task created: {task_id}")
    print(f"  {args.title}")
    print(f"  {args.from_project} --> {args.to_project}")


def cmd_list(args: argparse.Namespace) -> None:
    """List tasks across the ecosystem."""
    all_tasks = []

    scan_dirs = [PLANTILLA_DIR]
    scan_dirs.extend(list_ag_projects())

    for project_dir in scan_dirs:
        tasks_path = get_tasks_path(project_dir)
        tasks = parse_tasks_from_file(tasks_path)
        all_tasks.extend(tasks)

    if args.project:
        all_tasks = [t for t in all_tasks if t["project"] == args.project]
    if args.status:
        status_key = STATUS_MAP.get(args.status, args.status)
        all_tasks = [
            t for t in all_tasks if status_key in t["fields"].get("status", "")
        ]

    seen = set()
    unique = []
    for t in all_tasks:
        key = (t["id"], t["section"])
        if key not in seen:
            seen.add(key)
            unique.append(t)

    if not unique:
        print("No tasks found.")
        return

    print(f"\nCross-Project Tasks ({len(unique)})\n")
    for t in unique:
        direction = "[IN]" if t["section"] == "incoming" else "[OUT]"
        status = t["fields"].get("status", "PENDING")
        from_to = t["fields"].get("from", t["fields"].get("to", "?"))
        print(f"  {direction} {t['id']}: {t['title']}")
        print(f"       {status} | {t['project']} <-> {from_to}")
        print()


def cmd_update(args: argparse.Namespace) -> None:
    """Update a task's status across all projects."""
    new_status = STATUS_MAP.get(args.status, args.status)
    now = datetime.now().strftime("%Y-%m-%d")
    updated_count = 0

    scan_dirs = [PLANTILLA_DIR]
    scan_dirs.extend(list_ag_projects())

    for project_dir in scan_dirs:
        tasks_path = get_tasks_path(project_dir)
        if not tasks_path.exists():
            continue

        content = tasks_path.read_text(encoding="utf-8")
        if args.task_id not in content:
            continue

        # Update status line
        content = re.sub(
            rf"(### {re.escape(args.task_id)}:.*?\n(?:- \*\*.*?\n)*?- \*\*Status\*\*: ).*",
            rf"\g<1>{new_status}",
            content,
        )

        # If done, move to Completed section
        if args.status == "done":
            task_pattern = rf"(### {re.escape(args.task_id)}:.*?)(?=\n### |\n## |\Z)"
            match = re.search(task_pattern, content, re.DOTALL)
            if match:
                task_block = match.group(1).rstrip()
                content = content.replace(match.group(0), "")
                # Insert into Completed section
                for marker in ["## Completed", "## completed"]:
                    if marker in content:
                        old = marker + "\n\n(none)"
                        if old in content:
                            content = content.replace(old, marker + "\n\n" + task_block)
                        else:
                            content = content.replace(
                                marker, marker + "\n\n" + task_block, 1
                            )
                        break

        while "\n\n\n" in content:
            content = content.replace("\n\n\n", "\n\n")

        tasks_path.write_text(content, encoding="utf-8")
        updated_count += 1
        print(f"  [+] Updated in {tasks_path}")

    if updated_count == 0:
        print(f"[ERROR] Task {args.task_id} not found in any project")
    else:
        print(f"\n  {args.task_id} --> {new_status}")
        if args.notes:
            print(f"  Notes: {args.notes}")


def cmd_dashboard(args: argparse.Namespace) -> None:
    """Show ecosystem-wide task dashboard."""
    all_tasks = []

    scan_dirs = [PLANTILLA_DIR]
    scan_dirs.extend(list_ag_projects())

    for project_dir in scan_dirs:
        tasks_path = get_tasks_path(project_dir)
        tasks = parse_tasks_from_file(tasks_path)
        all_tasks.extend(tasks)

    seen = set()
    unique = []
    for t in all_tasks:
        if t["id"] not in seen:
            seen.add(t["id"])
            unique.append(t)

    pending = [t for t in unique if "PENDING" in t["fields"].get("status", "PENDING")]
    in_progress = [t for t in unique if "IN-PROGRESS" in t["fields"].get("status", "")]
    done = [t for t in unique if "DONE" in t["fields"].get("status", "")]

    print("\n" + "=" * 60)
    print("  Antigravity Cross-Project Task Dashboard")
    print("=" * 60)
    print(f"\n  Pending:     {len(pending)}")
    print(f"  In Progress: {len(in_progress)}")
    print(f"  Done:        {len(done)}")
    print(f"  Total:       {len(unique)}")

    if pending:
        print(f"\n  -- Pending Tasks {'-' * 40}")
        for t in pending:
            from_to = t["fields"].get("from", t["fields"].get("to", "?"))
            print(f"  {t['id']}: {t['title']}")
            print(f"    {t['project']} <-> {from_to}")
    print()


def cmd_normalize(args: argparse.Namespace) -> None:
    """Generate normalization checklist as cross-project tasks."""
    target = args.project
    target_root = find_project_root(target)

    if not target_root:
        print(f"[ERROR] Project not found: {target}")
        sys.exit(1)

    if target == "G_Plantilla":
        print("[ERROR] Cannot normalize G_Plantilla (it IS the standard)")
        sys.exit(1)

    # Ensure TASKS.md exists in both projects
    target_tasks = get_tasks_path(target_root)
    ensure_tasks_file(target_tasks, target)
    plantilla_tasks = get_tasks_path(PLANTILLA_DIR)
    ensure_tasks_file(plantilla_tasks, "G_Plantilla")

    created_count = 0

    for item in NORMALIZATION_CHECKLIST:
        title = f"[NORM] {item['title']}"
        task_id = get_next_task_id()
        priority = item["priority"]

        outgoing_entry = format_task_entry(
            task_id,
            title,
            "G_Plantilla",
            target,
            priority,
            item["description"],
            "outgoing",
        )
        incoming_entry = format_task_entry(
            task_id,
            title,
            "G_Plantilla",
            target,
            priority,
            item["description"],
            "incoming",
        )

        insert_task(plantilla_tasks, outgoing_entry, "outgoing")
        insert_task(target_tasks, incoming_entry, "incoming")
        update_index(task_id, title, "G_Plantilla", target, priority)

        created_count += 1
        print(f"  [+] {task_id}: {item['title']}")

    print(f"\n  Normalization tasks created: {created_count}")
    print(f"  Target: {target}")
    print("  Source: G_Plantilla")
    print(f"\n  Run 'python cross_task.py list --project {target}' to see all tasks.")


def update_index(
    task_id: str, title: str, from_project: str, to_project: str, priority: str
) -> None:
    """Update the central TASKS_INDEX.md in G_Plantilla."""
    now = datetime.now().strftime("%Y-%m-%d")
    priority_display = PRIORITY_MAP.get(priority, priority)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not INDEX_PATH.exists():
        header = """# Tasks Index -- Antigravity Ecosystem

> Central registry of all cross-project tasks.
> Auto-generated by `scripts/cross_task.py`. Do not edit manually.

| ID | Title | From | To | Priority | Status | Created |
|----|-------|------|----|----------|--------|---------|
"""
        INDEX_PATH.write_text(header, encoding="utf-8")

    content = INDEX_PATH.read_text(encoding="utf-8")
    row = f"| {task_id} | {title} | {from_project} | {to_project} | {priority_display} | PENDING | {now} |"
    content = content.rstrip() + "\n" + row + "\n"
    INDEX_PATH.write_text(content, encoding="utf-8")
    print(f"  [+] Index updated: {INDEX_PATH}")


# -- Local + Check + Stale Commands -------------------------------------------


def cmd_check(args: argparse.Namespace) -> None:
    """Show all pending tasks for a project (local + incoming)."""
    project_name = args.project
    root = find_project_root(project_name)
    if not root:
        print(f"\u274c Project '{project_name}' not found.")
        sys.exit(1)

    tasks_path = get_tasks_path(root)
    if not tasks_path.exists():
        print(f"\u26a0\ufe0f No TASKS.md found for {project_name}")
        return

    content = tasks_path.read_text(encoding="utf-8")
    print(f"\n\U0001f4cb Tasks for {project_name}")
    print("=" * 50)

    # Parse Local section
    local_tasks = []
    in_local = False
    for line in content.splitlines():
        if line.strip().startswith("## Local"):
            in_local = True
            continue
        if in_local and line.strip().startswith("## "):
            break
        if in_local and line.strip().startswith("- ["):
            if "[x]" not in line.lower():
                local_tasks.append(line.strip())

    # Parse Incoming section
    incoming_tasks = []
    in_incoming = False
    for line in content.splitlines():
        if "Incoming" in line and line.strip().startswith("## "):
            in_incoming = True
            continue
        if in_incoming and line.strip().startswith("## "):
            break
        if in_incoming and line.strip().startswith("- ") and "(none)" not in line:
            if "PENDING" in line or "IN-PROGRESS" in line:
                incoming_tasks.append(line.strip())

    if local_tasks:
        print("\n\U0001f3e0 Local:")
        for t in local_tasks:
            print(f"  {t}")
    if incoming_tasks:
        print("\n\U0001f4e5 Incoming:")
        for t in incoming_tasks:
            print(f"  {t}")
    if not local_tasks and not incoming_tasks:
        print("\n\u2705 No pending tasks!")

    total = len(local_tasks) + len(incoming_tasks)
    print(f"\n  Total pending: {total}")


def cmd_stale(args: argparse.Namespace) -> None:
    """Detect tasks that have been PENDING for more than N days."""
    days = args.days
    cutoff = datetime.now()
    stale_found = []

    # Scan all projects
    all_dirs = []
    if PLANTILLA_DIR.is_dir():
        all_dirs.append(("G_Plantilla", PLANTILLA_DIR))
    for d in list_ag_projects():
        all_dirs.append((d.name, d))

    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")

    for proj_name, proj_root in all_dirs:
        tasks_path = get_tasks_path(proj_root)
        if not tasks_path.exists():
            continue

        content = tasks_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "PENDING" not in line:
                continue
            match = date_pattern.search(line)
            if match:
                try:
                    task_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                    age = (cutoff - task_date).days
                    if age > days:
                        stale_found.append((proj_name, age, line.strip()))
                except ValueError:
                    pass

    if stale_found:
        print(f"\n\u26a0\ufe0f  Stale tasks (>{days} days):")
        print("=" * 60)
        for proj, age, line in sorted(stale_found, key=lambda x: -x[1]):
            print(f"  [{proj}] {age}d old: {line}")
        print(f"\n  Total stale: {len(stale_found)}")
    else:
        print(f"\n\u2705 No stale tasks (all PENDING < {days} days)")


# -- CLI -----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-Workspace Task Delegation -- Antigravity Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create --from G_NB_Apps --to G_Consultas --title "Create census query" --description "..."
  %(prog)s list --project G_Consultas --status pending
  %(prog)s update TASK-2026-0001 --status done --notes "Query delivered"
  %(prog)s check G_Hospital
  %(prog)s stale
  %(prog)s dashboard
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a cross-project task")
    p_create.add_argument(
        "--from", dest="from_project", required=True, help="Source project name"
    )
    p_create.add_argument(
        "--to", dest="to_project", required=True, help="Target project name"
    )
    p_create.add_argument("--title", required=True, help="Task title")
    p_create.add_argument("--description", required=True, help="Task description")
    p_create.add_argument(
        "--priority", choices=["critical", "high", "medium", "low"], default="medium"
    )

    # list
    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--project", help="Filter by project name")
    p_list.add_argument(
        "--status", choices=["pending", "in-progress", "done", "rejected"]
    )

    # update
    p_update = sub.add_parser("update", help="Update a task's status")
    p_update.add_argument("task_id", help="Task ID (e.g., TASK-2026-0001)")
    p_update.add_argument(
        "--status",
        required=True,
        choices=["pending", "in-progress", "done", "rejected"],
    )
    p_update.add_argument("--notes", help="Optional notes about the update")

    # dashboard
    sub.add_parser("dashboard", help="Show ecosystem-wide dashboard")

    # normalize
    p_normalize = sub.add_parser(
        "normalize", help="Generate normalization checklist as tasks for a project"
    )
    p_normalize.add_argument("project", help="Target project name (e.g., G_MyProject)")

    # check (NEW)
    p_check = sub.add_parser(
        "check", help="Show pending tasks for a project (local + incoming)"
    )
    p_check.add_argument("project", help="Project name (e.g., G_Hospital)")

    # stale (NEW)
    p_stale = sub.add_parser("stale", help="Detect PENDING tasks older than N days")
    p_stale.add_argument(
        "--days", type=int, default=14, help="Days threshold (default: 14)"
    )

    args = parser.parse_args()

    commands = {
        "create": cmd_create,
        "list": cmd_list,
        "update": cmd_update,
        "dashboard": cmd_dashboard,
        "normalize": cmd_normalize,
        "check": cmd_check,
        "stale": cmd_stale,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
