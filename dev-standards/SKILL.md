---
name: dev-standards
description: Use when you need guidance on production code standards - covers testing, error handling, logging, security, configuration, monitoring, reliability, data integrity, and documentation. Also useful when deciding what to relax for exploratory or internal-only work.
---

# Standards

## Overview

**Reference skill.** Provides production engineering standards — patterns, tradeoffs, and anti-patterns — for building reliable software. This skill does NOT own any project files and does NOT decide where outcomes are recorded.

When loaded, it informs decisions. The user and/or calling skill (e.g., project planning, sprint development) decide which standards to adopt, and the calling skill records decisions in the appropriate project file (typically `conventions.md` in `.context/project/implementation/`).

## Production by Default

**If a system is intended for production, build it for production from the start.** Runtime schemas (Zod/Pydantic), boundary validation, structured error handling, and startup config validation are not things you "add later" — they're foundational. Retrofitting them is significantly more expensive than including them from the beginning. See the testing topic's Build Order for the recommended sequence.

**The only reason to relax standards is if the code genuinely might not survive** — exploratory spikes, proof-of-concepts, throwaway prototypes, internal-only tools. If you're relaxing standards, do it consciously: know what you're skipping, know the cost if the code does survive, and track what was skipped (e.g., in a backlog). See MATRIX.md for a quick reference of what each relaxation looks like.

**The common mistake:** labelling something a "prototype" while knowing it will go to production. This creates a retrofit tax — every shortcut becomes a backlog item that must be addressed before the system is safe for real users and real data.

## Structure

- `MATRIX.md` — Quick reference: what to relax for exploratory/internal work, and the cost of each relaxation
- `topics/*.md` — Deep guidance on each topic

## Topics and How They Relate

The nine topics aren't independent — they form clusters that reinforce each other.

**Data safety cluster** (these three form a layered defense system — see [Data Integrity](./topics/data-integrity.md) for the three-layer model):
- **Data Integrity** — what data looks like, how it's validated at boundaries, and how storage enforces correctness
- **Testing** — how you prove the data safety layers work, plus code correctness generally
- **Configuration** — how secrets and settings are managed, validated, and injected

These three should be considered together. A data model decision affects what tests you write. A configuration decision affects how you validate at boundaries. See the cross-references within each topic file.

**Runtime behaviour cluster** (how the system behaves under real conditions):
- **Error Handling** — what happens when things go wrong, how errors are categorised and surfaced
- **Reliability** — retries, timeouts, idempotency, circuit breakers — designing for failure
- **Security** — trust boundaries, input validation, secrets, auth

**Observability cluster** (can you understand what the system is doing?):
- **Logging** — what to record, structured vs. plain, verbosity
- **Monitoring** — metrics, alerting, dashboards
- **Documentation** — setup instructions, runbooks, decision records

## When to Read What

This skill is useful at different project phases. You don't need to read everything — pick the topics relevant to your current work.

**During design and planning** — shaping architecture decisions:
- **Data Integrity** — what schemas and contracts are needed? What are the validation boundaries? How does the database enforce correctness (or not)?
- **Configuration** — what's a secret vs. a tunable? How are settings loaded and validated?
- **Security** — what are the trust boundaries? Who can access what?
- **Error Handling** — what failure modes exist? What's retryable vs. fatal?

**During implementation planning** — writing detailed plans for engineers:
- **Testing** — what test types are needed? What edge cases should be specified? Is the code structured for testability? What's the build order?
- **Data Integrity** — are the schemas defined as runtime schemas (not just interfaces)? Are boundary contracts in place?
- **Reliability** — what happens when external calls fail? What needs idempotency?

**During code review and hardening** — assessing existing code:
- **All topics** are fair game, but start with:
- **Testing** — are the right test types present? Are boundaries validated?
- **Error Handling** — are errors categorised correctly? Is anything leaking to clients?
- **Configuration** — does startup validate required config? Are there production defaults?
- Load `dev-standards-pitfalls` alongside this skill to check for named anti-patterns.

## Usage

1. Determine what phase of work you're in (see above)
2. Read the relevant topic files for that phase
3. If relaxing standards for exploratory work, use MATRIX.md to understand the cost of each relaxation
4. Record any convention decisions in the appropriate project file

---

**Status:** Work in Progress
