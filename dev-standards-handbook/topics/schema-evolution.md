# Schema Evolution and Migrations

> **Calibrate to the context.** Versioned migrations are cheap and worth adopting for
> nearly any database that outlives a prototype — they're just change-scripts in git.
> What scales with the stakes is the multi-deploy choreography for renames and type
> changes, and batched backfills: they earn their keep when users would notice downtime
> or tables are big, and a small app that can tolerate 30 seconds of downtime on deploy
> can collapse them into fewer deploys. Two things hold at any size: a column is dropped
> one deploy after the code stops using it, because that is what keeps a code rollback
> possible, and the safety rules below, which prevent data loss and cost nothing.
> Reference material, not a checklist.

## The Problem Nobody Thinks About on Day One

You design your database schema. Users have a `name` and `email`. You build the app, deploy it, real users sign up. Life is good.

Then the requirements change. You need to split `name` into `first_name` and `last_name`. Or add a `role` column. Or rename `email` to `primary_email` because now users can have multiple emails.

Your schema needs to change. But unlike application code, where you edit the file and redeploy, **your database has data in it.** Real user data. You can't drop the table and recreate it. You need to change the structure while preserving every row.

This is **schema evolution** — the discipline of changing your data model over time without losing data or breaking running code.

---

## What Is a Migration?

A migration is a versioned script that changes your database schema. Think of it like a git commit, but for your database structure:

```sql
-- PostgreSQL 10+ (identity columns)
-- Migration 001: Create users table
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Migration 002: Add role column
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member';

-- Migration 003: Split name into first_name and last_name
-- UNSAFE on a live system: it drops `name` while the running code still reads it.
-- Zero-Downtime Migrations below shows the failure and the phased version.
ALTER TABLE users ADD COLUMN first_name TEXT;
ALTER TABLE users ADD COLUMN last_name TEXT;
UPDATE users SET
    first_name = SPLIT_PART(name, ' ', 1),
    last_name = SPLIT_PART(name, ' ', 2);
ALTER TABLE users DROP COLUMN name;
```

Each migration has a number (or timestamp) and runs in order. The migration tool tracks which migrations have been applied. When you deploy, it runs only the new ones.

---

## Why Not Just Edit the Schema Directly?

Imagine three developers on a team. Each makes schema changes on their laptop. They deploy. Whose changes win? What order do they run in? What if developer A's change depends on developer B's change?

Migrations solve this by making schema changes:

- **Ordered** — migration 003 always runs after 002
- **Tracked** — the tool knows "this database has applied migrations 001 through 005"
- **Repeatable** — run the same migrations on any database (dev, staging, production) and get the same schema
- **Reviewable** — migrations are code, committed to git, reviewed in pull requests

---

## Migration Tools

**Default stack: TypeScript + Drizzle, with `drizzle-kit` for migrations.** Drizzle defines your schema in TypeScript, generates SQL migrations from it, gives you compile-time-typed queries, and — unlike most ORMs — declares Postgres Row-Level Security policies and roles in the *same* schema file (see [Multi-Tenant Isolation](./multi-tenant-isolation.md) → The Database Backstop). Reach for **Alembic** only when you're in a Python/SQLAlchemy codebase. The other tools below are documented for context and for working in existing projects that already use them.

The concepts (versioned, ordered, tracked, reviewable migrations) are identical across all of them — only the authoring surface differs.

### Alembic (Python / SQLAlchemy)

Alembic is the standard migration tool for Python projects using SQLAlchemy. SQLAlchemy is the most popular Python ORM — a library that lets you interact with your database using Python objects instead of raw SQL.

Alembic auto-generates migrations by comparing your Python models to the current database:

```python
# Your SQLAlchemy model (legacy declarative `Column()` style) — `name` removed, two columns added
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=True)    # you added this; nullable until backfilled
    last_name = Column(String, nullable=True)     # you added this; nullable until backfilled
    email = Column(String, unique=True, nullable=False)
```

```bash
# Alembic detects the difference and generates a migration
alembic revision --autogenerate -m "split name into first and last"
```

This creates a Python file with `upgrade()` and `downgrade()` functions:

```python
# Alembic 1.x — as generated, before review
def upgrade():
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
    op.drop_column('users', 'name')   # autogenerate read the split as a delete: every name is lost

def downgrade():
    op.add_column('users', sa.Column('name', sa.TEXT(), nullable=False))  # fails once rows exist
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
```

