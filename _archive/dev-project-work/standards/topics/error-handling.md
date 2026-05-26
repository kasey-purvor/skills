# Error Handling

## The Problem

When something goes wrong in your code, you throw an error. In most beginner code:

```typescript
throw new Error("Something went wrong");
```

```python
raise Exception("Something went wrong")
```

Now imagine you're catching this higher up the call stack. What do you do with it?

```typescript
try {
  await processOrder(orderId);
} catch (error) {
  // What kind of error is this?
  // - User sent invalid data? → return 400
  // - Order doesn't exist? → return 404
  // - Payment service is down? → return 502, maybe retry
  // - Bug in our code? → return 500, log it, alert someone

  // With generic Error, you have to inspect the message string:
  if (error.message.includes("not found")) {  // fragile!
    return res.status(404).json({ error: "Not found" });
  }
  // If someone changes the message wording, this silently breaks
}
```

You're pattern-matching on strings. If someone changes the error message from "not found" to "does not exist," your catch block falls through to a generic 500. This is fragile, untyped, and scales terribly.

---

## Error Hierarchies

A custom error hierarchy is a tree of error classes where the class itself tells you what kind of failure occurred:

```
AppError (base — everything your app throws)
├── ValidationError     (bad input from the user)
├── NotFoundError       (requested resource doesn't exist)
├── ExternalServiceError (a third-party API or database failed)
│   ├── TimeoutError
│   └── RateLimitError
├── AuthorizationError  (user isn't allowed to do this)
└── ConflictError       (action conflicts with current state)
```

### TypeScript Implementation

```typescript
// Base error — everything your app throws extends this
class AppError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number = 500,
    public readonly isOperational: boolean = true,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = this.constructor.name;
  }
}

// Specific error types
class ValidationError extends AppError {
  constructor(message: string, public readonly fields?: Record<string, string>) {
    super(message, 400);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} '${id}' not found`, 404);
  }
}

class ExternalServiceError extends AppError {
  constructor(service: string, cause?: Error) {
    super(`${service} request failed`, 502, true, { cause });
  }
}

class AuthenticationError extends AppError {
  constructor(message = "Authentication required") {
    super(message, 401);
  }
}

class AuthorizationError extends AppError {
  constructor(message = "Not authorized") {
    super(message, 403);
  }
}

class ConflictError extends AppError {
  constructor(message: string) {
    super(message, 409);
  }
}
```

**AuthenticationError (401) vs AuthorizationError (403):** Authentication = "I don't know who you are" (missing or invalid token). Authorization = "I know who you are, but you can't do this" (valid user, insufficient permissions). These are commonly confused — using distinct classes prevents misuse.

### Python Implementation

**Naming note:** FastAPI/Pydantic has its own `ValidationError` and `RequestValidationError`. To avoid collisions, either name yours `AppValidationError`, or handle both in your exception handlers. The examples below use `ValidationError` for clarity — in a FastAPI project, be explicit about which one you're catching.

```python
class AppError(Exception):
    """Base error for all application errors."""
    def __init__(self, message: str, status_code: int = 500, is_operational: bool = True):
        super().__init__(message)
        self.status_code = status_code
        self.is_operational = is_operational

class ValidationError(AppError):
    def __init__(self, message: str, fields: dict[str, str] | None = None):
        super().__init__(message, status_code=400)
        self.fields = fields or {}

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} '{id}' not found", status_code=404)

class ExternalServiceError(AppError):
    def __init__(self, service: str):
        super().__init__(f"{service} request failed", status_code=502)
    # To preserve the original exception, raise with `from`:
    # raise ExternalServiceError("database") from original_err
    # — see "Error Chaining" below. Do not assign self.__cause__ in __init__;
    # `raise ... from` is the idiomatic form and also sets __suppress_context__
    # so tracebacks render cleanly.

class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)

class AuthorizationError(AppError):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)

