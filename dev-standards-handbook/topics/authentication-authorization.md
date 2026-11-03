# Authentication & Authorization

> **Calibrate the investment, not the core rules.** How *much* auth machinery you build
> scales with the app: how many roles, how much defence-in-depth, whether you reach for
> full OIDC and an identity provider or a single known login is enough. What does *not*
> scale down is the handful of core rules — take identity from the verified session not
> the request, authorize the *specific* resource and action, never trust a client-supplied
> user or tenant id. A real auth hole doesn't care that you have three users. Treat this
> chapter as a reference to apply with judgment; on the core rules, judgment means sizing
> the investment, not skipping the check.

## The Problem

Every multi-user system answers two questions on every request: **who is this caller, and what are they allowed to do?** Authentication (AuthN) answers the first; authorization (AuthZ) answers the second. They sound alike, but different subsystems own each, and conflating them produces whole categories of vulnerability.

Most breach stories start here:
- A session check that never verified the user was authorised for *this specific resource* (BOLA — API1 in the OWASP API Security Top 10, 2023).
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

**Status codes:** return **401** when AuthN fails (no/invalid/expired token — the client should re-authenticate) and **403** when AuthN succeeded but AuthZ failed (re-authenticating won't help). The 401/403 split is about whether re-authenticating can help, not about secrecy: existence leaks through 403 versus 404. Return **404** rather than 403 when confirming the resource exists is itself a leak (another tenant's record) — the RLS backstop yields this naturally, because the row is simply invisible to the caller.

---

## OAuth 2.0 & OIDC

The most common confusion: **OAuth 2.0 is not about identity.** It's an authorization framework defining how a user lets App A access their data at Service B without sharing B's password. **OIDC** layers identity on top — a standard ID token (a JWT proving who the user is), standard claims (`sub`, `email`, …), a discovery document at `/.well-known/openid-configuration`, and a UserInfo endpoint. Because it's protocol-level, any OIDC app works against any OIDC provider (Google, Cognito, Auth0, Keycloak) with no provider-specific code; libraries like `oidc-client-ts` consume the discovery document and handle the rest.

**Grant types — which flow to use:**

| Grant type | Use case | Notes |
|-----------|----------|-------|
| **Authorization code + PKCE** | Every client that signs a user in: browser SPAs, mobile, and server-side (confidential) apps | The default for every client type (RFC 9700; required by the OAuth 2.1 draft). PKCE binds the code to its requester; it does not replace a confidential client's secret |
| **Authorization code without PKCE** | Older server-side apps that hold a client secret | Add PKCE — RFC 9700 recommends it for confidential clients too |
| **Client credentials** | Machine-to-machine, no user involved | A client ID plus a secret, or better a private-key JWT or mutual TLS (mTLS) (RFC 9700) |
| **Refresh token** | New access token without re-login | Used alongside the others |
| **Resource owner password** | Direct username/password to the token endpoint | Deprecated — defeats the point of delegated auth |
| **Implicit** | SPAs, historically | Retired — leaked tokens via the redirect URL |

**PKCE in brief:** the client generates a random `code_verifier`, sends its hash as a `code_challenge` on the authorize request, and presents the original verifier when exchanging the returned code for tokens. If an attacker intercepts the code, they still can't exchange it — they don't have the verifier, which never left the original browser. A library handles every step; application code calls something like `signinRedirect()` and reads the user from the callback. PKCE is not client authentication: a confidential client still authenticates at the token endpoint with its client secret or a private-key JWT. Register exact `redirect_uri` values and have the authorization server compare them as whole strings, with no wildcards or prefix matching, or a crafted redirect delivers the code to an attacker's host. Send an unguessable `state` and check it on the callback so an attacker can't splice their own authorization response into the user's session, and in OIDC send a `nonce` and check the ID token echoes it so a replayed ID token is refused.

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

**Verification is a library/middleware call in every framework — don't hand-roll it.** The mechanism worth understanding: the IdP publishes its public keys as a JSON Web Key Set (JWKS) at the `jwks_uri` its discovery document names; the verifier reads the token's `kid`, finds the matching key in *your configured* JWKS (cached ~1h), checks the signature, then validates `iss`, `aud`, and `exp`. Key rotation works because `kid` lets old tokens verify against old keys until they expire. Cloud gateways often run this step before your code does. The historic failures are each a trusted header or an omitted argument:

