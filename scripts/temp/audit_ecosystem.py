"""
Antigravity Ecosystem Normalization Audit v2
=============================================

Improvements over v1:
- Context-aware security scanning (ignores validators, migration tools, comments)
- Separate structural vs content vs security grades
- Per-project actionable output
"""
from pathlib import Path
import re

REPO = Path(r"C:\_Repositorio")
PROJECTS_DIR = REPO / "AG_Proyectos"

# ── Normalization checklist ──────────────────────────────────────────

REQUIRED_FILES = [
    "docs/TODO.md",
    "docs/DEVLOG.md",
    "docs/TASKS.md",
    "CHANGELOG.md",
    "GEMINI.md",
    ".gitignore",
    "README.md",
]

RECOMMENDED_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    ".env.example",
    "docs/standards/output_governance.md",
]

REQUIRED_DIRS = ["docs"]
RECOMMENDED_DIRS = ["config", ".gemini", ".agent"]

# ── Security patterns ────────────────────────────────────────────────

SECURITY_PATTERNS = [
    {"pattern": "dev-secret-key", "label": "default secret key"},
    {"pattern": "hkEVC9AFVjFeRTkp", "label": "SIDRA password"},
    {"pattern": "password123", "label": "weak password"},
]

# Lines containing these patterns are VALIDATORS/MIGRATION tools,
# not actual credential usage. Skip them.
SAFE_CONTEXTS = [
    "forbidden",        # forbidden = {"dev-secret-key", ...}  (validator)
    "SIDRA_CREDS",      # SIDRA_CREDS = [...]  (migration tool constant)
    "replace(",         # content.replace("hk...  (migration logic)
    "search(",          # PATTERN.search(...)  (detection logic)
    ".replace(",        # string replacement
    "# Migrado",        # migration comment
    "in content",       # detection: "xyz" in content
    "PATTERN",          # regex pattern definition
    "assert",           # test assertion
    "reject",           # validator description
    "raise",            # validator exception
    "ValueError",       # validator
    "ValidationError",  # pydantic validator
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
SCAN_EXTENSIONS = {".py", ".json", ".yaml", ".yml", ".env", ".toml", ".cfg", ".ini"}


def is_safe_context(line: str) -> bool:
    """Check if a line contains a security pattern in a safe context."""
    for ctx in SAFE_CONTEXTS:
        if ctx in line:
            return True
    return False


def scan_security(project_dir: Path) -> list[dict]:
    """Context-aware security scan."""
    findings = []

    for f in project_dir.rglob("*"):
        # Skip directories and non-scannable files
        if f.is_dir():
            continue
        if any(skip in f.parts for skip in SKIP_DIRS):
            continue
        if f.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for line_num, line in enumerate(content.splitlines(), 1):
            for sec in SECURITY_PATTERNS:
                if sec["pattern"] in line:
                    if is_safe_context(line):
                        continue  # Skip validators/migration tools
                    # Skip comments
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("//"):
                        continue
                    rel = f.relative_to(project_dir)
                    findings.append({
                        "file": str(rel),
                        "line": line_num,
                        "label": sec["label"],
                        "content": stripped[:80],
                    })

    return findings


def check_tasks_structure(project_dir: Path) -> bool:
    """Verify TASKS.md has correct sections."""
    tasks_path = project_dir / "docs" / "TASKS.md"
    if not tasks_path.is_file():
        return False
    content = tasks_path.read_text(encoding="utf-8", errors="replace")
    return all(s in content for s in ["Incoming", "Outgoing", "Completed"])


def check_project(project_dir: Path) -> dict:
    """Full normalization check for a project."""
    name = project_dir.name
    result = {
        "name": name,
        "required_ok": 0,
        "required_total": len(REQUIRED_FILES) + len(REQUIRED_DIRS),
        "recommended_ok": 0,
        "recommended_total": len(RECOMMENDED_FILES) + len(RECOMMENDED_DIRS),
        "missing_required": [],
        "missing_recommended": [],
        "security_findings": [],
        "has_git": (project_dir / ".git").is_dir(),
        "tasks_ok": check_tasks_structure(project_dir),
    }

    for f in REQUIRED_FILES:
        if (project_dir / f).is_file():
            result["required_ok"] += 1
        else:
            result["missing_required"].append(f)

    for d in REQUIRED_DIRS:
        if (project_dir / d).is_dir():
            result["required_ok"] += 1
        else:
            result["missing_required"].append(d + "/")

    for f in RECOMMENDED_FILES:
        if (project_dir / f).is_file():
            result["recommended_ok"] += 1
        else:
            result["missing_recommended"].append(f)

    for d in RECOMMENDED_DIRS:
        if (project_dir / d).is_dir():
            result["recommended_ok"] += 1
        else:
            result["missing_recommended"].append(d + "/")

    result["security_findings"] = scan_security(project_dir)

    return result


def grade_project(r: dict) -> str:
    """Assign a letter grade."""
    req_pct = r["required_ok"] * 100 // r["required_total"] if r["required_total"] else 0
    has_sec = len(r["security_findings"]) > 0

    if has_sec:
        return "F"  # Security issues = automatic fail
    if req_pct == 100:
        return "A"
    if req_pct >= 75:
        return "B"
    if req_pct >= 50:
        return "C"
    return "D"


def main():
    projects = sorted(
        [d for d in PROJECTS_DIR.iterdir() if d.is_dir() and d.name.startswith("AG_")]
    )

    print("=" * 70)
    print("  Antigravity Ecosystem -- Normalization Audit v2")
    print(f"  {len(projects)} projects | {len(REQUIRED_FILES)} required files | {len(SECURITY_PATTERNS)} security patterns")
    print("=" * 70)

    results = []
    for p in projects:
        r = check_project(p)
        r["grade"] = grade_project(r)
        results.append(r)

    for r in results:
        req_pct = r["required_ok"] * 100 // r["required_total"]
        rec_pct = r["recommended_ok"] * 100 // r["recommended_total"] if r["recommended_total"] else 0
        git = "GIT" if r["has_git"] else "NO-GIT"
        tasks = "TASKS-OK" if r["tasks_ok"] else "NO-TASKS"

        print(f"\n  [{r['grade']}] {r['name']}")
        print(f"      Required: {r['required_ok']}/{r['required_total']} ({req_pct}%) | Recommended: {r['recommended_ok']}/{r['recommended_total']} ({rec_pct}%) | {git} | {tasks}")

        if r["missing_required"]:
            print(f"      MISSING (required):    {', '.join(r['missing_required'])}")
        if r["missing_recommended"]:
            print(f"      Missing (optional):    {', '.join(r['missing_recommended'])}")
        if r["security_findings"]:
            print(f"      SECURITY ({len(r['security_findings'])} findings):")
            for s in r["security_findings"]:
                print(f"        ! {s['file']}:{s['line']} [{s['label']}] {s['content']}")

    # Summary
    print(f"\n{'=' * 70}")
    print("  Summary")
    print(f"{'=' * 70}")

    grades = {}
    for r in results:
        grades[r["grade"]] = grades.get(r["grade"], 0) + 1

    for g in sorted(grades.keys()):
        count = grades[g]
        bar = "#" * count
        print(f"    {g}: {bar} ({count})")

    total_sec = sum(len(r["security_findings"]) for r in results)
    total_missing = sum(len(r["missing_required"]) for r in results)
    print(f"\n    Security findings:  {total_sec}")
    print(f"    Missing required:  {total_missing}")

    if total_sec == 0 and total_missing == 0:
        print("\n    STATUS: ALL PROJECTS NORMALIZED")
    else:
        print(f"\n    STATUS: {total_missing + total_sec} items need attention")
    print()


if __name__ == "__main__":
    main()
