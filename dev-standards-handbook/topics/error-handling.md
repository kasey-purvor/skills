# Error Handling

> **Calibrate to the context — but note most of this chapter is cheap.** Typed error
> classes, one global handler, never swallowing errors, never leaking internals — these
> cost less than the sloppy alternative at any app size, so they're worth doing almost
> everywhere. What *does* scale with the audience is the formality around it: a strict
> response-body standard (RFC 9457) and a paid error-tracking service earn their keep
> when outside clients and real production users are involved; an internal tool can get
> by with a simpler consistent shape and its logs. Reference material, not a checklist.

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
AppError (base — everything your app throws on purpose)
├── ValidationError        (bad input from the user)
├── NotFoundError          (requested resource doesn't exist)
├── AuthenticationError    (no valid credentials: we don't know who you are)
├── AuthorizationError     (user isn't allowed to do this)
├── ConflictError          (action conflicts with current state)
└── ExternalServiceError   (a third-party API or database failed → 502)
    ├── UpstreamTimeoutError    (it didn't answer in time → 504)
    └── UpstreamRateLimitError  (it answered 429 to us → 503 + Retry-After)
```

`UpstreamTimeoutError`, not `TimeoutError`: in Python a class named `TimeoutError` shadows the built-in, which `asyncio.TimeoutError` aliases since 3.11.

### TypeScript Implementation

```typescript
// ES2022+ (ErrorOptions `cause`), TypeScript 4.3+ (`override`)
// Base error — everything your app throws on purpose extends this
abstract class AppError extends Error {
  // Stable, machine-readable code clients branch on, chosen independently of the class name
  // so a refactor never breaks the contract. Abstract, so a subclass without one won't compile.
  abstract readonly code: string;
  // Headers the status requires, which the global handler sends: WWW-Authenticate on a 401,
  // Retry-After on a 503. A subclass that needs one overrides this.
  readonly headers: Record<string, string> = {};

  constructor(
    message: string,
    public readonly statusCode: number = 500,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = this.constructor.name;
  }
}

// Specific error types
class ValidationError extends AppError {
  readonly code = "VALIDATION_ERROR";
  constructor(message: string, public readonly fields?: Record<string, string>) {
    super(message, 400);
  }
}

class NotFoundError extends AppError {
  readonly code = "NOT_FOUND";
  constructor(resource: string, id: string) {
    super(`${resource} '${id}' not found`, 404);
  }
}

class ExternalServiceError extends AppError {
  readonly code: string = "EXTERNAL_SERVICE_ERROR"; // typed `string` so subclasses can refine it
  constructor(
    public readonly service: string, // for the log line; `detail` never names your topology
    cause?: Error,
    statusCode = 502,
  ) {
    super("An upstream service failed", statusCode, { cause });
  }
}

class UpstreamTimeoutError extends ExternalServiceError {
  // `override` (required under noImplicitOverride): it replaces a concrete code, not an abstract one
  override readonly code = "UPSTREAM_TIMEOUT";
  constructor(service: string, cause?: Error) {
    super(service, cause, 504); // the upstream never answered: 504, not 502
  }
}

class AuthenticationError extends AppError {
  readonly code = "AUTHENTICATION_REQUIRED";
  override readonly headers = { "WWW-Authenticate": 'Bearer realm="api"' }; // a 401 must send one
  constructor(message = "Authentication required") {
    super(message, 401);
  }
}

class AuthorizationError extends AppError {
  readonly code = "FORBIDDEN";
  constructor(message = "Not authorized") {
    super(message, 403);
  }
}

class ConflictError extends AppError {
  readonly code = "CONFLICT";
  constructor(message: string) {
    super(message, 409);
  }
}
```

**AuthenticationError (401) vs AuthorizationError (403):** Authentication = "I don't know who you are" (missing or invalid token). Authorization = "I know who you are, but you can't do this" (valid user, insufficient permissions). These are commonly confused — using distinct classes prevents misuse.

### Python Implementation

**Naming note:** FastAPI/Pydantic has its own `ValidationError` and `RequestValidationError`. To avoid collisions, either name yours `AppValidationError`, or handle both in your exception handlers. The examples below use `ValidationError` for clarity — in a FastAPI project, be explicit about which one you're catching.

```python
# Python 3.11+ — subclasses mirror the TypeScript tree above
class AppError(Exception):
    """Base for every error the app raises on purpose."""
    # Class attributes, so a subclass overrides them in two lines. `code` is the stable,
    # machine-readable code clients branch on, chosen independently of the class name.
    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    headers: dict[str, str] | None = None  # WWW-Authenticate on a 401, Retry-After on a 503

class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409

class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 400

    def __init__(self, message: str, fields: dict[str, str] | None = None):
        super().__init__(message)
        self.fields = fields or {}

class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404

    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} '{id}' not found")

class ExternalServiceError(AppError):
    code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502

    def __init__(self, service: str):
        super().__init__("An upstream service failed")
        self.service = service  # for logs and metrics; `detail` never names your topology

class UpstreamTimeoutError(ExternalServiceError):
    code = "UPSTREAM_TIMEOUT"
    status_code = 504
```

The other classes in the tree are two-line subclasses like `ConflictError`: only a subclass that carries data needs an `__init__`. `AuthenticationError` adds a third line, `headers = {"WWW-Authenticate": 'Bearer realm="api"'}`. Keep the cause with `raise ... from e` (see Error Chaining below), not by assigning `__cause__`.

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
    // 502, 503 or 504: the subclass chose it
    return res.status(error.statusCode).json({ error: "Service temporarily unavailable" });
  }
  // Unknown error — this is a bug
  return res.status(500).json({ error: "Internal server error" });
}
```

But even better — you don't write this in every handler. You write it **once** in a global error handler (see below).

### Expected Errors vs Bugs

The hierarchy itself draws the line the global handler needs:

- **An `AppError` is an expected (operational) failure** — user sent bad data, resource not found, external service timed out. Your app knows how to handle these. They're part of normal operation.
- **Anything else is a bug (a programming error)** — null reference, wrong type, undefined variable. Your app does NOT know how to handle these. A deliberate invariant check that fails ("an order can't have zero lines") throws a plain `Error` for the same reason, so it takes the bug path.

Expected errors get a clean response and a WARN log. Bugs get a generic 500, an ERROR log and, if the app has real production users, a report to an error tracking service (Sentry, Datadog, etc.). Because an `AppError`'s message reaches the client as `detail`, write it for the client; anything you would not show a client belongs in the log or the `cause`.

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
// ES2022+ (Error `cause`); under `strict`, TypeScript 4.4+ types `err` as `unknown`
try {
  await db.execute(query);
} catch (err) {
  throw new ExternalServiceError("database", err instanceof Error ? err : undefined);
}

// When you log the full error, `service` and the cause keep the context:
// ExternalServiceError: An upstream service failed
//   service: 'database',
//   [cause]: DatabaseTimeoutError: connection timed out to postgres:5432
```

### Python

```python
# Python 3.11+, with the hierarchy above
try:
    db.execute(query)
except DatabaseTimeout as e:
    raise ExternalServiceError("database") from e
    #                                      ^^^^^^
    # "from e" preserves the original error

# The traceback shows both, the cause first:
# DatabaseTimeout: connection timed out to postgres:5432
#
# The above exception was the direct cause of the following exception:
#
# ExternalServiceError: An upstream service failed
```

**Why this matters:** When debugging a production incident at 2am, you need the full chain — not just "order failed" but "order failed → caused by charge failed → caused by database timeout on postgres:5432." Without chaining, you lose the trail.

---

## Global Error Handlers

Instead of writing error handling in every route handler, write it **once** as middleware. Every unhandled error flows through this single point.

### Express (TypeScript)

**Express 5+ (on Express 4 use `express-async-errors` or an async wrapper).** Express 5 forwards a rejected promise from an `async` route to this handler. Express 4 does not: the rejection skips the handler and becomes an unhandled rejection, which the process-level handler below turns into a crash.

```typescript
// Express 5+ (on Express 4 use express-async-errors or an async wrapper)
import { STATUS_CODES } from "node:http";
import { getRequestId } from "./request-context"; // Logging's accessor (Correlation IDs)

// A request body the parser refused before any route ran
class RequestBodyError extends AppError {
  readonly code = "INVALID_REQUEST_BODY";
}

// Register AFTER all your routes, behind a catch-all 404 so unknown paths get this
// shape instead of Express's default HTML page:
//   app.use((req, res, next) => next(new NotFoundError("Route", req.path)));
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  // Response already started (e.g. a stream failed midway) — let Express close it
  if (res.headersSent) return next(err);

  // body-parser's errors (400 bad JSON, 413 too large, 415 unsupported encoding) carry a
  // 4xx `status` and `expose: true` (http-errors): keep that status, not a logged 500
  const { status, expose } = err as { status?: number; expose?: boolean };
  if (!(err instanceof AppError) && expose && status !== undefined && status < 500) {
    err = new RequestBodyError(err.message, status);
  }

  // Known application error — expected, so WARN and its own status
  if (err instanceof AppError) {
    // `err` must go through Logging's safe `err` serializer ([Error text is data](./logging.md#scrubbing-sensitive-data))
    logger.warn({ err, path: req.path }, "Request failed with an expected error");

    const body: Record<string, unknown> = {
      type: "about:blank",        // or a stable tag: URI per problem type (see the schema section)
      code: err.code,
      title: STATUS_CODES[err.statusCode], // stable status phrase, e.g. "Not Found"
      status: err.statusCode,
      detail: err.message,                 // this occurrence, e.g. "User '999' not found"
      requestId: getRequestId(),           // the id on every log line for this request
    };

    // Include field-level errors for validation failures
    if (err instanceof ValidationError && err.fields) {
      body.errors = Object.entries(err.fields).map(([field, message]) => ({
        field,
        message,
      }));
    }

    res.set(err.headers); // WWW-Authenticate on a 401, Retry-After on a 503
    return res.status(err.statusCode).type("application/problem+json").json(body);
  }

  // Unknown error — this is a bug, not an expected failure
  logger.error({ err, path: req.path }, "Unhandled error");
  return res.status(500).type("application/problem+json").json({
    type: "about:blank",
    code: "INTERNAL_ERROR",
    title: "Internal Server Error",
    status: 500,
    requestId: getRequestId(), // the one thing a user can quote to support
    // Never the raw message or stack: they leak internals to attackers. Stack traces
    // belong in your logs and error tracker, not in a public response body.
  });
});
```

**Put the correlation id in every problem body.** It matters most on the 500, whose body otherwise gives the user nothing to report. Read it through Logging's accessor (`getRequestId()` / `get_request_id()` in [Correlation IDs](./logging.md#correlation-ids)) rather than minting one here: Logging owns the value, and echoing it in a response header is its middleware's job. Name the member in your API's field casing ([Field Naming](./api-design.md#field-naming)); Logging's `request_id` rule is for log lines.

### FastAPI (Python)

```python
# FastAPI 0.100+, structlog 25 — `logger` takes keyword fields, as elsewhere in this chapter
from http import HTTPStatus
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .request_context import get_request_id  # Logging's accessor (Correlation IDs)

PROBLEM_JSON = "application/problem+json"
app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning("Request failed with an expected error", path=request.url.path, error=str(exc))

    body = {
        "type": "about:blank",   # or a stable tag: URI per problem type (see the schema section)
        "code": exc.code,
        "title": HTTPStatus(exc.status_code).phrase,  # stable status phrase, e.g. "Not Found"
        "status": exc.status_code,
        "detail": str(exc),                            # this occurrence, e.g. "User '999' not found"
        "request_id": get_request_id(),                # snake_case, as this API's fields are
    }

    if isinstance(exc, ValidationError) and exc.fields:
        body["errors"] = [
            {"field": field, "message": msg}
            for field, msg in exc.fields.items()
        ]

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        media_type=PROBLEM_JSON,
        headers=exc.headers,  # WWW-Authenticate on a 401, Retry-After on a 503
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", path=request.url.path)  # logs the traceback
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "code": "INTERNAL_ERROR",
            "title": "Internal Server Error",
            "status": 500,
            "request_id": get_request_id(),
        },
        media_type=PROBLEM_JSON,
    )
