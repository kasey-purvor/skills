# Documentation Standards

**Status:** Draft (this document is a starting point — refine based on experience)

## Core Principle

Documentation captures knowledge that isn't obvious from the code. Focus on "why" over "what", and ensure future developers (human or AI) can understand and operate the system.

---

## Tier Requirements (Suggested Starting Point)

These tiers are a **prototype suggestion** — adjust based on project needs.

### Exploratory

- README with setup instructions (how to install, run, test)

### Internal

- All Exploratory requirements
- Docstrings for public functions/classes
- Architecture diagram (Mermaid or similar)

### Production

- All Internal requirements
- API documentation (if applicable)
- Runbooks for common operations/troubleshooting
- Decision records for significant choices

---

## Documentation Types

**Brainstorm with user to determine which are needed for each project.**

| Type | Purpose | When Useful |
|------|---------|-------------|
| **README** | Project entry point, setup instructions | Always |
| **API docs** | Endpoint/function reference | Public APIs, libraries |
| **Architecture docs** | System design, component relationships | Complex systems, team onboarding |
| **Decision records (ADRs)** | Why decisions were made | Long-lived projects, team handoffs |
| **Runbooks** | How to operate/troubleshoot | Production systems |
| **Context docs** | AI agent context | AI-assisted development (sprint skill creates these) |
| **Changelogs** | What changed per version | Released software, libraries |
| **Inline comments** | Explain "why" (not "what") | Non-obvious logic |
| **Docstrings** | Function/class documentation | Reusable code, libraries |

---

## Tools

**Brainstorm with user to determine which tools fit their workflow.**

| Tool | Use Case |
|------|----------|
| **Markdown** | General docs, READMEs, most text documentation |
| **Mermaid** | Diagrams as code (architecture, flow, sequence) |
| **OpenAPI/Swagger** | REST API documentation |
| **Docstrings** | In-code documentation (Python, JS, TS) |
| **MkDocs** | Static documentation site from markdown |
| **Sphinx** | Python-specific, auto-generates from docstrings |
| **Confluence** | Team wikis, living documentation |
| **TypeDoc** | TypeScript API documentation |

---

## AI Agent Context Documents

For AI-assisted development workflows:

| Document | Created By | Purpose |
|----------|------------|---------|
| **PLAN.md** | Sprint skill (Manager) | Sprint goals, chunks, approach |
| **CURRENT-STATE.md** | Sprint skill | Progress tracking, session continuity |
| **Implementation plans** | Implementer | Detailed task instructions |
| **SPRINT-SUMMARY.md** | Manager | Lessons learned, carry-forward items |

These are created during sprints and may need tidying for long-term reference.

---

## Expand During Brainstorming

For each project, determine:

1. What documentation types are needed?
2. What tools will be used?
3. Who maintains each document?
4. Where does documentation live? (repo, Confluence, both?)
5. What's the minimum viable documentation for this tier?
