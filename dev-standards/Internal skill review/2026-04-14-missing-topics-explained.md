# Missing Topics Explained From First Principles

Date: 2026-04-14

## Why This File Exists

The main review says the `dev-standards` skill is a good handbook for API-centric HTTP services, but not yet a complete production engineering handbook.

This file explains what those missing areas actually are, from the ground up, for someone who mostly builds web backends.

The key idea is simple:

- an **HTTP app** teaches you how to handle a request correctly
- a **production system** teaches you how the whole service behaves over time, under failure, at scale, and in a real cloud environment

These are not separate worlds. The missing topics are mostly the parts of normal web development that start to matter once the app is used heavily, integrated with other systems, or run by a team in production.

## The Mental Model

When people say "backend web development", they often imagine this:

1. Client sends HTTP request
2. App validates input
3. App runs business logic
4. App queries database
5. App returns HTTP response

That is real, and it is important.

But a real production web app often also does this:

1. Accept request
2. Write a record
3. Put work onto a queue
4. Worker processes it later
5. Another service is called asynchronously
6. Metrics, logs, and traces are shipped somewhere
7. Secrets are loaded from the cloud runtime
8. Deploy happens while users are still active
9. An outage happens and the team has to recover safely

That second layer is what the current handbook covers only partially.

## 1. Event-Driven Systems

### What It Is

An event-driven system is a system where some work happens **later** or **somewhere else**, not directly inside the original HTTP request.

Instead of:

- request comes in
- all work finishes now
- response goes back

you get:

- request comes in
- app records intent
- app emits an event or queue message
- another process handles the next step

### Why This Exists

You do this when work is:

- slow
- expensive
- retryable
- independent
- better handled outside the user's request path

### Common Web App Examples

- user signs up, and a background worker sends the welcome email
- user uploads a CSV, and a worker processes it over several minutes
- payment succeeds, and several downstream systems are notified asynchronously
- an incoming webhook is stored, acknowledged quickly, then processed by a worker

### Core Concepts

#### Queue

A queue is a holding area for work to be done later.

Example:

- API receives "process this file"
- API stores job request
- API pushes message onto queue
- worker pulls message and does the actual processing

#### Event

An event is a fact that happened.

Examples:

- `user.created`
- `invoice.paid`
- `document.uploaded`

The important idea is that the publisher says "this happened", not "you must call this function now".

#### Worker / Consumer

A worker is the process that takes queued or evented work and performs it.

#### Idempotent Consumer

An idempotent consumer is one that can safely process the same message more than once.

This matters because queues and event buses often deliver the same message more than once.

If the worker is not idempotent:

- one message can send two emails
- one webhook can create two invoices
- one retry can charge twice

#### Dead-Letter Queue

A dead-letter queue is where messages go after repeated failure.

That stops one broken message from blocking the whole system forever.

#### Poison Message

A poison message is a message that always fails because the payload is invalid, the code is wrong, or a business rule is impossible to satisfy.

#### Visibility Timeout

In queue systems like SQS, a worker can temporarily hide a message while processing it. If the worker crashes, the message becomes visible again and someone else can retry it.

### Why This Is Missing From A Pure HTTP Handbook

HTTP handbooks assume work begins and ends inside one request.

Event-driven systems force you to think about:

- retries
- duplicate delivery
- partial failure
- ordering
- replay
- delayed processing
- worker health

Those are different engineering problems from "what status code should this endpoint return?"

### What A Strong Handbook Would Cover

- queues vs events vs scheduled jobs
- idempotent consumers
- DLQs and poison-message handling
- outbox pattern
- partial batch failure
- visibility timeout and retry strategy
- worker observability and backpressure

## 2. Cloud Runtime and AWS-Native Operations

### What It Is

This is the layer where your application stops being just code and becomes a process running inside a specific cloud environment.

On AWS, your app might run on:

- Lambda
- ECS
- EKS
- EC2

Each one changes how startup, shutdown, scaling, logging, health, secrets, and networking behave.

### Why This Exists

Your code does not run in a vacuum.

The runtime decides:

- how instances start
- how they stop
- how credentials are provided
- how traffic reaches them
- how they scale
- what "healthy" means

### Core Concepts

#### IAM Role

An IAM role is the identity your workload uses to call AWS services.

This is the cloud equivalent of "who is this process?"

It controls whether your app can:

- read a secret
- write to S3
- publish to SNS
- read from SQS

#### Least Privilege

Give the workload only the permissions it actually needs.

If an API service only needs to read one secret and write one S3 bucket, it should not also be able to delete DynamoDB tables or read every secret in the account.

#### Secret Retrieval

In production, secrets often come from:

- AWS Secrets Manager
- SSM Parameter Store

This is different from local `.env` usage.

#### Runtime Model

Different runtimes behave differently:

- Lambda: short-lived, event-driven, cold starts, no normal server process
- ECS: long-running containers, health checks, rolling deploys
- EKS: Kubernetes orchestration, probes, pod lifecycle, sidecars