**Review every autogenerated migration before you commit it.** Autogenerate diffs the models against the database, so it can't tell a rename or a split from a delete: it reads them as a drop plus an add, and the `drop_column` above would destroy every user's name. It also misses some changes outright, such as anonymously named constraints. Keep new columns nullable (or give them a `server_default`) so they can be added to a populated table, delete the `drop_column`, and follow the expand-and-contract pattern below.

The `downgrade()` function is the reverse — it lets you undo the migration if something goes wrong. Not every migration can be cleanly reversed (if you dropped a column, the data is gone), but having the option is valuable.

**Key commands:**
```bash
alembic upgrade head      # apply all pending migrations
alembic downgrade -1      # undo the last migration
alembic history           # show migration history
alembic current           # show which migration the database is at
```

### Prisma Migrate (TypeScript / Prisma)

Prisma is a popular TypeScript ORM. You define your schema in a `.prisma` file, and Prisma generates SQL migrations:

```prisma
// schema.prisma
model User {
  id        Int      @id @default(autoincrement())
  firstName String   @map("first_name")
  lastName  String   @map("last_name")
  email     String   @unique
}
```

```bash
npx prisma migrate dev --name split-name
# Generates a SQL migration file and applies it to your dev database
```

Prisma also generates a TypeScript client from the schema (`prisma generate`), which keeps your application code in sync with the database structure. Since Prisma 7, `migrate dev` no longer runs `generate` for you, so run it after each schema change.

**No native RLS:** Prisma can't express Postgres Row-Level Security policies in its schema — you bolt RLS on with client extensions or community libraries (`prisma-rls`, Yates). On Postgres multi-tenant systems that want database-enforced isolation, that's a point in Drizzle's favour and the main reason this handbook defaults to Drizzle on TypeScript.

### Drizzle (TypeScript)

You define schemas directly in TypeScript — no separate schema file, no code-generation step:

```typescript
// drizzle-orm 0.45
import { bigint, pgTable, text, timestamp } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: bigint('id', { mode: 'number' }).primaryKey().generatedAlwaysAsIdentity(),
  firstName: text('first_name').notNull(),
  lastName: text('last_name').notNull(),
  email: text('email').unique().notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
});
```

```bash
npx drizzle-kit generate  # generates SQL migration from schema changes
npx drizzle-kit migrate   # applies pending migrations
```

The key difference from Prisma: your schema IS your TypeScript types. No separate `.prisma` file, no generated client — you import the schema directly.

**Five drizzle-kit behaviours shape the rules below** (read from drizzle-orm 0.45 and drizzle-kit 0.31 source; check the installed version):

