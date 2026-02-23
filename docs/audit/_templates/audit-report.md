---
# === Antigravity Audit Report ===
# Standard: AG-AUDIT-STD v1.0 (ISO 19011 / ISACA ITAF / CVSS v3.1 aligned)
#
# FILE NAMING CONVENTION:
#   YYYY-MM-DD_<type>_<scope>_<vendor>-<model>.md
#
#   type:   full | sec | norm | perf | code | infra | data | tools | plan
#   scope:  ecosystem | core | hp | hpub | {project-id}
#   vendor-model: claude-opus46 | claude-sonnet46 | claude-haiku45
#                 gemini-flash20 | gemini-pro25 | codex | team | human

audit_id: "AG-AUD-YYYY-MM-DD-NNN"
title: ""
date: "YYYY-MM-DD"
timestamp: "YYYY-MM-DDTHH:MM:SS-04:00"

agent:
  vendor: ""              # claude | gemini | codex | human
  model: ""               # opus-4.6 | sonnet-4.6 | haiku-4.5 | flash-2.0 | pro-2.5 | codex
  interface: ""           # cli | vscode | automated | web
  agent_name: ""          # From .subagents/manifest.json
  team_mode: null         # null | full-review | deep-audit | rapid-fix | feature-pipeline

scope:
  type: ""                # full | sec | norm | perf | code | infra | data | tools
  domain: ""              # ecosystem | 00_CORE | 01_HOSPITAL_PRIVADO | 02_HOSPITAL_PUBLICO
  projects: []            # List of project IDs from project_registry.json
  criteria: []            # Standards audited against

severity_summary:
  critical: 0             # CVSS 9.0-10.0 — Immediate action
  high: 0                 # CVSS 7.0-8.9 — Action within 24h
  medium: 0               # CVSS 4.0-6.9 — Action within 7 days
  low: 0                  # CVSS 0.1-3.9 — Action within 30 days
  info: 0                 # CVSS 0.0 — No action required

overall_score: 0          # 0-100 composite health score
overall_grade: ""         # A (90-100) | B (80-89) | C (70-79) | D (60-69) | F (<60)
status: "draft"           # draft | in-review | approved | superseded | archived
language: "es"            # es | en | mixed
supersedes: null          # audit_id of previous version if revision
tags: []
---

# {Title}

## 1. Executive Summary

<!-- 3-5 sentences: What was audited, why, overall score, key findings, conclusion -->

## 2. Audit Scope and Methodology

### 2.1 Scope

- **Projects:** {list from scope.projects}
- **Domain:** {scope.domain}
- **Period:** {date range or snapshot date}
- **Criteria:** {list from scope.criteria}

### 2.2 Methodology

- **Agent:** {agent.vendor} {agent.model} via {agent.interface}
- **Team mode:** {agent.team_mode or "N/A"}
- **Automated checks:** {list tools/scripts used}
- **Manual checks:** {describe if any}

## 3. Findings Summary

### 3.1 Severity Overview

| Level | Count | Action Deadline |
|-------|-------|-----------------|
| Critical | 0 | Immediate |
| High | 0 | 24 hours |
| Medium | 0 | 7 days |
| Low | 0 | 30 days |
| Info | 0 | None |

### 3.2 Scorecard by Category

| Category | Code | Score | Grade | C | H | M | L | I |
|----------|------|-------|-------|---|---|---|---|---|
| Security | SEC | /100 | | | | | | |
| Governance | GOV | /100 | | | | | | |
| Code Quality | QA | /100 | | | | | | |
| Architecture | ARCH | /100 | | | | | | |
| Data Integrity | DATA | /100 | | | | | | |
| Operations | OPS | /100 | | | | | | |
| Agent Config | AGENT | /100 | | | | | | |
| Documentation | DOC | /100 | | | | | | |

### 3.3 Critical and High Findings

<!-- Table of critical/high findings requiring immediate attention -->

| ID | Severity | Category | Finding | Project |
|----|----------|----------|---------|---------|
| | | | | |

## 4. Detailed Findings

### 4.1 Security (SEC)

<!-- Repeat the finding block below for each finding in this category -->

#### [H-SEC-001] Finding Title

- **Severity:** High (CVSS 7.5)
- **Category:** SEC
- **Project:** {project_id}
- **Location:** `path/to/file:line`
- **Description:** Brief description of the finding.
- **Evidence:** Code snippet, log output, or reference.
- **Impact:** What happens if not addressed.
- **Recommendation:** Specific remediation steps.
- **Status:** Open

### 4.2 Governance (GOV)

### 4.3 Code Quality (QA)

### 4.4 Architecture (ARCH)

### 4.5 Data Integrity (DATA)

### 4.6 Operations (OPS)

### 4.7 Agent Config (AGENT)

### 4.8 Documentation (DOC)

## 5. Recommendations

### 5.1 Immediate Actions (Critical/High)

1. **[ID]** — Description — Assignee — Deadline

### 5.2 Short-Term Improvements (Medium)

<!-- Within 7 days -->

1. **[ID]** — Description

### 5.3 Long-Term Improvements (Low/Info)

<!-- Within 30 days or next sprint -->

1. **[ID]** — Description

## 6. Appendix

### 6.1 Files Analyzed

<!-- Total count and key file list -->

### 6.2 Tools and Versions

| Tool | Version |
|------|---------|
| | |

### 6.3 Previous Audit Reference

<!-- audit_id of the previous audit for this scope, if any -->

### 6.4 Glossary

| Term | Definition |
|------|-----------|
| CVSS | Common Vulnerability Scoring System v3.1 |
| SEC | Security category |
| GOV | Governance category |
| QA | Code Quality category |
| ARCH | Architecture category |
| DATA | Data Integrity category |
| OPS | Operations category |
| AGENT | Agent Configuration category (Antigravity-specific) |
| DOC | Documentation category |
