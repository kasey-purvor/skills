# Configuration

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

**The solution: validate all config at startup, fail fast.**

---

## Environment Variable Validation

The same schema validation pattern you use for API data works for configuration.

### TypeScript (Zod)

```typescript
// src/config/env.ts — ONE file, loaded ONCE at startup
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  PORT: z.coerce.number().default(3000),      // coerce "3000" → 3000
  DEBUG: z.coerce.boolean().default(false),    // coerce "true" → true
  API_KEY: z.string().min(1),                  // required, non-empty
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

// Validate immediately — app crashes on startup with a clear error,
// not 3 hours later with a cryptic one
export const env = envSchema.parse(process.env);
```

Now everywhere in your codebase:

```typescript
import { env } from './config/env';

// env.PORT is a number, guaranteed
// env.DATABASE_URL is a valid URL string, guaranteed
// env.LOG_LEVEL is one of the four allowed values, guaranteed
app.listen(env.PORT);
```

For a friendlier error message on startup:

```typescript
const result = envSchema.safeParse(process.env);
if (!result.success) {
  const missing = result.error.issues
    .map(i => `  ${i.path.join('.')}: ${i.message}`)
    .join('\n');
  console.error(`Invalid environment configuration:\n${missing}\nSee .env.example`);
  process.exit(1);
}
export const env = result.data;
```

### Python (pydantic-settings)

**Important:** This uses `pydantic-settings`, a separate package from `pydantic` itself. It's specifically designed for reading configuration from environment variables and `.env` files. Install with `pip install pydantic-settings`.

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # reads from .env file in development
        env_file_encoding="utf-8",
    )

    database_url: str                    # required — app won't start without it
    port: int = 3000                     # optional, coerced from string automatically
    debug: bool = False                  # optional, coerced from string automatically
    api_key: str                         # required
    log_level: str = "info"              # optional with default

# Validate on construction — app crashes immediately if config is invalid
settings = Settings()
```

**Why pydantic-settings and not raw `os.getenv()`:**

```python
# BAD — no validation, no typing, failure is deferred and cryptic
class Config:
    @property
    def database_url(self) -> str | None:
        return os.getenv("DATABASE_URL")  # Returns None silently if missing

# GOOD — validated at startup, typed, fails fast with clear message
class Settings(BaseSettings):
    database_url: str  # Missing? App crashes immediately with "database_url: field required"
```

The `os.getenv()` approach directly contradicts the "validate at boundaries" principle. Environment variables are a boundary — external data entering your system. `BaseSettings` validates them. `os.getenv()` trusts them.

---

## The .env File

In development, you don't want to set environment variables manually every time you open a terminal. A `.env` file holds your local development config:

```bash
# .env (in your project root, NEVER committed to git)
DATABASE_URL=postgresql://localhost:5432/myapp
API_KEY=dev-key-not-real
DEBUG=true
LOG_LEVEL=debug
```

- **TypeScript:** Use the `dotenv` package, or frameworks like Next.js read `.env.local` automatically
- **Python:** pydantic-settings reads `.env` automatically when configured with `env_file=".env"`

### .env.example

Always commit a `.env.example` file — a template with placeholder values showing what environment variables are required:

```bash
# .env.example (committed to git — no real secrets)
DATABASE_URL=postgresql://localhost:5432/myapp_dev
API_KEY=your-api-key-here
DEBUG=false
LOG_LEVEL=info
```

This serves as documentation. A new developer clones the repo, copies `.env.example` to `.env`, fills in their values, and the app starts.

### Critical Rule: .env goes in .gitignore

`.env` files contain secrets (API keys, database passwords). If you commit them to git, anyone with access to the repo has your secrets. There are bots that scan GitHub for accidentally committed API keys and exploit them within minutes.

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

---

## Multi-Layer Configuration

Not all config is environment variables. There are different types of configuration with different characteristics:

```
Priority (highest to lowest):
1. Environment variables (.env)    — secrets, per-environment overrides
2. Config file (YAML/JSON)         — domain settings, tunables
3. Typed model defaults            — sensible fallbacks
4. Code constants                  — values that truly never change
```

### What Goes Where

| Type | Location | Example | Why |
|------|----------|---------|-----|
| **Secrets** | Environment variables / `.env` | API keys, database passwords | Must not be in code or config files (security) |
| **Per-environment settings** | Environment variables | Port, debug mode, log level | Different in dev/staging/production |
| **Tunables** | Config file (YAML/JSON) | Rate limits, batch sizes, timeouts | Change without code deploys, not secret |
| **Structural defaults** | Typed model defaults | Collection names, URL patterns | Sensible defaults that rarely change |
| **True constants** | Code | Math constants, protocol versions | Never change across environments |

### Config File Example

For tunables that aren't secrets and might need adjustment without a code change:

```yaml
# config/app-config.yaml
fetch:
  rate_limit_seconds: 0.5
  request_timeout: 30
  max_retries: 3

