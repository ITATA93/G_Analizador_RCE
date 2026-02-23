#!/usr/bin/env python3
"""Send normalization tasks to projects with specific gaps."""
import subprocess
import sys

CROSS_TASK = r"C:\_Repositorio\AG_Plantilla\scripts\cross_task.py"

# Tasks based on selftest gaps
tasks = [
    # Skills evaluation for massive libraries
    {"to": "AG_Consultas", "title": "Classify and archive unused Claude skills (200+)",
     "desc": "200+ Claude skills - classify as RELEVANT/GENERIC/NOT_APPLICABLE. Move NOT_APPLICABLE to .claude/skills/_archived/. Keep domain-relevant (medical, data science). Document decisions in DEVLOG.",
     "priority": "medium"},
    {"to": "AG_Hospital_Organizador", "title": "Classify and archive unused Claude skills (200+)",
     "desc": "200+ Claude skills inherited from template. Classify by domain relevance, archive non-hospital skills to .claude/skills/_archived/. Document decisions in DEVLOG.",
     "priority": "medium"},

    # Governance gaps
    {"to": "AG_Lists_Agent", "title": "Fix missing GEMINI.md governance rules",
     "desc": "Agent selftest shows missing rules file. Propagate GEMINI.md from AG_Plantilla template. Readiness score will improve from 70 to ~80.",
     "priority": "high"},
    {"to": "AG_SD_Plantilla", "title": "Fix missing GEMINI.md governance rules",
     "desc": "Agent selftest shows missing rules file. Propagate GEMINI.md from AG_Plantilla template. Readiness score will improve from 70 to ~80.",
     "priority": "high"},
    {"to": "AG_TrakCare_Explorer", "title": "Fix missing output_governance.md",
     "desc": "Agent selftest shows missing docs/standards/output_governance.md. Propagate from AG_Plantilla template. Readiness score will improve from 80 to ~85.",
     "priority": "high"},

    # Workflow gaps
    {"to": "AG_DeepResearch_Salud_Chile", "title": "Create project-specific workflows",
     "desc": "Currently 0 workflows. Create at minimum: deep-research-update.md, turbo-ops.md from AG_Plantilla template.",
     "priority": "low"},
    {"to": "AG_Notebook", "title": "Create project-specific workflows",
     "desc": "Currently 0 workflows. Create at minimum: deep-research-update.md, turbo-ops.md from AG_Plantilla template.",
     "priority": "low"},
]

for t in tasks:
    cmd = [
        sys.executable, CROSS_TASK, "create",
        "--from", "AG_Plantilla",
        "--to", t["to"],
        "--title", t["title"],
        "--description", t["desc"],
        "--priority", t["priority"],
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        # Extract task ID
        for line in r.stdout.split("\n"):
            if "Task created:" in line:
                print(f"  OK: {t['to']} <- {line.strip()}")
                break
    else:
        print(f"  FAIL: {t['to']} -> {r.stderr.strip()[:80]}")
