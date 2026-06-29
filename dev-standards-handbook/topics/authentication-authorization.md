# Authentication & Authorization

## The Problem

Every multi-user system has to answer two questions on every request: **who is this caller, and what are they allowed to do?** Authentication (AuthN) answers the first; authorization (AuthZ) answers the second. They sound similar and are often conflated, but different subsystems handle each and mixing them up produces entire categories of vulnerability.

Most breach stories start here:
- A session check that never verified the user was authorised for *this specific resource* (BOLA — #1 API vulnerability by volume)
- A token issued once and never rotated, harvested from a log
- A role check in middleware but not in a direct database query, which then ran with admin privileges
- A "tenant ID" pulled from the request body instead of the authenticated session — one tenant's admin reads another tenant's data by changing a URL parameter

The vocabulary in this area is dense (OIDC, JWKS, PKCE, SCIM, RLS, BYPASSRLS). The concepts are layered: protocol, token, session, policy, enforcement, data. This topic covers each layer with enough depth to read docs, library source, and security reviews without getting lost.

---

## Authentication vs Authorization

**Authentication (AuthN)** — verifies identity. The result is a fact: *this request is from user `abc-123`*. Usually expressed as a verified session token or signed JWT. Stateless: the token itself proves identity.

**Authorization (AuthZ)** — checks permission. The result is a decision: *is user `abc-123` allowed to do action X on resource Y?* Depends on the user's role, the resource's attributes, and sometimes the request context. Derived, not carried in the token.

A classic vulnerability — authenticated but not authorised:

```typescript
// BAD: verifies the user is logged in, but not that they own this resource
app.delete('/users/:id', requireAuth, async (req, res) => {
  await db.deleteUser(req.params.id);  // Any user can delete ANY other user
});

// GOOD: checks both authentication AND authorization
app.delete('/users/:id', requireAuth, async (req, res) => {
  if (req.user.id !== req.params.id && req.user.role !== 'admin') {
    throw new AuthorizationError("Can only delete your own account");
  }
  await db.deleteUser(req.params.id);
});
```

```python
# BAD
@app.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    await db.delete_user(user_id)  # Any authenticated user can delete anyone

# GOOD
@app.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != "admin":
        raise AuthorizationError("Can only delete your own account")
    await db.delete_user(user_id)
```

The AuthZ checklist for every state-changing or sensitive-read endpoint:
1. Authenticated — is the session/token valid?
2. Authorised for the resource — do they own it, or have admin privileges over it?
3. Authorised for the action — can they read but not write? View but not delete?

### HTTP status codes

- **401 Unauthorized** — AuthN failed (no token, invalid token, expired token). Client should re-authenticate.
- **403 Forbidden** — AuthN succeeded, AuthZ failed. Re-authenticating won't help.

Returning 401 where 403 is correct leaks information ("this resource exists, you just can't reach it" vs "we don't want to tell you whether this exists").

---

## A Brief History

Understanding where today's patterns came from makes them much easier to reason about.

| Era | Pattern | What it did | Why it lost or evolved |
|-----|---------|-------------|------------------------|
| 1990s | HTTP Basic Auth | Username + password in every request header | No logout, no MFA, password in every request |
| Late 90s–2000s | Session cookies | Server issues random session ID, looks up session state in memory/Redis/DB | Session store becomes a bottleneck; hard to scale stateless |
| 2005 | SAML | XML-based enterprise SSO | Still dominant in corporate IT, clunky for modern web |
| 2007 | OAuth 1.0 | Delegated access with complex signature dance | Signature complexity; deprecated |
| 2012 | OAuth 2.0 | Authorization framework with grant types | Source of confusion — *authorization framework, not identity* |
| 2014 | OpenID Connect (OIDC) | Thin identity layer on top of OAuth 2.0 | Won; basis of "Sign in with Google/Apple/Microsoft" |
| 2015 | JWT (RFC 7519) | Signed self-contained tokens carrying claims | Enables stateless scaling; dominant API auth shape today |

The crucial shift is JWTs. Before JWTs, the auth state lived in a shared session store that every request hit. With JWTs, the state travels with the request, signed by the issuer — anyone with the issuer's public key can verify without a callback. That's what makes stateless scaling and microservices auth work.

---

## OAuth 2.0 and OIDC

The single most common source of confusion: **OAuth 2.0 is not about identity.** It's an authorization framework that defines how a user can let App A access their data at Service B without sharing Service B's password. OIDC layers identity on top.

### What OIDC adds

1. A standardised **ID token** — a JWT that proves who the user is
2. Standardised **claims** (`sub`, `email`, `email_verified`, `name`) so every OIDC provider speaks the same identity vocabulary
3. A **discovery document** at `https://<issuer>/.well-known/openid-configuration` — lists the provider's endpoints, supported algorithms, supported scopes
4. A **UserInfo endpoint** for fetching extra user info beyond what's in the ID token

Because OIDC is protocol-level, any app that implements it works against any OIDC provider — Google, Cognito, Auth0, Keycloak — without provider-specific code. Libraries like `oidc-client-ts` (JavaScript) and `Authlib` (Python) consume the discovery document and handle the rest.

### Grant types — which flow to use

| Grant type | Use case | Notes |
|-----------|----------|-------|
| **Authorization code + PKCE** | Browser SPAs, mobile apps, public clients | The modern default. PKCE (Proof Key for Code Exchange, RFC 7636) removes the need for a client secret |
| **Authorization code (classic)** | Server-side web apps with a backend that can hold a client secret | Still fine when there's a confidential server |
| **Client credentials** | Machine-to-machine — service A calls service B on its own behalf, not a user's | No user involved; just a client ID and secret |
| **Refresh token** | Getting a new access token without re-login | Used alongside the others, not on its own |
| **Resource owner password** | Direct username/password submission to the token endpoint | Deprecated — defeats the point of delegated auth |
| **Implicit** | SPAs, historically | Retired. Returned tokens in the redirect URL where they leaked into browser history, referrer headers, and logs |

---

## The Authorization Code + PKCE Flow

This is what most modern SPAs and mobile apps do. Step-by-step:

```
1. SPA generates:
     code_verifier  = <random 43–128 chars>
     code_challenge = BASE64URL(SHA256(code_verifier))
     state          = <random>     // CSRF protection

2. SPA redirects browser to:
     GET https://<idp>/oauth2/authorize
       ?client_id=<id>
       &response_type=code
       &scope=openid+email
       &redirect_uri=https://app/callback
       &code_challenge=<challenge>
       &code_challenge_method=S256
       &state=<state>

3. User enters credentials on the IdP's hosted UI.

4. IdP redirects browser back:
     GET https://app/callback?code=<auth_code>&state=<state>

5. SPA verifies state matches. If not → abort (possible CSRF).

6. SPA POSTs (not via browser redirect) to:
     POST https://<idp>/oauth2/token
       grant_type=authorization_code
       code=<auth_code>
       code_verifier=<verifier>   // proves possession
       client_id=<id>
       redirect_uri=https://app/callback

7. IdP verifies SHA256(code_verifier) == code_challenge. If yes:
     returns { id_token, access_token, refresh_token }

8. SPA stores tokens; sends access token as Authorization: Bearer on subsequent calls.
```

**Why PKCE matters:** if an attacker intercepts the auth code in step 4 (malicious browser extension, open redirect, leaked logs), they still can't exchange it — they don't have the `code_verifier`, which never left the original browser.

In practice, a library like `oidc-client-ts` handles every step. Application code just calls `userManager.signinRedirect()` and reads the resulting user object from callback.

---

## Tokens

### JWT anatomy

A JWT is three base64-encoded segments separated by dots:

```
eyJhbGciOiJSUzI1NiJ9 . eyJzdWIiOiIxMjMiLCJjb21wYW55IjoieHl6In0 . SflKxwRJSMeK...
  └── header ──┘         └── payload (claims) ─────────────┘      └── signature ──┘
```

- **Header** — signing algorithm (e.g., `RS256`) plus key ID (`kid`)
- **Payload** — the claims: `sub` (subject/user ID), `iss` (issuer), `exp` (expiry), `aud` (audience), plus any custom claims
- **Signature** — HMAC or RSA over header + payload. Tampering invalidates it

The critical property: the signature is verifiable without calling the issuer. Any service with the issuer's public key can verify the token on its own. That's what makes JWT auth stateless.

**Never put secrets in a JWT payload.** It's base64-encoded, not encrypted. Anyone with the token can read the claims.

### ID token vs access token vs refresh token

Most OIDC flows return three tokens, each with a different job:

| Token | Purpose | Audience | Typical lifetime |
|-------|---------|----------|------------------|
| **ID token** | Proves who the user is (identity). Contains `sub`, `email`, etc. | Your application | Short (minutes) |
| **Access token** | Proves what the user can access (authorisation). Sent to APIs | Your API or downstream services | Short (5–60 min) |
| **Refresh token** | Exchanges for new access tokens without re-login | The IdP's token endpoint only | Long (days–weeks) |

The standard rule: **ID token for identity within the app, access token sent to APIs.** In practice, some stacks (like AWS Cognito) conflate the two — their access token is also a JWT with claims you can read in the app. Don't rely on that in portable code.

### Token storage in browsers

A persistent tension with no universally right answer:

| Storage | Pros | Cons |
|---------|------|------|
| `localStorage` | Simple to read from JavaScript. Survives tab close | Readable by any script on the page — XSS steals the token |
| `sessionStorage` | Clears on tab close | Same XSS risk as `localStorage` |
| `httpOnly` cookie | Not readable from JavaScript — XSS can't exfiltrate | Sent automatically with every request — CSRF concern; cross-origin complexity |
| In-memory only | XSS can only steal during page lifetime | Lost on refresh; needs silent-refresh flow |

The Cognito + SPA default (`oidc-client-ts`) puts tokens in `localStorage`. It accepts the XSS tradeoff because properly-audited SPAs shouldn't have XSS, and the bearer-token model avoids CSRF entirely. Higher-security apps (banking, healthcare) often move to `httpOnly` cookies with CSRF tokens or to in-memory storage with silent refresh.

### Session management shapes

Three common patterns appear in production:

**Opaque session tokens (cookie + server store)**
- Cookie carries a random ID; session state lives in Redis/DB
- Revocation is trivial — delete the row
- Every request = one session store lookup
- Common in traditional server-rendered web apps

**Pure JWT**
- Access token TTL 5–60 min, refresh token TTL days–weeks
- Stateless — no server store lookup per request
- Revocation is hard within the access token's TTL
- Common in API-first and microservice architectures

**Hybrid (what most production JWT systems actually do)**
- Short access token TTL to limit blast radius
- **Refresh token rotation:** each refresh issues a new refresh token and invalidates the old. Detects replay of stolen refresh tokens
- **Deny-list for critical revocations** (employee termination, password reset) — a small Redis set of revoked user IDs, checked in auth middleware. Scales because revocations are rare and entries can be dropped once the access token TTL has passed

### JWKS and stateless verification

How does a service with no connection to the IdP verify a JWT? Via the **JWKS** (JSON Web Key Set) endpoint — the IdP publishes its public keys at a well-known URL:

```
https://<issuer>/.well-known/jwks.json
```

```json
{
  "keys": [
    {
      "kid": "abc123",
      "kty": "RSA",
      "n": "...",            // RSA modulus (base64url)
      "e": "AQAB",
      "use": "sig",
      "alg": "RS256"
    }
  ]
}
```

Verification:

1. Parse the JWT header → read `kid`
2. Fetch JWKS (cached locally, usually ~1h)
3. Find the key matching `kid`
4. Verify the signature with that public key
5. Check `iss`, `aud`, `exp`, and any required claims

Only the private key (held by the IdP) can sign. Anyone with the public key can verify. Issuers rotate keys periodically; `kid` lets old tokens verify against old keys until they expire.

### Verifying a JWT in your code

Most frameworks make this a one-liner via library or middleware. If you're writing it yourself:

```typescript
// Express — with jose library and JWKS caching
import { createRemoteJWKSet, jwtVerify } from 'jose';

const JWKS = createRemoteJWKSet(new URL(`${env.ISSUER}/.well-known/jwks.json`));

async function requireAuth(req, res, next) {
  const header = req.headers.authorization;
  if (!header?.startsWith('Bearer ')) {
    return res.status(401).json({ type: 'UnauthorizedError', title: 'Missing token' });
  }

  try {
    const { payload } = await jwtVerify(header.slice(7), JWKS, {
      issuer: env.ISSUER,
      audience: env.AUDIENCE,
    });
    req.user = payload;
    next();
  } catch {
    return res.status(401).json({ type: 'UnauthorizedError', title: 'Invalid token' });
  }
}
```

```python
# FastAPI — with python-jose and JWKS caching
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
import httpx

_jwks_cache: dict | None = None

async def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{settings.ISSUER}/.well-known/jwks.json")
            _jwks_cache = r.json()
    return _jwks_cache

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    jwks = await get_jwks()
    unverified = jwt.get_unverified_header(credentials.credentials)
    key = next((k for k in jwks["keys"] if k["kid"] == unverified["kid"]), None)
    if not key:
        raise HTTPException(401, "Unknown signing key")
    try:
        return jwt.decode(
            credentials.credentials,
            jwk.construct(key).to_pem().decode(),
            algorithms=["RS256"],
            issuer=settings.ISSUER,
            audience=settings.AUDIENCE,
        )
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")
```

On AWS, API Gateway has a built-in JWT authoriser that does all of this before the Lambda even runs. Similar offerings exist on most cloud platforms.

---

## Password-Based Authentication

Even with OIDC becoming the default, many systems still manage passwords directly — either because they are the IdP or because they support a fallback login path.

### Hashing

Never store plain text. Never use MD5 or raw SHA256 — both are too fast for password use (attackers try billions of guesses per second). Use a purpose-built password hashing function with a cost parameter (intentionally slow) and a salt (random data mixed into each hash).

Common choices:

| Algorithm | Notes |
|-----------|-------|
| **bcrypt** | Oldest of the modern options. Widely supported. Work factor `rounds` — 12 is a common default in 2026 |
| **argon2** | Winner of the 2015 Password Hashing Competition. Tunable for memory, time, and parallelism. The current recommendation for new systems if your language has a good library |
| **scrypt** | Memory-hard like argon2 but less widely used |

```typescript
import bcrypt from 'bcrypt';

// Registration
const hash = await bcrypt.hash(password, 12);  // store the hash

// Login
const isValid = await bcrypt.compare(attempt, storedHash);
```

```python
import bcrypt

# Registration
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# Login
is_valid = bcrypt.checkpw(attempt.encode(), stored_hash)
```

The salt is included in bcrypt's output — you don't manage it separately. Without a salt, attackers precompute hashes for common passwords (a **rainbow table**) and look them up instantly. With a random salt per user, precomputation becomes useless.

### Password policy — the NIST reversal

NIST SP 800-63B (2017, updated 2024) reversed what most training materials still teach:

| Old advice (still common in policy docs) | Modern advice |
|-------------------------------------------|---------------|
| At least 8 chars, mix upper/lower/number/symbol | Allow up to 64 chars. Length matters far more than complexity |
| Force rotation every 90 days | Don't force rotation. Rotate only on evidence of compromise |
| Prohibit reuse of last N passwords | Fine if cheap; modest benefit |
| Password hints and security questions | Phase out — often easier to attack than the password itself |

Forced rotation produces `Password1`, `Password2`, `Password3`. Users adopting passphrases they can remember beats users forced into patterns they forget.

Two additions that *are* worth enforcing:
- **Check against known-breached lists.** haveibeenpwned has a k-anonymity API that lets you check without sending the full password. Many IdPs bake this in
- **Rate-limit auth attempts** per-IP and per-account with exponential backoff. Especially important on legacy password endpoints that don't have MFA

---

## Multi-Factor Authentication

Adding a second factor — something the user has (a phone, a key) in addition to something they know (a password) — dramatically reduces the impact of credential theft.

### MFA methods, in order of strength

| Method | How it works | Weaknesses |
|--------|--------------|-----------|
| **TOTP** (Time-based One-Time Password, RFC 6238) | Authenticator app (Google Authenticator, Authy, 1Password) and server share a secret; app generates a 6-digit code every 30s | Shared secret — a server breach leaks all seeds. Users can still be phished into entering codes on a fake site |
| **SMS codes** | Code sent as text message | SIM-swap attacks (attacker convinces carrier to transfer the number). Phased out by larger companies; still offered as a fallback |
| **Push notification** (Duo, Okta Verify) | Approve/deny prompt on the user's registered device | Vulnerable to "MFA fatigue" — attacker spams prompts until the user approves one |
| **WebAuthn / Passkeys** | Public-key crypto backed by device's secure enclave (Apple Secure Enclave, YubiKey, Android TEE) | Phishing-proof — browser binds signatures to the origin. The direction the industry is heading |

### Backup codes

Any MFA system needs a recovery path. The standard is a set of one-time backup codes generated at enrolment — the user prints them or stores them in a password manager. Each code can be used once; when the list is exhausted, the user generates a new set from within their account.

### When MFA is effectively mandatory

- Admin accounts on any production system
- Any role that can read other tenants' data
- Customer-facing accounts in regulated industries (financial, healthcare, identity)

### Library / provider support

Writing MFA from scratch is straightforward for TOTP and painful for WebAuthn. Most teams delegate to:

- **TOTP** — `speakeasy` (Node), `pyotp` (Python). Both well-maintained
- **WebAuthn** — `@simplewebauthn/server` (Node), `webauthn` (Python). Non-trivial; lean on library docs
- **Managed providers** — Cognito, Auth0, Clerk, Okta all offer TOTP and WebAuthn out of the box

---

## Account Flows

The lifecycle flows every user system ends up needing:

- **Email verification** — magic link or 6-digit code on signup. Token signed and short-lived (15-60 min)
- **Password reset** — signed token sent by email, one-time use, short TTL. After consumption, invalidate existing sessions for that user
- **Invite flow** — admin creates a user + role, signed invite token sent by email. On acceptance, user sets their password (or registers with OIDC) and the role is attached
- **Account linking** — one underlying user record, multiple identities attached (Google + email + Apple). Link by verifying possession of each — never match by email alone, because email ownership can change
- **Federated SSO** — a customer's corporate IdP trusted for their users only. Typically OIDC or SAML on the customer side, translated to your app's session
- **SCIM** (System for Cross-domain Identity Management, RFC 7644) — a protocol for enterprise IdPs to push user provisioning/deprovisioning into your app. Relevant once you have enterprise customers who expect deactivation to propagate automatically when an employee leaves

---

## Managed vs Self-Hosted Identity

| Option | Examples | Why teams choose it | Tradeoff |
|--------|----------|---------------------|---------|
| **Managed IdP** | Cognito, Auth0, Clerk, Okta, Firebase Auth, Supabase Auth, WorkOS | Handles password hashing, rate limiting, breach detection, MFA, account recovery, federated login, enterprise SSO. The overwhelming default | Vendor dependency, per-MAU pricing at scale |
| **Self-hosted IdP** | Keycloak, Ory (Kratos/Hydra/Oathkeeper) | Full UI control, air-gapped or regulated environments, avoid per-user pricing | You own operating an identity service — patching, backup, uptime |
| **Roll-your-own** | Custom implementation | Total control | Auth is easy to get mostly right and hard to get fully right. Most security incidents in this area come from homegrown systems |

Roll-your-own is rarely the right call for anything beyond a hobby project. The asymmetry is stark: the downside of a bug is "every user's credentials are compromised," and the upside over a managed provider is small.

---

## Authorization Models

Once you know who the caller is, you need a consistent way to decide what they can do. Ad-hoc `if (user.role === 'admin')` checks scattered across the codebase accumulate into untrackable complexity. Four named models cover most of what you'll encounter.

### ACL — Access Control List

One list per resource: "users A, B, C can read; user D can write." The earliest model. Common in filesystems (POSIX ACLs) and some object stores. Rarely used as a primary model for SaaS apps because it scales poorly with many resources.

### RBAC — Role-Based Access Control

Users have roles; roles have permissions. The application checks permissions, not users directly.

```typescript
const PERMISSIONS = {
  admin:  ['read', 'write', 'delete', 'manage_users'],
  editor: ['read', 'write'],
  viewer: ['read'],
} as const;

function canPerform(role: keyof typeof PERMISSIONS, action: string): boolean {
  return PERMISSIONS[role]?.includes(action) ?? false;
}
```

RBAC has more variations than it first appears:

- **Flat roles** — a small fixed set (`admin`, `user`). Simplest; what most apps start with
- **Hierarchical roles** — `admin` inherits `editor`'s permissions
- **Permissions as first-class** — `can_upload_course`, `can_view_assessments`. Roles are bags of permissions. Easier to grant narrow capabilities without adding new roles
- **Per-resource roles** — a user is `owner` of Course A, `viewer` of Course B. Common in collaboration tools (Notion, Linear, Google Drive)
- **Per-tenant roles** — a user is `admin` in Company A, `viewer` in Company B. Requires tenant context on every authz decision

### ABAC — Attribute-Based Access Control

Permissions are evaluated from attributes of the user, the resource, and the context. More expressive than RBAC, more complex to implement.

```typescript
function canEditDocument(user: User, document: Document): boolean {
  if (user.role === 'admin') return true;
  if (document.ownerId === user.id) return true;
  if (document.teamId === user.teamId && user.role === 'editor') return true;
  if (document.status === 'locked') return false;
  return false;
}
```

Most real-world apps use a hybrid: RBAC for broad categories, with attribute-based rules for resource-level checks ("can edit *only own* posts").

### ReBAC — Relationship-Based Access Control

Access is defined by graph relationships: "user can read a document if they are a member of a group that has been granted access." The reference implementation is Google Zanzibar (the permission system behind Drive, Docs, YouTube). Open-source implementations include SpiceDB and OpenFGA. Overkill for most apps; the right fit when permissions are natively graph-shaped (shared docs, team hierarchies, nested resources).

---

## Policy Engines

When authz rules grow beyond a few dozen simple checks, embedding them in application code becomes a maintenance problem. Policy engines externalise the rules.

| Engine | Shape | Rules language |
|--------|-------|----------------|
| **OPA** (Open Policy Agent) | Sidecar or library. CNCF-graduated | Rego (declarative) |
| **Oso** | Library, in-process | Polar (declarative) |
| **Cerbos** | Sidecar or library | YAML policies |
| **AWS IAM** | Cloud-native. The reference policy-as-document model | JSON policies with principal/action/resource/condition |

Most small SaaS don't need these. Reach for them when:

- Authz rules need to be editable by non-engineers (product managers, customer support)
- Per-tenant policies diverge and hard-coding branches becomes painful
- Compliance frameworks (SOC 2, ISO 27001) require policy-as-code with audit trail

---

## Enforcement Layers

Production systems don't check authorization in one place. They layer defences so that breaking any single layer doesn't grant access.

| Layer | What it checks | Example |
|-------|---------------|---------|
| **Gateway / CDN** | Rate limits, WAF rules, token signature | API Gateway JWT authoriser, Cloudflare WAF |
| **API middleware** | Role checks, feature flags | `requireAdmin(ctx)` before the handler runs |
| **Business logic** | Ownership, resource-specific rules | "`user.companyId == course.companyId`" inside a handler |
| **Data layer** | Structural invariants that bugs can't bypass | Postgres Row-Level Security, DynamoDB condition expressions |

Most systems have the first three. Adding the data layer is what takes authz from "we always remember to check" to "the database refuses non-matching rows." That's the jump to "audit-grade" isolation in multi-tenant systems.

### Enforce server-side, display client-side

Client-side checks exist for UX only — hiding buttons the user can't use, disabling forms they can't submit. A determined user can bypass any client-side check.

```typescript
// Client-side: UX convenience — hide the button
{canManageUsers && <Button>Manage Users</Button>}

// Server-side: actual enforcement — reject the request
if (!canPerform(user.role, 'manage_users')) {
  return errorResponse('Forbidden', 403);
}
```

If your frontend hides a button but the API endpoint doesn't check permissions, you have no security — just a hidden UI element.

### Privilege escalation through elevated functions

Database stored procedures, serverless functions, and backend API endpoints often run with elevated permissions — an admin database connection, a service account, or a privileged execution context. This is often necessary: the function needs data the caller normally can't reach.

The trap: if the function accepts a scope parameter (tenant ID, user ID, organisation ID) from the caller and doesn't independently verify the caller is authorised for that scope, any caller can read any scope by changing the parameter.

```python
# VULNERABLE: function runs with admin privileges, trusts caller-supplied tenant_id
def get_tenant_data(tenant_id: str, caller_token: str):
    verify_token(caller_token)  # verified authenticated — but not authorised for this tenant
    return db.query("SELECT * FROM data WHERE tenant_id = %s", tenant_id)
```

```python
# SAFE: function verifies the caller's relationship to the requested scope
def get_tenant_data(tenant_id: str, caller_token: str):
    caller = verify_token(caller_token)
    if not caller.has_access_to(tenant_id):
        raise AuthorizationError("Not authorised for this tenant")
    return db.query("SELECT * FROM data WHERE tenant_id = %s", tenant_id)
```

The rule: if the function runs with more permissions than the caller, it must independently verify the caller's authorisation for the requested scope.

---

## Multi-Tenant Isolation

In multi-tenant systems (one software instance serving many customer organisations), the authz question isn't just "can this user do X?" but "can this user do X *for this tenant*?" A single missed tenant check means one tenant can see another's data.

### Three database-level isolation strategies

| Strategy | How it works | When teams pick it |
|----------|--------------|-------------------|
| **Database per tenant** | Each tenant has its own physical database | Regulated industries, enterprise single-tenancy demands, very large tenants. Strongest isolation, highest ops cost |
| **Schema per tenant** | One database, one schema per tenant | Middle ground. Schema migrations multiply by tenant count |
| **Shared database, shared schema, tenant column** | One `company_id` column on every tenant-scoped table | Cheapest ops, weakest *default* isolation. The common SaaS pattern |

With the shared-schema approach, **how** the tenant filter is enforced matters enormously:

- **Convention** — "we always remember to filter by `company_id`." Easy to get wrong. A single missed `WHERE` clause leaks across tenants
- **Application-layer wrapper** (scoped DB builder) — a wrapper around the DB client that can't execute queries without injecting the filter. Structurally hard to bypass unless a caller imports the raw client
- **Database-layer** (Row-Level Security on Postgres) — the database itself refuses non-matching rows. Bugs, manual `psql` sessions, and malicious insiders cannot bypass

### Row-Level Security (Postgres)

Postgres feature since 9.5 (2016). Policies attach to tables; each policy is a per-row boolean expression evaluated at query time.

```sql
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON courses
  USING      (company_id = current_setting('app.company_id')::uuid)
  WITH CHECK (company_id = current_setting('app.company_id')::uuid);
```

**On the default stack (TypeScript + Drizzle), you don't hand-write this SQL.** You declare the policy in your schema with `pgPolicy` (and roles with `pgRole`), and `drizzle-kit` generates the `CREATE POLICY` / `ENABLE ROW LEVEL SECURITY` shown above — on any Postgres since `drizzle-orm` 0.36, not just Neon/Supabase. Prisma, by contrast, has no native RLS.

Per-request usage:

```sql
SET LOCAL app.company_id = 'abc-123';
SELECT * FROM courses;  -- only rows where company_id = abc-123
```

If the session variable isn't set, queries either error loudly or return zero rows depending on how the policy is written. Nothing leaks.

**Clauses:**
- `USING` — which rows are visible on `SELECT` / `UPDATE` / `DELETE`
- `WITH CHECK` — which rows you can `INSERT` / `UPDATE`. Writes that would produce a row failing this check are rejected with an error

**Enforcement mechanics:** RLS runs at the planner stage. The planner rewrites queries to inject the policy expression as an additional `WHERE` clause. You can see it in `EXPLAIN`. Indexes on `company_id` are used normally.

**The connection pooling trap:** `SET app.company_id = ...` persists for the whole Postgres session. Pool returns the connection → next request reuses it → `app.company_id` is still set to the previous request's value. Data leak. Use `SET LOCAL` inside a transaction — transaction-scoped, cleared on `COMMIT` / `ROLLBACK`.

```typescript
await db.transaction(async (tx) => {
  await tx.execute(sql`SET LOCAL app.company_id = ${companyId}`);
  // ... queries using tx are safely scoped ...
});
```

**Migration role:** Schema changes and data backfills need to bypass RLS. Standard pattern: migrations run as a role with `BYPASSRLS`; runtime queries run as a role without it. The migration Lambda or job uses the privileged role; request handlers do not. Note that `drizzle-kit` generates the policies and `ENABLE ROW LEVEL SECURITY`, but **not** the roles' `BYPASSRLS`/`NOLOGIN` attributes, the table `GRANT`s, or the backfills — keep those in hand-written companion migrations alongside the schema-declared policies.

**Permissive vs restrictive policies:** Multiple permissive policies on the same table are OR'd together — any match lets the row through. Restrictive policies (Postgres 10+) are AND'd — all must pass. Useful for combining a tenant filter (permissive) with a deactivation check (restrictive):

```sql
CREATE POLICY tenant_isolation ON courses
  USING (company_id = current_setting('app.company_id')::uuid);

CREATE POLICY not_deleted ON courses AS RESTRICTIVE
  USING (deleted_at IS NULL);
```

**Debugging RLS:** There's no "RLS debug log." When a query returns unexpectedly empty:
1. `SHOW app.company_id;` — is the session variable set?
2. `EXPLAIN SELECT ...` — is the injected predicate what you expect?
3. `SELECT * FROM pg_policies WHERE tablename = 'x';` — read the policy text directly

### Cross-tenant admin operations

RLS makes cross-tenant reads impossible by default. That's the point — but admin tooling, cross-tenant analytics, and customer-support workflows need a way through. Options:

- A separate role with `BYPASSRLS` used only by admin tooling, with its actions logged
- Policies that grant visibility to a superadmin role (`current_setting('app.is_superadmin') = 'true'`)
- A separate admin service running against a connection that bypasses RLS

---

## Common Vulnerabilities

Named patterns worth recognising. Most come from the OWASP API Security Top 10.

| Vulnerability | What it is | Defence |
|---------------|-----------|---------|
| **BOLA** (Broken Object-Level Authorization) | `GET /orders/456` works because ownership wasn't checked. The #1 API vulnerability by volume | Ownership check in every handler that takes an ID. Better: RLS or a scoped data layer |
| **IDOR** (Insecure Direct Object References) | UUIDs as path params without ownership check. Essentially a flavour of BOLA | Same as BOLA. Note that opaque IDs (UUIDs) don't fix this — only authorisation does |
| **Broken Function Level Authorization** | Admin endpoints exposed without the admin check. Often happens when a new endpoint is added to an existing route group with inconsistent middleware | Role check in middleware for admin route groups; test with a non-admin token |
| **Mass Assignment** | `PATCH /users/me` accepts `{role: "admin"}` because the handler passes the whole body to the ORM | Explicit allowlist at the boundary — Zod / Pydantic schemas that only accept safe fields |
| **Confused Deputy** | A service runs with its own (elevated) permissions and acts on a user's behalf without verifying the user's authorisation | Carry the user context into every decision point; see "Privilege escalation" above |
| **JWT `none` algorithm** | Some JWT libraries historically accepted the `alg: "none"` header — no signature. Attackers forge tokens | Use a library that rejects `none`; explicitly pin allowed algorithms (`algorithms=["RS256"]`) |
| **Expired JWT accepted** | Verifier didn't check `exp` | Use a library that checks `exp` by default; don't pass flags that disable expiry checking |
| **Wrong audience accepted** | Verifier didn't check `aud` — token issued for Service A is accepted by Service B | Always set and check the `audience` parameter |

---

## Audit Logging

SOC 2 (CC6+CC7) and most compliance frameworks require audit logs for authorization-relevant events. Treat them as separate from operational logs:

| Operational logs | Audit logs |
|------------------|-----------|
| Errors, warnings, debug traces | Who did what, when, to what, with what outcome |
| Retention: days to weeks | Retention: 1+ year typically |
| Often sampled | Never sampled |
| Same pipeline as other logs | Often a separate stream (e.g., dedicated CloudWatch log group) |

Minimum fields per audit event:

```
{actor, action, resource, outcome, timestamp, request_id}
```

Events worth logging:
- Every authn event — login (success and failure), logout, MFA challenge outcome
- Every authorization denial
- Every state-changing action (create / update / delete)
- Every admin / cross-tenant action

See [Logging](./logging.md) for structured logging patterns and [Security](./security.md) for secrets-in-logs scrubbing (never log tokens or passwords).

---

## Where auth state lives

Putting it together — "am I authenticated vs authorised?" depends on which layer you're asking at.

| Layer | What's stored there | Lifetime |
|-------|---------------------|----------|
| User's browser | `id_token`, `access_token`, `refresh_token` | Until logout or expiry |
| In-flight request header | `Authorization: Bearer <jwt>` | Single request |
| Gateway / proxy | JWKS cache (public keys) | ~1h cache |
| Application instance | Parsed user context after auth middleware | Single invocation |
| Database session | Session variables (`app.company_id`) | Current transaction (with `SET LOCAL`) |
| Database data | User rows, role assignments, policy definitions | Forever |
| IdP | User attributes, password hash, MFA config, identity ↔ user mapping | Forever |

"Is this user authenticated?" — resolved by verifying signature + expiry on the JWT. Stateless.

"Is this user authorised to do X?" — derived from identity + resource + action + context. Decision evaluated at one or more enforcement layers.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Store plain text / MD5 / SHA256 passwords | Use bcrypt or argon2 with cost factor 12+ | Weak hashing means stolen databases are cracked in minutes |
| Check authentication but not authorization | Verify the user has permission for the specific resource and action | Authenticated ≠ authorised; user A shouldn't access user B's data |
| Put secrets in a JWT payload | JWTs are signed, not encrypted — payload is readable by anyone | Anyone with the token (including anyone who read it from a log) can read every claim |
| Read tenant ID from the request body | Derive it from the authenticated session, server-side | Client-supplied tenant IDs let callers query any tenant |
| Pass user input straight to an ORM in PATCH | Explicit allowlist via Zod / Pydantic schema | Mass assignment — `{role: "admin"}` in the body escalates privileges |
| Accept `alg: "none"` JWTs | Pin allowed algorithms explicitly — `["RS256"]` | Historical library bug; forged tokens with no signature |
| Skip `aud` and `iss` checks | Always validate `iss`, `aud`, and `exp` | Tokens issued for a different service or a different environment can be replayed |
| Force password rotation every 90 days | Rotate only on evidence of compromise | Produces `Password1`, `Password2`; fails the usability test without improving security |
| Rely on client-side role checks alone | Enforce on the server; use client-side only for UX | Any user can disable the client check with devtools |
| Use a shared `admin` DB connection for all user-scoped queries | Use a runtime role without `BYPASSRLS`, wrap requests in transactions with `SET LOCAL` | One missed filter = cross-tenant leak. Structural defence beats convention |
| Return 401 where 403 is the right answer | 401 for AuthN failure, 403 for AuthZ failure | Leaks information about whether a resource exists |
| Roll your own auth service | Use a managed IdP (Cognito, Auth0, Clerk, Okta) | Auth is easy to get mostly right and hard to get fully right; most incidents come from homegrown systems |

---

## Deciding for Your Project

1. **Do you run your own identity?** If no → managed IdP (Cognito, Auth0, Clerk, Okta, Supabase Auth). If yes → Keycloak or Ory. Rolling your own is rarely the right call.
2. **What token shape?** OIDC authorization code + PKCE is the default for browser SPAs and mobile. Client credentials for pure machine-to-machine.
3. **Where do tokens live in the browser?** `localStorage` is common and accepts the XSS tradeoff. `httpOnly` cookies are stronger but add CSRF concerns. In-memory + silent refresh is the highest-assurance default for sensitive apps.
4. **Session shape?** Short-lived access tokens + refresh token rotation + deny-list for critical revocations is the modern hybrid. Opaque sessions remain fine for server-rendered web apps.
5. **AuthZ model?** Start with RBAC. Add ABAC for resource-level rules. Reach for policy engines or ReBAC only when the rules outgrow code.
6. **Multi-tenant isolation?** If on Postgres, plan for RLS — it's the only option where a bug cannot leak across tenants. If on a different store, map the equivalent (per-tenant partition, per-tenant encryption key).
7. **MFA?** TOTP as the table-stakes option. WebAuthn / passkeys where the UX and user base support it. Mandatory for admin accounts.
8. **Audit logging?** Separate stream, long retention, never sampled. Even if no framework requires it yet, incidents are much easier to triage with a clean audit trail.

---

## Related Topics

- **Secrets management (JWT signing keys, IdP client secrets)** — see [Configuration](./configuration.md)
- **Input validation (Zod / Pydantic at handler boundary for claim extraction and mass-assignment defence)** — see [Data Integrity](./data-integrity.md)
- **Error response shape (401 / 403 status codes, Problem Details format)** — see [Error Handling](./error-handling.md)
- **Structured logging and audit-log scrubbing** — see [Logging](./logging.md)
- **Rate limiting on login and token endpoints, CSRF, CORS, security headers** — see [Security](./security.md)
- **`Authorization` header conventions, 401 / 403 status selection** — see [API Design](./api-design.md)