chunking:
  batch_size: 100
  checkpoint_interval: 100

database:
  pool_size: 10
  pool_timeout: 30
```

### Typed Config Models for Tunables

**TypeScript:**
```typescript
const AppConfigSchema = z.object({
  fetch: z.object({
    rateLimitSeconds: z.number().default(0.5),
    requestTimeout: z.number().default(30),
    maxRetries: z.number().default(3),
  }).default({}),
  database: z.object({
    poolSize: z.number().default(10),
    poolTimeout: z.number().default(30),
  }).default({}),
});

// Load from file, validate with schema
const raw = JSON.parse(readFileSync('./config/app-config.json', 'utf-8'));
export const appConfig = AppConfigSchema.parse(raw);
```

**Python:**
```python
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
```

---

## Environment-Specific Configuration

Most apps run in multiple environments:

- **Development** — your laptop, debug mode on, local database
- **Staging** — a server that mimics production, for testing
- **Production** — real users, real data

The pattern:

- The **schema** (what config exists and what types it has) is defined in code — same across all environments
- The **values** come from the environment — different per environment
- **Secrets** come from a secret manager (AWS Secrets Manager, Vault, etc.) in production, from `.env` in development

This means your config module doesn't know or care which environment it's running in. It reads env vars and validates them. The deployment platform sets the right values. This avoids `if (process.env.NODE_ENV === 'production')` scattered through your code.

---

## Singleton Config Loading

Config should be loaded once and reused. Don't re-read env vars or config files on every request.

**Python:**
```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_app_config() -> AppConfig:
    config_path = Path("config/app-config.yaml")
    if not config_path.exists():
        return AppConfig()
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)
```

**TypeScript:**
```typescript
// Module-level const — loaded once on first import
export const env = envSchema.parse(process.env);
export const appConfig = loadAppConfig();
```

---

## Injectable Service Clients

Create service clients from validated config and pass them to consumers — don't hardcode connection details:

```typescript
// GOOD: client created from config, injectable, testable
export function createDbClient(config: { url: string }) {
  return createClient(config.url);
}

// BAD: module-level singleton with hardcoded URL
export const db = createClient("https://prod.example.com");
```

```python
# GOOD: client created from config, injectable, testable
def create_db_client(settings: DatabaseSettings):
    return MongoClient(settings.uri)

# BAD: module-level singleton with hardcoded URL
db = MongoClient("mongodb://prod.example.com")
```

Why injectable? Two reasons:
1. **Testing** — you can pass a test config that points to a test database
2. **Environment switching** — config determines the target, not hardcoded strings

---

## Coercion: When It Makes Sense

In the [Data Integrity](./data-integrity.md) topic, we discuss strict vs coercing mode. Configuration is the one place where **coercion is almost always the right choice:**

- Environment variables are always strings — `PORT=3000` is the string `"3000"`
- You want `env.PORT` to be the number `3000`
- Rejecting `"3000"` because it's not a number would be absurdly pedantic

Both Zod (`z.coerce.number()`) and pydantic-settings (coerces by default) handle this correctly. This is one of the rare cases where coercion makes more sense than strict validation.

---

## Serverless and Edge Function Configuration

The patterns above assume your application starts once and stays running — a server that boots, validates config, then serves requests indefinitely. In serverless environments (AWS Lambda, Vercel Functions, Deno edge functions), there's no persistent "startup." Each function invocation might be a fresh start, or it might reuse a warm instance from a previous invocation. You don't control which.

This leads developers to skip centralized config validation and instead read environment variables inline, wherever they're needed:

```typescript
// Scattered across 15 different function files
export default function handler(req: Request) {
  const apiKey = Deno.env.get('ANTHROPIC_API_KEY'); // string | undefined
  const dbUrl = Deno.env.get('SUPABASE_URL');       // might be missing
  // ... use them directly, hope they exist
}
```

This has the same three problems as the traditional server case — no validation, no types, no fail-fast — but it's worse because:

1. **You can't test before deploying.** A traditional server crashes on startup with a missing var. A serverless function only crashes when a request hits the specific code path that reads that var. The function might work fine for days before someone triggers the path that needs the missing key.

2. **Cold starts scatter the reads.** Each function file independently reads its own env vars, often with inconsistent fallback patterns (`KEY || ALTERNATE_KEY`). No single file lists what the function needs.

3. **Warm instances create false confidence.** A warm instance has already read the env vars successfully. If you change a var in your deployment dashboard but the instance is still warm with the old value, you see stale config until the next cold start.

**The fix is the same pattern, just triggered differently.** Instead of validating at "app startup," validate on first import:

```typescript
// _shared/config.ts — one file, imported by every function
import { z } from 'zod';

