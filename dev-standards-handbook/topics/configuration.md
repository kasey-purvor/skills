# Configuration

> **Calibrate to the context.** How much config machinery an app needs scales with how
> it's deployed and how long it lives: a local script or small internal tool needs little
> more than a few env vars checked at startup; secret managers, multi-layer config, and
> per-environment plumbing earn their keep on deployed, longer-lived systems. Two cheap
> habits pay at any size: fail fast on missing critical values, and keep secrets out of
> git. The serverless section applies only to code that runs without a long-lived process.
> Reference material, not a checklist.

## The Problem

Your app's configuration — database URLs, API keys, feature flags, port numbers — is data entering your system from an external source (environment variables, config files, secret managers). It deserves the same validation discipline as any other external data.

Here's what happens in most projects:

```typescript
// Scattered throughout the codebase
const dbUrl = process.env.DATABASE_URL;  // string | undefined
const port = process.env.PORT;            // string | undefined (even if you want a number)
const debug = process.env.DEBUG;          // string | undefined (even if you want a boolean)
```

Three problems:

1. **No validation at startup.** If `DATABASE_URL` is missing, you don't find out until the first database query — maybe 30 seconds after the app starts, maybe 3 hours later when a user triggers that code path. In production, this means you deployed a broken app and didn't know it.

2. **Types are wrong.** Environment variables are always strings. `PORT` is `"3000"` not `3000`. `DEBUG` is `"true"` not `true`. Every place that reads these values needs to convert them, and every place does it slightly differently.

3. **No single source of truth.** Different files read different env vars. Nobody knows the complete list of what the app needs to run. A new developer clones the repo and gets a cryptic crash because they're missing an env var nobody documented.

**The fix that addresses all three: validate config at startup and fail fast.** It's cheap — a small schema and one call at the entry point — so it's worth doing even on small apps; how much *more* machinery you add beyond it is where scale comes in.

---

## Environment Variable Validation

The same schema validation pattern you use for API data works for configuration. Keep the parser pure: it takes its source as an argument instead of reading `process.env` at import, so the entry point calls it once and tests call it with a plain object.

### TypeScript (Zod)

```typescript
// Zod 4 — src/config/env.ts: ONE schema and ONE pure parser; nothing here reads process.env
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.url(),
  PORT: z.coerce.number().int().positive().default(3000), // "3000" → 3000; an empty PORT= coerces to 0, so reject it
  // Safe boolean parser — z.stringbool(), never z.coerce.boolean(). Coercion
  // follows JS truthiness: "false" and "0" become true, since any non-empty
  // string is truthy in JavaScript. Feature flags and security toggles can
  // silently flip on. stringbool maps an explicit allowlist (e.g. "true"/"1"/"yes"
  // vs "false"/"0"/"no", case-insensitive) and rejects anything else. Zod 4's .default()
  // skips parsing, so it takes the OUTPUT type: false, not the truthy string 'false'.
  DEBUG: z.stringbool().default(false),
  API_KEY: z.string().min(1),                  // required, non-empty
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

export type Env = z.infer<typeof envSchema>;

export function parseEnv(source: Record<string, string | undefined>): Env {
  const result = envSchema.safeParse(source);
  if (!result.success) {
    const issues = result.error.issues.map((i) => `  ${i.path.join('.')}: ${i.message}`).join('\n');
    throw new Error(`Invalid environment configuration:\n${issues}\nSee .env.example`);
  }
  return result.data;
}

// src/main.ts — the entry point parses once, before anything else starts:
//   const env = parseEnv(process.env); // throws → the process exits non-zero, naming each bad variable
```