```

**Two built-in errors bypass the `AppError` handler.** FastAPI's `RequestValidationError` (422, body `{"detail": [...]}`) and Starlette's `HTTPException` (unmatched routes 404, wrong method 405) have their own default handlers and their own body shape. Register a handler for each that emits the same problem body, or the API ships two error shapes. For `RequestValidationError`, build each entry from `loc` (as a JSON Pointer) and `msg`; drop `input`, which echoes what the client sent. Import `HTTPException` from `starlette.exceptions`, so the handler also catches FastAPI's subclass.

**So does an `AppError` raised inside an `asyncio.TaskGroup`** (Python 3.11+): it arrives wrapped in an `ExceptionGroup`, which matches no `AppError` handler and becomes a 500. Unwrap it at the fan-out site: in `except* AppError as eg`, take `e = eg.exceptions[0]`; where a helper nests its own TaskGroup, walk to the first leaf (`while isinstance(e, BaseExceptionGroup): e = e.exceptions[0]`); then `raise e`.

**The 500 carries no CORS headers** unless `CORSMiddleware` wraps the finished app at the ASGI level; without that, the browser reports every 500 as a CORS failure and the front end never sees the problem body. [The 500 Without CORS Headers](./pitfalls.md#the-500-without-cors-headers) has the mechanism and the test.

### React Error Boundaries (Vite, CRA, Remix, any React app)

React error boundaries catch JavaScript errors in the component tree and display a fallback UI instead of a crashed page. They're the frontend equivalent of a global error handler — without them, a single component error unmounts the entire app. A class component is still the only native API, even in React 19, so use the `react-error-boundary` library, which also adds reset keys and the `useErrorBoundary` hook:

```tsx
// react-error-boundary 6 (React 18 or 19); `error` in its callbacks is typed `unknown`
import { ErrorBoundary } from "react-error-boundary";