const ConfigSchema = z.object({
  anthropicApiKey: z.string().min(1),
  supabaseUrl: z.string().url(),
  supabaseServiceKey: z.string().min(1),
  environment: z.enum(['development', 'production']).default('production'),
});

// Validates on first import — if a var is missing, the function
// fails immediately on cold start, not deep in business logic
export const config = ConfigSchema.parse({
  anthropicApiKey: Deno.env.get('ANTHROPIC_API_KEY'),
  supabaseUrl: Deno.env.get('SUPABASE_URL'),
  supabaseServiceKey: Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),
  environment: Deno.env.get('ENVIRONMENT'),
});
```

```typescript
// In your function handler — import typed config, never read env directly
import { config } from './_shared/config.ts';

export default function handler(req: Request) {
  const result = await callApi(config.anthropicApiKey); // typed, validated, guaranteed present
}
```

**One additional trap in serverless: in-memory state doesn't persist.** If you store anything in a module-level variable (a cache, a rate-limit counter, a connection pool), it resets on every cold start and is not shared across concurrent instances. This isn't a config issue per se, but it's the same "serverless doesn't work like a server" family of mistakes. Anything that needs to persist across invocations must be stored externally (database, cache service, etc.).

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Read `process.env` / `os.getenv()` directly throughout code | Centralise in one config module with schema validation | Scattered reads mean no single source of truth, no validation, no typing |
| Hardcode secrets in code | Use environment variables | Secrets in code end up in git history — effectively public forever |
| Use `process.env.NODE_ENV` checks everywhere | Use explicit config values (`env.DEBUG`, `settings.log_level`) | NODE_ENV checks create invisible behaviour differences between environments |
| Skip validation for "obvious" vars | Validate all required vars at startup | "Obviously" set vars are the ones that silently break production deploys |
| Default to production URLs/credentials | Required credentials have no default — fail at startup | Accidentally connecting to production from development is a real incident |
| Commit `.env` to git | Add to `.gitignore`, commit `.env.example` instead | Secrets in git are exploited within minutes by automated scanners |
| Mix secrets into config files | Config files for tunables, `.env` for secrets | Config files might be committed; secrets must not be |
| Re-read env vars on every request | Load once at startup, reuse | Env vars don't change during runtime; re-reading is waste |
| Use `as` assertions on `process.env` (TypeScript) | Parse through Zod schema | Assertions skip validation — you're back to trusting external data |

---

## Deciding for Your Project

When starting a new project, determine:

1. What environment variables are required? (Database, API keys, feature flags)
2. What's a secret vs a tunable? (Secrets in `.env`, tunables in config files)
3. Do you need a config file for tunables, or are env vars sufficient? (Small apps often just need env vars)
4. Are there environment-specific configs? (Usually handled by different env var values, not different config files)
5. What secret manager will production use? (AWS Secrets Manager, Vault, etc.)

---

## Related Topics

- **Config is data integrity** — see [Data Integrity](./data-integrity.md) for the validation boundary concept that applies here
- **When config loading fails** — see [Error Handling](./error-handling.md) for how to structure startup errors
- **Secrets management** — see [Security](./security.md) for production secret storage and rotation
- **Config in deployment** — see [Deployment](./deployment.md) for how environment-specific config is managed across environments
