"""
Knowledge Sync — G_Plantilla
Replaces the primitive memory_sync.py with structured knowledge extraction.

Usage:
    python scripts/knowledge_sync.py              # Full sync
    python scripts/knowledge_sync.py --snapshot    # Generate context snapshot only
    python scripts/knowledge_sync.py --index       # Update memory index only
"""

import datetime
import re
import sys as _sys
from pathlib import Path

# Add project src/ to path for vault import
_sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from core.vault import KnowledgeVault

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DEVLOG_PATH = PROJECT_ROOT / "docs" / "DEVLOG.md"
TODO_PATH = PROJECT_ROOT / "docs" / "TODO.md"
BRAIN_PATH = PROJECT_ROOT / ".gemini" / "brain"
EPISODES_PATH = BRAIN_PATH / "episodes"
MEMORY_INDEX = BRAIN_PATH / "memory-index.md"
SNAPSHOT_PATH = BRAIN_PATH / "context-snapshot.md"
CHANGELOG_PATH = PROJECT_ROOT / "CHANGELOG.md"


def parse_devlog_latest() -> dict:
    """Extract the latest session entry from DEVLOG.md."""
    if not DEVLOG_PATH.exists():
        return {"date": "unknown", "topic": "none", "accomplished": [], "decisions": []}

    content = DEVLOG_PATH.read_text(encoding="utf-8")
    # Match ## YYYY-MM-DD sections
    sessions = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", content, flags=re.MULTILINE)
    sessions = [s.strip() for s in sessions if s.strip() and s.startswith("## 20")]

    if not sessions:
        return {"date": "unknown", "topic": "none", "accomplished": [], "decisions": []}

    latest = sessions[0]
    # Extract date and topic
    header_match = re.match(r"## (\d{4}-\d{2}-\d{2}).*?\((.*?)\)", latest)
    date = header_match.group(1) if header_match else "unknown"
    topic = header_match.group(2) if header_match else "unknown"

    # Extract accomplishments
    accomplished = []
    acc_match = re.search(r"### Accomplished\s*\n((?:- .*\n?)*)", latest)
    if acc_match:
        accomplished = [
            line.strip("- ").strip()
            for line in acc_match.group(1).strip().split("\n")
            if line.strip()
        ]

    # Extract decisions
    decisions = []
    dec_match = re.search(r"### Decisions\s*\n((?:- .*\n?)*)", latest)
    if dec_match:
        decisions = [
            line.strip("- ").strip()
            for line in dec_match.group(1).strip().split("\n")
            if line.strip()
        ]

    return {
        "date": date,
        "topic": topic,
        "accomplished": accomplished,
        "decisions": decisions,
    }


def parse_devlog_all() -> list[dict]:
    """Extract ALL session entries from DEVLOG.md."""
    if not DEVLOG_PATH.exists():
        return []

    content = DEVLOG_PATH.read_text(encoding="utf-8")
    sessions_raw = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", content, flags=re.MULTILINE)
    sessions_raw = [s.strip() for s in sessions_raw if s.strip() and s.startswith("## 20")]

    sessions = []
    for raw in sessions_raw:
        header_match = re.match(r"## (\d{4}-\d{2}-\d{2}).*?\((.*?)\)", raw)
        date = header_match.group(1) if header_match else "unknown"
        topic = header_match.group(2) if header_match else "unknown"

        accomplished = []
        acc_match = re.search(r"### Accomplished\s*\n((?:(?:\d+\.|-).*\n?)*)", raw)
        if acc_match:
            accomplished = [
                re.sub(r"^\d+\.\s*|-\s*", "", line).strip()
                for line in acc_match.group(1).strip().split("\n")
                if line.strip()
            ]

        decisions = []
        dec_match = re.search(
            r"### (?:Decisions|Architecture Decisions|Key Decisions)\s*\n((?:(?:\d+\.|-).*\n?)*)",
            raw,
        )
        if dec_match:
            decisions = [
                re.sub(r"^\d+\.\s*|-\s*", "", line).strip()
                for line in dec_match.group(1).strip().split("\n")
                if line.strip()
            ]

        metrics = []
        met_match = re.search(r"### Metrics\s*\n((?:- .*\n?)*)", raw)
        if met_match:
            metrics = [
                line.strip("- ").strip()
                for line in met_match.group(1).strip().split("\n")
                if line.strip()
            ]

        sessions.append(
            {
                "date": date,
                "topic": topic,
                "accomplished": accomplished,
                "decisions": decisions,
                "metrics": metrics,
                "raw": raw,
            }
        )

    return sessions


