"""Audit AG_Plantilla content quality."""
from pathlib import Path

root = Path(r"C:\_Repositorio\AG_Plantilla")
issues = []

# 1. GEMINI.md references
gemini = (root / "GEMINI.md").read_text(encoding="utf-8")
for kw in ["docs/", "DEVLOG", "TODO", "CHANGELOG", "sub-agent", "ROUTING"]:
    if kw not in gemini:
        issues.append(f"GEMINI.md missing reference to: {kw}")

# 2. .gitignore patterns
gi = (root / ".gitignore").read_text(encoding="utf-8")
for pat in [".env", "__pycache__", "node_modules", "*.db"]:
    if pat not in gi:
        issues.append(f".gitignore missing pattern: {pat}")

# 3. .env.example no real creds
env_ex = (root / ".env.example").read_text(encoding="utf-8")
for f in ["hkEVC9AFVjFeRTkp", "dev-secret-key", "password123"]:
    if f in env_ex:
        issues.append(f".env.example contains forbidden value: {f}")

# 4. config.py validator
config = (root / "src" / "config.py").read_text(encoding="utf-8")
if "model_validator" not in config:
    issues.append("src/config.py missing model_validator for API key")
if "change-me" not in config:
    issues.append("src/config.py missing change-me placeholder")

# 5. main.py CORS - check for wildcard origin
main = (root / "src" / "main.py").read_text(encoding="utf-8")
if '"*"' in main and "origins" in main:
    issues.append("src/main.py may have CORS wildcard")

# 6. dispatch scripts delimiters
for script in ["dispatch.sh", "dispatch.ps1"]:
    sp = root / ".subagents" / script
    if sp.exists():
        content = sp.read_text(encoding="utf-8")
        if "user_task" not in content:
            issues.append(f".subagents/{script} missing prompt injection delimiters")

# 7. Memory system
mi = (root / ".gemini" / "brain" / "memory-index.md").read_text(encoding="utf-8")
cs = (root / ".gemini" / "brain" / "context-snapshot.md").read_text(encoding="utf-8")
if "Security Audit" not in mi:
    issues.append("memory-index.md missing Security Audit session")
if "Backlog" not in cs:
    issues.append("context-snapshot.md missing backlog section")

# 8. Template TASKS.md structure
ts = (root / "_template" / "workspace" / "docs" / "TASKS.md").read_text(encoding="utf-8")
for section in ["Incoming", "Outgoing", "Completed"]:
    if section not in ts:
        issues.append(f"Template TASKS.md missing section: {section}")

# 9. output_governance.md mentions TASKS
og = (root / "docs" / "standards" / "output_governance.md").read_text(encoding="utf-8")
if "TASKS" not in og:
    issues.append("output_governance.md does not mention TASKS.md system")

print("=" * 60)
print("  AG_Plantilla Content Quality Audit")
print("=" * 60)
if not issues:
    print("\n  [PASS] All 9 content quality checks passed")
else:
    print(f"\n  [ISSUES] {len(issues)} found:")
    for i in issues:
        print(f"    - {i}")
print()
