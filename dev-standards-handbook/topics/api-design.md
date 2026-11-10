# API Design & Contracts

> **Calibrate to your context.** How much of this applies depends on who consumes the
> API. A public or multi-client API you don't control earns strict response-shape
> consistency, versioning, and pagination discipline. An internal API whose only
> callers are known — and changeable in the same commit — needs far less; adopt the
> conventions that save you pain and skip the ceremony that doesn't. Reference
> material, not a checklist.

## The Problem

An API (the HTTP endpoints your backend exposes) is a **contract**. Once you ship an endpoint that returns `{ "user": { "name": "Kasey" } }`, every client that calls it depends on that exact shape. How much a change hurts depends on how many clients there are and whether you control them: a public API with third-party consumers is unforgiving, whereas an internal endpoint whose only caller is your own frontend can change shape freely — as long as you update both sides together.

Without design standards, every endpoint is different:

```
GET  /users/123          → { name: "Kasey" }
GET  /api/v2/orders/456  → { data: { order_name: "..." } }
POST /createPayment      → { success: true, payment_id: 789 }
```

Three URL patterns, three response shapes. Your frontend needs special handling for each. Multiply by 50 endpoints and you have a maintenance nightmare.

---

## URL Conventions

### Resources, Not Actions

REST APIs use nouns (resources), not verbs (actions). The HTTP method IS the verb:

```
GOOD:                           BAD:
GET    /api/users               GET    /api/getUsers
GET    /api/users/123           GET    /api/getUserById?id=123
POST   /api/users               POST   /api/createUser
PUT    /api/users/123           POST   /api/updateUser
DELETE /api/users/123           POST   /api/deleteUser
```

### Naming Rules

- **Plural nouns:** `/api/users` not `/api/user`. Collections are plural, individual items use an ID: `/api/users/123`.
- **Kebab-case:** `/api/user-groups` not `/api/userGroups` or `/api/user_groups`. URL paths are technically case-sensitive (per RFC 3986), but using lowercase kebab-case avoids ambiguity and is the REST convention.
- **Nesting for relationships:** `/api/users/123/orders` — orders belonging to user 123. But don't nest more than two levels deep — `/api/users/123/orders/456/items/789/reviews` is unwieldy. Flatten: `/api/order-items/789/reviews`.

### HTTP Methods

| Method     | Purpose                     | Idempotent? | Request body? | Example                 |
| ---------- | --------------------------- | :---------: | :-----------: | ----------------------- |
| **GET**    | Read a resource             | Yes         | No            | `GET /api/users/123`    |
| **POST**   | Create a new resource       | No          | Yes           | `POST /api/users`       |
| **PUT**    | Replace a resource entirely | Yes         | Yes           | `PUT /api/users/123`    |
| **PATCH**  | Partially update a resource | No*         | Yes           | `PATCH /api/users/123`  |
| **DELETE** | Remove a resource           | Yes         | No            | `DELETE /api/users/123` |

*PATCH can be made idempotent depending on implementation.

**Idempotent** means calling it multiple times produces the same result as calling it once. `DELETE /api/users/123` is idempotent — deleting an already-deleted user is a no-op (or a 404). `POST /api/users` is NOT idempotent — calling it twice creates two users. See [Resilience](./resilience.md) for idempotency keys on non-idempotent operations.

---

## Response Shape Consistency

Every endpoint should follow the same response pattern: a single resource returned directly, and every collection wrapped in an object.

### Single Resource: Direct

```json
GET /api/users/123
{
  "id": "123",
  "name": "Kasey",
  "email": "kasey@example.com",
  "createdAt": "2026-03-15T10:30:00Z"
}
```

### Collections: Always Wrapped

```json
GET /api/users
{
  "data": [
    { "id": "123", "name": "Kasey" },
    { "id": "456", "name": "Alex" }
  ]
}
```

Wrap every collection, even one that does not need pagination yet. A bare array can never gain a `nextCursor` or `hasMore` without breaking every client, which the additive-only rule under API Versioning forbids; an object gains them as new fields. When the collection is paginated, the metadata sits beside `data`:

```json
GET /api/users?page=2&limit=10
{
  "data": [
    { "id": "123", "name": "Kasey" },
    { "id": "456", "name": "Alex" }
  ],
  "pagination": {
    "page": 2,
    "limit": 10,
    "total": 47,
    "hasMore": true
  }
}
```

### Error Response

Use one error shape on every endpoint. For an API that external clients consume, that's the RFC 9457 Problem Details format defined in [Error Handling](./error-handling.md); an internal API may use a simpler shape, as long as it's one shape:

```json
{
  "type": "about:blank",
  "code": "NOT_FOUND",
  "title": "Not Found",
  "status": 404,
  "detail": "User '999' not found",
  "requestId": "req_abc123"
}
```

### Field Naming

Choose the casing for the API's primary consumer, then use it everywhere, query parameters included. A web or TypeScript frontend usually means camelCase (`{ "firstName": "Kasey" }`). snake_case is a legitimate choice for a public API too; Stripe and GitHub use it. What matters is one casing across every endpoint.

A Python API serving camelCase sets `alias_generator=to_camel` on its Pydantic models, and FastAPI serialises responses by alias by default. Set `validate_by_name=True` as well (Pydantic 2.11+), or code that builds a model by its Python field names, `first_name=…`, fails validation.

### Timestamps

Use RFC 3339 (the strict profile of ISO 8601) with an explicit offset for instants: `"2026-04-01T10:23:45.123Z"`. A calendar date with no time of day, such as a birthday or a due date, is date-only (`"2026-04-01"`), because attaching a time zone can shift it to the day before or after. Prefer these over Unix timestamps, which are unambiguous but not human-readable (some APIs, Stripe's among them, use them consistently, and that works too). Never use locale-specific formats ("April 1, 2026" is unparseable).

---

## Pagination

Endpoints that return unbounded collections need pagination. Without it, `GET /api/users` on a 100,000-row table returns the lot — slow, memory-intensive, and liable to crash the client. The exception is small reference lists whose size is known to stay bounded (country codes, currency codes, status enums); returning these in one response is fine, still wrapped in `{ "data": [...] }`.

### Offset-Based (simpler)

```
GET /api/users?page=2&limit=20
```

Returns items 21-40.

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 153
  }
}
```

**Problems:** If someone inserts a new user while you're paginating, you might see duplicates or miss items (the offset shifts). It also slows with depth: `OFFSET 10000` makes the database read and discard 10,000 rows, and `total` needs a `COUNT(*)` over every matching row on each request. On a large table, drop `total` or cache it.

### Cursor-Based (more robust)

```
GET /api/users?limit=20&cursor=eyJpZCI6MTIzfQ
```

The cursor is an opaque token (usually base64-encoded JSON) holding the sort position of the last item seen. The server returns "the next 20 items after this cursor." It must hold the full sort key plus a tiebreaker: for a sort on `createdAt`, that is `{"createdAt": "…", "id": "…"}`, and the next page is `WHERE (created_at, id) < ($1, $2)` with both columns ordered the same way. That is the form for a descending sort, served by an index on `(created_at, id)`. Keep the cursor's timestamp at the database's precision, or the next page silently skips rows ([The Millisecond Cursor](./pitfalls.md#the-millisecond-cursor)). The example cursor above decodes to `{"id":123}`, which works only when the sort is by id.

Treat the cursor as untrusted input. Decode it and parse it through a schema, return 400 for anything that does not parse, and never put authorisation-bearing state in it, such as a tenant or user id: the query takes its scope from the session, as every other query does.

```json
{
  "data": [...],
  "pagination": {
    "nextCursor": "eyJpZCI6MTQzfQ",
    "hasMore": true
  }
}
```

With a deterministic sort order, cursor pagination avoids the duplicate/missed-item problem of offset pagination. "Deterministic" means the sort column combined with a tiebreaker (typically the primary key) produces a total order that doesn't shift between requests. If the sort is on a mutable column (`updated_at`, `score`) without a tiebreaker, rows can still move across cursor boundaries between pages — the guarantee is "no drift from concurrent inserts assuming stable ordering," not absolute.

### When to Use Which

- **Offset:** Admin pages, dashboards — when exact page numbers matter and data changes infrequently.
- **Cursor:** Feeds, timelines, real-time lists — when data changes frequently and consistency matters.

---

## Filtering and Sorting

Use consistent query parameter patterns:

```
GET /api/users?status=active&role=admin           # filtering by field values
GET /api/users?sort=createdAt&order=desc           # sorting
GET /api/users?search=kasey                        # full-text search
GET /api/users?createdAfter=2026-01-01             # date range filtering
```

Query parameters use the same casing as the JSON fields they name.

**Server-side validation:** Always validate and allowlist sort fields and filter fields. A sort field ends up as a column name in `ORDER BY`, and a column name cannot be bound as a query parameter the way a value can, so an allowlist that maps each accepted name to a known column is the injection defence. It is also the performance one: sorting by an unindexed column on a million-row table is slow.

---

## API Versioning

Your API will change. The question: how do you change it without breaking existing clients?

### Strategy 1: Additive Changes Only (recommended)

Never remove or rename fields. Only add new ones:

```json
// Original: { "name": "Kasey" }
// After:    { "name": "Kasey", "firstName": "Kasey", "lastName": "Smith" }
```

Old clients read `name` and ignore new fields. New clients read `firstName` and `lastName`. Eventually deprecate `name` after all clients migrate.

**This is the simplest approach and avoids versioning infrastructure.** Most API changes can be additive. Use it as the default strategy.

### Strategy 2: URL Versioning (when breaking changes are unavoidable)

```
/api/v1/users  → old response shape
/api/v2/users  → new response shape
```

Simple to understand. But you're maintaining two codepaths. Use sparingly — a new version should be a rare event, not a regular occurrence.

### Strategy 3: Header Versioning

```
GET /api/users
Accept: application/vnd.myapp.v2+json
```

Cleaner URLs but harder to test in a browser and less visible.

### What Constitutes a Breaking Change?

| Change                             | Breaking? | How to handle                               |
| ---------------------------------- | --------- | ------------------------------------------- |
| Add a new field to a response      | No        | Clients should ignore unknown fields        |
| Add a new optional query parameter | No        | Existing requests still work                |
| Add a new endpoint                 | No        | Existing endpoints unchanged                |
| Add a value to a response enum or union | **Yes** | A client that switches exhaustively or parses a closed enum rejects it. Document that enums may grow, or ship the value in a later release than the clients that understand it |
| Remove a field from a response     | **Yes**   | Deprecate first, remove in next version     |
| Rename a field                     | **Yes**   | Add new name, keep old name, deprecate old  |
| Change a field's type              | **Yes**   | Add new field with new type, deprecate old  |
| Make an optional field required    | **Yes**   | This rejects previously valid requests      |
| Tighten validation on a request field | **Yes** | Requests that passed before now fail; loosen freely, tighten only with a new version |
| Change a status code or error `code` | **Yes** | Clients branch on them; add a new code for a new case instead |
| Change the default sort or page size | **Yes** | Clients that never set them silently get different pages; keep the default and let clients ask for the new one |
| Change the URL structure           | **Yes**   | Keep old URLs working, redirect if possible |

The "No" rows assume clients ignore unknown fields. A client that parses responses with a strict schema (Zod's `z.strictObject`, Pydantic's `extra="forbid"`) breaks on the first added field, so parse responses leniently and say so in the API's docs. For a public API, announce a removal with the `Deprecation` header (RFC 9745) on the affected responses and a `Sunset` header (RFC 8594) carrying the date it stops working. `Deprecation` takes a Structured Fields date (`Deprecation: @1798761599`), and `Sunset` an HTTP-date (`Sunset: Thu, 31 Dec 2026 23:59:59 GMT`), no earlier than the deprecation.

---

## Type-Safe API Contracts

The most powerful approach: share types between frontend and backend so they can never drift apart.

### tRPC (TypeScript full-stack)

When your frontend and backend are both TypeScript (e.g., Next.js):

```typescript
// tRPC 11, Zod 4 — Server: define the API with Zod validation
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, publicProcedure } from './trpc';