class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)
```

### Using the Hierarchy

Now catch blocks are clean and type-safe:

```typescript
try {
  await processOrder(orderId);
} catch (error) {
  if (error instanceof ValidationError) {
    return res.status(400).json({ error: error.message, fields: error.fields });
  }
  if (error instanceof NotFoundError) {
    return res.status(404).json({ error: error.message });
  }
  if (error instanceof ExternalServiceError) {
    return res.status(502).json({ error: "Service temporarily unavailable" });
  }
  // Unknown error — this is a bug
  return res.status(500).json({ error: "Internal server error" });
}
```

But even better — you don't write this in every handler. You write it **once** in a global error handler (see below).

### The `isOperational` Flag

This is a crucial distinction on the base `AppError`:

- **Operational errors** are expected failures — user sent bad data, resource not found, external service timed out. Your app knows how to handle these. They're part of normal operation.
- **Programming errors** are bugs — null reference, wrong type, undefined variable. Your app does NOT know how to handle these. They mean something is wrong with the code itself.

Why this matters: operational errors get a clean response to the user. Programming errors get logged, reported to your error tracking service (Sentry, Datadog, etc.), and might trigger an alert. The `isOperational` flag lets your global error handler decide which treatment to apply.

---

## Error Chaining (Preserving Context)

When an error bubbles up through multiple layers, each layer should add context without losing the original cause:

```
User clicks "Place Order"
  → Order Service calls Payment Service
    → Payment Service calls Database
      → Database times out              ← original error
    → Payment Service: "charge failed"  ← context lost!
  → Order Service: "order failed"       ← even more context lost!
→ User sees: "order failed"             ← useless for debugging
```

**With error chaining, you preserve the full trail:**

### TypeScript (ES2022+)

```typescript
try {
  await db.execute(query);
} catch (err) {
  // The ExternalServiceError constructor (shown above) accepts cause
  // positionally and forwards it to the Error constructor as { cause }.
  throw new ExternalServiceError("database", err instanceof Error ? err : undefined);
}

// When you log the full error:
// ExternalServiceError: database request failed
//   [cause]: DatabaseTimeoutError: connection timed out to postgres:5432
```

Behind the scenes, the `ErrorOptions` { cause } form was added in ES2022 and is supported by all modern runtimes. Your error classes can accept the cause in whatever shape makes sense for their call sites (a positional `Error` argument here) and forward it to `super(message, { cause })` — the important thing is that the signatures line up.

### Python

```python
try:
    db.execute(query)
except DatabaseTimeout as e:
    raise ExternalServiceError("database") from e
    #                                      ^^^^^^
    # "from e" preserves the original error

# The traceback shows both:
# ExternalServiceError: database request failed
#
# The above exception was the direct cause of the following exception:
#
# DatabaseTimeout: connection timed out to postgres:5432
```

**Why this matters:** When debugging a production incident at 2am, you need the full chain — not just "order failed" but "order failed → caused by charge failed → caused by database timeout on postgres:5432." Without chaining, you lose the trail.

---

## Global Error Handlers

Instead of writing error handling in every route handler, write it **once** as middleware. Every unhandled error flows through this single point.

### Express (TypeScript)

```typescript
// Register AFTER all your routes
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  // Known application error — use the hierarchy
  if (err instanceof AppError) {
    if (err.isOperational) {
      logger.warn({ err, path: req.path }, "Operational error");
    } else {
      logger.error({ err, path: req.path }, "Non-operational AppError");
    }

    const body: Record<string, unknown> = {
      type: err.name,
      title: err.message,
      status: err.statusCode,
    };

    // Include field-level errors for validation failures
    if (err instanceof ValidationError && err.fields) {
      body.errors = Object.entries(err.fields).map(([field, message]) => ({
        field,
        message,
      }));
    }

    return res.status(err.statusCode).json(body);
  }

  // Unknown error — this is a bug, not an expected failure
  logger.error({ err, path: req.path }, "Unhandled error");
  return res.status(500).json({
    type: "InternalError",
    title: "Internal server error",
    status: 500,
    // Don't include the raw error message or stack trace in responses to
    // untrusted clients — it can leak internal details to attackers. Stack
    // traces still belong in your server logs and in your error-tracking
    // service (Sentry, Datadog); they just shouldn't be in the HTTP response
    // body a public caller receives.
  });
});
```

### FastAPI (Python)

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    if exc.is_operational:
        logger.warning("Operational error", path=str(request.url), error=str(exc))
    else:
        logger.error("Non-operational error", path=str(request.url), error=str(exc))

    body = {
        "type": type(exc).__name__,
        "title": str(exc),
        "status": exc.status_code,
    }

    if isinstance(exc, ValidationError) and exc.fields:
        body["errors"] = [
            {"field": field, "message": msg}
            for field, msg in exc.fields.items()
        ]

    return JSONResponse(status_code=exc.status_code, content=body)

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled error", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "type": "InternalError",
            "title": "Internal server error",
            "status": 500,
        },
    )
```

