"""
Template Sync — G_Plantilla
Syncs core files from project root to _global-profile/ and _template/workspace/.

Usage:
    python scripts/template_sync.py            # Dry run (shows what would be synced)
    python scripts/template_sync.py --apply     # Actually sync files
"""

import shutil
import sys
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent.parent

# Files/dirs to sync to both _global-profile and _template/workspace
SYNC_TARGETS = [
    # Universal rules
    ".agent/rules/project-rules.md",
    ".agent/rules/session-protocol.md",
    # Universal skills
    ".agent/skills/session-management.md",
    ".agent/skills/deep-research.md",
    ".agent/skills/project-init.md",
    # Universal workflows
    ".agent/workflows/turbo-ops.md",
    ".agent/workflows/deep-research-update.md",
    # Subagent manifest + dispatch
    ".subagents/manifest.json",
    ".subagents/dispatch.sh",
    ".subagents/dispatch.ps1",
    # Root instruction files
    "GEMINI.md",
    "CLAUDE.md",
    "AGENTS.md",
    # Standards
    "docs/standards/output_governance.md",
]

DESTINATIONS = [
    PROJECT_ROOT / "_global-profile",
    PROJECT_ROOT / "_template" / "workspace",
]


def sync_files(dry_run: bool = True) -> int:
    """Sync files to template directories."""
    synced = 0

    for rel_path in SYNC_TARGETS:
        src = PROJECT_ROOT / rel_path
        if not src.exists():
            print(f"  ⚠️  SKIP (not found): {rel_path}")
            continue

        for dest_root in DESTINATIONS:
            dest = dest_root / rel_path
            dest_label = str(dest_root.relative_to(PROJECT_ROOT))

            # Check if file needs update
            needs_update = True
            if dest.exists():
                src_content = src.read_bytes()
                dest_content = dest.read_bytes()
                if src_content == dest_content:
                    needs_update = False

            if needs_update:
                if dry_run:
                    action = "CREATE" if not dest.exists() else "UPDATE"
                    print(f"  [{action}] {dest_label}/{rel_path}")
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    action = "CREATED" if not dest.exists() else "UPDATED"
                    print(f"  ✅ [{action}] {dest_label}/{rel_path}")
                synced += 1

    return synced


def main():
    dry_run = "--apply" not in sys.argv

    print("🔄 Template Sync — G_Plantilla")
    print("=" * 40)

    if dry_run:
        print("📋 DRY RUN (use --apply to sync)")
    else:
        print("🚀 APPLYING changes")

    print()
    count = sync_files(dry_run)

    print()
    if count == 0:
        print("✅ Everything is in sync!")
    elif dry_run:
        print(f"📋 {count} files would be synced. Run with --apply to execute.")
    else:
        print(f"✅ {count} files synced successfully.")


if __name__ == "__main__":
    main()
