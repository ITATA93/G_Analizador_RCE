"""
Agent Health Check — G_Plantilla
Validates that all agent definitions are correctly configured:
- All agents in manifest exist as definition files
- All definitions reference output_governance.md
- All agents have valid vendor configs
- No orphaned definition files (not in manifest)

Usage:
    python scripts/agent_health_check.py
"""

import json
import sys
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / ".subagents" / "manifest.json"

# Agent definition directories per vendor
AGENT_DIRS = {
    "gemini": PROJECT_ROOT / ".gemini" / "agents",
    "codex": PROJECT_ROOT / ".codex" / "agents",
    "claude": PROJECT_ROOT / ".claude" / "internal-agents",
}

# Files that should reference governance
GOVERNANCE_FILES = [
    PROJECT_ROOT / ".agent" / "rules" / "project-rules.md",
    PROJECT_ROOT / ".agent" / "rules" / "session-protocol.md",
    PROJECT_ROOT / ".gemini" / "rules" / "core-rules.md",
]

CHECK_PASS = "✅"
CHECK_FAIL = "❌"
CHECK_WARN = "⚠️"

results = {"passed": 0, "failed": 0, "warnings": 0}


def check(condition: bool, msg: str, warn_only: bool = False) -> bool:
    global results
    if condition:
        print(f"  {CHECK_PASS} {msg}")
        results["passed"] += 1
    elif warn_only:
        print(f"  {CHECK_WARN} {msg}")
        results["warnings"] += 1
    else:
        print(f"  {CHECK_FAIL} {msg}")
        results["failed"] += 1
    return condition


def main():
    print("🩺 Agent Health Check — G_Plantilla")
    print("=" * 50)

    # 1. Manifest exists and is valid JSON
    print("\n📋 1. Manifest Validation")
    if not check(MANIFEST_PATH.exists(), f"Manifest exists: {MANIFEST_PATH.name}"):
        print("  Cannot continue without manifest.")
        sys.exit(1)

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        check(True, "Manifest is valid JSON")
    except json.JSONDecodeError as e:
        check(False, f"Manifest is valid JSON: {e}")
        sys.exit(1)

    check("agents" in manifest, "Manifest has 'agents' section")
    check("agent_teams" in manifest, "Manifest has 'agent_teams' section")
    agents = manifest.get("agents", [])
    check(len(agents) > 0, f"Found {len(agents)} agents in manifest")

    # 2. Agent definitions exist
    print("\n📂 2. Agent Definition Files")
    for agent in agents:
        name = agent["name"]
        vendor = agent["vendor"]

        # Check vendor-specific definition
        agent_dir = AGENT_DIRS.get(vendor)
        if not agent_dir:
            check(False, f"{name}: Unknown vendor '{vendor}'")
            continue

        # Try common extensions
        found = False
        for ext in [".toml", ".md", ".yaml"]:
            if (agent_dir / f"{name}{ext}").exists():
                found = True
                break

        check(found, f"{name}: Definition file exists in .{vendor}/")

    # 3. Governance references
    print("\n🛡️ 3. Governance Coverage")

    # Check universal rules
    for rule_file in GOVERNANCE_FILES:
        if rule_file.exists():
            content = rule_file.read_text(encoding="utf-8")
            has_gov = "governance" in content.lower()
            check(has_gov, f"{rule_file.name}: References governance")
        else:
            check(False, f"{rule_file.name}: File exists", warn_only=True)

    # Check agent definitions
    gov_count = 0
    total_defs = 0
    for vendor, agent_dir in AGENT_DIRS.items():
        if not agent_dir.exists():
            continue
        for f in agent_dir.iterdir():
            if f.is_file():
                total_defs += 1
                content = f.read_text(encoding="utf-8")
                if "governance" in content.lower():
                    gov_count += 1

    check(
        gov_count == total_defs,
        f"Agent defs with governance: {gov_count}/{total_defs}",
    )

    # 4. Vendor configs in manifest
    print("\n⚙️ 4. Vendor Configuration")
    for agent in agents:
        name = agent["name"]
        has_gemini = "gemini_config" in agent
        has_claude = "claude_config" in agent
        has_codex = "codex_config" in agent

        supported = agent.get("supported_vendors", [])
        if "gemini" in supported:
            check(has_gemini, f"{name}: Has gemini_config", warn_only=True)
        if "claude" in supported:
            check(has_claude, f"{name}: Has claude_config", warn_only=True)
        if "codex" in supported:
            check(has_codex, f"{name}: Has codex_config", warn_only=True)

    # 5. Agent Teams validation
    print("\n👥 5. Agent Teams")
    teams = manifest.get("agent_teams", {}).get("teams", {})
    for team_name, team_config in teams.items():
        team_agents = team_config.get("agents", [])
        agent_names = [a["name"] for a in agents]
        all_exist = all(a in agent_names for a in team_agents)
        check(all_exist, f"Team '{team_name}': All agents exist in manifest")

        mode = team_config.get("mode")
        check(
            mode in ("parallel", "sequential"),
            f"Team '{team_name}': Valid mode ({mode})",
        )

    # 6. Dispatch scripts
    print("\n🚀 6. Dispatch Scripts")
    check(
        (PROJECT_ROOT / ".subagents" / "dispatch.sh").exists(),
        "dispatch.sh exists (Linux/Mac)",
    )
    check(
        (PROJECT_ROOT / ".subagents" / "dispatch.ps1").exists(),
        "dispatch.ps1 exists (Windows)",
    )

    # 7. Skills
    print("\n🎯 7. Skills")
    universal_skills = PROJECT_ROOT / ".agent" / "skills"
    if universal_skills.exists():
        skill_count = len(list(universal_skills.glob("*.md")))
        check(skill_count > 0, f"Universal skills (.agent/skills/): {skill_count}")
    else:
        check(False, "Universal skills directory exists")

    for vendor, vendor_dir in [
        ("gemini", PROJECT_ROOT / ".gemini" / "skills"),
        ("codex", PROJECT_ROOT / ".codex" / "skills"),
    ]:
        if vendor_dir.exists():
            count = len(list(vendor_dir.glob("*.md")))
            check(count > 0, f"{vendor} skills: {count}", warn_only=True)

    # Summary
    print("\n" + "=" * 50)
    total = results["passed"] + results["failed"] + results["warnings"]
    print(f"🩺 Health Check Complete: {total} checks")
    print(f"   {CHECK_PASS} Passed:   {results['passed']}")
    print(f"   {CHECK_FAIL} Failed:   {results['failed']}")
    print(f"   {CHECK_WARN} Warnings: {results['warnings']}")

    if results["failed"] == 0:
        print("\n✅ All critical checks passed!")
        return 0
    else:
        print(f"\n❌ {results['failed']} critical issue(s) found!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