### React Error Boundaries (Vite, CRA, Remix, any React app)

React error boundaries catch JavaScript errors in the component tree and display a fallback UI instead of a crashed page. They're the frontend equivalent of a global error handler — without them, a single component error unmounts the entire app.

```tsx
// ErrorBoundary.tsx — reusable, wrap around any subtree that might fail
import { Component, type ReactNode } from 'react';

interface Props {
  fallback: ReactNode | ((error: Error, reset: () => void) => ReactNode);
  children: ReactNode;
}

interface State {
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Log to your error tracking service (Sentry, Datadog, etc.)
    console.error('Error boundary caught:', error, info.componentStack);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (this.state.error) {
      const { fallback } = this.props;
      return typeof fallback === 'function'
        ? fallback(this.state.error, this.reset)
        : fallback;
    }
    return this.props.children;
  }
}
```

```tsx
// Usage — wrap around components that might fail (iframes, third-party widgets, data-dependent views)
<ErrorBoundary fallback={(error, reset) => (
  <div>
    <h2>Something went wrong</h2>
    <p>{error.message}</p>
    <button onClick={reset}>Try again</button>
  </div>
)}>
  <CoursePlayer />
</ErrorBoundary>
```

**Where to place boundaries:** Don't wrap the entire app in one boundary — that gives a full-page error for a single broken component. Place boundaries around **isolated risk areas**: third-party content (iframes, embeds), data-heavy views, and any component that depends on external state.

**Limitation:** Error boundaries only catch errors during rendering, lifecycle methods, and constructors. They do NOT catch errors in event handlers, async code, or `useEffect`. For those, use try/catch in the handler and set error state manually.

### Next.js (error.tsx)

Next.js provides a built-in error boundary convention using file-based routing:

```tsx
// app/error.tsx — catches errors in any route segment (built on React error boundaries)
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}

// app/global-error.tsx — catches errors in the root layout itself
```

For API routes in Next.js, you'd handle errors in route handlers or use a wrapper function that catches and formats errors.

### Process-Level Handlers (Last Resort)

Even with framework error handlers, some errors escape — unhandled Promise rejections, errors thrown outside request context:

```typescript
// Node.js — catch unhandled Promise rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.fatal({ reason }, 'Unhandled rejection — shutting down');
  process.exit(1);
});

// Node.js — catch uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.fatal({ error }, 'Uncaught exception — shutting down');
  process.exit(1);
});
```

```python
import sys

def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.fatal("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.exit(1)

sys.excepthook = global_exception_handler
```

**Why exit on unhandled errors?** After an unhandled error, your process is in an unknown state. Memory might be corrupted, connections might be half-open. The safest thing is to exit and let your process manager (Docker, systemd, Kubernetes) restart a clean instance. This connects to [Resilience](./resilience.md) — graceful shutdown means finishing in-flight work before exiting.

---

## HTTP Error Response Schema

When your API returns an error, the response body should always have the same shape. **RFC 9457 (Problem Details for HTTP APIs)** is the internet standard for this:

**Note:** RFC 9457 specifies that the `type` field should be a URI reference (e.g., `"type": "https://api.example.com/errors/validation"`). Using class names like `"ValidationError"` is a common pragmatic simplification that's easier to work with. Either approach works — be consistent.

