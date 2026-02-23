# CLAUDE.md — G_Analizador_RCE

## Identity
This is the **G_Analizador_RCE** satellite project under the Antigravity ecosystem.
Domain: `01_HOSPITAL_PRIVADO`

Analizador de Resumen Clinico Electronico (RCE) para hospital privado

## Rules
1. Follow the governance standards defined in `docs/standards/`.
2. All scripts must be registered in `docs/library/scripts.md`.
3. Update CHANGELOG.md and DEVLOG.md with significant changes.
4. Cross-reference integrity: check `impacts:` frontmatter before finalizing edits.

## Regla de Consistencia Cruzada
Antes de finalizar cualquier edicion a un archivo que contenga frontmatter `impacts:`,
DEBES leer cada archivo listado en `impacts` y verificar que las referencias cruzadas
sigan siendo correctas. Si no lo son, corrigelas en el mismo commit/sesion.

## Project Structure
```
G_Analizador_RCE/
  .claude/          # Claude Code configuration
  .gemini/          # Gemini CLI configuration
  .codex/           # Codex CLI configuration
  .agent/           # Agent rules and workflows
  .subagents/       # Subagent manifest, dispatch, and skills
  docs/             # Documentation
    standards/      # Governance standards
    library/        # Living dictionary
    research/       # Research artifacts
  scripts/          # Automation scripts
  config/           # Configuration files
  tests/            # Test suite
```
