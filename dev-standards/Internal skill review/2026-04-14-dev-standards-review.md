# Dev Standards Internal Skill Review

Date: 2026-04-14

## Scope

Reviewed:

- `SKILL.md`
- `topics/api-design.md`
- `topics/configuration.md`
- `topics/data-integrity.md`
- `topics/deployment.md`
- `topics/error-handling.md`
- `topics/logging.md`
- `topics/monitoring.md`
- `topics/resilience.md`
- `topics/schema-evolution.md`
- `topics/security.md`
- `topics/testing.md`

## Overall Assessment

This is a strong handbook for API-centric HTTP services and a good teaching reference for mid-level Python and TypeScript engineers.

It is not yet a comprehensive production engineering handbook for AWS-oriented teams. The biggest issues are:

- a few pieces of guidance are unsafe if copied literally
- some cross-topic examples contradict each other
- several production topics are missing entirely, especially event-driven systems, cloud runtime concerns, and operational maturity topics

## Top Priority Findings

### Critical

1. `configuration.md` recommends `z.coerce.boolean()` for env vars.
   - References: `topics/configuration.md:41`, `topics/configuration.md:327`
   - Problem: in Zod this follows JavaScript truthiness, so values like `"false"` and `"0"` become `true`.
   - Impact: feature flags, debug flags, and security-sensitive toggles can silently flip on.

### High

1. The idempotency-key pattern is race-prone.
   - References: `topics/resilience.md:254`, `topics/resilience.md:261`, `topics/resilience.md:268`, `topics/resilience.md:271`, `topics/resilience.md:278`, `topics/resilience.md:285`, `topics/resilience.md:290`
   - Problem: both examples do `lookup -> side effect -> save`.
   - Impact: duplicate side effects under concurrency, including double charges.

2. The Node graceful-shutdown example is unsafe.
   - References: `topics/resilience.md:324`, `topics/resilience.md:328`, `topics/resilience.md:340`, `topics/resilience.md:341`, `topics/resilience.md:346`
   - Problem: it closes dependencies before waiting for in-flight requests to finish.
   - Impact: live requests can fail during deploys.

3. TypeScript error `cause` handling is internally inconsistent.
   - References: `topics/error-handling.md:58`, `topics/error-handling.md:84`, `topics/error-handling.md:206`, `topics/error-handling.md:541`
   - Problem: constructor signatures and example calls do not match.
   - Impact: copied examples will either fail type-checking or lose error-chain semantics.

4. Observability guidance mixes incompatible tracing models.
   - References: `topics/logging.md:105`, `topics/logging.md:130`, `topics/logging.md:195`, `topics/logging.md:286`, `topics/monitoring.md:287`
   - Problem: request ID, correlation ID, custom `x-trace-id`, and W3C `traceparent` are treated as interchangeable.
   - Impact: fragmented tracing in OpenTelemetry and AWS ADOT/X-Ray style setups.

5. Monitoring examples encourage high-cardinality labels.
   - References: `topics/monitoring.md:127`, `topics/monitoring.md:144`, `topics/monitoring.md:463`
   - Problem: path labels are shown without an explicit low-cardinality rule.
   - Impact: expensive and noisy metrics in Datadog and CloudWatch.

6. Retry helpers default to retrying everything.
   - References: `topics/resilience.md:60`, `topics/resilience.md:66`, `topics/resilience.md:97`, `topics/resilience.md:103`, `topics/resilience.md:119`, `topics/resilience.md:127`
   - Problem: the safe default contradicts the text's own advice.
   - Impact: validation, auth, and business-logic failures can get retried unnecessarily.

7. Schema evolution guidance is conceptually strong but example quality is inconsistent.
   - References: `topics/schema-evolution.md:31`, `topics/schema-evolution.md:37`, `topics/schema-evolution.md:84`, `topics/schema-evolution.md:85`, `topics/schema-evolution.md:300`, `topics/schema-evolution.md:349`
   - Problem: some examples show exactly the unsafe migration patterns the chapter warns against.
   - Impact: copy-paste risk for real migrations.

8. Cursor pagination is overstated.
   - References: `topics/api-design.md:158`, `topics/api-design.md:170`
   - Problem: the text says cursor pagination means "no duplicates, no missed items" without qualification.
   - Impact: readers miss the need for deterministic sort order and stable cursor fields.

9. The data-integrity chapter is too weak for DynamoDB-style systems.
   - References: `topics/data-integrity.md:224`, `topics/data-integrity.md:415`, `topics/data-integrity.md:445`, `topics/data-integrity.md:458`
   - Problem: it understates conditional writes, optimistic locking, and transactional patterns, and the transaction prose is loose around rollback.
   - Impact: weak guidance for AWS-heavy teams.

## Medium Findings

1. The API chapter never covers conditional updates.
   - References: `topics/api-design.md:42`, `topics/api-design.md:195`
   - Missing: `ETag`, `If-Match`, version fields, optimistic concurrency at the contract layer.

2. JSON field naming is tied to backend language.
   - References: `topics/api-design.md:116`, `topics/api-design.md:117`, `topics/api-design.md:348`
   - Problem: wire format should be a product/API decision, not a Python vs TypeScript implementation detail.

3. Configuration examples are internally inconsistent.
   - References: `topics/configuration.md:186`, `topics/configuration.md:206`, `topics/configuration.md:219`
   - Problem: the chapter shows YAML with `snake_case` keys, then TypeScript code reads JSON with `camelCase` keys.

4. `SKILL.md` makes audit completeness ambiguous.
   - References: `SKILL.md:49`, `SKILL.md:115`
   - Problem: missing project files mean "not considered yet", but later irrelevant topics may omit files entirely.

