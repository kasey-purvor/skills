# Research Instructions

These instructions apply to anyone doing research — the planning agent directly or a dispatched sub-agent. The rules are the same regardless of who reads this file.

## Core Principle

An LLM confidently stating wrong information is worse than saying "I don't know." Every finding must be verified against authoritative sources and explicitly tagged with its confidence level.

## When Patterns Apply (and When They Don't)

The pattern files in `patterns/` are guides for structured investigation — multi-question research that benefits from a consistent approach. Use them when the research is substantial enough that structure helps.

If the research doesn't fit a pattern — a quick factual lookup, a one-off question, something that's just common sense to go find — skip the pattern. Follow the source tiering and verification tagging rules from this file, and use your judgement. The patterns exist to help, not to bureaucratise every web fetch.

## Source Tiering

| Tier | Description | Trust Level |
|------|-------------|-------------|
| **1 — Official/Primary** | The authoritative source itself (government sites, official API docs, primary legislation, the actual API responses) | High — cite directly |
| **2 — Established Authority** | Recognised institutions that curate or explain primary sources (Cornell LII, university references, established professional bodies, official SDKs) | High — cross-check with Tier 1 when possible |
| **3 — Reputable Secondary** | Professional publications with editorial standards (textbooks, peer-reviewed journals) | Medium — verify key claims against Tier 1-2 |
| **Banned** | Reddit, Stack Overflow, forums, blog posts, Medium articles, Wikipedia, AI-generated content, unofficial tutorials | Never use — even if they appear correct |

## Verification Tags

Every finding must be tagged. No exceptions.

| Tag | Meaning |
|-----|---------|
| **Verified (Tier 1)** | Confirmed from official/primary source — cite the URL |
| **Verified (Tier 2)** | Confirmed from established authority — cite the URL |
| **Unverified** | Existing knowledge, not confirmed against sources |
| **Contradicted** | Expectation was wrong — source says otherwise |

**Contradicted is the most valuable tag.** It catches exactly the failure mode these rules exist to prevent.

## Output Format

Return findings as a structured, numbered report matching the research questions you were given. For each finding:

1. State the finding
2. Tag it (Verified Tier 1/2, Unverified, or Contradicted)
3. Cite the source URL for verified findings
4. For Contradicted findings: state what was previously assumed and what the source actually says

## Web Fetching

Use Scrapfly MCP tools for web access. Before any scraping, read the `scraping_instruction_enhanced` tool to understand current best practices.

- `web_scrape` — fetch and parse web content
- `web_get_page` — get raw page content
- `screenshot` — capture visual documentation when needed

Always check: "Is there an API/XML/JSON version, or just HTML/PDF?"

## Parallelisation

Dispatch multiple research tracks simultaneously when they are **independent** — the answer to one doesn't change the questions for another. Run sequentially when one track's findings inform the next track's questions.
