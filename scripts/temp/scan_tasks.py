#!/usr/bin/env python3
"""Scan all projects for TASKS.md status and pending items."""
from pathlib import Path

AG_PROY = Path(r"C:\_Repositorio\AG_Proyectos")
report = []

for d in sorted(AG_PROY.iterdir()):
    if not d.is_dir() or not d.name.startswith("AG_"):
        continue
    tasks = d / "docs" / "TASKS.md"
    if not tasks.exists():
        report.append(f"{d.name}: NO TASKS.md")
        continue
    content = tasks.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    has_incoming = any("Incoming" in l for l in lines)
    has_outgoing = any("Outgoing" in l for l in lines)
    has_eval = any("EVALUATE" in l.upper() for l in lines)
    pending_cb = [l.strip() for l in lines if "[ ]" in l or "[/]" in l]
    pending_tp = [l.strip() for l in lines if "PENDING" in l]
    fmt = "OK" if (has_incoming and has_outgoing) else "MISSING_SECTIONS"
    report.append(f"{d.name} | fmt={fmt} | eval={has_eval} | cb_pending={len(pending_cb)} | task_pending={len(pending_tp)}")
    for p in pending_cb[:3]:
        report.append(f"  CB: {p[:100]}")
    for p in pending_tp[:3]:
        report.append(f"  TP: {p[:100]}")

txt = "\n".join(report)
Path(r"C:\_Repositorio\AG_Plantilla\scripts\temp\tasks_report.txt").write_text(txt, encoding="utf-8")
print(txt)