<ErrorBoundary
  fallbackRender={({ resetErrorBoundary }) => (
    <div role="alert">
      <p>Something went wrong.</p>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  )}
  onError={(error) => tracker.captureException(error)} // your error-tracking service
>
  <CoursePlayer />
</ErrorBoundary>
```

**Where to place boundaries:** Keep one root boundary as the last resort, so an unexpected error shows a fallback instead of a blank page. Don't rely on it alone — on its own it turns a single broken component into a full-page error. Add granular boundaries around **isolated risk areas**: third-party content (iframes, embeds), data-heavy views, and any component that depends on external state.

**Limitation:** Error boundaries catch errors thrown during rendering, in lifecycle methods and constructors, and synchronously inside `useEffect`. They do NOT catch errors in event handlers or async code (promises, timers, anything after an `await` — including async work started inside `useEffect`). For those, catch the error and set error state, or hand it to the nearest boundary with `react-error-boundary`'s `showBoundary`.

**For reporting,** React 19's root options `onCaughtError` (a boundary caught it) and `onUncaughtError` (nothing did) on `createRoot` give one place to send every render error to your tracker.

### Next.js (error.tsx)

Next.js provides a built-in error boundary convention using file-based routing:

```tsx
// Next.js 16.3+ App Router (before 16.3 the prop is `reset`; see below)
// app/error.tsx — catches errors in any route segment (built on React error boundaries)
'use client';