- **Pin the allowed algorithm.** A verifier that takes `alg` from the token accepts `alg: none`, or suffers algorithm confusion: an RS256 verifier handed an HS256 token checks it with the server's *public* key as the HMAC secret, which the attacker also has.
- **Keys come only from your configured JWKS, never from the token.** Ignore the `jku`, `x5u` and `jwk` headers; honouring them lets the attacker supply the key that verifies their own forgery.
- **Check `iss`, `aud` and `exp`.** Many libraries check `iss` and `aud` only when you pass the expected values.
- **Check the token type.** An API refuses an ID token where it expects an access token: check `typ: at+jwt` (RFC 9068) or the provider's own claim, such as Cognito's `token_use`. Cognito access tokens carry `client_id` and, unless the app requests a resource binding, no `aud`; check `client_id` rather than switching the audience check off ([The Audience Check Switched Off](./pitfalls.md#the-audience-check-switched-off)).

```typescript
// jose 6 — audience and issuer are checked only when you pass them
const { payload } = await jwtVerify(token, JWKS, { algorithms: ['RS256'], issuer: ISSUER, audience: AUDIENCE });
```

```python
# PyJWT 2 — algorithms is required; issuer is checked only when you pass it
claims = jwt.decode(token, key, algorithms=["RS256"], issuer=ISSUER, audience=AUDIENCE)
```

**Where the browser's tokens live**, most secure first:

| Storage | Pro | Con |
|---------|-----|-----|
| **Backend-for-frontend (BFF)** — your server holds the tokens; the browser holds only an `httpOnly` session cookie | No token in the browser to steal. The most secure pattern for an app with a backend (RFC 10017, BCP 212, August 2026) | API calls go through your server; the cookie needs CSRF defence |
| `httpOnly` cookie carrying the token itself | Not readable from JS | Sent automatically, so it needs CSRF defence; cross-origin complexity. Encrypt it (RFC 10017) |
| In-memory (a JS variable) | Not persisted; gone on reload | Lost on refresh, so it needs a silent-refresh flow; script in the page can still read it |
| `sessionStorage` | Clears on tab close | Readable by any script in the page |
| `localStorage` | Simple; survives tab close | Readable by any script in the page, which can carry it away |

**Under XSS, storage changes only what the attacker can carry away.** Script running in your page can use any token the page can use, wherever it is stored, and can call your API through a BFF's cookie too. A BFF stops token theft, because nothing long-lived ever reaches the browser; it does not stop XSS acting inside the live session, so XSS prevention stays the real defence (see [Security](./security.md#xss-cross-site-scripting)). Choose a BFF where the app has a backend. A browser-only SPA keeping tokens in `localStorage` is an accepted risk, not a default. Rotation does not save it: script that keeps taking the latest refresh token is never caught reusing one, so RFC 10017 advises against browser-only token handling for business apps and personal data. A bearer token in a header carries no CSRF risk, but any XSS can carry it away, so keep access tokens short-lived and the CSP strict. A session cookie is `Secure`, `HttpOnly` and `SameSite`, with the `__Host-` prefix, `Path=/` and no `Domain`; [Security](./security.md#csrf-cross-site-request-forgery) covers why, and the CSRF defence it still needs.

**Session shapes:** *opaque session tokens* (random ID in a cookie, state in Redis/DB — trivial revocation, one store lookup per request, common in server-rendered apps); *pure JWT* (stateless, no per-request lookup, but revocation is hard within the access-token TTL); and the *hybrid* most JWT systems actually run — short access-token TTL, **refresh-token rotation** (each refresh issues a new refresh token and invalidates the old, detecting replay), and a small **deny-list** for critical revocations (termination, password reset) checked in middleware. When a used refresh token comes back, revoke the whole family (every refresh token descended from that sign-in): you cannot tell the thief from the user, so both sign in again. Binding tokens to a key the client holds, with DPoP (RFC 9449), is the optional step beyond rotation.

---

## Passwords & MFA

If you manage passwords directly: **never store plain text, MD5, or raw SHA256** — all are too fast (attackers try billions of guesses per second). Use a purpose-built hash with a cost factor and a per-user salt, in OWASP's order of preference: **Argon2id** (memory-hard; the pick for new systems — at least 19 MiB memory, 2 iterations, 1 lane), then **scrypt**, then **bcrypt** for legacy systems only (cost at least 10; it rejects or silently truncates input over 72 bytes, which collides with long passphrases), and **PBKDF2-HMAC-SHA256** at 600,000 iterations where FIPS compliance applies. Store the parameters with the hash and rehash on the next successful login when you upgrade them. The salt defeats precomputed rainbow tables.

Password policy — NIST SP 800-63B reversed the advice most training still teaches, and revision 4 (SP 800-63B-4) makes most of it mandatory:

| Old advice (still in many policy docs) | Modern advice |
|----------------------------------------|---------------|
| 8 chars, mixed character classes | Minimum 15 characters for a password used alone (8 when it is one factor of MFA); permit at least 64; no composition rules (a SHALL NOT). Length beats complexity |
| Force rotation every 90 days | Don't — rotate only on evidence of compromise |
| Prohibit reuse of last N | Fine if cheap; modest benefit |
| Hints / security questions | Don't — hints and knowledge-based questions are both a SHALL NOT; often easier to attack than the password |

Two things *are* worth enforcing: check passwords against known-breached lists (haveibeenpwned's k-anonymity API lets you do this without sending the full password), and rate-limit auth attempts per-IP and per-account.

**MFA**, weakest to strongest:

| Method | How it works | Weakness |
|--------|--------------|----------|
| **SMS** | Code by text message | SIM-swap attacks; NIST treats it as a restricted authenticator; being phased out |
| **TOTP** | Authenticator app + shared secret, 6-digit code every 30s | Server breach leaks all seeds; users can still be phished |
| **Push with number matching** | Approve a prompt on a registered device by entering the number shown at sign-in | Number matching blunts "MFA fatigue" (spam prompts until the user approves), but a real-time phishing proxy can still relay it |
| **WebAuthn / passkeys** | Public-key credential bound to the site's origin | Phishing-resistant (origin-bound). Where the industry is heading |

Only the last is phishing-resistant — the property that matters for admins. Passkeys are also a **primary, passwordless sign-in**, not only a second factor: a passkey with on-device user verification (biometric or PIN) replaces the password and satisfies MFA on its own. Synced passkeys live in a platform or password-manager keychain and are copied across the user's devices, so they are not device-bound; use device-bound passkeys on hardware security keys where policy demands it.

Give every MFA setup a recovery path (one-time backup codes at enrolment). MFA is effectively mandatory for admin accounts, any role that can read other tenants' data, and customer accounts in regulated industries. Use a library for TOTP (pyotp, otplib) rather than writing it yourself; WebAuthn is painful — lean on libraries or a managed provider.

---

## Account Flows

The lifecycle flows most user systems end up needing:
- **Email verification** — a signed, short-lived (15–60 min) link or code on signup.
- **Password reset** — a one-time, short-TTL token by email; store only its hash, because it is a password-equivalent, and invalidate existing sessions after use.
- **Responses that don't enumerate accounts** — sign-in, sign-up and reset give the same message, status and roughly the same timing whether or not the account exists (hash a dummy password when the user is missing).
- **Session-ID regeneration** — issue a new session identifier on sign-in and on every privilege change (MFA step-up, role grant), and destroy the old one; otherwise a session an attacker planted before sign-in inherits the user's rights (session fixation). This is a core rule, not polish.
- **Email change** — confirm the new address by a link sent to it, notify the old address, and require recent re-authentication. The address is usually the recovery channel, so an unconfirmed change is an account takeover.
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
| **Oso Cloud** | Managed service (the open-source Oso library is archived) | Polar |
| **Cerbos** | Sidecar or library | YAML |
| **Cedar** | In-process library; managed as Amazon Verified Permissions | Cedar |
| **Casbin** | In-process library, many languages | Model file (PERM) + policy rows |

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

**Enforce server-side, display client-side.** Client-side checks are for UX only — hiding buttons, disabling forms. A determined user bypasses any of them. If the UI hides a button but the endpoint doesn't check, you have no security — just a hidden element. When the UI needs to know which actions a user may take, derive the permitted-action set on the server from the same policy the endpoints enforce, and project it into the response. One policy source feeds both, so the hint and the check cannot drift; the projection is a hint for rendering, never the check.

**Privilege escalation through elevated contexts.** Stored procedures, serverless functions, and admin endpoints often run with elevated permissions because they need data the caller can't normally reach. The trap: if such a function takes a scope parameter (tenant ID, user ID) from the caller and doesn't independently verify the caller is authorised for that scope, any caller reads any scope by changing the parameter. The rule: a function that runs with more permission than its caller must verify the caller's authorisation for the requested scope itself. (This is the "Confused Deputy" pattern below.)

---

## Multi-Tenant Isolation

Multi-tenant systems turn every authorization question from "can this user do X?" into "can they do X *for this tenant*?" — and one missed tenant check silently leaks one customer's data to another. The tenant identity must always come from the authenticated session, never the request. Choosing an isolation strategy, enforcing the boundary in a scoped data layer, backing it with a database backstop (RLS on Postgres), and the deliberate cross-tenant exceptions are covered in full in [Multi-Tenant Isolation](./multi-tenant-isolation.md).

---

## Common Vulnerabilities

Named patterns worth recognising — most from the OWASP API Security Top 10:

| Vulnerability | What it is | Defence |
|---------------|-----------|---------|
| **BOLA** (Broken Object-Level Authorization; **IDOR**, Insecure Direct Object Reference, is the older name) | `GET /orders/456` works because ownership wasn't checked — with any kind of identifier, sequential integers classically, UUIDs too. API1 in the OWASP API Security Top 10 (2023) | Ownership check in every handler that takes an ID; better, data-layer isolation. Opaque IDs don't fix it; only authorisation does |
| **Broken Function-Level Authorization** | An admin endpoint exposed without the admin check | Role check on admin route groups; test with a non-admin token |
| **Mass Assignment** | `PATCH /users/me` accepts `{role: "admin"}` because the whole body is trusted | Allowlist accepted fields at the boundary (schema validation) |
| **Confused Deputy** | An elevated service acts on a user's behalf without verifying the user's authorisation | Carry user context into every decision (see Privilege escalation) |
| **JWT `alg: none` / algorithm confusion** | The verifier takes the algorithm or the key from the token header | Pin the allowed algorithms; take keys only from your configured JWKS |
| **Expired, wrong-audience or wrong-type token accepted** | Verifier skipped `exp` / `aud`, or accepted an ID token as an access token | Validate `iss`, `aud`, `exp` and the token type |

---

## Audit Logging

Compliance frameworks (SOC 2 CC6/CC7) require audit logs for authorization-relevant events — keep them separate from operational logs:

| Operational logs | Audit logs |
|------------------|-----------|
| Errors, warnings, debug traces | Who did what, when, to what, with what outcome |
| Retention: 30–90 days | Retention: 1+ year |
| Often sampled | Never sampled |

Minimum fields per event: actor, action, resource, outcome, timestamp, request id. Log every authn event (login success/failure, logout, MFA outcome), every authorization denial, every state-changing action, and every admin / cross-tenant action. Write the log append-only or tamper-evident (write-once storage, or hash-chained entries), so whoever compromises the app cannot erase their tracks, and never put tokens, passwords or session ids in it.

---

## Managed vs Self-Hosted Identity

| Option | Examples | Why teams choose it | Tradeoff |
|--------|----------|---------------------|----------|
| **Managed IdP** | Cognito, Auth0, Clerk, Okta, Microsoft Entra ID (Entra External ID for customers), Supabase Auth, WorkOS | Handles hashing, rate limiting, breach detection, MFA, recovery, federated/enterprise SSO. The default | Vendor dependency, per-MAU pricing at scale |
| **In-app library** | Better Auth (TypeScript) | Users live in your own database; no per-user pricing; fits one app | Password storage, MFA, recovery and breach response come back to you |
| **Self-hosted IdP** | Keycloak, Ory | Full control, air-gapped/regulated environments, no per-user pricing | You own operating an identity service |
| **Roll-your-own** | Custom | Total control | Auth is easy to get mostly right and hard to get fully right: every flow above, and every attack on it, is yours |

Roll-your-own is rarely the right call beyond a hobby project: the downside is "every credential compromised" and the upside over a managed provider is small. In Python, the usual pick is a managed IdP with Authlib as its OIDC client. You will still meet two older libraries in existing code that are not fresh picks: Auth.js (formerly NextAuth.js) has been maintained by the Better Auth team since September 2025, and FastAPI-Users has been in maintenance mode since December 2025.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Store plain / MD5 / SHA256 passwords | Argon2id (bcrypt at cost 10 or more on legacy systems only) | Weak hashing means stolen databases are cracked in minutes |
| Check authentication but not authorization | Verify permission for the specific resource and action | Authenticated ≠ authorised |
| Put secrets in a JWT payload | It's signed, not encrypted | Anyone with the token reads every claim |
| Read the tenant ID from the request body | Derive it from the authenticated session | Client-supplied tenant IDs let callers query any tenant |
| Pass request bodies straight into a write | Allowlist accepted fields at the boundary | Mass assignment escalates privileges |
| Take the algorithm or key from the token; skip `iss`/`aud`/`exp` or the token type | Pin algorithms; keys from your JWKS only; validate claims and type | Forged, confused or replayed tokens |
| Keep the same session ID across sign-in | Issue a new session ID on sign-in and privilege change | A session planted before sign-in inherits the user's rights |
| Keep long-lived tokens in `localStorage` by default | A BFF where the app has a backend | Any XSS carries the token away |
| Force password rotation every 90 days | Rotate only on evidence of compromise | Produces `Password1`, `Password2`; no security gain |
| Rely on client-side role checks | Enforce server-side; client is UX only | Any user disables the client check in devtools |
| Return 401 where 403 is the right answer | 401 = AuthN failure, 403 = AuthZ failure; 404 where confirming existence is itself a leak | 401 tells the client to re-authenticate, which can't help |
| Roll your own auth service | Use a managed IdP or a maintained in-app library | Every flow and every attack on it becomes yours to get right |

---

## Deciding for Your Project

1. **Run your own identity?** No → a managed IdP, or an in-app library such as Better Auth when one app wants its users in its own database. Yes → Keycloak or Ory. Rolling your own is rarely right.
2. **Token shape?** OIDC authorization code + PKCE for every client that signs a user in, server-side apps included; client credentials for machine-to-machine.
3. **Tokens in the browser?** A BFF where the app has a backend: tokens stay on the server, and the browser holds a `__Host-` session cookie with a CSRF defence. A browser-only SPA keeps short-lived tokens in memory or `localStorage` and accepts the XSS risk, which RFC 10017 advises against for business apps and personal data.
4. **Session shape?** Short-lived access tokens + refresh-token rotation + a deny-list for critical revocations. Opaque sessions remain fine for server-rendered apps.
5. **AuthZ model?** Start with RBAC; add ABAC for resource-level rules; reach for policy engines or ReBAC only when the rules outgrow code. Resolve the live permission set from your store per request (token role = informational) when revocations must propagate fast.
6. **Multi-tenant isolation?** Shared-schema + a tenant column is the usual default — see [Multi-Tenant Isolation](./multi-tenant-isolation.md) for strategies and the data-layer backstop.
7. **Sign-in and MFA?** Passkeys first, as a passwordless primary sign-in; TOTP as the fallback; SMS only as a last resort; phishing-resistant MFA (passkeys / WebAuthn) mandatory for admin accounts.
8. **Audit logging?** Separate stream, append-only, long retention, never sampled, no tokens.

---

## Related Topics

- **Secrets (JWT signing keys, IdP client secrets)** — see [Security](./security.md#secrets-management) for storage, rotation and least privilege, and [Configuration](./configuration.md#secret-delivery-and-rotation) for how they reach the app
- **Input validation (schema allowlists at the boundary, mass-assignment defence)** — see [Data Integrity](./data-integrity.md)
- **Error response shape (401 / 403, Problem Details format)** — see [Error Handling](./error-handling.md)
- **Structured logging, logger-level redaction and personal data in logs** — see [Logging](./logging.md#scrubbing-sensitive-data); audit logs are this chapter's
- **CSRF defence and session-cookie attributes, XSS, rate limiting on login and token endpoints, CORS** — see [Security](./security.md)
- **Testing the authentication gate and the ownership check** — see [Security](./security.md#testing-security) for what to assert and [Testing](./testing.md) for the real-database harness
- **Server-projected capabilities in the UI** — the server side is [Enforcement Layers](#enforcement-layers) above; see [Front-end Development](./frontend-development.md#data-loading-and-changes) for rendering from the projection instead of rebuilding the rules in the browser
- **Multi-tenant isolation (tenant scoping, RLS backstop, cross-tenant exceptions)** — see [Multi-Tenant Isolation](./multi-tenant-isolation.md)
- **`Authorization` header conventions** — see [API Design](./api-design.md)