def sync_to_vault() -> None:
    """Store all parsed DEVLOG sessions into the Knowledge Vault (SQLite)."""
    vault = KnowledgeVault(str(PROJECT_ROOT))
    sessions = parse_devlog_all()

    total_stored = 0
    for session in sessions:
        entries = []
        for item in session["accomplished"]:
            entries.append({"entry_type": "accomplished", "content": item})
        for item in session["decisions"]:
            entries.append({"entry_type": "decision", "content": item})
        for item in session.get("metrics", []):
            entries.append({"entry_type": "metric", "content": item})

        stored = vault.store_session(session["date"], session["topic"], entries)
        total_stored += stored

    print(f"  Vault: {total_stored} new entries stored ({len(sessions)} sessions processed)")


def parse_todo() -> dict:
    """Extract current TODO state."""
    if not TODO_PATH.exists():
        return {"blockers": [], "in_progress": [], "backlog": []}

    content = TODO_PATH.read_text(encoding="utf-8")
    result = {"blockers": [], "in_progress": [], "backlog": []}

    current_section = None
    for line in content.split("\n"):
        lower = line.lower()
        if "blocker" in lower:
            current_section = "blockers"
        elif "in progress" in lower or "inprogress" in lower:
            current_section = "in_progress"
        elif "backlog" in lower:
            current_section = "backlog"
        elif "done" in lower:
            current_section = None  # Skip done items

        if current_section and line.strip().startswith("- "):
            task = line.strip("- ").strip()
            if task:
                result[current_section].append(task)

    return result


def generate_snapshot(devlog: dict, todo: dict) -> str:
    """Generate a compact context snapshot (<50 lines)."""
    today = datetime.date.today().isoformat()
    lines = [
        f"# Context Snapshot — {today}",
        "",
        f"## Last Session: {devlog['date']} ({devlog['topic']})",
        "",
    ]

    if devlog["accomplished"]:
        lines.append("### Accomplished")
        for item in devlog["accomplished"][:5]:
            lines.append(f"- {item}")
        lines.append("")

    if devlog["decisions"]:
        lines.append("### Key Decisions")
        for item in devlog["decisions"][:3]:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## Current State")
    lines.append("")

    if todo["blockers"]:
        lines.append(f"### 🔴 Blockers ({len(todo['blockers'])})")
        for item in todo["blockers"]:
            lines.append(f"- {item}")
        lines.append("")

    if todo["in_progress"]:
        lines.append(f"### 🟡 In Progress ({len(todo['in_progress'])})")
        for item in todo["in_progress"]:
            lines.append(f"- {item}")
        lines.append("")

    if todo["backlog"]:
        lines.append(f"### 📋 Backlog ({len(todo['backlog'])})")
        for item in todo["backlog"][:5]:
            lines.append(f"- {item}")
        if len(todo["backlog"]) > 5:
            lines.append(f"- ... and {len(todo['backlog']) - 5} more")
        lines.append("")

    return "\n".join(lines)


