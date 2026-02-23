# AGENTS.md — G_Analizador_RCE

## Subagent Manifest
Agents for this project are defined in `.subagents/manifest.json`.

## Available Agents

| Name | Default Vendor | Priority | Supported Vendors |
|------|---------------|----------|--------------------|
| researcher | codex | 1 | gemini, claude, codex |
| code-reviewer | claude | 2 | gemini, claude, codex |
| code-analyst | gemini | 3 | gemini, claude, codex |
| doc-writer | gemini | 4 | gemini, claude, codex |
| test-writer | gemini | 5 | gemini, claude, codex |
| db-analyst | claude | 6 | gemini, claude, codex |
| deployer | gemini | 7 | gemini, claude, codex |

## Teams

| Team | Agents | Mode | Use Case |
|------|--------|------|----------|
| full-audit | code-reviewer, code-analyst | sequential | Full project audit with orchestrator oversight |
| code-and-review | code-analyst, code-reviewer | sequential | Generate code then review for quality and security |
| research-and-document | researcher, doc-writer | sequential | Research a topic then document findings |
| adversarial-review | code-analyst, code-reviewer | sequential | Generate code then have isolated critic validate output |
| full-review | code-reviewer, test-writer, doc-writer | parallel | Comprehensive pre-merge review: code quality + test coverage + docs sync |
| feature-pipeline | code-analyst, test-writer, code-reviewer | sequential | TDD pipeline: analyze → write tests → review implementation |
| deep-audit | code-reviewer, db-analyst, deployer | parallel | Full-stack audit: code security + database + infrastructure |
| rapid-fix | code-analyst, code-reviewer | sequential | Quick bug diagnosis and validation |

## Dispatch
```bash
bash .subagents/dispatch.sh <agent-name> "<prompt>"
bash .subagents/dispatch-team.sh <team-name> "<prompt>"
```