### Common Web App Examples

- API on ECS reads DB credentials via task role and secret injection
- worker on Lambda consumes SQS messages with retries and DLQ behavior
- app on EKS uses readiness probes and autoscaling

### Why This Matters Even For "Normal Web Apps"

Because your API's behavior during deploys, incidents, and scale events depends on the runtime.

A handbook that only explains route handlers misses:

- IAM design
- secret access model
- health check semantics
- container lifecycle
- platform-driven retries

### What A Strong Handbook Would Cover

- IAM roles and least privilege
- Secrets Manager vs SSM Parameter Store vs AppConfig
- ECS vs Lambda vs EKS operational differences
- health checks in AWS terms
- ADOT / X-Ray / CloudWatch integration basics
- security implications like IMDS and SSRF

## 3. Security Beyond Basic Web Vulnerabilities

### What It Is

This is the part of security that goes beyond classic web-app bugs like SQL injection and XSS.

The current skill covers the basics well. The missing part is the production-depth layer.

### Why This Exists

In real systems, security failures often come from:

- bad token validation
- weak cloud permissions
- exposed internal metadata services
- unsafe file handling
- SSRF
- poor key rotation

not only from raw SQL concatenation.

### Core Concepts

#### OIDC / OAuth

These are standardized ways of handling identity and delegated access.

Very roughly:

- **OIDC** answers "who is this user?"
- **OAuth** answers "what access has been granted?"

In modern apps, you often rely on an identity provider instead of building auth from scratch.

#### JWT Validation

A JWT is not safe just because it is signed.

You also need to check:

- issuer
- audience
- expiry
- algorithm
- signing key rotation

#### JWKS

A JWKS endpoint publishes public keys used to validate tokens.

If keys rotate and your app does not handle that properly, auth breaks or becomes insecure.

#### SSRF

Server-Side Request Forgery means an attacker tricks your server into making requests to internal resources.

On AWS this matters because internal metadata endpoints can expose credentials if not protected.

#### File Upload Safety

File uploads are not just bytes to save somewhere.

You need to think about:

- file type validation
- malware scanning
- decompression bombs
- path traversal
- access control

### Common Web App Examples

- app accepts user-uploaded CSVs or PDFs
- app consumes tokens from Auth0 or Cognito
- app fetches URLs submitted by users
- internal admin tools rely on cloud credentials

### What A Strong Handbook Would Cover

- production-grade JWT/OIDC validation
- provider-based auth tradeoffs
- SSRF and metadata-service exposure
- file upload handling
- path traversal and unsafe deserialization
- workload IAM boundaries and cloud security assumptions

## 4. Delivery and Runtime Hardening

### What It Is

This is about the thing you deploy, not only the source code.

If your app is packed into a container or artifact, the artifact itself has a security and reliability posture.

### Why This Exists

You can have perfectly good application code and still ship an unsafe runtime.

Examples:

- container runs as root
- image includes unnecessary tools
- deployment uses mutable tags like `latest`
- rollback deploys a different build than staging tested

### Core Concepts

#### Immutable Artifact

Build one artifact once, then promote that exact artifact through environments.

This avoids:

- "it worked in staging but production was built slightly differently"

#### Image Digest Pinning

Deploy by content hash, not just a tag.

`myapp:latest` can change.
`sha256:...` refers to one exact image.

#### Non-Root Runtime

Your app process should not run as the Linux root user unless absolutely necessary.

#### Distroless / Minimal Images

Smaller runtime images reduce attack surface and often improve startup and patch management.

### Common Web App Examples

- Python FastAPI app deployed in Docker
- Node API container running on ECS
- CI builds image, pushes to ECR, deploys to ECS

### What A Strong Handbook Would Cover

- build-once promote-many
- image digests
- non-root users
- minimal images
- runtime limits and resource sizing
- rollback via deployment alarms, not only manual judgment

## 5. Data Operations and Recovery

### What It Is

This is the part of engineering that answers:

- what if data is lost?
- what if a migration damages rows?
- what if someone deletes the wrong table?

### Why This Exists

A database is not production-ready just because:

- schemas are validated
- migrations exist
- queries are typed

That covers correctness during normal operation.

Recovery is about abnormal operation.

### Core Concepts

#### Backup

A copy of your data that can be restored later.

#### Restore

Actually recovering from backup into a usable state.

This is the important part. Many teams have backups they have never successfully restored.

#### RPO

Recovery Point Objective.

How much data can you afford to lose?

Example:

- RPO of 5 minutes means losing the last 5 minutes of writes is acceptable

#### RTO

Recovery Time Objective.

How long can recovery take?

Example:

- RTO of 1 hour means the system must be usable again within 1 hour

### Common Web App Examples

- restore a Postgres database after accidental destructive migration
- recover deleted user records
- replay a queue or rehydrate derived tables after a failure

### What A Strong Handbook Would Cover

- backup strategy
- restore drills
- retention rules
- failover strategy
- recovery runbooks
- how migrations interact with recovery

