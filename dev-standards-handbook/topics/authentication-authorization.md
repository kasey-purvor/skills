# Authentication & Authorization

## The Problem

Every multi-user system answers two questions on every request: **who is this caller, and what are they allowed to do?** Authentication (AuthN) answers the first; authorization (AuthZ) answers the second. They sound alike, but different subsystems own each, and conflating them produces whole categories of vulnerability.

Most breach stories start here:
- A session check that never verified the user was authorised for *this specific resource* (BOLA — the #1 API vulnerability by volume).
- A token issued once and never rotated, then harvested from a log.
- A role checked in middleware but not in the direct database query underneath it.
- A tenant ID read from the request body instead of the authenticated session — change a parameter, read another tenant's data.

The vocabulary is dense (OIDC, JWKS, PKCE, SCIM) and the concepts layer up: protocol → token → session → policy → enforcement → data. This topic covers each layer at enough depth to read docs and security reviews without getting lost.

---

## Authentication vs Authorization

**Authentication (AuthN)** verifies identity — the result is a fact: *this request is from user `abc-123`*, usually carried as a signed token. **Authorization (AuthZ)** checks permission — the result is a decision: *may user `abc-123` do action X on resource Y?* — derived from the user's role, the resource, and sometimes the request context. It is not carried in the token.

The classic vulnerability is authenticated-but-not-authorised: an endpoint that confirms the caller is logged in, then acts on a resource ID from the URL without checking the caller owns it. A `DELETE /users/:id` that only verifies the token lets any user delete any account. Every state-changing or sensitive-read endpoint needs three checks:

1. **Authenticated** — is the session/token valid?
2. **Authorised for the resource** — do they own it, or have admin rights over it?
3. **Authorised for the action** — read but not write? view but not delete?

**Status codes:** return **401** when AuthN fails (no/invalid/expired token — the client should re-authenticate) and **403** when AuthN succeeded but AuthZ failed (re-authenticating won't help). Returning 401 where 403 is correct leaks whether the resource exists.

---

## OAuth 2.0 & OIDC

The most common confusion: **OAuth 2.0 is not about identity.** It's an authorization framework defining how a user lets App A access their data at Service B without sharing B's password. **OIDC** layers identity on top — a standard ID token (a JWT proving who the user is), standard claims (`sub`, `email`, …), a discovery document at `/.well-known/openid-configuration`, and a UserInfo endpoint. Because it's protocol-level, any OIDC app works against any OIDC provider (Google, Cognito, Auth0, Keycloak) with no provider-specific code; libraries like `oidc-client-ts` consume the discovery document and handle the rest.

**Grant types — which flow to use:**

| Grant type | Use case | Notes |
|-----------|----------|-------|
| **Authorization code + PKCE** | Browser SPAs, mobile, public clients | The modern default. PKCE removes the need for a client secret |
| **Authorization code (classic)** | Server-side apps that can hold a client secret | Fine when there's a confidential backend |
| **Client credentials** | Machine-to-machine, no user involved | Just a client ID + secret |
| **Refresh token** | New access token without re-login | Used alongside the others |
| **Resource owner password** | Direct username/password to the token endpoint | Deprecated — defeats the point of delegated auth |
| **Implicit** | SPAs, historically | Retired — leaked tokens via the redirect URL |

**PKCE in brief:** the client generates a random `code_verifier`, sends its hash as a `code_challenge` on the authorize request, and presents the original verifier when exchanging the returned code for tokens. If an attacker intercepts the code, they still can't exchange it — they don't have the verifier, which never left the original browser. A library handles every step; application code calls something like `signinRedirect()` and reads the user from the callback.

---

## Tokens

A JWT is a signed (not encrypted) token in three base64 parts — header (algorithm + key id), payload (claims: `sub`, `iss`, `exp`, `aud`, plus custom), and signature. The key property: anyone with the issuer's public key can verify it *without calling the issuer* — that's what makes auth stateless. **Never put secrets in the payload; anyone holding the token can read every claim.**

Most OIDC flows return three tokens, each with a different job:

| Token | Purpose | Sent to | Lifetime |
|-------|---------|---------|----------|
| **ID token** | Proves who the user is | Your app | Short (minutes) |
| **Access token** | Proves what they can access | Your API / downstream services | Short (5–60 min) |
| **Refresh token** | Buys new access tokens without re-login | The IdP token endpoint only | Long (days–weeks) |

Rule of thumb: ID token for identity inside the app, access token sent to APIs. (Some stacks, e.g. Cognito, conflate the two — don't rely on that in portable code.)

**Verification is a library/middleware one-liner in every framework — don't hand-roll it.** The mechanism worth understanding: the IdP publishes its public keys at a JWKS endpoint (`/.well-known/jwks.json`); the verifier reads the token's `kid`, finds the matching key (cached ~1h), checks the signature, then validates `iss`, `aud`, and `exp`. Key rotation works because `kid` lets old tokens verify against old keys until they expire. **Always pin the allowed algorithm and check `iss`/`aud`/`exp`** — the historic failures here are accepting `alg: none` or skipping the audience check. Cloud gateways often run this step before your code does.

**Browser token storage** — a real tradeoff with no universally right answer:

| Storage | Pro | Con |
|---------|-----|-----|
| `localStorage` | Simple; survives tab close | Readable by any script — XSS steals it |
| `sessionStorage` | Clears on tab close | Same XSS risk |
| `httpOnly` cookie | Not readable from JS | Sent automatically — CSRF concern, cross-origin complexity |
| In-memory | XSS can only steal during page life | Lost on refresh; needs a silent-refresh flow |

The SPA default (`localStorage`) accepts the XSS tradeoff because a bearer-token model avoids CSRF entirely; higher-assurance apps move to `httpOnly` cookies with CSRF tokens, or in-memory storage with silent refresh.

**Session shapes:** *opaque session tokens* (random ID in a cookie, state in Redis/DB — trivial revocation, one store lookup per request, common in server-rendered apps); *pure JWT* (stateless, no per-request lookup, but revocation is hard within the access-token TTL); and the *hybrid* most JWT systems actually run — short access-token TTL, **refresh-token rotation** (each refresh issues a new refresh token and invalidates the old, detecting replay), and a small **deny-list** for critical revocations (termination, password reset) checked in middleware.

---

## Passwords & MFA

If you manage passwords directly: **never store plain text, MD5, or raw SHA256** — all are too fast (attackers try billions of guesses per second). Use a purpose-built hash with a cost factor and a per-user salt: **bcrypt** (cost ~12) or **argon2** (memory-hard; the current pick for new systems). The salt defeats precomputed rainbow tables.

Password policy — NIST SP 800-63B reversed the advice most training still teaches:

| Old advice (still in many policy docs) | Modern advice |
|----------------------------------------|---------------|
| 8 chars, mixed character classes | Allow long passphrases (up to 64). Length beats complexity |
| Force rotation every 90 days | Don't — rotate only on evidence of compromise |
| Prohibit reuse of last N | Fine if cheap; modest benefit |
| Hints / security questions | Phase out — often easier to attack than the password |

Two things *are* worth enforcing: check passwords against known-breached lists (haveibeenpwned's k-anonymity API lets you do this without sending the full password), and rate-limit auth attempts per-IP and per-account.

**MFA**, weakest to strongest:

| Method | How it works | Weakness |
|--------|--------------|----------|
| **TOTP** | Authenticator app + shared secret, 6-digit code every 30s | Server breach leaks all seeds; users can still be phished |
| **SMS** | Code by text message | SIM-swap attacks; being phased out |
| **Push** | Approve/deny prompt on a registered device | "MFA fatigue" — spam prompts until the user approves |
| **WebAuthn / passkeys** | Device secure-enclave public-key crypto | Phishing-proof (origin-bound). Where the industry is heading |

Give every MFA setup a recovery path (one-time backup codes at enrolment). MFA is effectively mandatory for admin accounts, any role that can read other tenants' data, and customer accounts in regulated industries. Writing TOTP yourself is straightforward; WebAuthn is painful — lean on libraries or a managed provider.

---

## Account Flows

The lifecycle flows most user systems end up needing:
- **Email verification** — a signed, short-lived (15–60 min) link or code on signup.
- **Password reset** — a signed, one-time, short-TTL token by email; invalidate existing sessions after use.
- **Invite** — admin creates a user + role; a signed invite token is emailed; on acceptance the user sets a password (or registers via OIDC) and the role attaches.
- **Account linking** — one user record, multiple identities; link by verifying possession of each, never by matching email alone (email ownership can change).
- **Federated SSO** — a customer's corporate IdP (OIDC or SAML) trusted for their users only.
- **SCIM** — a protocol for enterprise IdPs to push user provisioning/deprovisioning; relevant once you have enterprise customers who expect deactivation to propagate automatically.

---

## Authorization Models

Once you know who the caller is, you need a consistent way to decide what they can do — scattered `if (user.role === 'admin')` checks become untrackable. Four named models cover most cases:

- **ACL (Access Control List)** — a per-resource list of who can do what. The earliest model; scales poorly as a primary model for SaaS.
- **RBAC (Role-Based Access Control)** — users have roles, roles have permissions, and the app checks the *permission*, not the role directly. The common default. Its variations matter because they change the data model: flat roles (`admin`, `user`); hierarchical (admin inherits editor); permissions-as-first-class (`can_upload_course` — grant narrow capabilities without inventing roles); per-resource roles (owner of A, viewer of B — collaboration tools); per-tenant roles (admin in Company A, viewer in B — needs tenant context on every decision).
- **ABAC (Attribute-Based Access Control)** — decisions computed from attributes of the user, the resource, and the context ("edit only *own* posts", "not if the record is locked"). More expressive, more complex. Most apps end up hybrid: RBAC for broad categories, attribute rules for resource-level checks.
- **ReBAC (Relationship-Based Access Control)** — access defined by graph relationships (the Google Zanzibar model; SpiceDB, OpenFGA). The right fit only when permissions are natively graph-shaped (shared docs, nested resources). Overkill otherwise.

**Where the live permission set comes from.** A role or permission baked into a token is a point-in-time snapshot, frozen until that token expires — gate on the token's role claim and a revoked admin stays an admin, a freshly-granted permission stays invisible, until the next refresh. Where grants and revocations must take effect promptly, keep only *identity* authoritative-from-token (`sub`, tenant, user id) and resolve the effective *permission set* from your store on each request, treating any role claim as an informational hint. The cost is one lookup on the authorization path; resolve it once and cache it for the life of the request (optionally for a short TTL across requests) to bound it. This is the thorough end of a spectrum; its cheaper neighbour keeps the token's claims authoritative and checks only a small revocation deny-list in middleware — so choose by how fast authorization changes must propagate.

---

## Policy Engines

When authz rules outgrow a few dozen checks, externalise them rather than scattering them through code:

| Engine | Shape | Rules language |
|--------|-------|----------------|
| **OPA** | Sidecar or library (CNCF-graduated) | Rego |
| **Oso** | In-process library | Polar |
| **Cerbos** | Sidecar or library | YAML |
| **AWS IAM** | Cloud-native; the reference document model | JSON |

Reach for one when authz rules must be editable by non-engineers, per-tenant policies diverge and hard-coded branches become painful, or compliance requires policy-as-code with an audit trail. Most small SaaS don't need them.

---

## Enforcement Layers

Production systems don't check authorization in one place — they layer defences so breaking any single one doesn't grant access:

| Layer | What it checks | Example |
|-------|---------------|---------|
| **Gateway / CDN** | Rate limits, WAF rules, token signature | Gateway JWT authoriser |
| **API middleware** | Role checks, feature flags | `requireAdmin` before the handler runs |
| **Business logic** | Ownership, resource-specific rules | the caller's org matches the resource's org |
| **Data layer** | Structural invariants bugs can't bypass | the store refuses rows outside the caller's tenant |

Most systems have the first three. Adding the data layer is the jump from "we always remember to check" to "the store refuses non-matching rows" — audit-grade isolation.

**Enforce server-side, display client-side.** Client-side checks are for UX only — hiding buttons, disabling forms. A determined user bypasses any of them. If the UI hides a button but the endpoint doesn't check, you have no security — just a hidden element.

**Privilege escalation through elevated contexts.** Stored procedures, serverless functions, and admin endpoints often run with elevated permissions because they need data the caller can't normally reach. The trap: if such a function takes a scope parameter (tenant ID, user ID) from the caller and doesn't independently verify the caller is authorised for that scope, any caller reads any scope by changing the parameter. The rule: a function that runs with more permission than its caller must verify the caller's authorisation for the requested scope itself. (This is the "Confused Deputy" pattern below.)

---

## Multi-Tenant Isolation

Multi-tenant systems turn every authorization question from "can this user do X?" into "can they do X *for this tenant*?" — and one missed tenant check silently leaks one customer's data to another. The tenant identity must always come from the authenticated session, never the request. Choosing an isolation strategy, enforcing the boundary in a scoped data layer, backing it with a database backstop (RLS on Postgres), and the deliberate cross-tenant exceptions are covered in full in [Multi-Tenant Isolation](./multi-tenant-isolation.md).

---

## Common Vulnerabilities

Named patterns worth recognising — most from the OWASP API Security Top 10:

| Vulnerability | What it is | Defence |
|---------------|-----------|---------|
| **BOLA** (Broken Object-Level Authorization) | `GET /orders/456` works because ownership wasn't checked. #1 API vulnerability by volume | Ownership check in every handler that takes an ID; better, data-layer isolation |
| **IDOR** (Insecure Direct Object Reference) | UUIDs as path params without an ownership check — a flavour of BOLA | Opaque IDs don't fix it; only authorisation does |
| **Broken Function-Level Authorization** | An admin endpoint exposed without the admin check | Role check on admin route groups; test with a non-admin token |
| **Mass Assignment** | `PATCH /users/me` accepts `{role: "admin"}` because the whole body is trusted | Allowlist accepted fields at the boundary (schema validation) |
| **Confused Deputy** | An elevated service acts on a user's behalf without verifying the user's authorisation | Carry user context into every decision (see Privilege escalation) |
| **JWT `alg: none`** | A library accepts an unsigned token and forged claims | Pin the allowed algorithms explicitly |
| **Expired / wrong-audience token accepted** | Verifier skipped `exp` / `aud` | Always validate `iss`, `aud`, and `exp` |

---

## Audit Logging

Compliance frameworks (SOC 2 CC6/CC7) require audit logs for authorization-relevant events — keep them separate from operational logs:

| Operational logs | Audit logs |
|------------------|-----------|
| Errors, warnings, debug traces | Who did what, when, to what, with what outcome |
| Retention: days–weeks | Retention: 1+ year |
| Often sampled | Never sampled |

Minimum fields per event: actor, action, resource, outcome, timestamp, request id. Log every authn event (login success/failure, logout, MFA outcome), every authorization denial, every state-changing action, and every admin / cross-tenant action.

---

## Managed vs Self-Hosted Identity

| Option | Examples | Why teams choose it | Tradeoff |
|--------|----------|---------------------|----------|
| **Managed IdP** | Cognito, Auth0, Clerk, Okta, Supabase Auth, WorkOS | Handles hashing, rate limiting, breach detection, MFA, recovery, federated/enterprise SSO. The default | Vendor dependency, per-MAU pricing at scale |
| **Self-hosted IdP** | Keycloak, Ory | Full control, air-gapped/regulated environments, no per-user pricing | You own operating an identity service |
| **Roll-your-own** | Custom | Total control | Auth is easy to get mostly right and hard to get fully right — most incidents come from homegrown systems |

Roll-your-own is rarely the right call beyond a hobby project: the downside is "every credential compromised" and the upside over a managed provider is small.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Store plain / MD5 / SHA256 passwords | bcrypt or argon2 with a cost factor | Weak hashing means stolen databases are cracked in minutes |
| Check authentication but not authorization | Verify permission for the specific resource and action | Authenticated ≠ authorised |
| Put secrets in a JWT payload | It's signed, not encrypted | Anyone with the token reads every claim |
| Read the tenant ID from the request body | Derive it from the authenticated session | Client-supplied tenant IDs let callers query any tenant |
| Pass request bodies straight into a write | Allowlist accepted fields at the boundary | Mass assignment escalates privileges |
| Accept `alg: none`; skip `iss`/`aud`/`exp` | Pin algorithms; validate claims | Forged or replayed tokens |
| Force password rotation every 90 days | Rotate only on evidence of compromise | Produces `Password1`, `Password2`; no security gain |
| Rely on client-side role checks | Enforce server-side; client is UX only | Any user disables the client check in devtools |
| Return 401 where 403 is the right answer | 401 = AuthN failure, 403 = AuthZ failure | Leaks whether a resource exists |
| Roll your own auth service | Use a managed IdP | Most incidents in this area come from homegrown auth |

---

## Deciding for Your Project

1. **Run your own identity?** No → a managed IdP. Yes → Keycloak or Ory. Rolling your own is rarely right.
2. **Token shape?** OIDC authorization code + PKCE for browser SPAs and mobile; client credentials for machine-to-machine.
3. **Tokens in the browser?** `localStorage` is common (accepts the XSS tradeoff); `httpOnly` cookies are stronger (CSRF cost); in-memory + silent refresh for sensitive apps.
4. **Session shape?** Short-lived access tokens + refresh-token rotation + a deny-list for critical revocations. Opaque sessions remain fine for server-rendered apps.
5. **AuthZ model?** Start with RBAC; add ABAC for resource-level rules; reach for policy engines or ReBAC only when the rules outgrow code. Resolve the live permission set from your store per request (token role = informational) when revocations must propagate fast.
6. **Multi-tenant isolation?** Shared-schema + a tenant column is the usual default — see [Multi-Tenant Isolation](./multi-tenant-isolation.md) for strategies and the data-layer backstop.
7. **MFA?** TOTP as table stakes; WebAuthn / passkeys where the user base supports it; mandatory for admin accounts.
8. **Audit logging?** Separate stream, long retention, never sampled.

---

## Related Topics

- **Secrets management (JWT signing keys, IdP client secrets)** — see [Configuration](./configuration.md)
- **Input validation (schema allowlists at the boundary, mass-assignment defence)** — see [Data Integrity](./data-integrity.md)
- **Error response shape (401 / 403, Problem Details format)** — see [Error Handling](./error-handling.md)
- **Structured logging and audit-log scrubbing** — see [Logging](./logging.md)
- **Rate limiting on login / token endpoints, CSRF, CORS, security headers** — see [Security](./security.md)
- **Multi-tenant isolation (tenant scoping, RLS backstop, cross-tenant exceptions)** — see [Multi-Tenant Isolation](./multi-tenant-isolation.md)
- **`Authorization` header conventions** — see [API Design](./api-design.md)