def update_memory_index(devlog: dict) -> None:
    """Add latest session to memory-index.md."""
    if devlog["date"] == "unknown":
        print("⚠️  No session data to index")
        return

    if not MEMORY_INDEX.exists():
        print("⚠️  Memory index not found, creating...")
        MEMORY_INDEX.parent.mkdir(parents=True, exist_ok=True)

    content = MEMORY_INDEX.read_text(encoding="utf-8") if MEMORY_INDEX.exists() else ""

    # Check if entry already exists
    if devlog["date"] in content:
        print(f"ℹ️  Entry for {devlog['date']} already exists in index")
        return

    entry = f"""
### {devlog['date']} — {devlog['topic']}
- **Session**: {devlog['topic']}
- **Key learnings**:
"""
    for item in devlog["accomplished"][:3]:
        entry += f"  - {item}\n"
    if devlog["decisions"]:
        entry += "- **Decisions made**:\n"
        for item in devlog["decisions"][:3]:
            entry += f"  - {item}\n"

    # Insert after ## Memory Entries
    if "## Memory Entries" in content:
        content = content.replace("## Memory Entries\n", f"## Memory Entries\n{entry}")
    else:
        content += f"\n{entry}"

    MEMORY_INDEX.write_text(content, encoding="utf-8")
    print(f"✅ Memory index updated with {devlog['date']} entry")


def save_episode(devlog: dict) -> None:
    """Save structured episode file."""
    EPISODES_PATH.mkdir(parents=True, exist_ok=True)
    episode_file = EPISODES_PATH / f"session_{devlog['date']}.md"

    episode_content = f"""# Session: {devlog['date']} — {devlog['topic']}

## Accomplished
"""
    for item in devlog["accomplished"]:
        episode_content += f"- {item}\n"

    if devlog["decisions"]:
        episode_content += "\n## Decisions\n"
        for item in devlog["decisions"]:
            episode_content += f"- {item}\n"

    episode_file.write_text(episode_content, encoding="utf-8")
    print(f"✅ Episode saved: {episode_file.name}")


