# Data Integrity Standards

**Status:** Draft

## Core Principle

Data should be validated at boundaries, typed throughout, and stored correctly. Use typed schemas to define contracts between components. Every piece of data that crosses a boundary needs a formal definition of its shape — this is the authoritative definition of "correct" that code and tests validate against.

---

## The Three Layers of Data Safety

Data correctness is enforced by three layers, each catching failures the others miss. All three are needed in production systems.

### Layer 1: Type System (compile-time)

TypeScript interfaces, type annotations, strict compiler settings. Checked when you write code and when `tsc` runs in CI. Catches wrong argument types, missing fields, and type mismatches.

**What it can't catch:** Anything that arrives at runtime from outside your code. API requests, database responses, user uploads, webhook payloads — the type system is erased before the code runs, so it doesn't exist when real data flows through.

### Layer 2: Runtime Validation (schemas)

Zod schemas (TypeScript), Pydantic models (Python). Code that runs and inspects actual data at runtime. Applied at **boundaries** — the moment data enters or leaves your system.

**What a boundary is:** The line between code you control and data you don't. Concretely:
- An API request arrives from a client → validate the JSON body
- A database returns a record → validate it matches your schema
- A third-party webhook sends data → validate the payload
- A file is uploaded → validate its structure

**What it catches:** Everything Layer 1 can't. A client sends `{ courseId: 42 }` instead of `{ courseId: "abc-123" }` — TypeScript won't catch this because the request body is `unknown` at runtime. A Zod schema will.

### Layer 3: Storage Constraints (database-level)

Rules enforced by the database itself, regardless of what code sent the data. In relational databases: `NOT NULL`, `FOREIGN KEY`, `CHECK`, `UNIQUE` constraints. These catch everything that bypasses your application — migration scripts, manual console edits, bugs that somehow get past validation.

**NoSQL and constraint-limited databases (DynamoDB, MongoDB, etc.):** These databases enforce very little — typically just key schema and basic data types on keys. There are no CHECK constraints, no foreign keys, no UNIQUE constraints on non-key attributes. This means **Layers 1 and 2 carry significantly more weight** — the database won't save you from bad data. Runtime validation at boundaries becomes critical, not optional.

### Why All Three Layers

| Scenario | Layer 1 (Types) | Layer 2 (Schemas) | Layer 3 (DB Constraints) |
|----------|:---:|:---:|:---:|
| Developer writes wrong type in code | Catches | - | - |
| Client sends malformed JSON | - | Catches | - |
| Migration script writes bad data directly | - | - | Catches |
| Field renamed in code but not in DB records | - | Catches | - |
| Two services write conflicting data | - | - | Catches |
| Code deploys with a bug that skips validation | - | - | Catches |

No single layer covers all scenarios. The gaps in one are filled by the others.

