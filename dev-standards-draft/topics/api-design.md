# API Design & Contracts

## The Problem

An API (the HTTP endpoints your backend exposes) is a **contract**. Once you ship an endpoint that returns `{ "user": { "name": "Kasey" } }`, every client that calls it depends on that exact shape — your frontend, mobile apps, third-party integrations. Changing it breaks them.

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

| Method | Purpose | Idempotent? | Request body? | Example |
|--------|---------|:-----------:|:------------:|---------|
| **GET** | Read a resource | Yes | No | `GET /api/users/123` |
| **POST** | Create a new resource | No | Yes | `POST /api/users` |
| **PUT** | Replace a resource entirely | Yes | Yes | `PUT /api/users/123` |
| **PATCH** | Partially update a resource | No* | Yes | `PATCH /api/users/123` |
| **DELETE** | Remove a resource | Yes | No | `DELETE /api/users/123` |

*PATCH can be made idempotent depending on implementation.

**Idempotent** means calling it multiple times produces the same result as calling it once. `DELETE /api/users/123` is idempotent — deleting an already-deleted user is a no-op (or a 404). `POST /api/users` is NOT idempotent — calling it twice creates two users. See [Resilience](./resilience.md) for idempotency keys on non-idempotent operations.

---

## Response Shape Consistency

Every endpoint should follow the same response pattern. Pick one and use it everywhere.

### Direct Response (recommended for most APIs)

```json
// Single resource
GET /api/users/123
{
  "id": "123",
  "name": "Kasey",
  "email": "kasey@example.com",
  "createdAt": "2026-03-15T10:30:00Z"
}

// Collection (simple)
GET /api/users
[
  { "id": "123", "name": "Kasey" },
  { "id": "456", "name": "Alex" }
]
```

Simple, direct, no wrapper. Use this when you don't need metadata alongside the data.

### Envelope Response (when you need metadata)

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

Use this when endpoints return collections with pagination, filtering metadata, or other contextual information.

### Error Response

Always use the RFC 9457 Problem Details format defined in [Error Handling](./error-handling.md):

```json
{
  "type": "NotFoundError",
  "title": "User '999' not found",
  "status": 404
}
```

### Field Naming

- **camelCase** for JSON fields in TypeScript APIs: `{ "firstName": "Kasey", "createdAt": "..." }`
- **snake_case** for JSON fields in Python APIs: `{ "first_name": "Kasey", "created_at": "..." }`

Pick based on your primary language and be consistent. If your API serves both TypeScript and Python clients, camelCase is more common in web APIs.

### Timestamps

Always use ISO 8601 format with timezone: `"2026-04-01T10:23:45.123Z"`. Never use Unix timestamps (not human-readable) or locale-specific formats ("April 1, 2026" is unparseable).

---

## Pagination

Any endpoint that returns a list needs pagination. Without it, `GET /api/users` returns all 100,000 users — slow, memory-intensive, potentially crashes the client.

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

**Problem:** If someone inserts a new user while you're paginating, you might see duplicates or miss items (the offset shifts).

### Cursor-Based (more robust)

```
GET /api/users?limit=20&cursor=eyJpZCI6MTIzfQ
```

The cursor is an opaque token (usually base64-encoded) pointing to the last item seen. The server returns "the next 20 items after this cursor."

```json
{
  "data": [...],
  "pagination": {
    "nextCursor": "eyJpZCI6MTQzfQ",
    "hasMore": true
  }
}
```

**No duplicates, no missed items**, even with concurrent inserts.

### When to Use Which

- **Offset:** Admin pages, dashboards — when exact page numbers matter and data changes infrequently.
- **Cursor:** Feeds, timelines, real-time lists — when data changes frequently and consistency matters.

---

## Filtering and Sorting

Use consistent query parameter patterns:

```
GET /api/users?status=active&role=admin           # filtering by field values
GET /api/users?sort=created_at&order=desc          # sorting
GET /api/users?fields=id,name,email                # sparse fieldsets
GET /api/users?search=kasey                        # full-text search
GET /api/users?created_after=2026-01-01            # date range filtering
```

**Server-side validation:** Always validate and whitelist sort fields and filter fields. Don't let clients sort by arbitrary columns — that's a performance risk (sorting by an unindexed column on a million-row table).

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