- `migrate` applies **every pending migration inside one transaction**. Separate files are therefore not separate transactions, `CREATE INDEX CONCURRENTLY` cannot go through it at all, and a lock the first migration takes is held until the last one commits.
- `migrate` applies by timestamp, not by name (drizzle-orm 0.x; v1 selects by name), so a branch's migration can be skipped silently. [The Migration Skipped by Its Timestamp](./pitfalls.md#the-migration-skipped-by-its-timestamp) has the mechanism and the guard.
- It takes no lock against a second runner, so two processes migrating at once race each other (see [Deployment](./deployment.md#migrations-in-the-pipeline)).
- `push` applies the schema diff straight to a database with no migration file, so keep it to throwaway prototype databases.
- `generate` stops to ask whether a changed column is a rename or a drop plus an add, so run it where someone can answer.

**Drizzle handles Postgres RLS natively.** Since `drizzle-orm` 0.36 (Oct 2024), you declare policies and roles in the schema next to the table with `pgPolicy` / `pgRole` (and `crudPolicy` from `drizzle-orm/neon`), and `drizzle-kit` emits the `CREATE POLICY` / `ENABLE ROW LEVEL SECURITY` DDL. This works on **any** Postgres — not just Neon/Supabase. See [Multi-Tenant Isolation](./multi-tenant-isolation.md) → The Database Backstop for how the policy is used.

**What `drizzle-kit` does *not* generate** (keep these as hand-written SQL companion migrations): table-level `GRANT`/`REVOKE`, role attributes (`BYPASSRLS`, `NOLOGIN`, `LOGIN`), and data backfills. `CHECK` constraints *are* generated — declare them with `check()` from `drizzle-orm/pg-core` rather than in raw SQL, so the schema file keeps describing the database. A real RLS setup is therefore a hybrid — policies in the schema, grants/roles/backfills in raw SQL — and that's expected, not a workaround.

### Choosing Between Them

| Tool | Language | Approach | Notes |
|------|----------|----------|-------|
| **Drizzle Kit** | TypeScript | Generate from TypeScript schema definitions | **The default.** Schema *is* your types, close to raw SQL, native in-schema RLS |
| **Prisma Migrate** | TypeScript | Generate from `.prisma` schema file | Polished DX, but a separate schema language and no native RLS |
| **Alembic** | Python | Auto-generate from SQLAlchemy models, manual editing | The standard for Python/SQLAlchemy codebases |

---

## Zero-Downtime Migrations

Everything above works fine when you can take your app offline, run the migration, and bring it back up. But in production, users are actively using the system.

Here's why a simple schema change can break a running app:

```
Timeline:
1. Old code is running, reads "name" column
2. You run migration: DROP COLUMN name, ADD COLUMN first_name, last_name
3. Old code tries to read "name" — CRASH, column doesn't exist
4. New code deploys, reads "first_name" — works
```

There's a window between steps 2 and 4 where old code runs against the new schema. Every request in that window fails.

### The Expand-and-Contract Pattern

This solves the problem by splitting the change into phases, each of which leaves the
database usable by both the code version that is running and the one about to deploy.
**The order matters:** code that writes the new columns must be live *before* the
backfill runs, and nothing may still read or write the old column when it is dropped.
"Live" means every writer has drained the old version: all instances, background
workers and cron jobs, not just the web tier.

With the migration step as a pre-deploy job
([Deployment](./deployment.md#migrations-in-the-pipeline)), each migration ships with the
*next* phase's code: the expand with the dual-write code, the backfill with the read
switch, the drop in the release after the one that stops touching `name`. The backfill
never ships alongside the dual-write code, because the pre-deploy step would run it
before that code is live.

**Phase 1: Expand** (add new things, don't remove old things)

```sql
-- PostgreSQL — Migration A: add new columns, nullable (old code ignores them — safe)
ALTER TABLE users ADD COLUMN first_name TEXT;
ALTER TABLE users ADD COLUMN last_name TEXT;
-- The old column was NOT NULL; relax it now, or Phase 5 code that stops
-- writing `name` cannot insert
ALTER TABLE users ALTER COLUMN name DROP NOT NULL;
```

Old code keeps working — it reads and writes `name` and never sees the new columns.

**Phase 2: Deploy code that writes BOTH columns and still reads the old one**

```python
# Every write populates both; reads still come from `name`
user.name = "Kasey Smith"
user.first_name = "Kasey"
user.last_name = "Smith"
```

From this deploy on, every row the new code writes has the new columns filled. Two kinds
of row still need the backfill: rows untouched since before this deploy, and rows old
code changed during the rollout overlap, when it updated `name` and left the new columns
stale.

**Phase 3: Backfill** (copy old data into the new columns wherever they are missing or stale)

```sql
-- PostgreSQL — idempotent: re-run freely until Phase 5 ships, never after.
-- A small table takes it as one migration; a big one runs it batched as a
-- pipeline job (see Batched Backfills below)
UPDATE users SET
    first_name = SPLIT_PART(name, ' ', 1),
    last_name  = SPLIT_PART(name, ' ', 2)
WHERE first_name IS NULL                                          -- never filled
   OR concat_ws(' ', first_name, last_name) IS DISTINCT FROM name;  -- `name` changed since
```

Running the backfill *before* Phase 2 is the classic mistake: old code keeps writing rows
with only `name` after the backfill has finished, and nothing ever fills them. Guarding on
`first_name IS NULL` alone is the subtler one: it misses rows old code *updated*. A
trigger that keeps the columns in sync during the overlap is the alternative to the
disagreement guard. (The `SPLIT_PART` is illustrative — it loses middle names; derive
real data carefully.)

Retire the backfill, and any sync trigger, before Phase 5 deploys. From then on `name`
goes stale by design, so the guard matches every row the new code changes: a re-run
restores the old value, and wipes the new columns of rows inserted without `name`. Build
the guard from the exact expression the dual-write code uses for `name`, and expect rows
the split cannot reproduce to match on every run, so a count of rows left never reaches
zero.

**Phase 4: Deploy code that reads the new columns and still writes `name`**

This is the risky switch, and it rolls back cleanly: the previous code reads `name`,
which every write still keeps current.

**Phase 5: Deploy code that stops touching `name`**

Remove `name` from the model/ORM mapping entirely, not just from the writes. ORMs select
every mapped column, so a column that is still mapped breaks the moment it is dropped.
Rolling this phase back to Phase 4's code is still safe, because that code reads only
the new columns. The backfill stays retired even then: `name` is already stale on every
row Phase 5 changed.

**Phase 6: Contract** (remove old things, at least one deploy after Phase 5)

```sql
-- PostgreSQL — Migration C: drop the old column (nothing reads or writes it any more)
ALTER TABLE users DROP COLUMN name;
```

At every step the schema serves both the code that is running and the code about to
deploy, so rolling back a phase's code never hits a missing column. It can reopen a data
gap, though: rolling Phase 2's code back after the backfill brings back code that writes
only `name`, so re-run the idempotent backfill once the dual-write code is live again.
The drop is the one step with no way back but a restore.

### When Do You Need Expand-and-Contract?

| Change | Needs expand-and-contract? | Why |
|--------|---------------------------|-----|
| **Renaming a column** | Yes | Old code reads old name; new code reads new name |
| **Changing a column's type** | Yes | Old code expects old type |
| **Removing a column** | Yes | Old code reads the column |
| **Adding a new column with a default** | No | Old code ignores it |
| **Adding a new table** | No | Old code doesn't query it |
| **Adding an index** | Usually no | But on large tables, use `CREATE INDEX CONCURRENTLY` in Postgres to avoid locking |
| **Adding NOT NULL, a foreign key, CHECK or UNIQUE to a big existing table** | No, but not in one statement | A plain add validates every row while blocking writes; split it as in Adding Constraints to Existing Tables below |

**For small projects and solo developers:** if you can tolerate 30 seconds of downtime during deploy, you can collapse the add, dual-write and backfill phases into fewer deploys. The drop still waits one deploy after the code stops using the column, at any size, because that is what keeps a code rollback possible.

### Lock Queueing — the Outage Expand-and-Contract Does Not Prevent

Even a "safe" expand step can take the site down, and table size does not protect you.
Most `ALTER TABLE` forms take an ACCESS EXCLUSIVE lock, which conflicts even with plain
reads, and the weaker locks of `ADD FOREIGN KEY` (on the referenced table too) and a plain
`CREATE INDEX` still block writes. If one slow query (a report, a long transaction) is
holding the table when the DDL arrives, the DDL waits behind it — and every *new* query
that conflicts with the DDL's lock then queues behind the DDL. Nothing is wrong with the
migration; the app is simply frozen until the slow query finishes. This is the most common
way a one-line migration becomes an incident on Postgres.

The guard is a short lock timeout before any DDL, set to the stall the app can absorb,
often 1–2s (`SET lock_timeout = '2s';`). The DDL then gives up instead of blocking
everyone. Neither drizzle-kit nor Alembic retries, so the deploy fails; rerun it, or wrap
the migrate step in a retry loop with backoff. A rerun is safe because a single-transaction
runner rolls back the whole pending batch.

Two related rules. `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block:
Alembic needs `with op.get_context().autocommit_block():`, and Drizzle's migrator wraps
every pending migration in one transaction, so under Drizzle it runs as a separate
pipeline step outside the migrator. A failed `CONCURRENTLY` build is the exception to the
safe rerun: it leaves an INVALID index behind
([The Invalid Index Left Behind](./pitfalls.md#the-invalid-index-left-behind)). And a
backfill never shares a transaction with the DDL that precedes it (see safety rule 5
below).

### Adding Constraints to Existing Tables

Adding a constraint the plain way scans every existing row while holding a lock that
blocks writes. Split it so the scan runs under a lock that does not:

- **Foreign key or CHECK:** add it `NOT VALID`, which skips the scan but checks every new
  and updated row from that moment. Then `VALIDATE CONSTRAINT` scans the old rows under
  SHARE UPDATE EXCLUSIVE, which blocks neither reads nor writes. Validation fails until
  existing bad rows are fixed, so the split also suits cleaning up dirty data.
- **NOT NULL:** PostgreSQL 18 accepts `NOT NULL … NOT VALID` directly. On 12–17, add
  `CHECK (col IS NOT NULL) NOT VALID`, validate it, then `SET NOT NULL`, which uses the
  validated check to skip its own scan, and drop the check.
- **UNIQUE** cannot be `NOT VALID`. Build a unique index `CONCURRENTLY`, then promote it.

```sql
-- PostgreSQL 12+ (verified on 17 and 18). Set lock_timeout first; the adds still lock briefly.
-- Each VALIDATE ships in a later deploy than its ADD (see below).
ALTER TABLE orders ADD CONSTRAINT fk_customer
  FOREIGN KEY (customer_code) REFERENCES customers (customer_code) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT fk_customer;

-- NOT NULL on PostgreSQL 12–17
ALTER TABLE orders ADD CONSTRAINT orders_region_nn CHECK (region IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_region_nn;
ALTER TABLE orders ALTER COLUMN region SET NOT NULL;     -- no scan: the check proves it
ALTER TABLE orders DROP CONSTRAINT orders_region_nn;
-- PostgreSQL 18+: ADD CONSTRAINT orders_region_nn NOT NULL region NOT VALID, then VALIDATE

-- UNIQUE: build without blocking writes (outside any transaction), then promote
CREATE UNIQUE INDEX CONCURRENTLY orders_ref_key ON orders (ref);
ALTER TABLE orders ADD CONSTRAINT orders_ref_key UNIQUE USING INDEX orders_ref_key;
```

Under a single-transaction runner the split only works across deploys. If the add and the
`VALIDATE` are pending together, they run in one transaction, and the validation scan runs
while the add's write-blocking lock is still held. drizzle-kit does not emit `NOT VALID`,
so write these steps as hand-written SQL migrations, and run the `CONCURRENTLY` step outside
the migrator as above.

---

## Data Backfills

Adding a column is easy. Populating it for existing rows is the part people forget.

```sql
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member';
```

New rows get `role = 'member'` automatically. But what about existing rows? It depends on where the default lives:

- **PostgreSQL:** a constant `DEFAULT` fills existing rows at `ADD COLUMN` time — and since PG 11 it does so without rewriting the table (a volatile default such as `gen_random_uuid()` still rewrites it). No backfill needed.
- **MySQL:** behaviour varies by version
- **ORM defaults:** many live in application code only and never reach the database, so existing rows get `NULL`. SQLAlchemy `default=` is Python-side (`server_default=` is the database one); Drizzle `$defaultFn()` is app-side (`.default()` is the database one); Prisma's `@default(uuid())` and `@default(cuid())` are generated by the client.

**The check that matters:** confirm the default is database-side — it appears as `DEFAULT ...` in the migration's SQL. A constant database default needs no backfill; write an explicit backfill only for values derived from other data.

### Batched Backfills for Large Tables

Batch when the new value is derived from other columns — say `role` computed from an old `is_admin` flag, on a column added without a default. For tables with millions of rows, a single `UPDATE` holds a lock on every row it touches until it commits, writes a burst of WAL that replicas lag behind, and leaves the table bloated with dead rows. Walk the primary key as a keyset instead — take the next batch of ids after the last one seen (`WHERE id > $last ORDER BY id LIMIT n`), update just those, and commit — so each batch is an index range scan whatever the key type. Because it commits per batch, it cannot live in a migration file, which the runner wraps in a transaction: run it as a tracked pipeline job (safety rule 5).

```python
# SQLAlchemy 2.0, PostgreSQL — derived value, batched by keyset on the primary key
import time
from sqlalchemy import select, text

BATCH = 1000
last = None
while True:
    q = select(User.id).order_by(User.id).limit(BATCH)
    if last is not None:
        q = q.where(User.id > last)       # keyset: works for integer and uuid keys
    ids = db.execute(q).scalars().all()
    if not ids:
        break
    db.execute(text("""
        UPDATE users SET role = CASE WHEN is_admin THEN 'admin' ELSE 'member' END
        WHERE id = ANY(:ids) AND role IS NULL
    """), {"ids": list(ids)})
    db.commit()
    last = ids[-1]
    time.sleep(0.1)  # small pause to avoid overwhelming the DB
```

```typescript
// drizzle-orm 0.36+, PostgreSQL — derived value, batched by keyset on the primary key
import { and, asc, gt, inArray, isNull, sql } from 'drizzle-orm';

const BATCH = 1000;
let last: (typeof users.$inferSelect)['id'] | undefined;
while (true) {
  const batch = await db.select({ id: users.id }).from(users)
    .where(last === undefined ? undefined : gt(users.id, last))   // keyset: any key type
    .orderBy(asc(users.id)).limit(BATCH);
  if (batch.length === 0) break;
  const ids = batch.map((r) => r.id);
  await db.update(users)
    .set({ role: sql`CASE WHEN ${users.isAdmin} THEN 'admin' ELSE 'member' END` })
    .where(and(inArray(users.id, ids), isNull(users.role)));
  last = ids[ids.length - 1];
  await new Promise((r) => setTimeout(r, 100));
}
```

**Why a keyset, not `WHERE role IS NULL LIMIT 1000`:** with no index on `role`, every iteration of that loop re-scans the table to find the next nulls, so the job slows as it goes. A keyset on the primary key is an index lookup each time, for integer and uuid keys alike, and the `role IS NULL` guard keeps the backfill safe to re-run. (`UPDATE ... LIMIT` isn't valid in Postgres anyway.)

---

## Migration Safety Rules

These come from painful production experience:

### 1. Never edit a migration that's already been applied

If migration 003 has run on staging and you edit the file, your local database and staging now have different schemas with the same migration number. The tool thinks they're in sync. They're not. **Always create a new migration instead.**

### 2. Test migrations against production-like data

A migration that works on your empty dev database might fail on production because of data that violates a new constraint. "Add NOT NULL column" fails if existing rows have NULL values. Test against a masked or anonymised copy of production data, never a raw copy on a laptop or in CI.

### 3. Every deploy leaves the previous code working against the new schema

Rolling back means redeploying the previous code, and that only works if the schema still serves it. drizzle-kit and Prisma Migrate have no down migrations, and Alembic's `downgrade()` cannot bring back dropped data, so expand-and-contract is the rollback plan, not a reverse script. The contract step is one-way: once a column is dropped, only a restore brings it back.

### 4. Never run migrations manually in production

Migrations should run as part of your deployment pipeline, automatically. Manual SQL in a production terminal is how data loss happens. If you need to run a one-off fix, make it a migration (or, for a batched backfill, a tracked pipeline job — rule 5) so it's tracked and reviewable.

### 5. Separate schema migrations from data migrations

- **Schema migrations** (add column, create table) are fast and structural
- **Data migrations** (backfill values, transform data) can be slow and are about content

Postgres DDL is transactional, so a failed mix rolls back cleanly; the hazard is the lock. The DDL's ACCESS EXCLUSIVE lock is held until the transaction commits, so a slow backfill in the same transaction blocks every query on the table for its whole run. Separate files are not enough: Drizzle's migrator runs every pending migration in one transaction, and Alembic does the same by default (`transaction_per_migration` is False). Keep a small backfill in a later deploy's migration, and run a batched one as a tracked pipeline job — versioned in git, idempotent, started by the deploy pipeline — not as a migration file.

---

## Testing Migrations

Safety rule #2 — *test against production-like data* — is the floor. Two kinds of migration test catch the failures that slip through review:

- **Behavioural tests — does the migration actually do what it claims?** Assert the *effect*, red-before/green-after: a new `CHECK` or `NOT NULL` constraint must reject the rows it's meant to (on both `INSERT` *and* `UPDATE` — it's easy to guard one and forget the other); a backfill must leave no nulls behind; a dropped column must actually be gone. A migration that runs without error isn't the same as one that did the right thing.
- **Replay-parity tests — does a clean build reproduce production's shape?** Drop the schema and replay every migration from empty, then assert the seeded reference data matches the same source-of-truth constant the application reads. This catches the slow drift where a hand-applied production fix was never captured as a migration, so a fresh environment comes up subtly different.

Both run against a real database engine — see [Testing](./testing.md) for the real-database test setup (containers, truncate-and-reseed, running these in CI).

---

## Keeping Application Schemas in Sync

When your database schema changes, your application schemas (Zod, Pydantic) need to change too. This is a coordination problem:

```
Database: users table now has first_name, last_name (no name column)
Zod schema: still expects { name: string }  ← BUG
```

**The rule:** Every migration ships with code that works against the schema both before and after it. The reviewer checks the migration and the application schemas together — though under expand-and-contract the code that *uses* a change may land a deploy later, not in the same pull request.

With **Drizzle**, the TypeScript schema generates the migrations, so your query types match the schema you *declared*. The database itself can still drift — a migration not yet applied, a fix hand-applied in production (what replay-parity tests catch) — and Drizzle does nothing for your Zod schemas, which you update by hand. With Prisma, run `prisma generate` after migrating; since Prisma 7, `migrate dev` no longer does it for you. With Alembic + Pydantic, it's manual — you update both the SQLAlchemy model and the Pydantic schema.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Edit the database directly in production | Create a migration | Direct edits are untracked, unreviewable, unrepeatable |
| Edit an already-applied migration | Create a new migration | Edited migrations cause schema drift between environments |
| Run one giant migration that adds columns, backfills data, and drops old columns | Split into expand, backfill and contract steps across deploys | The drop breaks the code still running, and the backfill holds the DDL's lock for its whole run |
| Run DDL with no lock timeout | `SET lock_timeout` to the stall the app can absorb, and rerun the deploy if it trips | A DDL waiting behind one slow query queues every query on the table behind it |
| Put `CREATE INDEX CONCURRENTLY` in a Drizzle migration | Run it as a pipeline step outside the migrator | The migrator wraps every pending migration in one transaction, and `CONCURRENTLY` refuses to run in one |
| Assume an ORM default fills existing rows | Check the default is database-side; backfill derived values explicitly | App-side defaults (SQLAlchemy `default=`, Prisma `@default(uuid())`) never reach existing rows |
| Run `UPDATE` on millions of rows without batching | Batch in chunks with small pauses | One huge update holds every touched row's lock until commit, spikes WAL and replication lag, and leaves bloat behind |
| Assume the migration works because it ran on dev | Test against production-like data | Dev has 10 rows; production has 10 million with edge cases |
| Deploy code that uses a new column before the migration that adds it | Run expand migrations before the code that uses them; run contract migrations *after* the code that stops using the column | Code that reads a non-existent column crashes, in either direction |
| Drop a column without checking what reads it | Search codebase for all references before dropping | Forgotten references cause runtime crashes |

---

## Deciding for Your Project

When starting a new project, determine:

1. **Which migration tool?** Default to **Drizzle + drizzle-kit** (TypeScript). Use Alembic only if the project is Python/SQLAlchemy. Don't introduce a second toolchain into an existing project.
2. **Do you need zero-downtime migrations?** Depends on your deployment model and user expectations — solo project with brief downtime tolerance? Collapse the phases into fewer deploys, but still drop a column one deploy after the code stops using it. Production service with SLOs? Use expand-and-contract.
3. **Where does the migration step run?** In one pre-deploy pipeline job. [Deployment](./deployment.md#migrations-in-the-pipeline) says why not on app startup, and [The Expand-and-Contract Pattern](#the-expand-and-contract-pattern) says which release each migration rides in.
4. **Do you have existing data?** If productionising a prototype, the first migration might need to match the existing schema exactly, then subsequent migrations evolve it.

---

## Related Topics

- **What valid data looks like** — see [Data Integrity](./data-integrity.md) for schemas, validation boundaries and the database-level integrity layer that migrations must maintain. Migrations change what "valid" means; your application schemas must stay in sync.
- **When migrations fail** — see [Deployment](./deployment.md) → Rollback Strategy for rollback procedures, and [Monitoring](./monitoring.md) for runbooks
- **Migrations and deployment** — see [Deployment](./deployment.md#migrations-in-the-pipeline) for running the migration step as a pre-deploy job and shipping only the expand half with each release
- **The API contract over a schema change** — see [API Design](./api-design.md) → What Constitutes a Breaking Change? for keeping the response shape additive while the columns behind it change
- **Testing migrations** — see [Testing](./testing.md) for the real-database setup behavioural and replay-parity migration tests need