See [Testing Standards — Test Types](./testing.md#test-types) for how to verify each layer works correctly.

---

## Related Topics

- **Testing against schemas**: See [Testing Standards](./testing.md) — "Testing Against Specifications" section for using schemas as test input constructors and output validators
- **Boundary/contract tests**: See [Testing Standards](./testing.md) — "Test Types" section for how boundary tests differ from unit tests
- **Idempotency**: See [Reliability Standards](./reliability.md) — idempotency patterns for safe retries
- **Config validation**: See [Configuration Standards](./configuration.md) — environment variable validation is a data integrity concern
- **Trust boundaries**: See [Security Standards](./security.md) — input validation at trust boundaries overlaps with validation at data boundaries

---

## Tier Requirements

### Exploratory

- Basic type hints / type annotations
- Validation where convenient
- No formal model structure required

### Internal

- Typed schemas for external data (Pydantic for Python, Zod for TypeScript, equivalent for other languages)
- Type hints / annotations throughout
- Validation at entry points
- Database constraints on key columns (primary keys, unique constraints on natural keys)

### Production

- **Formal data models** for every business entity — typed schemas organized by concern in a `models/` directory
- **Boundary contracts** for every system interface — API request/response, database queries, RPC calls, service layer outputs
- **Runtime validation at boundaries** — `Schema.parse(data)` (Zod) / model instantiation (Pydantic) at every point data enters or leaves a component
- **Strict type checking** — TypeScript `strict: true` (especially `strictNullChecks`) / Python mypy with strict settings
- **Schema verification against real data** — prove that schemas match what the database/API actually returns, not just what documentation says
- All database entities have corresponding typed schemas
- Literal/enum types for constrained values (no loose strings)

---

## Data Specification as a Production Requirement

Production code requires formal data models and contracts. Without them, there is no authoritative definition of "correct" and no way to verify that code changes are safe.

**What this means concretely:**

1. **Entity models** — A typed schema for every business entity the application works with (customer, order, activity, etc.). Not a raw database row type — a schema describing what the application actually uses.
2. **Boundary contracts** — A typed schema for every point where data crosses a system boundary: API request/response, database query results, RPC calls, hook/service outputs.
3. **Runtime validation** — Schema parsing at boundaries, not just compile-time types. `Schema.parse(data)` (Zod) or model instantiation (Pydantic) catches mismatches that type annotations alone miss.
4. **Strict type checking** — The strictest compiler settings the language supports. TypeScript `strict: true` (especially `strictNullChecks`), Python mypy strict mode. This is free safety that catches bugs the compiler can handle.
5. **Schema verification against real data** — Run schemas against actual production data (via a database clone or API snapshot) to prove they match reality. Documentation and code can disagree; real data is the arbiter.

The key distinction: a `CustomerRow` type describes what the database gives you. A `CustomerSummary` schema describes what the application actually uses. The gap between them is where bugs live.

---

## Models Folder Structure

For Production tier, organize models by concern:

**Python:**
```
src/
└── models/
    ├── __init__.py       # Re-exports
    ├── common.py         # Shared infrastructure
    ├── <domain1>.py      # Domain-specific models
    └── <domain2>.py      # Domain-specific models
```

**TypeScript:**
```
src/
├── models/
│   ├── index.ts          # Re-exports
│   ├── common.ts         # Shared infrastructure
│   ├── <domain1>.ts      # Domain-specific schemas
│   └── <domain2>.ts      # Domain-specific schemas
└── contracts/
    ├── rpc/              # RPC/API response contracts
    ├── views/            # Database view contracts
    └── hooks/            # Data layer output contracts
```

---

## Established Patterns

### Nested Composition

Build complex structures from simple building blocks:

**Python (Pydantic):**
```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class User(BaseModel):
    name: str
    address: Address  # Nested model
```

**TypeScript (Zod):**
```typescript
const AddressSchema = z.object({
  street: z.string(),
  city: z.string(),
  country: z.string(),
});

const UserSchema = z.object({
  name: z.string(),
  address: AddressSchema,  // Nested schema
});
type User = z.infer<typeof UserSchema>;
```

### Literal Types for Enums

Use constrained types for strict valid values:

**Python:**
```python
from typing import Literal

class Rule(BaseModel):
    modality: Literal["must", "must_not", "may", "shall"]
    status: Literal["active", "draft", "archived"]
```

**TypeScript:**
```typescript
const RuleSchema = z.object({
  modality: z.enum(["must", "must_not", "may", "shall"]),
  status: z.enum(["active", "draft", "archived"]),
});
```

### Optional Fields for Flexibility

Allow graceful degradation and extensibility:

**Python:**
```python
class Result(BaseModel):
    value: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
```

**TypeScript:**
```typescript
const ResultSchema = z.object({
  value: z.string(),
  confidence: z.number().nullable(),
  reasoning: z.string().nullable(),
});
```

### Factory Methods and Defaults

Generate IDs and timestamps automatically:

**Python:**
```python
from datetime import datetime, timezone
from secrets import token_hex

class Run(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{token_hex(4)}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**TypeScript:**
```typescript
const RunSchema = z.object({
  runId: z.string().default(() => `run_${crypto.randomUUID().slice(0, 8)}`),
  timestamp: z.string().datetime().default(() => new Date().toISOString()),
});
```

### Discriminated Unions

Handle polymorphic data with type discriminators:

**Python:**
```python
class ExtractedItem(BaseModel):
    item_type: Literal["rule", "definition", "other"]
    rule_content: Optional[RuleContent] = None
    definition_content: Optional[DefinitionContent] = None
    other_content: Optional[OtherContent] = None
```

**TypeScript:**
```typescript
const ExtractedItemSchema = z.discriminatedUnion("itemType", [
  z.object({ itemType: z.literal("rule"), content: RuleContentSchema }),
  z.object({ itemType: z.literal("definition"), content: DefinitionContentSchema }),
  z.object({ itemType: z.literal("other"), content: OtherContentSchema }),
]);
```

---

## Database-Level Integrity

Application-layer validation (Pydantic, Zod, typed schemas) protects the happy path. Database constraints protect everything else — direct queries, ETL pipelines, migration scripts, and bugs in application code all bypass your application models.

### Enforce at Both Layers

| Constraint | Application Layer | Database Layer |
|------------|------------------|----------------|
| **Required fields** | Schema validation, form validation | `NOT NULL` |
| **Valid values** | Enum types, literal types | `CHECK` constraints |
| **Relationships** | Type references, FK types | `FOREIGN KEY` constraints |
| **Uniqueness** | Pre-check before insert | `UNIQUE` constraints |
| **Data format** | String parsing, regex | `CHECK` with regex or domain types |

Application validation gives good error messages. Database constraints prevent bad data. Both are needed.

### Adding Constraints to Existing Tables

When adding FK or CHECK constraints to tables that may already contain dirty data, use `NOT VALID` to avoid scanning all existing rows:

```sql
ALTER TABLE orders ADD CONSTRAINT fk_customer
  FOREIGN KEY (customer_code) REFERENCES customers(customer_code)
  NOT VALID;
```

Then validate after confirming data quality: `ALTER TABLE orders VALIDATE CONSTRAINT fk_customer;`

### Normalise at Ingest

String values that serve as categories or statuses (e.g., account status, order type) must be normalised on entry — not left to queries to handle mixed casing. Lowercase at the point of insert, then add a CHECK constraint to enforce it.

### Strict Type Checking as Data Integrity

Strict compiler settings are a data integrity tool, not just a code quality preference. They catch an entire category of bugs that runtime validation cannot.

- **TypeScript:** `strict: true` in tsconfig (especially `strictNullChecks`). Without it, the type system silently allows `null` and `undefined` to flow through the entire codebase — the single biggest category of runtime crashes. Enable strict mode from day one; retrofitting it is extremely expensive.
- **Python:** mypy with strict settings + type annotations on all function signatures. Without it, type mismatches are invisible until they crash at runtime.

---

## Reverse-Engineering Data Specifications

When productionising a codebase that was built without formal data models (common with AI-generated code, prototypes, MVPs, and vibe-coded applications), the specification must be reverse-engineered from the working implementation before any code changes are made. The working behaviour is treated as the de facto specification.

This is a pattern, not a prescriptive workflow. The detailed steps belong in project-level conventions (e.g., `.context/project/implementation/conventions.md`). The principle is:

1. **Tighten type checking first** — enable the strictest compiler settings. Fix what surfaces. This is free safety.
2. **Define entity models bottom-up** — start at the database layer and work up. Each layer's contract is grounded in the layer below, not guessed.
3. **Define boundary contracts** — typed schemas for every RPC, API endpoint, view, hook, or service function.
4. **Verify schemas against real data** — run schemas against actual production data (database clone or API snapshots) to prove they match reality. This step catches mismatches that code review alone misses.
5. **Only then write tests** — tests use the schemas as both input constructors and output validators. They validate code against a formal specification, not assumptions.

**Why this order matters:** Strict types catch bugs the compiler can handle, reducing test scope. Models define what "correct" means, so tests validate against a spec rather than guesswork. Bottom-up (database to RPC to hooks to components) means each layer's contract is grounded in the layer below.

---

## Validation Boundaries

Validate data when it crosses trust boundaries:

| Boundary | Example | Validation |
|----------|---------|------------|
| **External API → App** | Third-party response | Parse through typed schema |
| **User input → App** | Form submission | Validate with schema |
| **File → App** | CSV/JSON import | Validate each record |
| **App → Database** | Insert/update | Schema ensures correct shape |
| **Database → App** | Query result | Parse through schema (recommended — proves the DB returns what you expect) |
| **Service → Service** | RPC response, hook output | Parse through boundary contract |

---

## Tooling

| Language | Model Library | Validation |
|----------|---------------|------------|
| Python | `pydantic` | Built-in |
| TypeScript | `zod`, interfaces | Zod for runtime |
| JavaScript | `joi`, `yup` | Runtime validation |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Pass raw dicts between functions | Define models for data structures |
| Use loose strings for enums | Use `Literal` types |
| Scatter validation throughout code | Validate at boundaries via models |
| Skip validation for "trusted" internal data | Trust the model, validate at entry |
| Store unvalidated external data | Always parse through model first |

---

## Expand During Brainstorming

For each project, determine:

1. What external data sources exist? (APIs, files, user input)
2. What database collections/tables are needed?
3. What models should be shared vs domain-specific?
4. Are there polymorphic data types requiring discriminators?
5. What metadata (confidence, timestamps, provenance) should be tracked?