// Not named `Error`: that shadows the global, so `instanceof Error` would test this component
export default function ErrorPage({ error, retry }: { error: unknown; retry: () => void }) {
  // Narrow first: a Client Component can throw a value that isn't an Error
  const digest = error instanceof Error ? (error as Error & { digest?: string }).digest : undefined;
  return (
    <div>
      <h2>Something went wrong</h2>
      {digest && <p>Reference: {digest}</p>}
      <button onClick={retry}>Try again</button>
    </div>
  );
}

// app/global-error.tsx — catches errors in the root layout itself. It replaces the
// root layout when it renders, so it must render its own <html> and <body>.
```

**Before 16.3 the prop is `reset`, which does not re-fetch:** call `router.refresh()` and `reset()` inside `startTransition`, or "Try again" re-renders the same failed Server Component payload.

**In production, server errors arrive scrubbed.** An error thrown in a Server Component reaches `error.tsx` with a generic `message` and a `digest`. The same `digest` is in the server log entry for that error, so it is the correlation id to search the logs by. A Server Action is scrubbed the same way, so an expected error thrown from one ("email already taken") reaches the user as a generic failure. Return expected errors from the action as values, read them with `useActionState`, and throw only for bugs; see [Front-end Development](./frontend-development.md#forms-and-recovery).

**Don't swallow `redirect()` and `notFound()`.** Both work by throwing a special error, so a try/catch around them catches it and the navigation never happens. Call `unstable_rethrow(err)` (from `next/navigation`) first in the catch block, or keep those calls outside the try.

For API routes in Next.js, you'd handle errors in route handlers or use a wrapper function that catches and formats errors.

### Process-Level Handlers (Last Resort)

Even with framework error handlers, some errors escape — unhandled Promise rejections, errors thrown outside request context:

```typescript
// Node 15+ — an unhandled rejection already crashes the process by default. Registering a
// handler replaces that crash, so the handler must log, shut down, and exit itself.
// shutdown() is the app's SIGTERM handler from Resilience > Graceful Shutdown; `immediate`
// skips its step-1 wait, so a suspect process stops taking traffic at once.
let shuttingDown = false;

