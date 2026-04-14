# Schema Evolution and Migrations

## The Problem Nobody Thinks About on Day One

You design your database schema. Users have a `name` and `email`. You build the app, deploy it, real users sign up. Life is good.

Then the requirements change. You need to split `name` into `first_name` and `last_name`. Or add a `role` column. Or rename `email` to `primary_email` because now users can have multiple emails.

Your schema needs to change. But unlike application code, where you edit the file and redeploy, **your database has data in it.** Real user data. You can't drop the table and recreate it. You need to change the structure while preserving every row.

This is **schema evolution** — the discipline of changing your data model over time without losing data or breaking running code.

---

## What Is a Migration?

A migration is a versioned script that changes your database schema. Think of it like a git commit, but for your database structure:

```sql
-- Migration 001: Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Migration 002: Add role column
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member';

-- Migration 003: Split name into first_name and last_name
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

### Alembic (Python / SQLAlchemy)

Alembic is the standard migration tool for Python projects using SQLAlchemy. SQLAlchemy is the most popular Python ORM — a library that lets you interact with your database using Python objects instead of raw SQL.

Alembic auto-generates migrations by comparing your Python models to the current database:

```python
# Your SQLAlchemy model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)   # you added this
    last_name = Column(String, nullable=False)    # you added this
    email = Column(String, unique=True, nullable=False)
```

```bash
# Alembic detects the difference and generates a migration
alembic revision --autogenerate -m "split name into first and last"
```

This creates a Python file with `upgrade()` and `downgrade()` functions:

```python
def upgrade():
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=False))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=False))

def downgrade():
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
```

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

Prisma also generates a TypeScript client from the schema, so your application code is always in sync with the database structure.

### Drizzle (TypeScript)

Drizzle is a newer TypeScript ORM that's gaining popularity. You define schemas directly in TypeScript — no separate schema file, no code generation step:

```typescript
import { pgTable, serial, text, timestamp } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  firstName: text('first_name').notNull(),
  lastName: text('last_name').notNull(),
  email: text('email').unique().notNull(),
  createdAt: timestamp('created_at').defaultNow(),
});
```

```bash
npx drizzle-kit generate  # generates SQL migration from schema changes
npx drizzle-kit migrate   # applies pending migrations
```

The key difference from Prisma: your schema IS your TypeScript types. No separate `.prisma` file, no generated client — you import the schema directly.

### Choosing Between Them

| Tool | Language | Approach | Best for |
|------|----------|----------|----------|
| **Alembic** | Python | Auto-generate from SQLAlchemy models, manual editing | Most flexible, Python projects, complex migrations |
| **Prisma Migrate** | TypeScript | Generate from `.prisma` schema file | Great developer experience, opinionated, rapid development |
| **Drizzle Kit** | TypeScript | Generate from TypeScript schema definitions | Lighter weight, closer to raw SQL, newer projects |

**This is a project-specific choice** — it depends on your ORM, your language, and your team's preferences. The concepts (versioned migrations, up/down, tracking) are the same regardless of tool.

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

This solves the problem by splitting the change into safe phases:

**Phase 1: Expand** (add new things, don't remove old things)

```sql
-- Migration A: Add new columns (old code ignores them — safe)
ALTER TABLE users ADD COLUMN first_name TEXT;
ALTER TABLE users ADD COLUMN last_name TEXT;
```

Deploy this migration. Old code keeps working — it reads `name` and ignores `first_name`/`last_name`.

**Phase 2: Backfill** (copy data from old to new)

```sql
-- Migration B: Populate new columns from old data
UPDATE users SET
    first_name = SPLIT_PART(name, ' ', 1),
    last_name = SPLIT_PART(name, ' ', 2);
