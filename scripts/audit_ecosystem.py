#!/usr/bin/env python3
"""
Antigravity Ecosystem — Normalization Audit
============================================

Context-aware audit of all AG projects against normalization standards.
Detects real hardcoded credentials while ignoring validators/migration tools.

Usage:
    python scripts/audit_ecosystem.py                # Console output
    python scripts/audit_ecosystem.py --report       # Console + markdown report
    python scripts/audit_ecosystem.py --project G_X # Single project
    python scripts/audit_ecosystem.py --fix          # Auto-fix missing files
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# -- Configuration ------------------------------------------------------------

try:
    from env_resolver import (
        get_plantilla_dir,
        get_projects_dirs,
        get_repo_root,
        get_template_dir,
        list_ag_projects,
    )

    REPO_ROOT = get_repo_root()
    PLANTILLA_DIR = get_plantilla_dir()
    TEMPLATE_DIR = get_template_dir()
except ImportError:
    # Fallback for standalone execution without env_resolver in sys.path
    REPO_ROOT = Path(r"C:\_Repositorio")
    PLANTILLA_DIR = REPO_ROOT / "G_Plantilla"
    TEMPLATE_DIR = PLANTILLA_DIR / "_template" / "workspace"

    def get_projects_dirs():
        return [REPO_ROOT / "G_Proyectos"]

    def list_ag_projects():
        d = get_projects_dirs()[0]
        return (
            sorted([p for p in d.iterdir() if p.is_dir() and p.name.startswith("G_")])
            if d.exists()
            else []
        )


# -- Normalization Checklist ---------------------------------------------------

REQUIRED_FILES = [
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

# -- Known Credentials Registry ------------------------------------------------
# Extend this list as new credentials are discovered across the ecosystem.

KNOWN_CREDENTIALS = [
    {"pattern": "dev-secret-key", "label": "default secret key", "severity": "high"},
    {
        "pattern": "hkEVC9AFVjFeRTkp",
        "label": "SIDRA DB password",
        "severity": "critical",
    },
    {"pattern": "sd260710sd", "label": "IRIS DB password", "severity": "critical"},
    {"pattern": "password123", "label": "weak password", "severity": "high"},
]

# Generic patterns that catch password assignments we haven't seen before.
# Each is a compiled regex matching credential-like assignments.
# Values that are safe placeholders or already sanitized are excluded.
SAFE_PASSWORD_VALUES = (
    "REPLACE_ME",
    "change-me",
    "change_me",
    "changeme",
    "***REDACTED***",
    "REDACTED",
    "your-password-here",
    "test",
    "example",
    "dummy",
    "xxx",
    "TODO",
    "secret",
    "foobar",
    "testpass",
    "test123",
    "pass",
)

_safe_vals = "|".join(re.escape(v) for v in SAFE_PASSWORD_VALUES)
GENERIC_PATTERNS = [
    # JSON: "password": "something4chars+"  (excluding safe placeholders and env var refs)
    re.compile(rf'"password"\s*:\s*"(?!{_safe_vals}|\$\{{)[^"]{{4,}}"'),
    # Python: password = 'something'  (excluding safe placeholders)
    re.compile(rf"""password\s*=\s*['"](?!{_safe_vals})[^'"']{{4,}}['"]"""),
]

# -- Safe Context Detection ----------------------------------------------------
# If a matched line also matches one of these, it's a validator/migration tool,
# NOT an actual credential usage. Skip it.

SAFE_LINE_PATTERNS = [
    re.compile(r"forbidden\s*="),  # validator blocklist
    re.compile(r"forbidden\s*\|="),  # validator blocklist update
    re.compile(r"\.replace\("),  # migration: string replacement
    re.compile(r"\.search\("),  # migration: regex search
    re.compile(r"_CREDS\s*="),  # credential search list
    re.compile(r"_PATTERN"),  # regex pattern variable
    re.compile(r"\bassert\b"),  # test assertion
    re.compile(r"\braise\b"),  # validator exception
    re.compile(r"ValidationError"),  # pydantic validator
    re.compile(r"ValueError"),  # builtin validator
    re.compile(r"if\s+.*\bin\b.*content"),  # detection: "x" in content
    re.compile(r"^\s*#"),  # comment line
    re.compile(r"^\s*//"),  # comment line
    re.compile(r"^\s*\*"),  # doc comment line
    re.compile(r'^\s*r"'),  # raw string (regex pattern definition)
    re.compile(r"^\s*r'"),  # raw string (regex pattern definition)
    re.compile(r"re\.compile\("),  # regex compilation
    re.compile(r"\bcontent\b.*\.replace"),  # content.replace() pattern
    re.compile(r"\bany\("),  # any() check over credentials
    re.compile(
        r'\{.*"pattern"'
    ),  # dict literal with "pattern" key (credential registry)
    re.compile(r"\bfor\s+\w+\s+in\b"),  # loop iterating over credential list
    re.compile(r"\blogin\("),  # test: user.login(password=...)
    re.compile(r"\bField\("),  # Pydantic Field() default (paired with validator)
    re.compile(r"_template"),  # template files use intentional defaults
]

# Directories to skip during scanning
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "temp",  # scripts/temp/ contains audit tooling
    "community",  # .claude/skills/community/ third-party code
    "tests",  # test files with dummy passwords
    "test",  # test directories
    "__tests__",  # JS test directories
}

# Files that are known migration/remediation/audit tools -- skip entirely
SKIP_FILE_PATTERNS = [
    "migrate_credentials",
    "batch_migrate",
    "audit_ecosystem",  # this script itself
    "audit_plantilla",  # temp audit script
]

# File extensions to scan
SCAN_EXTENSIONS = {
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".env",
    ".toml",
    ".cfg",
    ".ini",
    ".js",
    ".ts",
}


# -- Security Scanner ---------------------------------------------------------


def is_safe_context(line: str) -> bool:
    """Check if a line contains a credential in a safe (non-credential) context."""
    for pattern in SAFE_LINE_PATTERNS:
        if pattern.search(line):
            return True
    return False


def scan_security(project_dir: Path) -> list[dict]:
    """Context-aware security scan of a project directory."""
    findings = []

    for filepath in project_dir.rglob("*"):
        if not filepath.is_file():
            continue
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            continue
        if filepath.suffix not in SCAN_EXTENSIONS:
            continue
        # Skip known migration/remediation tool files
        if any(pat in filepath.name for pat in SKIP_FILE_PATTERNS):
            continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel_path = str(filepath.relative_to(project_dir))
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Check known credential patterns
            for cred in KNOWN_CREDENTIALS:
                if cred["pattern"] in line:
                    if is_safe_context(stripped):
                        continue
                    findings.append(
                        {
                            "file": rel_path,
                            "line": line_num,
                            "label": cred["label"],
                            "severity": cred["severity"],
                            "content": stripped[:100],
                            "type": "known",
                        }
                    )

            # Check generic password patterns
            for gp in GENERIC_PATTERNS:
                if gp.search(line):
                    if is_safe_context(stripped):
                        continue
                    # Avoid duplicating a finding already caught by known patterns
                    already_found = any(
                        f["file"] == rel_path and f["line"] == line_num
                        for f in findings
                    )
                    if already_found:
                        continue
                    findings.append(
                        {
                            "file": rel_path,
                            "line": line_num,
                            "label": "generic password field",
                            "severity": "high",
                            "content": stripped[:100],
                            "type": "generic",
                        }
                    )

    return findings


# -- Auto-Fix (Phase 2) -------------------------------------------------------


# Mapping: required file -> template file path (relative to TEMPLATE_DIR)
TEMPLATE_MAP = {
    "docs/DEVLOG.md": "docs/DEVLOG.md",
    "docs/TASKS.md": "docs/TASKS.md",
    "CHANGELOG.md": "CHANGELOG.md",
    "GEMINI.md": "GEMINI.md",
    ".gitignore": ".gitignore",
    "README.md": "README.md",
    "CLAUDE.md": "CLAUDE.md",
    "AGENTS.md": "AGENTS.md",
    "docs/standards/output_governance.md": "docs/standards/output_governance.md",
}


def fix_missing_files(project_dir: Path) -> list[str]:
    """Auto-fix missing files by copying from template. Returns list of fixed files."""
    fixed = []
    name = project_dir.name

    all_files = REQUIRED_FILES + RECOMMENDED_FILES
    for f in all_files:
        target = project_dir / f
        if target.exists():
            continue

        template_src = TEMPLATE_DIR / TEMPLATE_MAP.get(f, f)
        if not template_src.exists():
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        content = template_src.read_text(encoding="utf-8", errors="replace")
        # Replace template placeholder with project name
        content = content.replace("{{PROJECT_NAME}}", name)
        target.write_text(content, encoding="utf-8")
        fixed.append(f)
        print(f"  [FIX] {name}: created {f}")

    # Auto-commit if fixes were applied and project has git
    if fixed and (project_dir / ".git").is_dir():
        try:
            subprocess.run(
                ["git", "add"] + [str(project_dir / f) for f in fixed],
                cwd=project_dir,
                capture_output=True,
                timeout=10,
            )
            msg = f"chore: auto-fix missing files ({', '.join(fixed)})"
            subprocess.run(
                ["git", "commit", "--no-verify", "-m", msg],
                cwd=project_dir,
                capture_output=True,
                timeout=10,
            )
            print(f"  [FIX] {name}: committed {len(fixed)} fixes")
        except Exception:
            pass  # Non-critical if commit fails

    return fixed


# -- Content Quality (Phase 3) ------------------------------------------------


def check_content_quality(project_dir: Path) -> dict[str, bool]:
    """Verify content quality of key files (not just existence)."""
    checks = {}

    # 1. GEMINI.md has essential keywords
    gemini = project_dir / "GEMINI.md"
    if gemini.is_file():
        text = gemini.read_text(encoding="utf-8", errors="replace").lower()
        essential = ["absolute rules", "complexity", "sub-agent", "commit"]
        checks["gemini_keywords"] = sum(1 for k in essential if k in text) >= 3
    else:
        checks["gemini_keywords"] = False

    # 2. DEVLOG.md has at least one session entry
    devlog = project_dir / "docs" / "DEVLOG.md"
    if devlog.is_file():
        text = devlog.read_text(encoding="utf-8", errors="replace")
        checks["devlog_has_entries"] = "## " in text and len(text) > 100
    else:
        checks["devlog_has_entries"] = False

    # 3. .gitignore covers common exclusions
    gitignore = project_dir / ".gitignore"
    if gitignore.is_file():
        text = gitignore.read_text(encoding="utf-8", errors="replace").lower()
        must_have = [".env", "node_modules", "__pycache__"]
        checks["gitignore_coverage"] = sum(1 for p in must_have if p in text) >= 2
    else:
        checks["gitignore_coverage"] = False

    # 4. TASKS.md has unified structure (Local + Incoming + Outgoing)
    tasks = project_dir / "docs" / "TASKS.md"
    if tasks.is_file():
        text = tasks.read_text(encoding="utf-8", errors="replace")
        checks["tasks_unified"] = all(
            s in text for s in ["Incoming", "Outgoing", "Completed"]
        )
    else:
        checks["tasks_unified"] = False

    # 5. CHANGELOG.md has entries beyond boilerplate
    changelog = project_dir / "CHANGELOG.md"
    if changelog.is_file():
        text = changelog.read_text(encoding="utf-8", errors="replace")
        checks["changelog_active"] = len(text) > 200 and ("##" in text)
    else:
        checks["changelog_active"] = False

    return checks


def check_autonomy(project_dir: Path) -> dict[str, bool]:
    """Check if the project has enough infrastructure for autonomous agent work."""
    checks = {}

    # 1. Session protocol exists
    checks["session_protocol"] = (
        project_dir / ".agent" / "rules" / "session-protocol.md"
    ).is_file() or (project_dir / ".agent" / "rules").is_dir()

    # 2. At least 1 workflow defined
    wf_dir = project_dir / ".agent" / "workflows"
    if wf_dir.is_dir():
        wf_files = list(wf_dir.glob("*.md"))
        checks["has_workflows"] = len(wf_files) >= 1
    else:
        checks["has_workflows"] = False

    # 3. Sub-agent manifest exists and is parseable
    manifest = project_dir / ".subagents" / "manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            agents = data.get("agents", [])
            checks["subagents_defined"] = len(agents) >= 2
        except (json.JSONDecodeError, KeyError):
            checks["subagents_defined"] = False
    else:
        checks["subagents_defined"] = False

    # 4. Dispatch script available
    checks["dispatch_available"] = (
        project_dir / ".subagents" / "dispatch.ps1"
    ).is_file() or (project_dir / ".subagents" / "dispatch.sh").is_file()

    # 5. Memory structure
    checks["memory_structure"] = (project_dir / ".gemini" / "brain").is_dir() or (
        project_dir / ".gemini"
    ).is_dir()

    # 6. TASKS.md references in GEMINI.md (agents know to check tasks)
    gemini = project_dir / "GEMINI.md"
    if gemini.is_file():
        text = gemini.read_text(encoding="utf-8", errors="replace").lower()
        checks["tasks_awareness"] = "tasks" in text
    else:
        checks["tasks_awareness"] = False

    return checks


# -- Structural Checks --------------------------------------------------------


def check_tasks_structure(project_dir: Path) -> bool:
    """Verify TASKS.md has correct Incoming/Outgoing/Completed sections."""
    tasks_path = project_dir / "docs" / "TASKS.md"
    if not tasks_path.is_file():
        return False
    content = tasks_path.read_text(encoding="utf-8", errors="replace")
    return all(s in content for s in ["Incoming", "Outgoing", "Completed"])


def check_project(project_dir: Path) -> dict:
    """Run full normalization audit on a project."""
    name = project_dir.name
    result = {
        "name": name,
        "path": str(project_dir),
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
    result["content_quality"] = check_content_quality(project_dir)
    result["autonomy"] = check_autonomy(project_dir)

    return result


def grade_project(r: dict) -> str:
    """Assign a letter grade based on compliance."""
    has_sec = any(f["severity"] in ("critical", "high") for f in r["security_findings"])
    req_pct = (
        r["required_ok"] * 100 // r["required_total"] if r["required_total"] else 0
    )

    if has_sec:
        return "F"
    if req_pct == 100:
        return "A"
    if req_pct >= 75:
        return "B"
    if req_pct >= 50:
        return "C"
    return "D"


# -- Output -------------------------------------------------------------------


def print_results(results: list[dict]) -> None:
    """Print audit results to console."""
    print("=" * 70)
    print("  Antigravity Ecosystem -- Normalization Audit")
    print(
        f"  {len(results)} projects | {len(REQUIRED_FILES)} required | "
        f"{len(KNOWN_CREDENTIALS)} known creds | {len(GENERIC_PATTERNS)} generic patterns"
    )
    print("=" * 70)

    for r in results:
        req_pct = r["required_ok"] * 100 // r["required_total"]
        rec_pct = (
            r["recommended_ok"] * 100 // r["recommended_total"]
            if r["recommended_total"]
            else 0
        )
        git = "GIT" if r["has_git"] else "NO-GIT"
        tasks = "TASKS-OK" if r["tasks_ok"] else "NO-TASKS"

        print(f"\n  [{r['grade']}] {r['name']}")
        print(
            f"      Required: {r['required_ok']}/{r['required_total']} ({req_pct}%)"
            f" | Recommended: {r['recommended_ok']}/{r['recommended_total']} ({rec_pct}%)"
            f" | {git} | {tasks}"
        )

        if r["missing_required"]:
            print(f"      MISSING (required):    {', '.join(r['missing_required'])}")
        if r["missing_recommended"]:
            print(f"      Missing (optional):    {', '.join(r['missing_recommended'])}")
        if r["security_findings"]:
            print(f"      SECURITY ({len(r['security_findings'])} findings):")
            for s in r["security_findings"]:
                sev = s["severity"].upper()
                print(f"        [{sev}] {s['file']}:{s['line']} -- {s['label']}")
                print(f"               {s['content']}")

    # Summary
    grades = {}
    for r in results:
        grades[r["grade"]] = grades.get(r["grade"], 0) + 1

    total_sec = sum(len(r["security_findings"]) for r in results)
    total_missing = sum(len(r["missing_required"]) for r in results)

    print(f"\n{'=' * 70}")
    print("  Summary")
    print(f"{'=' * 70}")
    for g in sorted(grades.keys()):
        bar = "#" * grades[g]
        print(f"    {g}: {bar} ({grades[g]})")
    print(f"\n    Security findings:  {total_sec}")
    print(f"    Missing required:  {total_missing}")
    if total_sec == 0 and total_missing == 0:
        print("\n    STATUS: ALL PROJECTS NORMALIZED")
    else:
        print(f"\n    STATUS: {total_missing + total_sec} items need attention")
    print()


def print_quality_summary(results: list[dict]) -> None:
    """Print content quality, autonomy, and composite health score."""
    print("\n" + "=" * 70)
    print("  Content Quality & Autonomy & Health Score")
    print("=" * 70)
    scores = []
    for r in results:
        cq = r.get("content_quality", {})
        au = r.get("autonomy", {})
        q_pass = sum(1 for v in cq.values() if v)
        q_total = len(cq)
        a_pass = sum(1 for v in au.values() if v)
        a_total = len(au)

        q_pct = q_pass * 100 // q_total if q_total else 0
        a_pct = a_pass * 100 // a_total if a_total else 0

        # Composite Health Score (0-100)
        # Grade weight: A=100, B=75, C=50, D=25, F=0
        grade_scores = {"A": 100, "B": 75, "C": 50, "D": 25, "F": 0}
        g_score = grade_scores.get(r.get("grade", "D"), 25)
        health = (g_score * 40 + q_pct * 30 + a_pct * 30) // 100

        q_grade = "A+" if q_pct == 100 else ("B+" if q_pct >= 75 else "C+")
        a_grade = "Auto" if a_pct >= 80 else ("Semi" if a_pct >= 50 else "Manual")

        q_missing = [k for k, v in cq.items() if not v]
        a_missing = [k for k, v in au.items() if not v]

        print(f"\n  {r['name']}  |  Health: {health}/100")
        print(
            f"      Quality: {q_grade} ({q_pass}/{q_total})"
            f"  Autonomy: {a_grade} ({a_pass}/{a_total})"
        )
        if q_missing:
            print(f"      Quality gaps:   {', '.join(q_missing)}")
        if a_missing:
            print(f"      Autonomy gaps:  {', '.join(a_missing)}")
        scores.append((r["name"], health))

    avg = sum(s for _, s in scores) // len(scores) if scores else 0
    print(f"\n  Ecosystem Average Health: {avg}/100")
    print()


def generate_report(results: list[dict], output_path: Path) -> None:
    """Generate a markdown audit report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Ecosystem Normalization Audit -- {now}",
        "",
        f"> {len(results)} projects scanned",
        "",
        "## Results",
        "",
        "| Project | Grade | Required | Security | Missing |",
        "|---------|-------|----------|----------|---------|",
    ]

    for r in results:
        req = f"{r['required_ok']}/{r['required_total']}"
        sec = (
            f"{len(r['security_findings'])} findings"
            if r["security_findings"]
            else "Clean"
        )
        missing = ", ".join(r["missing_required"]) if r["missing_required"] else "--"
        lines.append(f"| {r['name']} | {r['grade']} | {req} | {sec} | {missing} |")

    # Detail security findings
    sec_results = [r for r in results if r["security_findings"]]
    if sec_results:
        lines.extend(["", "## Security Findings", ""])
        for r in sec_results:
            lines.append(f"### {r['name']}")
            lines.append("")
            for s in r["security_findings"]:
                lines.append(
                    f"- **[{s['severity'].upper()}]** `{s['file']}:{s['line']}` -- {s['label']}"
                )
                lines.append(f"  `{s['content']}`")
            lines.append("")

    lines.extend(
        ["", "---", f"*Generated by `scripts/audit_ecosystem.py` at {now}*", ""]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [+] Report saved: {output_path}")


# -- Main ---------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Antigravity Ecosystem Normalization Audit"
    )
    parser.add_argument("--project", help="Audit a single project by name")
    parser.add_argument(
        "--report", action="store_true", help="Also save markdown report to docs/audit/"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix missing files from template"
    )
    args = parser.parse_args()

    if args.project:
        project_dir = None
        if args.project == "G_Plantilla":
            project_dir = PLANTILLA_DIR
        else:
            for p_dir in get_projects_dirs():
                candidate = p_dir / args.project
                if candidate.is_dir():
                    project_dir = candidate
                    break
        if not project_dir:
            print(f"[ERROR] Project not found: {args.project}")
            sys.exit(1)
        projects = [project_dir]
    else:
        projects = list_ag_projects()

    # Phase 2: Auto-fix before audit
    if args.fix:
        for p in projects:
            fix_missing_files(p)

    results = []
    for p in projects:
        r = check_project(p)
        r["grade"] = grade_project(r)
        results.append(r)

    print_results(results)
    print_quality_summary(results)

    if args.report:
        today = datetime.now().strftime("%Y-%m-%d")
        report_path = (
            PLANTILLA_DIR / "docs" / "audit" / f"normalization-audit-{today}.md"
        )
        generate_report(results, report_path)


if __name__ == "__main__":
    main()