function crash(err: unknown, msg: string) {
  logger.fatal({ err }, msg);                          // pino serialises an Error (with stack) only under `err`
  if (shuttingDown) return;                            // a second error mid-shutdown: log it, don't start again
  shuttingDown = true;
  setTimeout(() => process.exit(1), 10_000).unref();  // short hard deadline — the process state is suspect
  shutdown({ immediate: true }).finally(() => process.exit(1));
}

process.on('unhandledRejection', (reason) => crash(reason, 'Unhandled rejection — shutting down'));
process.on('uncaughtException', (error) => crash(error, 'Uncaught exception — shutting down'));
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

`sys.excepthook` only sees an exception that reaches the top of the main thread. Exceptions in other threads go to `threading.excepthook`, and exceptions in asyncio tasks nobody awaits go to the event loop's handler (`loop.set_exception_handler`). Under FastAPI and Uvicorn, those two are the paths that matter.

**Why exit on unhandled errors?** After an unhandled error, your process is in an unknown state. Memory might be corrupted, connections might be half-open. The safest thing is to exit and let your process manager (Docker, systemd, Kubernetes) restart a clean instance. This connects to [Resilience](./resilience.md) — graceful shutdown means finishing in-flight work before exiting.

---

## HTTP Error Response Schema

When your API returns an error, the response body should have the same shape on every endpoint — consistency is the rule; one error-handling function on the client, not per-endpoint parsing. **RFC 9457 (Problem Details for HTTP APIs)** is the internet standard shape, and the natural pick when external clients consume your API; an internal API can use a simpler shape, as long as it's one shape:

**Branch on one stable identifier, never on a class name.** It's tempting to put your error *class name* in `type` for clients to switch on — don't. That welds your public contract to internal class names, so renaming a class in a refactor silently breaks every client. RFC 9457 says consumers MUST use `type` as the problem type's primary identifier and allows a URI that resolves to nothing, so the strict option is a stable `tag:` URI per problem type (`tag:example.com,2026:validation-error`), chosen independently of class names. The pragmatic option, used in this chapter, is a departure clients usually find simpler: leave `type` as `"about:blank"` and add a `code` extension member (e.g. `"VALIDATION_ERROR"`) for them to branch on. See [The Class-Name Error Contract](./pitfalls.md#the-class-name-error-contract).

```json
{
  "type": "about:blank",
  "code": "VALIDATION_ERROR",
  "title": "Bad Request",
  "status": 400,
  "detail": "Invalid request data: 2 validation errors in request body",
  "errors": [
    { "field": "#/email", "message": "Must be a valid email address" },
    { "field": "#/items/2/qty", "message": "Must be a positive integer" }
  ],
  "requestId": "req_abc123"
}
```

