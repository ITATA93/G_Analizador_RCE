#!/usr/bin/env python3
"""Commit TASKS.md changes in satellite projects that received incoming tasks."""
import subprocess
from pathlib import Path

AG_PROY = Path(r"C:\_Repositorio\AG_Proyectos")
for d in sorted(AG_PROY.iterdir()):
    if not d.is_dir() or not d.name.startswith("AG_"):
        continue
    subprocess.run(["git", "add", "docs/TASKS.md"], cwd=str(d), capture_output=True)
    r = subprocess.run(
        ["git", "commit", "--no-verify", "-m", "feat(tasks): incoming normalization tasks from AG_Plantilla"],
        cwd=str(d), capture_output=True, text=True
    )
    if r.returncode == 0:
        print(f"  COMMITTED: {d.name}")
    elif "nothing to commit" in (r.stdout + r.stderr):
        print(f"  CLEAN: {d.name}")
    else:
        print(f"  SKIP: {d.name}")