const appRouter = router({
  getUser: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      const user = await db.findUser(input.id);
      // Throw TRPCError (or map your own errors to it in middleware): anything else becomes a 500
      if (!user) throw new TRPCError({ code: 'NOT_FOUND', message: `User '${input.id}' not found` });
      return user;
    }),

  createUser: publicProcedure
    .input(z.object({
      name: z.string().min(1),
      email: z.email(),
    }))
    .mutation(async ({ input }) => {
      return db.createUser(input);
    }),
});

export type AppRouter = typeof appRouter;
```

```typescript
// Client — call with full type safety, zero code generation
import { trpc } from './trpc-client';

const user = await trpc.getUser.query({ id: '123' });
// TypeScript knows the exact return type — no manual type definitions
// If you typo a field name, the compiler catches it instantly
```

tRPC eliminates the gap between frontend and backend types. No OpenAPI spec, no code generation — types flow through the TypeScript compiler directly. The procedure names are verbs on purpose: tRPC is RPC, so the resource-and-method naming rules above deliberately don't apply. The tradeoff is reach — it serves TypeScript clients only, with no OpenAPI spec out of the box for a mobile app or third party to build against.

### OpenAPI / Swagger (language-agnostic)

A YAML/JSON spec describing your API. Can auto-generate documentation, client libraries, and server stubs.

**FastAPI generates this automatically:**

```python
# FastAPI 0.162, Pydantic 2
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

# response_model, not a return annotation: the handler returns an ORM row, which
# FastAPI validates into UserResponse (reading attributes) and serialises
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await db.find_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user