The key names inside `errors` are yours to choose; the decision that matters is addressing. Locate each field with a JSON Pointer, as RFC 9457's own example does in `pointer`, because a bare name cannot say which array item failed.

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `code` | Yes, in the pragmatic shape | **Stable, machine-readable error code clients branch on** (e.g. `VALIDATION_ERROR`), chosen independently of class names so refactors never change the wire contract |
| `type` | Optional | URI identifying the problem type. In the strict shape it is what clients branch on (a `tag:` URI needs no docs site); in the pragmatic shape it stays `"about:blank"` |
| `title` | Yes | Stable status phrase (e.g. `"Not Found"`), the same on every occurrence |
| `status` | Yes | HTTP status code (repeated in body for convenience — clients don't always have access to the response status) |
| `detail` | Optional | This occurrence's explanation (e.g. `"User '999' not found"`) |
| `errors` | Optional | Array of field-level validation errors (for 400/422 responses), each located by a JSON Pointer |
| `requestId` | Recommended | The request's correlation id, named in the API's field casing, so a user can quote it and you can find the logs |

### HTTP Status Code Selection

| Code | When to use | Example |
|------|------------|---------|
| **400** Bad Request | Client sent invalid data | Validation failed, malformed JSON |
| **401** Unauthorized | No authentication or expired token | Missing `Authorization` header (the response must carry a `WWW-Authenticate` header) |
| **403** Forbidden | Authenticated but not allowed | User tries to access admin resource |
| **404** Not Found | Resource doesn't exist | `GET /users/999` where user 999 doesn't exist |
| **408** Request Timeout | Client took too long to send the request | Request body didn't arrive within the server's read timeout |
| **409** Conflict | Conflicts with current state | Creating a user with an email that already exists |
| **422** Unprocessable Content | Valid syntax but semantically wrong | Valid JSON but business rules reject it |
| **429** Too Many Requests | Rate limit exceeded | Client sending too many requests too fast — send `Retry-After` |
| **500** Internal Server Error | Bug in your code | Unhandled exception, programming error |
| **502** Bad Gateway | Upstream service failed | Payment API returned an error |
| **503** Service Unavailable | Temporarily overloaded | Database connection pool exhausted; an upstream answered 429 |
| **504** Gateway Timeout | Upstream service didn't answer in time | Payment API call exceeded your timeout |

**400 vs 422:** Long-running debate. 400 = "I can't parse your request." 422 = "I parsed it but it doesn't make sense." (RFC 9110 renamed 422 from "Unprocessable Entity" to "Unprocessable Content".) Most APIs just use 400 for all client validation errors, but FastAPI defaults to 422 for request validation. Pick one and be consistent across your entire API.

### Connecting Error Hierarchy to HTTP Responses

The error hierarchy maps directly to HTTP responses through the global error handler:

```
ValidationError          → 400 + field-level errors
AuthenticationError      → 401 (+ WWW-Authenticate header)
AuthorizationError       → 403
NotFoundError            → 404
ConflictError            → 409
ExternalServiceError     → 502
  UpstreamTimeoutError   → 504
  UpstreamRateLimitError → 503 (+ Retry-After)
Unknown Error            → 500 (never expose internal details)
```

A pool-acquire timeout is the same case: raise a 503 error, since the work never started, not a 502. The two headers ride on the error's `headers`, which the handler copies onto the response.

This mapping is defined **once** in the global error handler, not in every route. Your route handlers just throw the right error type:

```typescript
// Express 5+ — the async throw reaches the global handler (on Express 4, see "Global Error Handlers")
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

## Testing Error Handling

A typed hierarchy and a single global handler only pay off if the handler is actually wired in and fires for every error shape — so these tests live at the wire, driving a request through the whole chain and asserting the response, not unit-testing the error classes in isolation:

- **Hierarchy-to-response mapping.** From "Connecting Error Hierarchy to HTTP Responses": a route that throws `NotFoundError` comes back `404`/`NOT_FOUND`, and a validation failure comes back `400`/`VALIDATION_ERROR` carrying the field-level `errors` array — confirming the RFC 9457 shape (`code`/`title`/`status`/`errors`) is populated, not just declared.
- **The unknown-error path** — the check that matters most, since it's the one that leaks in production. Force a dependency to throw an unexpected (non-`AppError`) error and assert the response is a generic `500`/`INTERNAL_ERROR` whose body carries no stack trace and none of the underlying message (its request id is the one per-occurrence field); assert that *negative* explicitly. In FastAPI the `Exception` handler runs in `ServerErrorMiddleware`, which re-raises after sending the 500, so build the client as `TestClient(app, raise_server_exceptions=False)` or the test raises instead of seeing the response. This is the split from [Expected Errors vs Bugs](#expected-errors-vs-bugs). (Leakage overlaps with Security — this version stays on the error-handler path; [Security](./security.md) owns the attacker-facing source-path sweep.)

These exercise the full middleware chain against a real backend, so they belong with the integration tests — see [Testing](./testing.md) for the real-database setup and the request/handler-invocation craft.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| `throw new Error("not found")` — generic errors with message strings | `throw new NotFoundError("User", id)` — typed error classes | String matching is fragile; class matching is type-safe |
| Catch-and-ignore: `catch (e) { /* do nothing */ }` | Catch only to recover (logging the fallback at WARN) or to add context; otherwise let it reach the global handler | Swallowed errors hide bugs and make debugging impossible |
| Log-and-rethrow: `catch (e) { logger.error(e); throw e }` | Log once, in the global handler; wrap with context on the way up instead of logging | Every layer logs the same failure, so one error becomes N log lines and N alerts |
| Catch-and-rethrow without context: `catch (e) { throw e }` | Wrap with a typed error that forwards the cause (e.g. `throw new ExternalServiceError("payments", e)`) | Naked rethrow adds no value; wrapping adds context and preserves the chain |
| Expose stack traces to clients: `res.json({ stack: err.stack })` | Return safe, generic messages to clients | Stack traces leak internal code paths — security and UX issue |
| Handle errors in every route handler individually | Use a global error handler | DRY — one place to maintain error→response mapping |
| Use HTTP status codes inconsistently (404 sometimes, 400 other times for same thing) | Define the mapping once in the error hierarchy | Inconsistent codes confuse frontend developers and monitoring |
| Log operational errors at ERROR level | Log operational errors at WARN, programming errors at ERROR | Otherwise your error alerts fire for expected situations (user typos, etc.) |
| Return different error response shapes per endpoint | Pick one shape and use it everywhere (RFC 9457 for public APIs) | Frontend needs one error-handling function, not per-endpoint parsing |

---

## Deciding for Your Project

When starting a new project, determine:

1. **Strict RFC 9457, or one simple shape?** For outside clients, RFC 9457, and then whether clients branch on `type` URIs (strict; a `tag:` URI needs no docs site) or on a `code` extension with `type: "about:blank"` (pragmatic). An internal API can use a simpler shape, as long as it's one shape.
2. **Do you need field-level validation errors?** If your API accepts complex forms, yes — include an `errors` array in validation responses, located by JSON Pointer.
3. **What error tracking service, if any?** For apps with real production users, bugs (anything that isn't an `AppError`) should be reported to one (Sentry, Datadog, Bugsnag). For a small internal tool, logs alone are usually enough.
4. **400 or 422 for validation?** Pick one, document it, use it everywhere.

---

## Related Topics

- **User-facing recovery** — see [Front-end Development](./frontend-development.md#forms-and-recovery) for validation, preserved drafts, pending feedback, and the distinction between submission failures and render failures
- **The contract that defers here** — see [API Design](./api-design.md#error-response) for where the error shape sits among the response conventions, and its Field Naming for the casing of members like `requestId`
- **401, 403 and hiding existence** — see [Authentication & Authorization](./authentication-authorization.md#authentication-vs-authorization) for when a failed check is a 401, a 403, or a 404 that hides the resource
- **When data validation fails** — see [Data Integrity](./data-integrity.md) for what triggers `ValidationError` in the first place
- **Resilience patterns** — see [Resilience](./resilience.md) for which `ExternalServiceError`s to retry and when, circuit breakers, timeouts, and the graceful shutdown the crash path reuses
- **Structured error logging** — see [Logging](./logging.md#correlation-ids) for the correlation id the problem body carries and the accessor that reads it
- **Alerting on bugs** — see [Monitoring](./monitoring.md#alerting) for alerting on the error rate without alert fatigue, the reason expected errors log at WARN
- **Security and error responses** — see [Security](./security.md) for why you must never expose internal error details to clients
- **Testing error handling** — see [Testing](./testing.md) for the real-database setup the error-response and unknown-error tests build on