def generate_devlog_from_git(topic: str = "Session") -> None:
    """Generate a DEVLOG entry from recent git commits."""
    import subprocess

    today = datetime.date.today().isoformat()

    # Get recent commits (since beginning of day or last 10)
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"--since={today} 00:00", "--no-decorate"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        commits = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except FileNotFoundError:
        print("[!] git not found")
        return

    if not commits:
        # Fallback: last 10 commits
        result = subprocess.run(
            ["git", "log", "--oneline", "-10", "--no-decorate"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        commits = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

    if not commits:
        print("[!] No commits found")
        return

    # Get diff stats
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD~" + str(len(commits)), "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    stats_line = result.stdout.strip().split("\n")[-1] if result.stdout.strip() else ""

    # Parse commits into categories
    feats, fixes, docs, others = [], [], [], []
    for commit in commits:
        # Remove hash prefix
        msg = commit.split(" ", 1)[1] if " " in commit else commit
        if msg.startswith("feat"):
            feats.append(msg)
        elif msg.startswith("fix"):
            fixes.append(msg)
        elif msg.startswith("docs"):
            docs.append(msg)
        else:
            others.append(msg)

    # Build entry
    entry_lines = [
        f"\n## {today} (Session: {topic})",
        "",
        "### Accomplished",
    ]

    for msg in feats:
        entry_lines.append(f"- {msg}")
    for msg in fixes:
        entry_lines.append(f"- {msg}")
    for msg in docs:
        entry_lines.append(f"- {msg}")
    for msg in others:
        entry_lines.append(f"- {msg}")

    entry_lines.append("")
    entry_lines.append("### Metrics")
    entry_lines.append(f"- Commits: {len(commits)}")
    if stats_line:
        entry_lines.append(f"- {stats_line.strip()}")
    entry_lines.append("")

    entry_text = "\n".join(entry_lines)

    # Read existing DEVLOG
    content = DEVLOG_PATH.read_text(encoding="utf-8") if DEVLOG_PATH.exists() else "# DEVLOG\n"

    # Check if today already has an entry
    if f"## {today}" in content:
        print(f"[i] DEVLOG already has entry for {today}, skipping")
        print(entry_text)
        return

    # Insert after the first heading line
    lines = content.split("\n")
    insert_idx = 1  # After first line
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_idx = i + 1
            break

    lines.insert(insert_idx, entry_text)
    DEVLOG_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[+] DEVLOG entry generated for {today}")
    print(entry_text)


def generate_team_context(description: str) -> None:
    """Generate a shared context file for agent team members.

    Combines context-snapshot + task description + recent vault sessions
    into .subagents/_team_context.md for team members to read.
    """
    team_context_path = PROJECT_ROOT / ".subagents" / "_team_context.md"
    today = datetime.date.today().isoformat()

    lines = [
        f"# Team Context — {today}",
        "",
        "## Task Description",
        "",
        description,
        "",
    ]

    # Include context snapshot if available
    if SNAPSHOT_PATH.exists():
        snapshot = SNAPSHOT_PATH.read_text(encoding="utf-8")
        lines.extend(["## Project Context", "", snapshot, ""])
    else:
        lines.extend(
            [
                "## Project Context",
                "",
                "(No context snapshot available. Run `python scripts/knowledge_sync.py --snapshot` first.)",
                "",
            ]
        )

    # Include recent vault entries if database exists
    db_path = PROJECT_ROOT / "data" / "knowledge_vault.db"
    if db_path.exists():
        try:
            vault = KnowledgeVault(str(PROJECT_ROOT))
            recent = vault.get_recent_sessions(3)
            if recent:
                lines.append("## Recent Session History")
                lines.append("")
                current_date = ""
                for r in recent:
                    if r["session_date"] != current_date:
                        current_date = r["session_date"]
                        lines.append(f"### {r['session_date']} ({r['topic']})")
                    lines.append(f"- [{r['entry_type']}] {r['content']}")
                lines.append("")
        except Exception:
            pass  # Vault not ready, skip

    lines.extend(["---", f"*Generated: {today} by knowledge_sync.py*"])

    team_context_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Team context saved: {team_context_path}")


def cleanup_team_context() -> None:
    """Remove the temporary team context file."""
    team_context_path = PROJECT_ROOT / ".subagents" / "_team_context.md"
    if team_context_path.exists():
        team_context_path.unlink()
        print(f"Team context removed: {team_context_path}")
    else:
        print("[i] No team context file to clean up")


def compact_devlog(keep_recent: int = 10) -> None:
    """Compact DEVLOG.md by archiving older sessions.

    Keeps the N most recent sessions in DEVLOG.md.
    Older sessions get summarized (1-line) and moved to docs/DEVLOG_archive.md.
    Original detailed sessions are preserved in .gemini/brain/episodes/.
    """
    if not DEVLOG_PATH.exists():
        print("[!] DEVLOG.md not found")
        return

    sessions = parse_devlog_all()

    if len(sessions) <= keep_recent:
        print(
            f"[i] DEVLOG has {len(sessions)} sessions (threshold: {keep_recent}), no compaction needed"
        )
        return

    recent = sessions[:keep_recent]
    older = sessions[keep_recent:]

    print(f"[i] Compacting: keeping {len(recent)} recent, archiving {len(older)} older sessions")

    # 1. Ensure all older sessions have episode files saved
    for session in older:
        save_episode(session)

    # 2. Build summary lines for the archive
    archive_path = PROJECT_ROOT / "docs" / "DEVLOG_archive.md"
    archive_header = (
        "# DEVLOG Archive\n\n> Compacted sessions. Full details in `.gemini/brain/episodes/`.\n\n"
    )

    existing_archive = ""
    if archive_path.exists():
        existing_archive = archive_path.read_text(encoding="utf-8")

    new_summaries = []
    for session in older:
        summary_line = "(no accomplishments recorded)"
        if session["accomplished"]:
            first = session["accomplished"][0]
            first = re.sub(r"\*\*(.*?)\*\*", r"\1", first)
            summary_line = first[:100] + ("..." if len(first) > 100 else "")

        entry = f"- **{session['date']}** ({session['topic']}): {summary_line}"

        if session["date"] not in existing_archive:
            new_summaries.append(entry)

    if new_summaries:
        if not existing_archive:
            archive_content = archive_header + "\n".join(new_summaries) + "\n"
        else:
            lines = existing_archive.split("\n")
            insert_idx = len(lines)
            for i, line in enumerate(lines):
                if line.startswith("- **"):
                    insert_idx = i
                    break

            for j, summary in enumerate(new_summaries):
                lines.insert(insert_idx + j, summary)
            archive_content = "\n".join(lines)

        archive_path.write_text(archive_content, encoding="utf-8")
        print(f"  Archived {len(new_summaries)} sessions to {archive_path.name}")

    # 3. Rebuild DEVLOG.md with only recent sessions
    new_devlog = "# Development Log\n"
    for session in recent:
        new_devlog += "\n" + session["raw"] + "\n"

    DEVLOG_PATH.write_text(new_devlog, encoding="utf-8")
    print(f"  DEVLOG.md trimmed to {len(recent)} sessions")
    print("  Original entries preserved in .gemini/brain/episodes/")


def main():
    import sys

    # Fix Windows encoding
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print("🧠 Knowledge Sync — G_Plantilla")
    print("=" * 40)

    # Parse sources
    devlog = parse_devlog_latest()
    todo = parse_todo()

    if "--snapshot" in sys.argv:
        snapshot = generate_snapshot(devlog, todo)
        SNAPSHOT_PATH.write_text(snapshot, encoding="utf-8")
        print(f"✅ Snapshot saved: {SNAPSHOT_PATH}")
        print(snapshot)
        return

    if "--index" in sys.argv:
        update_memory_index(devlog)
        return

    if "--devlog" in sys.argv:
        # Extract topic from args: --devlog "My Topic"
        topic = "Session"
        try:
            idx = sys.argv.index("--devlog")
            if idx + 1 < len(sys.argv):
                topic = sys.argv[idx + 1]
        except (ValueError, IndexError):
            pass
        generate_devlog_from_git(topic)
        return

    if "--query" in sys.argv:
        try:
            idx = sys.argv.index("--query")
            if idx + 1 < len(sys.argv):
                search_term = sys.argv[idx + 1]
            else:
                print('Usage: --query "search term"')
                return
        except (ValueError, IndexError):
            print('Usage: --query "search term"')
            return

        vault = KnowledgeVault(str(PROJECT_ROOT))
        results = vault.search_sessions(search_term)
        if not results:
            print(f"No results found for: {search_term}")
            return

        print(f'Found {len(results)} results for "{search_term}":\n')
        current_date = ""
        for r in results:
            if r["session_date"] != current_date:
                current_date = r["session_date"]
                print(f"\n## {r['session_date']} ({r['topic']})")
            print(f"  [{r['entry_type']}] {r['content']}")
        return

    if "--compact" in sys.argv:
        compact_devlog(keep_recent=10)
        return

    if "--team-context" in sys.argv:
        try:
            idx = sys.argv.index("--team-context")
            if idx + 1 < len(sys.argv):
                description = sys.argv[idx + 1]
            else:
                print('Usage: --team-context "task description"')
                return
        except (ValueError, IndexError):
            print('Usage: --team-context "task description"')
            return
        generate_team_context(description)
        return

    if "--team-cleanup" in sys.argv:
        cleanup_team_context()
        return

    # Full sync
    print(f"\n📖 Latest session: {devlog['date']} ({devlog['topic']})")
    print(
        f"📋 TODO: {len(todo['blockers'])} blockers, {len(todo['in_progress'])} in-progress, {len(todo['backlog'])} backlog"
    )

    # 1. Save episode
    save_episode(devlog)

    # 2. Update memory index
    update_memory_index(devlog)

    # 3. Sync to vault (SQLite)
    sync_to_vault()

    # 4. Generate context snapshot
    snapshot = generate_snapshot(devlog, todo)
    SNAPSHOT_PATH.write_text(snapshot, encoding="utf-8")
    print(f"✅ Snapshot saved: {SNAPSHOT_PATH}")

    print("\n🎯 Sync complete!")


if __name__ == "__main__":
    main()
