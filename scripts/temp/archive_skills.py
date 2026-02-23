import os
import sys
import shutil
from pathlib import Path


def archive_skills(project_dir: str, keep_keywords: list[str], log_file: str):
    skills_dir = Path(project_dir) / ".claude" / "skills"
    if not skills_dir.exists():
        print(f"No skills dir found in {project_dir}")
        return

    archive_dir = skills_dir / "_archived"
    archive_dir.mkdir(exist_ok=True)

    archived_count = 0
    kept_count = 0

    log_path = Path(project_dir) / "docs" / "DEVLOG.md"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## Automated Skill Archiving\n\n")

        for item in skills_dir.iterdir():
            if not item.is_dir() or item.name in ["_archived", "archive"]:
                continue

            name = item.name.lower()
            is_relevant = any(kw in name for kw in keep_keywords)

            if is_relevant:
                kept_count += 1
                f.write(f"- Kept (RELEVANT): {item.name}\n")
            else:
                archived_count += 1
                f.write(f"- Archived (NOT_APPLICABLE): {item.name}\n")
                shutil.move(str(item), str(archive_dir / item.name))

    print(f"[{project_dir}] Kept: {kept_count}, Archived: {archived_count}")


if __name__ == "__main__":
    archive_skills("W:/AG_Proyectos/AG_NB_Apps", ["nocobase"], "DEVLOG.md")
    archive_skills(
        "W:/AG_Proyectos/AG_Consultas",
        ["medical", "med", "data", "science", "analys", "health"],
        "DEVLOG.md",
    )
    archive_skills(
        "W:/AG_Proyectos/AG_Hospital_Organizador",
        ["hospital", "med", "health", "clinic", "pacient", "ward", "trakcare", "ugco"],
        "DEVLOG.md",
    )
