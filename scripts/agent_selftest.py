#!/usr/bin/env python3
"""
Agent Self-Test — Antigravity Ecosystem
=========================================

Verifies that each project has the infrastructure for autonomous agent work.
Checks dispatch scripts, sub-agent manifests, workflows, memory, and session protocol.

Usage:
    python scripts/agent_selftest.py                    # Full ecosystem test
    python scripts/agent_selftest.py --project AG_Hospital  # Single project
"""

import argparse
import json
import sys
from pathlib import Path

# -- Configuration -------------------------------------------------------------

REPO_ROOT = Path(r"C:\_Repositorio")
PROJECTS_DIR = REPO_ROOT / "AG_Proyectos"
PLANTILLA_DIR = REPO_ROOT / "AG_Plantilla"
REGISTRY_PATH = PLANTILLA_DIR / "config" / "project_registry.json"


# -- Helpers -------------------------------------------------------------------


def get_projects(filter_name: str | None = None) -> list[tuple[str, Path]]:
    """Return AG projects, optionally filtered."""
    projects = []
    if not filter_name or filter_name == "AG_Plantilla":
        if PLANTILLA_DIR.is_dir():
            projects.append(("AG_Plantilla", PLANTILLA_DIR))
    if PROJECTS_DIR.is_dir():
        for d in sorted(PROJECTS_DIR.iterdir()):
            if not d.is_dir() or not d.name.startswith("AG_"):
                continue
            if filter_name and d.name != filter_name:
                continue
            projects.append((d.name, d))
    return projects


def load_registry() -> dict:
    """Load project registry."""
    if REGISTRY_PATH.is_file():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {}


# -- Test Categories -----------------------------------------------------------


def test_dispatch(project_dir: Path) -> dict:
    """Test dispatch infrastructure."""
    results = {}

    # Check dispatch scripts
    ps1 = project_dir / ".subagents" / "dispatch.ps1"
    sh = project_dir / ".subagents" / "dispatch.sh"
    results["dispatch_script"] = ps1.is_file() or sh.is_file()

    # Check manifest
    manifest = project_dir / ".subagents" / "manifest.json"
    results["manifest_exists"] = manifest.is_file()
    results["manifest_valid"] = False
    results["agent_count"] = 0

    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            agents = data.get("agents", [])
            results["manifest_valid"] = len(agents) > 0
            results["agent_count"] = len(agents)
        except (json.JSONDecodeError, KeyError):
            pass

    return results


def test_workflows(project_dir: Path) -> dict:
    """Test workflow infrastructure."""
    results = {}

    wf_dir = project_dir / ".agent" / "workflows"
    results["workflows_dir"] = wf_dir.is_dir()
    results["workflow_count"] = 0

    if wf_dir.is_dir():
        wf_files = list(wf_dir.glob("*.md"))
        results["workflow_count"] = len(wf_files)

        # Check frontmatter validity
        valid = 0
        for wf in wf_files:
            content = wf.read_text(encoding="utf-8", errors="replace")
            if content.startswith("---") and "description:" in content:
                valid += 1
        results["valid_workflows"] = valid

    # Check rules
    rules_dir = project_dir / ".agent" / "rules"
    results["rules_dir"] = rules_dir.is_dir()
    results["session_protocol"] = (rules_dir / "session-protocol.md").is_file() if rules_dir.is_dir() else False

    return results


def test_memory(project_dir: Path) -> dict:
    """Test memory infrastructure."""
    results = {}

    gemini_dir = project_dir / ".gemini"
    results["gemini_dir"] = gemini_dir.is_dir()

    brain_dir = gemini_dir / "brain"
    results["brain_dir"] = brain_dir.is_dir()

    # Check for skills
    skills_dir = gemini_dir / "skills"
    results["skills_dir"] = skills_dir.is_dir()
    results["skill_count"] = len(list(skills_dir.glob("**/SKILL.md"))) if skills_dir.is_dir() else 0

    return results


def test_governance(project_dir: Path) -> dict:
    """Test governance and documentation quality."""
    results = {}

    # GEMINI.md quality
    gemini = project_dir / "GEMINI.md"
    results["gemini_exists"] = gemini.is_file()
    if gemini.is_file():
        text = gemini.read_text(encoding="utf-8", errors="replace").lower()
        results["gemini_has_rules"] = "absolute rules" in text or "reglas" in text
        results["gemini_has_complexity"] = "complexity" in text or "complejidad" in text
        results["gemini_has_dispatch"] = "dispatch" in text or "sub-agent" in text
        results["gemini_refs_tasks"] = "tasks" in text
    else:
        results["gemini_has_rules"] = False
        results["gemini_has_complexity"] = False
        results["gemini_has_dispatch"] = False
        results["gemini_refs_tasks"] = False

    # Output governance
    results["output_governance"] = (project_dir / "docs" / "standards" / "output_governance.md").is_file()

    return results