| Change | Breaking? | How to handle |
|--------|-----------|---------------|
| Add a new field to a response | No | Clients should ignore unknown fields |
| Add a new optional query parameter | No | Existing requests still work |
| Add a new endpoint | No | Existing endpoints unchanged |
| Remove a field from a response | **Yes** | Deprecate first, remove in next version |
| Rename a field | **Yes** | Add new name, keep old name, deprecate old |
| Change a field's type | **Yes** | Add new field with new type, deprecate old |
| Make an optional field required | **Yes** | This rejects previously valid requests |
| Change the URL structure | **Yes** | Keep old URLs working, redirect if possible |

---

## Type-Safe API Contracts

The most powerful approach: share types between frontend and backend so they can never drift apart.

### tRPC (TypeScript full-stack)

When your frontend and backend are both TypeScript (e.g., Next.js):

```typescript
// Server — define the API with Zod validation
import { z } from 'zod';
import { router, publicProcedure } from './trpc';

const appRouter = router({
  getUser: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      const user = await db.findUser(input.id);
      if (!user) throw new NotFoundError("User", input.id);
      return user;
    }),

  createUser: publicProcedure
    .input(z.object({
      name: z.string().min(1),
      email: z.string().email(),
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

tRPC eliminates the gap between frontend and backend types. No OpenAPI spec, no code generation — types flow through the TypeScript compiler directly.

### OpenAPI / Swagger (language-agnostic)

A YAML/JSON spec describing your API. Can auto-generate documentation, client libraries, and server stubs.

**FastAPI generates this automatically:**

```python
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    user = await db.find_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user

# Interactive API docs automatically available at /docs (Swagger UI)
# and /redoc (ReDoc)
```

### When to Use Which

| Situation | Recommendation |
|-----------|---------------|
| TypeScript frontend + TypeScript backend | **tRPC** — type safety with zero overhead |
| Python backend + any frontend | **OpenAPI** via FastAPI — auto-generated from type hints |
| Public API consumed by third parties | **OpenAPI** — language-agnostic, generates client libraries |
| Multi-language team | **OpenAPI** — the universal API description language |

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Use verbs in URLs: `/api/getUsers` | Use nouns: `GET /api/users` | The HTTP method is the verb |
| Return different response shapes per endpoint | Pick one pattern (direct or envelope) and use it everywhere | Clients need one response-handling function, not per-endpoint parsing |
| Return all fields always | Support sparse fieldsets or have summary vs detail endpoints | Returning 50 fields when the client needs 3 wastes bandwidth |
| Return a list without pagination | Always paginate collections | Unbounded lists cause memory issues and slow responses |
| Make breaking changes without versioning | Use additive changes; version only when breaking changes are unavoidable | Breaking changes break clients |
| Let clients sort by any field | Whitelist allowed sort fields | Sorting by unindexed columns kills database performance |
| Use different date formats across endpoints | Always use ISO 8601 with timezone | Inconsistent formats cause parsing bugs |
| Return raw database IDs in URLs without validation | Validate ID format in your schema | Prevents injection and makes errors clearer |

---

## Deciding for Your Project

1. **REST or tRPC?** If TypeScript full-stack → tRPC. If multi-language or public API → REST with OpenAPI.
2. **Response format?** Direct for simple APIs, envelope when you need pagination metadata.
3. **Pagination style?** Cursor for user-facing lists, offset for admin tools.
4. **Versioning strategy?** Additive changes by default. URL versioning when breaking changes are truly necessary.
5. **Field naming?** camelCase for TypeScript APIs, snake_case for Python APIs.

---

## Related Topics

- **Request/response validation** — see [Data Integrity](./data-integrity.md) for validating API inputs with Zod/Pydantic schemas
- **Error responses** — see [Error Handling](./error-handling.md) for RFC 9457 Problem Details format and status code selection
- **API security** — see [Security](./security.md) for CORS, authentication, authorization, and rate limiting
- **API metrics** — see [Monitoring](./monitoring.md) for RED method (Rate, Errors, Duration) applied to API endpoints
- **Schema changes** — see [Schema Evolution](./schema-evolution.md) for how database changes affect API response shapes