Everything downstream receives `env`, or the clients built from it, and gets typed values: `env.PORT` is a number, `env.LOG_LEVEL` one of four strings. Parsed config is immutable data, so holding that one object for the life of the process is fine. The trap is building *clients* at import time ([below](#service-clients-are-built-in-the-composition-root)).

### Python (pydantic-settings)

`pydantic-settings` is a separate package from `pydantic`, built for reading environment variables and `.env` files. Raw `os.getenv()` returns `None` for a missing variable and defers the failure to first use; `BaseSettings` validates on construction and names the missing field.

```python
# pydantic-settings 2 · FastAPI 0.95+ — src/config.py
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")  # development convenience; real env vars win

    database_url: SecretStr              # required: "database_url: Field required" if missing
    port: int = 3000                     # coerced from the string "3000"
    debug: bool = False                  # "false"/"0" parse to False; no truthiness trap here
    api_key: SecretStr                   # masked in repr/logs; read via .get_secret_value()
    log_level: Literal["debug", "info", "warn", "error"] = "info"  # same set as the TypeScript enum

@lru_cache                               # built once, on first call, not at import
def get_settings() -> Settings:
    return Settings()

SettingsDep = Annotated[Settings, Depends(get_settings)]  # a route declares `settings: SettingsDep`
```

Call `get_settings()` once in the app's lifespan handler, so a bad environment still fails the boot rather than the first request that needs it. That call is not a dependency, so `app.dependency_overrides[get_settings]` never reaches it or the engine built from it. Build the app in a factory that takes its settings (`create_app(settings: Settings | None = None)`, whose lifespan uses `settings or get_settings()`). Tests pass it `Settings(_env_file=None, ...)` and override `get_settings` with the same object.

---

## The .env File

In development, a `.env` file in the project root holds local values so you don't export them in every terminal. It is a development convenience only: deployed environments get their values from the platform or a secret manager ([Secret Delivery and Rotation](#secret-delivery-and-rotation)). Keep `.env`, `.env.local` and `.env.*.local` out of git *and* out of the image, by listing them in both `.gitignore` and `.dockerignore`.

- **TypeScript:** Node reads `.env` natively — `node --env-file=.env` (20.6+), `process.loadEnvFile()` (20.12+), and `--env-file-if-exists` (22.9+) for a file that may be absent — so the `dotenv` package is optional on Node 22. Frameworks like Next.js read `.env.local` automatically
- **Python:** pydantic-settings reads `.env` when configured with `env_file=".env"`

In Node, `dotenv` and pydantic-settings alike, a real environment variable beats the `.env` value for the same key. The file only fills gaps; it never overrides what the shell or platform sets.

**Commit a `.env.example` instead**: every variable the app reads, with placeholder values and no real secrets. A new developer copies it to `.env` and fills in their values, and the startup error above points at it. Never commit `.env` itself: bots scan public repositories for leaked keys and use them within minutes, and a deleted secret still lives in git history.

---

## Multi-Layer Configuration

Not all config is environment variables. Priority, highest first:

1. **Real environment variables** — secrets, per-environment overrides
2. **`.env` file** (development only) — fills only keys the real environment leaves unset
3. **Config file** (YAML) — domain settings, tunables
4. **Typed model defaults** — sensible fallbacks
5. **Code constants** — values that truly never change

### What Goes Where

| Type | Location | Example | Why |
|------|----------|---------|-----|
| **Secrets** | Environment, injected by the platform or fetched from a secret manager; `.env` in development only | API keys, database passwords | Must not be in code, config files or the image (security) |
| **Per-environment settings** | Environment variables, read at runtime | Port, debug mode, log level, API base URL | Different in dev/staging/production; one artifact serves them all |
| **Tunables** | Config file (YAML) | Rate limits, batch sizes, timeouts | Nested, reviewable in diffs, keeps non-secrets out of env |
| **Structural defaults** | Typed model defaults | Collection names, URL patterns | Sensible defaults that rarely change |
| **True constants** | Code | Math constants, protocol versions | Never change across environments |

### Config Files for Tunables

Use a config file for tunables that aren't secrets and read better nested, with every change reviewed as a diff. This chapter uses YAML; JSON works the same way. A file that ships inside the build artifact still changes only through a deploy; a value that must change at runtime needs a flag service or dynamic config (see [Deployment](./deployment.md#feature-flags)).

A missing file is an error, not a cue to fall back to defaults: running on defaults nobody chose is the deferred failure this chapter exists to prevent. If the file is genuinely optional, make that an explicit setting.

```typescript
// Zod 4 · yaml 2 — tunables from config/app-config.yaml
import { readFileSync } from 'node:fs';
import { parse } from 'yaml';
import { z } from 'zod';

const AppConfigSchema = z.object({
  fetch: z.object({
    rateLimitSeconds: z.number().default(0.5),
    requestTimeout: z.number().default(30),
    maxRetries: z.number().default(3),
  }).prefault({}), // prefault parses {} so inner defaults apply; .default({}) returns {} as-is
  database: z.object({
    poolSize: z.number().default(10),
    poolTimeout: z.number().default(30),
  }).prefault({}),
});

export function loadAppConfig(path = './config/app-config.yaml') {
  // readFileSync throws on a missing file; an empty file parses to null and fails validation
  return AppConfigSchema.parse(parse(readFileSync(path, 'utf-8')));
}
```

```python
# Pydantic 2 · PyYAML 6 — tunables from config/app-config.yaml
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

class FetchSettings(BaseModel):
    rate_limit_seconds: float = 0.5
    request_timeout: int = 30
    max_retries: int = 3

class DatabaseSettings(BaseModel):
    pool_size: int = 10
    pool_timeout: int = 30

class AppConfig(BaseModel):
    fetch: FetchSettings = Field(default_factory=FetchSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

@lru_cache
def get_app_config(path: Path = Path("config/app-config.yaml")) -> AppConfig:
    # read_text raises on a missing file. An empty file loads as None: model_validate rejects it
    # with a ValidationError, where AppConfig(**None) would raise a bare TypeError.
    return AppConfig.model_validate(yaml.safe_load(path.read_text()))
```

---

## Environment-Specific Configuration

Most apps run in development (your laptop, debug mode on, local database), staging (mimics production, for testing) and production (real users, real data). The pattern:

- The **schema** (what config exists and what types it has) is defined in code — same across all environments
- The **values** come from the environment at runtime — different per environment
- **Secrets** come from a secret manager in deployed environments, from `.env` in development

This means your config module doesn't know or care which environment it's running in. It reads env vars and validates them. The deployment platform sets the right values. This avoids `if (process.env.NODE_ENV === 'production')` scattered through your code.

---

## Build-Time vs Runtime Configuration

A value read while the artifact is built is frozen into it, and changing the deployed environment later changes nothing. Next.js inlines `NEXT_PUBLIC_*` into the client bundle at `next build`, Vite does the same for `VITE_*`, and a Docker build `ARG` that a build step reads, or that sets an `ENV`, is baked into the image. Server code is not automatically safe: a page rendered statically at build reads env then, and bundlers can inline `process.env` reads in edge code ([The Mode Frozen Into the Bundle](./pitfalls.md#the-mode-frozen-into-the-bundle)).

- **Keep environment-selecting values out of the build** (API base URLs, auth mode, feature switches), so one artifact can be promoted from staging to production unchanged ([Deployment](./deployment.md#environment-promotion)).
- **Values the browser needs per environment come from the server at runtime**, rendered by server code or served from a config endpoint, not from a build-time public variable.
- **Anything built into client code is public**, whatever its prefix ([Front-end Development](./frontend-development.md#framework-specific-decisions)).
- **Prove it:** boot the built image with a different runtime value and check that the runtime value wins.

---

## Secret Delivery and Rotation

How a secret reaches the process decides what rotation means, because config loaded once at startup never sees a later change.

- **Platform-injected env var** (ECS task-definition `secrets`, Kubernetes `secretKeyRef`): the platform reads the secret manager when the process starts. The app's config code is unchanged, but a rotated value arrives only with a new process: ECS documents that a running task keeps the old value until a new task launches.
- **Mounted file** (a Kubernetes Secret volume): Kubernetes updates the file in place (not under a `subPath` mount), but an app that read it at boot still holds the old value until it reads again.
- **SDK fetch at startup or on demand**: the app calls the secret manager itself. It needs read permission on that one secret and a cache with a lifetime, so a rotation is picked up when the cache expires rather than costing a call per request.

Plan rotation around that. Either restart on rotation (force a new deployment) under a rotation scheme where old and new credentials overlap, or fetch through a cache and rebuild the client when the cache refreshes or authentication fails. Short-lived federated credentials (an IAM task role, RDS IAM authentication) sidestep both, because nothing long-lived is stored, so prefer them to a calendar rotation wherever the platform offers them. The SDK refreshes an IAM task role's credentials itself. An RDS IAM token lasts 15 minutes and is checked only when a connection opens, so the pool mints one per new connection (a node-postgres `password` function, a SQLAlchemy `do_connect` hook). Where secrets are stored, how often static keys rotate and who may read them is [Security](./security.md#secrets-management)'s side.

---

## Service Clients Are Built in the Composition Root

Build clients (database pools, HTTP SDKs, queue producers) from parsed config in the composition root, the entry point that wires the app together, and pass them to what uses them. A client built at import time is the singleton trap: every importer, a unit test included, gets the one instance aimed at whatever `process.env` held when the module first loaded, and nothing can hand in another.

```typescript
// node-postgres 8 — Env is the type from src/config/env.ts above
import { Pool } from 'pg';

// BAD: built from env at import. Anything that imports this module, a unit test included,
// shares a pool aimed at the developer's database and cannot substitute its own.
export const pool = new Pool({ connectionString: process.env.DATABASE_URL });

// GOOD: a factory; main.ts calls it once with parsed config and passes the pool down
export function createPool(env: Pick<Env, 'DATABASE_URL'>) {
  return new Pool({ connectionString: env.DATABASE_URL, max: 10 });
}
```

In FastAPI the composition root is the lifespan handler: build the engine there from the settings the app factory received ([above](#python-pydantic-settings)) and hand it out through a dependency. Whether that client also sits behind a port is [Module Design](./module-design.md#structuring-around-dependencies)'s call.

---

## Coercion: When It Makes Sense

In the [Data Integrity](./data-integrity.md) topic, we discuss strict vs coercing mode. Configuration is the one place where **coercion is almost always the right choice:**

- Environment variables are always strings — `PORT=3000` is the string `"3000"`
- You want `env.PORT` to be the number `3000`
- Rejecting `"3000"` because it's not a number would be absurdly pedantic

`z.coerce.number()` in Zod and pydantic-settings' default coercion both handle numbers correctly. Booleans are the exception: `z.coerce.boolean()` follows JavaScript truthiness — any non-empty string becomes `true`, so `"false"` and `"0"` silently coerce to `true`. Use an explicit allowlist: Zod 4's `z.stringbool()` (see the env schema at the top of this topic). pydantic-settings v2 handles boolean strings correctly on its own (`"true"`/`"false"`/`"1"`/`"0"`), so the Python side doesn't need the same workaround.

This is one of the rare cases where type coercion makes more sense than strict validation — provided the coercion itself is safe.

---

## Testing Configuration

This topic's whole promise is **fail fast at the boundary**, so the tests prove the boundary actually fails. None of them needs a database, since config validation is pure parsing:

- **Fail-fast on a missing variable.** Call `parseEnv` (or construct `Settings`) with a required variable removed: it must throw, and the error must *name* the variable. A config that accepts a missing `DATABASE_URL` has just deferred the crash to the first query three hours later. (In serverless, this stands in for the cold-start failure that would otherwise hide deep in a handler.)
- **Coercion is real and safe.** Feed `PORT` in as a string and assert you get back a typed number. Booleans get their own case: a naive coercion treats `"false"` and `"0"` as `true`, so assert the `DEBUG` parser (`z.stringbool()`) maps them to `false` and rejects unknown strings — a flag silently flipping on is the bug this guards against.
- **Tests pin their own environment.** Env files are ambient: a test runner, or a harness that spawns the app, can load the same `.env.local` a runbook just changed, and the suite silently runs in another mode ([The Env File the Test Runner Also Read](./pitfalls.md#the-env-file-the-test-runner-also-read)). Pass config explicitly: a literal object to `parseEnv`, `Settings(_env_file=None, ...)` in pydantic-settings, the settings handed to the FastAPI app factory (an override alone misses the lifespan), and an explicit `env` for any server the harness spawns.

See [Testing](./testing.md) for the test-suite setup and where these sit in the pyramid.

---

## Serverless and Edge Functions

The patterns above assume a process that boots once and stays up. Serverless functions (AWS Lambda, Vercel Functions, Supabase or Deno edge functions, Cloudflare Workers) have no single startup, which tempts people to read env inline in each handler. That has the server case's three problems and a worse one: a missing variable surfaces only when a request reaches the code that reads it, possibly days after the deploy.

The fix is the same parser, called at module scope in each function's entry file, its composition root (`parseEnv(Deno.env.toObject())` on Deno), so a bad environment fails the cold start instead of a request deep in business logic. The shared module exports only the parser, and the code below the entry file takes `env` as a parameter. Cloudflare Workers are no exception: since March 2025 a Worker can `import { env } from 'cloudflare:workers'` at global scope, where before env reached only the handler.

- **Env vars don't go stale on warm instances; values fetched at init do.** Lambda runs invocations on the new configuration once an update completes, and Vercel applies a changed variable to the next deployment. A secret a warm instance fetched at init stays as fetched until the instance is recycled, so give that fetch a cache lifetime.
- **Module-level state is per instance.** A cache or rate-limit counter in a module variable resets on cold start and is not shared across concurrent instances; anything that must persist across invocations belongs in an external store. On Vercel's Fluid compute, the default for new projects since April 2025, and on Lambda Managed Instances, one instance also serves several requests at once, so per-request data never goes in a module variable.
- **Create database clients at module scope, behind a pooler.** Warm invocations then reuse the connection, but every concurrent instance holds its own, so put a pooler (RDS Proxy, PgBouncer, the provider's pooled endpoint) in front of Postgres. Pool sizing and the multiplication rule are in [Resilience](./resilience.md#fan-out-and-connection-pools).

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Read `process.env` / `os.getenv()` directly throughout code | Centralise in one config module with schema validation | Scattered reads mean no single source of truth, no validation, no typing |
| Hardcode secrets in code | Inject them through the environment or a secret manager | Secrets in code end up in git history — effectively public forever |
| Use `process.env.NODE_ENV` checks everywhere | Use explicit config values (`env.DEBUG`, `settings.log_level`); keep `NODE_ENV=production` in every deployed environment, staging included, and name the deployment environment with a separate variable (e.g. `APP_ENV`) | NODE_ENV checks create invisible behaviour differences between environments, and libraries and frameworks such as Next.js switch to dev-mode behaviour and slower paths when it isn't `production` |
| Skip validation for "obvious" vars | Validate all required vars at startup | "Obviously" set vars are the ones that silently break production deploys |
| Default to production URLs/credentials | Required credentials have no default — fail at startup | Accidentally connecting to production from development is a real incident |
| Commit `.env` to git, or copy it into the image | List it in `.gitignore` and `.dockerignore`; commit `.env.example` instead | Secrets in git are exploited within minutes by automated scanners |
| Mix secrets into config files | Config files for tunables; secrets from the environment or a secret manager (`.env` in development only) | Config files are committed and shipped in the artifact; secrets must not be |
| Fall back to defaults when the config file is missing | Fail at startup; make an optional file an explicit setting | Silent defaults are the deferred failure validation exists to prevent |
| Bake environment-selecting values into the build (`NEXT_PUBLIC_*`, `VITE_*`, Docker `ARG`) | Read them at runtime | The artifact keeps the build's value, so it can't be promoted unchanged |
| Re-read env vars on every request | Load once at startup; give a rotating secret a cached fetch with a lifetime | Env vars don't change during runtime; re-reading is waste |
| Use `as` assertions on `process.env` (TypeScript) | Parse through Zod schema | Assertions skip validation — you're back to trusting external data |

---

## Deciding for Your Project

When starting a new project, determine:

1. **Where is config parsed, and how do tests supply it?** One `parseEnv` or `get_settings` called at the entry point; tests pass an explicit object, never the ambient env file.
2. **What's a secret and what's a tunable?** Secrets from the environment or a secret manager, with `.env` in development only; tunables in a config file or plain env vars.
3. **Do you need a config file, or are env vars enough?** Small apps often need only env vars.
4. **Which values must change without a deploy?** Those need a flag service or dynamic config, not an env var or a file inside the artifact.
5. **Which values are read at build time or visible to the client?** Keep environment-selecting ones out of the build, and treat anything client-visible as public.
6. **How does each secret reach the process, and what happens when it rotates?** Platform injection means a restart per rotation; a runtime fetch needs a cache lifetime; short-lived federated credentials avoid the question where the platform offers them.

---

## Related Topics

- **Client-visible configuration** — see [Front-end Development](./frontend-development.md#framework-specific-decisions) for framework boundaries and public values built into browser code
- **Config is data integrity** — see [Data Integrity](./data-integrity.md#validation-boundaries) for the validation boundary concept that applies here
- **Secret storage and access** — see [Security](./security.md#secrets-management) for secret managers, least privilege and keeping secrets out of logs; delivery and rotation are covered above
- **One artifact for every environment** — see [Deployment](./deployment.md#environment-promotion) for build-once-promote, which is why environment-selecting values stay out of the build
- **Where clients are built** — see [Module Design](./module-design.md#structuring-around-dependencies) for ports, adapters and when a seam needs one
- **Testing configuration** — see [Testing](./testing.md) for the test-suite setup these startup-validation and coercion tests sit in