```

**Phase 3: Deploy new code** that reads/writes BOTH old and new columns

```python
# New code writes to BOTH columns during transition
user.first_name = "Kasey"
user.last_name = "Smith"
user.name = "Kasey Smith"  # keep old column updated for safety
```

**Phase 4: Contract** (remove old things, once confident)

```sql
-- Migration C: Drop old column (new code doesn't use it — safe)
ALTER TABLE users DROP COLUMN name;
```

At no point does running code break. Every phase is safe for both old and new code.

### When Do You Need Expand-and-Contract?

| Change | Needs expand-and-contract? | Why |
|--------|---------------------------|-----|
| **Renaming a column** | Yes | Old code reads old name; new code reads new name |
| **Changing a column's type** | Yes | Old code expects old type |
| **Removing a column** | Yes | Old code reads the column |
| **Adding a new column with a default** | No | Old code ignores it |
| **Adding a new table** | No | Old code doesn't query it |
| **Adding an index** | Usually no | But on large tables, use `CREATE INDEX CONCURRENTLY` in Postgres to avoid locking |

**For small projects and solo developers:** You might not need expand-and-contract. If you can tolerate 30 seconds of downtime during deploy, a simple migration is fine. The pattern matters when users would notice the outage, or when your deployment takes minutes.

---

## Data Backfills

Adding a column is easy. Populating it for existing rows is the part people forget.

```sql
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member';
```

New rows get `role = 'member'` automatically. But what about existing rows? Behaviour varies:

- **PostgreSQL (modern):** `DEFAULT` backfills existing rows
- **MySQL:** behaviour varies by version
- **Some ORMs:** set defaults in application code only, not at the database level — existing rows get `NULL`

**The safe approach:** always write an explicit backfill, don't rely on `DEFAULT` behaviour.

### Batched Backfills for Large Tables

For tables with millions of rows, a single `UPDATE` would lock the table for too long:

```python
# Backfill in batches of 1000 (PostgreSQL — use a subquery for batching)
while True:
    result = db.execute("""
        UPDATE users SET role = 'member'
        WHERE id IN (
            SELECT id FROM users WHERE role IS NULL LIMIT 1000
        )
    """)
    if result.rowcount == 0:
        break
    db.commit()
    time.sleep(0.1)  # small pause to avoid overwhelming the DB
```

```typescript
// TypeScript equivalent (PostgreSQL)
let updated = 0;
do {
  const result = await db.execute(sql`
    UPDATE users SET role = 'member'
    WHERE id IN (
      SELECT id FROM users WHERE role IS NULL LIMIT 1000
    )
  `);
  updated = result.rowCount ?? 0;
  if (updated > 0) await new Promise(r => setTimeout(r, 100));
} while (updated > 0);
```

**Note:** `UPDATE ... LIMIT` works directly in MySQL. In PostgreSQL, use the subquery approach shown above. The concept is the same — update a bounded number of rows per iteration.

---

## Migration Safety Rules

These come from painful production experience:

### 1. Never edit a migration that's already been applied

If migration 003 has run on staging and you edit the file, your local database and staging now have different schemas with the same migration number. The tool thinks they're in sync. They're not. **Always create a new migration instead.**

### 2. Test migrations against production-like data

A migration that works on your empty dev database might fail on production because of data that violates a new constraint. "Add NOT NULL column" fails if existing rows have NULL values. Test against a clone or snapshot of production data.

### 3. Every migration should be reversible when possible

Write the `downgrade()` function (Alembic) or keep the reverse SQL handy. You might not need it, but the one time you do, you'll be grateful. Some operations aren't reversible (dropped column = data gone), and that's OK — just be aware of it.

### 4. Never run migrations manually in production

Migrations should run as part of your deployment pipeline, automatically. Manual SQL in a production terminal is how data loss happens. If you need to run a one-off fix, make it a migration so it's tracked and reviewable.

### 5. Separate schema migrations from data migrations

- **Schema migrations** (add column, create table) are fast and structural
- **Data migrations** (backfill values, transform data) can be slow and are about content

Keep them in separate migration files. Schema migrations are straightforward to roll back. Data migrations might not be. Mixing them makes rollback impossible.

---

## Keeping Application Schemas in Sync

When your database schema changes, your application schemas (Zod, Pydantic) need to change too. This is a coordination problem:

```
Database: users table now has first_name, last_name (no name column)
Zod schema: still expects { name: string }  ← BUG
```

**The rule:** Every database migration should have a corresponding application schema update in the same pull request. The reviewer should check both.

With Prisma, this is automatic — `prisma migrate dev` updates the generated client. With Drizzle, your TypeScript schema IS the database schema, so they can't drift. With Alembic + Pydantic, it's manual — you update both the SQLAlchemy model and the Pydantic schema.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Edit the database directly in production | Create a migration | Direct edits are untracked, unreviewable, unrepeatable |
| Edit an already-applied migration | Create a new migration | Edited migrations cause schema drift between environments |
| Run one giant migration that adds columns, backfills data, and drops old columns | Split into separate expand/backfill/contract migrations | Giant migrations can't be partially rolled back |
| Skip the backfill step | Explicitly backfill existing rows | Relying on DEFAULT behaviour is database-version-dependent |
| Run `UPDATE` on millions of rows without batching | Batch in chunks with small pauses | Unbatched updates lock the table and can crash the database |
| Assume the migration works because it ran on dev | Test against production-like data | Dev has 10 rows; production has 10 million with edge cases |
| Deploy new code before running the migration | Run migration first, then deploy code that uses new columns | Code that reads non-existent columns crashes |
| Drop a column without checking what reads it | Search codebase for all references before dropping | Forgotten references cause runtime crashes |

---

## Deciding for Your Project

When starting a new project, determine:

1. **Which migration tool?** Depends on your ORM and language (Alembic for SQLAlchemy, Prisma Migrate or Drizzle Kit for TypeScript)
2. **Do you need zero-downtime migrations?** Depends on your deployment model and user expectations — solo project with brief downtime tolerance? Simple migrations are fine. Production service with SLOs? Use expand-and-contract.
3. **How will migrations run?** As part of the deployment pipeline (recommended) or manually?
4. **Do you have existing data?** If productionising a prototype, the first migration might need to match the existing schema exactly, then subsequent migrations evolve it.

---

## Related Topics

- **What valid data looks like** — see [Data Integrity](./data-integrity.md) for schemas and validation boundaries. Migrations change what "valid" means; your application schemas must stay in sync.
- **When migrations fail** — see [Error Handling](./error-handling.md) for rollback procedures and incident response
- **Migrations and deployment** — see [Deployment](./deployment.md) for how migration phases fit into deploy pipelines
- **Database constraints** — see [Data Integrity](./data-integrity.md) for the database-level integrity layer that migrations must maintain