## 6. Performance and Capacity

### What It Is

This area answers:

- can the app stay fast under realistic load?
- where are the bottlenecks?
- how much traffic can it handle?
- how much does it cost to run?

### Why This Exists

A system can be functionally correct and still fail in production because:

- queries get too slow
- cache misses pile up
- connection pools saturate
- one endpoint becomes too expensive
- logs and metrics cost too much

### Core Concepts

#### Caching

Caching stores expensive-to-compute or expensive-to-fetch data closer to where it is needed.

Examples:

- caching DB query results
- caching rendered API responses
- caching auth metadata or configuration

#### Cache Invalidation

The hard part of caching is deciding when old cached data is no longer valid.

#### Capacity Planning

Estimating what resources the system needs under expected and peak load.

#### Load Testing

Generating realistic traffic to see how the system behaves under stress.

#### Latency Budget

If your API should respond in 500ms total, and it calls three downstream services, each dependency only gets a portion of that time budget.

### Common Web App Examples

- dashboard endpoint becomes slow after customer count grows
- background jobs starve the DB connection pool
- trace volume becomes too expensive
- a cache hides DB cost until invalidation bug causes a thundering herd

### What A Strong Handbook Would Cover

- caching patterns
- load and stress testing
- connection-pool saturation
- query budgets
- performance regression testing
- observability cost controls

## 7. Incident Operations

### What It Is

Incident operations is the discipline of responding well when production breaks.

### Why This Exists

Failures happen even in good systems.

Production maturity is not only:

- how many bugs you prevent

It is also:

- how quickly you detect them
- how clearly you coordinate
- how safely you recover
- how well you learn afterwards

### Core Concepts

#### On-Call

A defined person is responsible for responding when something urgent breaks.

#### Severity

A shared scale for how bad an incident is.

Example:

- Sev 1: major user-facing outage
- Sev 2: serious degradation
- Sev 3: minor issue

#### Runbook

A step-by-step guide for how to investigate or recover from a known class of problem.

#### Postmortem

A structured write-up after the incident explaining:

- what happened
- why it happened
- what worked
- what did not
- what will change

### Common Web App Examples

- deploy causes 500s
- queue backlog explodes overnight
- DB pool exhaustion causes cascading latency
- token validation starts failing after key rotation

### What A Strong Handbook Would Cover

- incident roles
- severity model
- alert ownership
- runbook standards
- postmortem expectations
- rollback and communication during incidents

## 8. Supply Chain and Artifact Integrity

### What It Is

This is about trusting what you build and deploy.

Not just "did `npm install` work?" but:

- what dependencies are in the build?
- where did they come from?
- was the artifact tampered with?
- can we prove which source produced which deployment?

### Why This Exists

Modern systems use a large number of third-party packages and build steps.

A compromise in the build chain can affect production even if your own code is fine.

### Core Concepts

#### SBOM

Software Bill of Materials.

A list of what components are inside the software artifact.

#### Provenance

Evidence of where the artifact came from and how it was built.

#### Signing

Cryptographically asserting that an artifact or release came from a trusted builder or publisher.

### Common Web App Examples

- Node app depends on hundreds of transitive packages
- Python service deploys a container built in CI
- security team wants to know whether a vulnerable package is present in deployed artifacts

### What A Strong Handbook Would Cover

- SBOM basics
- provenance and trusted builds
- artifact signing
- dependency admission policy
- deploying only verified artifacts

## Why These Topics Still Matter If You Mostly Build HTTP Apps

If you mostly build APIs, admin backends, dashboards, internal tools, and SaaS backends, you may think:

"I am not building distributed systems. I am building normal web apps."

That is fair.

But normal web apps usually become all of the following once they are successful:

- they have background jobs
- they send emails asynchronously
- they consume webhooks
- they use queues
- they deploy with zero downtime
- they rely on cloud IAM and secret management
- they need backups and restores
- they get paged when things break

So the missing topics are not "advanced topics for some completely different kind of software".

They are the next layer of the same web apps you already build.

## What Is Most Important For This Skill's Likely Audience

If `dev-standards` is meant for the kind of HTTP services the owner usually builds, the most valuable next additions would probably be:

1. Event-driven systems for background jobs, queues, and webhooks
2. AWS runtime concerns: IAM, secrets, ECS/Lambda/EKS behavior
3. Performance and capacity for APIs and workers
4. Recovery: backups, restore drills, migration safety plus recovery thinking
5. Production auth depth: OIDC/JWT validation and cloud security implications
6. Incident operations and runbook quality

Those topics would extend the handbook naturally without changing its core identity as a web-backend engineering skill.

## Bottom Line

The current handbook already covers a large portion of backend web engineering.

What it does not yet cover well is:

- work that happens outside the request
- cloud runtime behavior
- recovery and operational response
- deeper security and artifact trust
- performance and scale as first-class concerns

That is the difference between:

- "a strong handbook for building HTTP services"

and:

- "a comprehensive handbook for production software engineering"