def compute_readiness_score(dispatch: dict, workflows: dict, memory: dict, governance: dict) -> int:
    """Compute 0-100 readiness score from test results."""
    score = 0
    max_score = 0

    # Dispatch (30 points max)
    weights = [
        (dispatch.get("dispatch_script", False), 10),
        (dispatch.get("manifest_valid", False), 10),
        (dispatch.get("agent_count", 0) >= 3, 10),
    ]
    for passed, weight in weights:
        max_score += weight
        if passed:
            score += weight

    # Workflows (25 points max)
    weights = [
        (workflows.get("workflows_dir", False), 5),
        (workflows.get("workflow_count", 0) >= 1, 5),
        (workflows.get("workflow_count", 0) >= 3, 5),
        (workflows.get("session_protocol", False), 10),
    ]
    for passed, weight in weights:
        max_score += weight
        if passed:
            score += weight

    # Memory (20 points max)
    weights = [
        (memory.get("gemini_dir", False), 5),
        (memory.get("brain_dir", False), 5),
        (memory.get("skills_dir", False), 5),
        (memory.get("skill_count", 0) >= 1, 5),
    ]
    for passed, weight in weights:
        max_score += weight
        if passed:
            score += weight

    # Governance (25 points max)
    weights = [
        (governance.get("gemini_exists", False), 5),
        (governance.get("gemini_has_rules", False), 5),
        (governance.get("gemini_has_complexity", False), 5),
        (governance.get("gemini_has_dispatch", False), 5),
        (governance.get("output_governance", False), 5),
    ]
    for passed, weight in weights:
        max_score += weight
        if passed:
            score += weight

    return round(score * 100 / max_score) if max_score else 0


def classify_readiness(score: int) -> str:
    """Classify readiness score."""
    if score >= 90:
        return "🟢 Autonomous"
    if score >= 70:
        return "🟡 Semi-auto"
    if score >= 50:
        return "🟠 Assisted"
    return "🔴 Manual"


# -- Main Flow ----------------------------------------------------------------


def run_selftest(projects: list[tuple[str, Path]]) -> None:
    """Run self-test across projects."""
    print(f"\n{'=' * 65}")
    print("  Agent Self-Test — Antigravity Ecosystem")
    print(f"  {len(projects)} projects")
    print(f"{'=' * 65}")

    all_scores = []

    for name, path in projects:
        dispatch = test_dispatch(path)
        workflows = test_workflows(path)
        memory = test_memory(path)
        governance = test_governance(path)
        score = compute_readiness_score(dispatch, workflows, memory, governance)
        level = classify_readiness(score)
        all_scores.append((name, score, level))

        print(f"\n  {name}  →  {level} ({score}/100)")
        print(f"    Dispatch:    {'✅' if dispatch['dispatch_script'] else '❌'} script"
              f" | {'✅' if dispatch['manifest_valid'] else '❌'} manifest"
              f" ({dispatch['agent_count']} agents)")
        print(f"    Workflows:   {workflows.get('workflow_count', 0)} workflows"
              f" | {'✅' if workflows['session_protocol'] else '❌'} session-protocol")
        print(f"    Memory:      {'✅' if memory['brain_dir'] else '❌'} brain"
              f" | {memory.get('skill_count', 0)} skills")
        print(f"    Governance:  {'✅' if governance['gemini_has_rules'] else '❌'} rules"
              f" | {'✅' if governance['output_governance'] else '❌'} output-gov")

    # Summary
    avg = sum(s for _, s, _ in all_scores) // len(all_scores) if all_scores else 0
    autonomous = sum(1 for _, s, _ in all_scores if s >= 90)
    semi = sum(1 for _, s, _ in all_scores if 70 <= s < 90)
    manual = sum(1 for _, s, _ in all_scores if s < 50)

    print(f"\n{'=' * 65}")
    print("  Summary")
    print(f"{'=' * 65}")
    print(f"    Average score:  {avg}/100")
    print(f"    🟢 Autonomous:  {autonomous}")
    print(f"    🟡 Semi-auto:   {semi}")
    print(f"    🔴 Manual:      {manual}")

    # Bottom 3
    bottom = sorted(all_scores, key=lambda x: x[1])[:3]
    if bottom and bottom[0][1] < 90:
        print(f"\n    ⚠️  Lowest scores:")
        for name, score, level in bottom:
            print(f"      {name}: {score}/100 {level}")
    print()


# -- CLI -----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent Self-Test — Antigravity Ecosystem"
    )
    parser.add_argument("--project", help="Test a single project")
    args = parser.parse_args()

    projects = get_projects(args.project)
    if not projects:
        print(f"❌ Project not found: {args.project}")
        sys.exit(1)

    run_selftest(projects)


if __name__ == "__main__":
    main()
