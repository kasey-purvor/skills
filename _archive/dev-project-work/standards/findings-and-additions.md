# Findings and Future Additions

> **Superseded.** This file is a legacy consolidation. New findings should be added as a dated review file under `Internal skill review/`, not here. See `standards/README.md` ("Iterative nature") for the current process.

Consolidated from the 2026-04-14 internal skill review and the 2026-04-16 production audit. This is the single source of truth for "what could be improved in this skill." The original review files in `Internal skill review/` are historical reference.

Last updated: 2026-04-17

---

## Recently addressed (2026-04-16)

These items from the 2026-04-14 review or the 2026-04-16 audit have been added to topic files:

| Item | Resolution |
|------|------------|
| No product analytics coverage | New topic file: `topics/product-analytics.md` |
| No frontend logging guidance | New section in `topics/logging.md` — "Frontend Logging" |
| Security topic thin on authorization (RBAC, ABAC, privilege escalation) | New section in `topics/security.md` — "Authorization Models" |
| Configuration topic assumes persistent startup (no serverless guidance) | New section in `topics/configuration.md` — "Serverless Configuration" |

---

## Code quality issues in existing examples

Bugs or unsafe patterns in the current topic files. From the 2026-04-14 review. Should be fixed before examples are copied into real projects.

### Critical

| Issue | File | Detail |
|-------|------|--------|
| `z.coerce.boolean()` is unsafe for env vars | `configuration.md:41, :327` | Follows JS truthiness — `"false"` and `"0"` become `true`. Feature flags and security toggles can silently flip on |

### High

| Issue | File | Detail |
|-------|------|--------|
| Idempotency-key pattern is race-prone | `resilience.md:254-290` | Both examples do `lookup -> side effect -> save`. Duplicate side effects under concurrency |
| Node graceful-shutdown example closes deps before draining requests | `resilience.md:324-346` | Live requests fail during deploys |
| TypeScript error `cause` handling is internally inconsistent | `error-handling.md:58, :84, :206, :541` | Constructor signatures and example calls don't match |
| Observability mixes incompatible tracing models | `logging.md:105-286`, `monitoring.md:287` | Request ID, correlation ID, custom `x-trace-id`, and W3C `traceparent` treated as interchangeable |
| Monitoring examples encourage high-cardinality labels | `monitoring.md:127-463` | Path labels without explicit low-cardinality rule. Expensive in Datadog/CloudWatch |
| Retry helpers default to retrying everything | `resilience.md:60-127` | Contradicts the text's own advice. Validation/auth/business-logic failures get retried |
| Schema evolution examples show unsafe patterns | `schema-evolution.md:31-349` | Some examples demonstrate exactly what the chapter warns against |
| Cursor pagination overstated | `api-design.md:158-170` | "No duplicates, no missed items" without qualification about deterministic sort order |
| Data-integrity chapter weak for DynamoDB-style systems | `data-integrity.md:224-458` | Understates conditional writes, optimistic locking, transactions |

### Medium (12 items)

See `Internal skill review/2026-04-14-dev-standards-review.md` Medium Findings section for full list. Summary:

- API chapter missing conditional updates (ETag, If-Match)
- JSON field naming tied to backend language
- Configuration examples internally inconsistent (YAML snake_case vs JSON camelCase)
- SKILL.md audit completeness ambiguous
- FastAPI validation not integrated into error-response standard
- RFC 9457 field semantics inconsistent in examples
- Python logging examples lose traceback context
- Process-level error handlers too abrupt
- Feature-flag guidance internally inconsistent
- ECS health-check mapping inaccurate
- RED examples hard-code "errors = 5xx only"
- Pydantic discriminated union example not actually modeled as one

---

## Missing topic areas

Production engineering areas not yet covered by any topic file. Grouped by how likely they are to matter for the projects this skill is currently used on.

### Likely needed soon

| Topic area | What it covers | Why not added yet |
|------------|---------------|-------------------|
| **Event-driven systems** | Queues, async workers, dead-letter queues, idempotent consumers, poison messages, outbox pattern, partial batch failure | No current project uses message queues. ETL cron jobs are the closest thing. Add when a project introduces BullMQ, Celery, SQS, or similar |
| **Data operations and recovery** | Backup strategy, restore testing, disaster recovery, retention, failover, recovery runbooks | Current projects use managed databases (Supabase) with provider-managed backups. Add when a team needs to own their recovery strategy |
| **Incident operations** | On-call expectations, severity levels, incident command, postmortems, alert ownership, runbooks | No team yet has on-call rotation or incident response process. Add when a product reaches that maturity |

### Relevant but not urgent

| Topic area | What it covers | Why not added yet |
|------------|---------------|-------------------|
| **Performance and capacity** | Caching strategy, cache invalidation, load testing, capacity planning, latency budgets, query performance, connection pool tuning, observability cost controls | No current project has hit performance problems. Add when one does |
| **Security depth** | OIDC/OAuth production patterns, JWT validation (issuer, audience, key rotation, JWKS), file upload safety, path traversal, SSRF, insecure deserialization | Authorization section added 2026-04-16. Remaining items are deeper production auth and cloud security surfaces. Add incrementally |
| **Log aggregation pipeline** | Shipping logs to Datadog, CloudWatch, ELK. The gap between "write structured logs" and "see them somewhere useful" | Explicitly out of scope (infrastructure), but the gap is real. Revisit |

### Not yet relevant

| Topic area | What it covers | Why not added yet |
|------------|---------------|-------------------|
| **Cloud runtime / AWS-native operations** | IAM roles, least privilege, temporary credentials, Secrets Manager vs SSM, IMDS/SSRF, ECS vs Lambda vs EKS operational differences, ADOT/X-Ray | Current projects deploy on Vercel + Supabase, not AWS. Valuable when projects use AWS runtimes directly |
| **Delivery and runtime hardening** | Container image hardening, non-root users, distroless images, immutable artifact promotion, image digest pinning, deployment alarms, autoscaling | No current project uses containers. Add when one does |
| **Supply chain and artifact integrity** | SBOM, provenance, signing, dependency admission policy | Lockfiles and `npm audit` are covered in deployment. Full supply chain is overkill for current project scale |
| **API schema evolution** | GraphQL schema changes, protobuf field deprecation | No current project uses GraphQL or protobuf |
| **Real user monitoring (RUM)** | Core Web Vitals, LCP, FID, frontend performance metrics | Product analytics covers user behaviour. RUM is performance. Add when a project needs performance budgets |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-04-14 | Initial internal skill review — 1 critical, 9 high, 12 medium code issues. 8 missing topic areas identified |
| 2026-04-16 | Production audit of Orbit CRM. Added product-analytics topic, frontend logging, authorization models, serverless configuration sections |
| 2026-04-17 | Consolidated 2026-04-14 review and 2026-04-16 audit findings into this single file |