```json
{
  "type": "ValidationError",
  "title": "Invalid request data",
  "status": 400,
  "detail": "2 validation errors in request body",
  "errors": [
    { "field": "email", "message": "Must be a valid email address" },
    { "field": "age", "message": "Must be a positive integer" }
  ]
}
```

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `type` | Yes | Machine-readable error type (maps to your error hierarchy class name) |
| `title` | Yes | Short human-readable summary |
| `status` | Yes | HTTP status code (repeated in body for convenience — clients don't always have access to the response status) |
| `detail` | Optional | More specific explanation of what went wrong |
| `errors` | Optional | Array of field-level validation errors (for 400/422 responses) |

### HTTP Status Code Selection

| Code | When to use | Example |
|------|------------|---------|
| **400** Bad Request | Client sent invalid data | Validation failed, malformed JSON |
| **401** Unauthorized | No authentication or expired token | Missing `Authorization` header |
| **403** Forbidden | Authenticated but not allowed | User tries to access admin resource |
| **404** Not Found | Resource doesn't exist | `GET /users/999` where user 999 doesn't exist |
| **409** Conflict | Conflicts with current state | Creating a user with an email that already exists |
| **422** Unprocessable Entity | Valid syntax but semantically wrong | Valid JSON but business rules reject it |
| **429** Too Many Requests | Rate limit exceeded | Client sending too many requests too fast |
| **500** Internal Server Error | Bug in your code | Unhandled exception, programming error |
| **502** Bad Gateway | Upstream service failed | Payment API returned an error |
| **503** Service Unavailable | Temporarily overloaded | Database connection pool exhausted |

**400 vs 422:** Long-running debate. 400 = "I can't parse your request." 422 = "I parsed it but it doesn't make sense." Most APIs just use 400 for all client validation errors. Pick one and be consistent across your entire API.

### Connecting Error Hierarchy to HTTP Responses

The error hierarchy maps directly to HTTP responses through the global error handler:

```
ValidationError  → 400 + field-level errors
NotFoundError    → 404
AuthorizationError → 403
ConflictError    → 409
ExternalServiceError → 502
Unknown Error    → 500 (never expose internal details)
```

This mapping is defined **once** in the global error handler, not in every route. Your route handlers just throw the right error type:

```typescript
// In your route — clean, no HTTP status code logic
async function getUser(req: Request, res: Response) {
  const user = await db.findUser(req.params.id);
  if (!user) throw new NotFoundError("User", req.params.id);
  res.json(user);
}
// The global error handler turns NotFoundError into a 404 response
```

```python
# In your route — clean, no HTTP status code logic
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await db.find_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user
# The exception handler turns NotFoundError into a 404 response
```

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| `throw new Error("not found")` — generic errors with message strings | `throw new NotFoundError("User", id)` — typed error classes | String matching is fragile; class matching is type-safe |
| Catch-and-ignore: `catch (e) { /* do nothing */ }` | At minimum, log the error | Swallowed errors hide bugs and make debugging impossible |
| Catch-and-rethrow without context: `catch (e) { throw e }` | Wrap with a typed error that forwards the cause (e.g. `throw new ExternalServiceError("payments", e)`) | Naked rethrow adds no value; wrapping adds context and preserves the chain |
| Expose stack traces to clients: `res.json({ stack: err.stack })` | Return safe, generic messages to clients | Stack traces leak internal code paths — security and UX issue |
| Handle errors in every route handler individually | Use a global error handler | DRY — one place to maintain error→response mapping |
| Use HTTP status codes inconsistently (404 sometimes, 400 other times for same thing) | Define the mapping once in the error hierarchy | Inconsistent codes confuse frontend developers and monitoring |
| Log operational errors at ERROR level | Log operational errors at WARN, programming errors at ERROR | Otherwise your error alerts fire for expected situations (user typos, etc.) |
| Return different error response shapes per endpoint | Use RFC 9457 Problem Details everywhere | Frontend needs one error-handling function, not per-endpoint parsing |

---

## Deciding for Your Project

When starting a new project, determine:

1. **What error types will your app encounter?** Map your domain to the hierarchy — most apps need at least: Validation, NotFound, Authorization, ExternalService.
2. **What framework are you using?** This determines how the global error handler is registered (Express middleware, FastAPI exception handler, Next.js error.tsx).
3. **Do you need field-level validation errors?** If your API accepts complex forms, yes — include an `errors` array in validation responses.
4. **What error tracking service?** Sentry, Datadog, Bugsnag — programming errors (non-operational) should be reported to one of these.
5. **400 or 422 for validation?** Pick one, document it, use it everywhere.

---

## Related Topics

- **When data validation fails** — see [Data Integrity](./data-integrity.md) for what triggers `ValidationError` in the first place
- **Resilience patterns** — see [Resilience](./resilience.md) for retries, circuit breakers, timeouts, graceful shutdown, and health checks
- **Structured error logging** — see [Logging](./logging.md) for how to log errors with correlation IDs and structured context
- **Security and error responses** — see [Security](./security.md) for why you must never expose internal error details to clients