5. FastAPI validation is not fully integrated into the handbook's error-response standard.
   - References: `topics/error-handling.md:112`, `topics/error-handling.md:294`, `topics/error-handling.md:315`, `topics/error-handling.md:453`, `topics/error-handling.md:495`
   - Problem: request validation will still return framework-default payloads unless handled separately.

6. RFC 9457 field semantics are inconsistent in examples.
   - References: `topics/error-handling.md:259`, `topics/error-handling.md:303`, `topics/error-handling.md:475`, `topics/error-handling.md:477`
   - Problem: handlers put detailed error text into `title` instead of using `detail`.

7. Python logging examples lose traceback context.
   - References: `topics/logging.md:89`, `topics/error-handling.md:297`, `topics/error-handling.md:299`, `topics/error-handling.md:317`
   - Problem: examples log only strings, not exception info.

8. Process-level error handlers are too abrupt.
   - References: `topics/error-handling.md:423`, `topics/error-handling.md:424`, `topics/error-handling.md:441`, `topics/error-handling.md:442`, `topics/error-handling.md:447`
   - Problem: they exit immediately without a stronger connection to draining and flush behavior.

9. Feature-flag guidance is internally inconsistent.
   - References: `topics/deployment.md:71`, `topics/deployment.md:78`, `topics/deployment.md:82`
   - Problem: the text explains runtime release control, then recommends env vars as a feature flag mechanism.

10. ECS health-check mapping is inaccurate.
    - References: `topics/resilience.md:453`, `topics/resilience.md:457`, `topics/resilience.md:458`
    - Problem: ECS container health checks, ALB target-group health checks, and grace periods are collapsed into one simplified model.

11. The RED examples hard-code "errors = 5xx only".
    - References: `topics/monitoring.md:129`, `topics/monitoring.md:146`, `topics/error-handling.md:490`, `topics/error-handling.md:495`
    - Problem: that can be a valid SLI definition, but it is presented like a rule rather than a deliberate policy choice.

12. The Pydantic discriminated union example is not actually modeled as a discriminated union.
    - References: `topics/data-integrity.md:345`, `topics/data-integrity.md:346`

## Missing Topics

These are the biggest missing areas if the skill is intended to be a professional productionization handbook for the sort of web services normally deployed on AWS.

### 1. Event-Driven Systems

Missing:

- queues and async workers
- SQS, SNS, EventBridge, Kinesis style processing
- poison messages
- dead-letter queues
- visibility timeout
- partial batch failure
- idempotent consumers
- outbox and inbox patterns

Why this matters:

Many web apps are not only "receive HTTP request, return HTTP response". They also send emails asynchronously, process uploads later, consume webhooks through queues, fan out background work, and integrate with other services through events.

### 2. Cloud Runtime and AWS-Native Operations

Missing:

- IAM roles and least privilege for workloads
- temporary credentials and STS
- KMS and envelope encryption concepts
- Secrets Manager vs SSM Parameter Store vs AppConfig
- IMDSv2 and SSRF implications
- ALB, ECS, EKS, Lambda runtime differences
- ADOT or X-Ray collector patterns

Why this matters:

On AWS, production behavior is shaped heavily by the runtime environment, not just the application code.

### 3. Security Beyond Basic Web Vulnerabilities

Missing:

- OIDC and OAuth production patterns
- JWT issuer, audience, key rotation, JWKS, revocation tradeoffs
- file upload safety
- path traversal
- insecure deserialization
- SSRF
- cloud perimeter controls like WAF and network assumptions

Why this matters:

The current security chapter is good on classic web attacks, but thinner on production auth and cloud-runtime attack surfaces.

### 4. Delivery and Runtime Hardening

Missing:

- container image hardening
- non-root users
- distroless or slim runtime images
- immutable artifact promotion
- image digest pinning
- deployment alarms and automatic rollback
- autoscaling and resource requests/limits

Why this matters:

A production web service is not just source code plus CI. It is also the built artifact and the runtime envelope around it.

### 5. Data Operations and Recovery

Missing:

- backup strategy
- restore testing
- disaster recovery
- retention and archival
- failover tradeoffs
- data recovery runbooks

Why this matters:

A database is not productionized just because migrations exist. Recovery capability is part of production readiness.

### 6. Performance and Capacity

Missing:

- caching strategy
- cache invalidation
- query budgets
- load testing
- capacity planning
- latency budgets across dependencies
- cost controls for logs, traces, and metrics

Why this matters:

HTTP correctness is not enough if the service collapses under realistic load or becomes too expensive to operate.

### 7. Incident Operations

Missing:

- on-call expectations
- severity levels tied to response
- incident command basics
- postmortems
- ownership of alerts and runbooks

Why this matters:

Production software engineering includes how teams respond when things fail, not only how they try to prevent failure.

### 8. Supply Chain and Artifact Integrity

Missing:

- SBOM
- provenance and signing
- artifact integrity
- dependency policy and admission rules

Why this matters:

Lockfiles are good, but modern production engineering also cares about what artifact was built, from which source, and whether it can be trusted.

## What This Handbook Already Does Well

1. Strong first-principles teaching style instead of shallow checklists.
2. Good structure in `SKILL.md` around design-time, review, and implementation reference modes.
3. Strong data-integrity framing around trust boundaries.
4. Good explanation of operational vs programming errors.
5. Good expand-and-contract explanation for schema changes.
6. Strong testing chapter for API-centric systems.

## Bottom Line

If the intended scope is "how to build robust API-centric web services in Python and TypeScript", this handbook is already valuable.

If the intended scope is "comprehensive production software engineering handbook", it is not there yet.

The next improvement wave should be:

1. Fix unsafe and internally inconsistent examples.
2. Tighten AWS and observability guidance.
3. Add missing event-driven, cloud-runtime, recovery, and incident-management topics.