# Interactive API docs automatically available at /docs (Swagger UI)
# and /redoc (ReDoc)
```

---

## Testing the API Contract

The contract is a promise about *shape* and *status*, so the tests assert exactly those two things against the running endpoints — not the business logic behind them:

- **Consistent response shape.** Every endpoint returns the shape from **Response Shape Consistency** — a single resource directly, every collection as `{ data }`, with `pagination` (and `hasMore`) beside it when paginated — and no endpoint drifts to a bare array or an ad-hoc third shape. Pick the shape once; let a test catch the drift.
- **Status matches method.** Mutations return the status their HTTP method promises — a create returns 201, not a generic 200 — which is just the **HTTP Methods** table asserted at runtime.
- **Empty-collection edge case.** A query that legitimately matches nothing returns 200 with an empty collection (`{ "data": [] }`), not a 404: "no rows" is a successful empty collection, not a missing endpoint. The same discipline covers the other **Pagination** boundaries (last page, invalid cursor) and the additive-change rule from **API Versioning** — a response that grew a field is still backwards-compatible; one that dropped or renamed a field is not.

These are response-shape and status tests, run as integration tests that drive the real endpoint end to end — see [Testing](./testing.md) for the real-handler-against-a-real-database harness.

---

## Anti-Patterns

| Don't                                              | Do Instead                                                               | Why                                                                   |
| -------------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| Use verbs in URLs: `/api/getUsers`                 | Use nouns: `GET /api/users`                                              | The HTTP method is the verb                                           |
| Return different response shapes per endpoint      | Single resources direct, every collection as `{ data }`, everywhere      | Clients need one response-handling function, not per-endpoint parsing |
| Return a collection as a bare array                | Wrap it in `{ data }` from the first release                             | A bare array cannot gain pagination fields without breaking clients   |
| Return every column of every row in a list         | A summary shape in lists, the full shape on the detail endpoint; add `?fields=` only when a real client needs it | List payloads grow with every column added; field selection multiplies the shapes to test |
| Return an unbounded list without pagination        | Paginate every collection that can grow                                  | Unbounded lists cause memory issues and slow responses                |
| Make breaking changes without versioning           | Use additive changes; version only when breaking changes are unavoidable | Breaking changes break clients                                        |
| Let clients sort by any field                      | Allowlist sort fields, mapping each to a known column                    | A column name cannot be bound as a parameter, and unindexed sorts are slow |
| Use different date formats across endpoints        | Use RFC 3339 with an offset; date-only for calendar dates                | Inconsistent formats cause parsing bugs                               |
| Accept path IDs without validation                 | Validate ID format in your schema                                        | A malformed id becomes a clear 400, not a database error; parameter binding is what stops injection |

---

## Deciding for Your Project

When starting a new project, decide these. Each line gives the default.

1. **Who consumes the API?** If only your own frontend, change both sides in one commit and skip versioning ceremony. If anyone else does, version, deprecate with headers, and test the contract.
2. **REST, RPC or spec-first?** REST with resource URLs. tRPC when every client is your own TypeScript code. Publish an OpenAPI spec, generated from the code as FastAPI does, once anyone else builds against the API.
3. **Collection shape?** `{ data }` on every collection, with `pagination` beside it when paginated; single resources direct.
4. **Offset or cursor?** Cursor for feeds and anything large or fast-changing; offset for small admin tables where page numbers matter.
5. **Versioning?** Additive changes only; a URL version (`/v2`) for the rare break that cannot be made additive.
6. **Field casing?** The primary consumer's, applied to JSON fields and query parameters alike; camelCase for a web frontend.

---

## Related Topics

- **Request/response validation** — see [Data Integrity](./data-integrity.md) for validating API inputs with Zod/Pydantic schemas
- **Error responses** — see [Error Handling](./error-handling.md) for RFC 9457 Problem Details format and status code selection
- **API security** — see [Security](./security.md) for CORS, authentication, authorization, and rate limiting
- **Permitted actions in a response** — see [Authentication & Authorization](./authentication-authorization.md#enforcement-layers): when a response projects which actions the user may take, that set comes from the same policy source as the endpoint check, and it is a hint for rendering, never the check
- **API metrics** — see [Monitoring](./monitoring.md) for RED method (Rate, Errors, Duration) applied to API endpoints
- **Schema changes** — see [Schema Evolution](./schema-evolution.md) for how database changes affect API response shapes
- **Testing the API** — see [Testing](./testing.md) for the real-endpoint harness behind the response-shape and status tests in **Testing the API Contract** above, and for schema-conformance tests that check your schemas against the third-party responses you parse