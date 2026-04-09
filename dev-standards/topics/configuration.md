# Configuration Standards

**Status:** Draft

## Core Principle

Configuration should be centralized, typed, and validated. Follow the established multi-layer pattern from existing projects.

---

## Related Topics

- **Env validation as data integrity**: See [Data Integrity Standards](./data-integrity.md) — environment variable validation is a boundary validation concern
- **Secrets and trust boundaries**: See [Security Standards](./security.md) — what's a secret, how secrets are managed in production

---

## Tier Requirements

### Exploratory

- `.env` file for secrets (gitignored)
- Read environment variables with inline defaults (`os.getenv()` in Python, `process.env` in TypeScript)
- Single env-loading call at entry point (`load_dotenv()` in Python, `dotenv.config()` in TypeScript)

### Internal

- Centralized config loading (single module)
- Typed config models for type safety (Pydantic for Python, Zod for TypeScript)
- YAML or JSON file for domain/tunable settings
- Singleton config loader (Python: `@lru_cache`; TypeScript: module-level `const`)

### Production

- All Internal requirements
- Validate ALL required vars at startup (fail fast)
- Clear error messages listing missing vars
- Environment-specific config files if needed

---

## Established Patterns

### Multi-Layer Configuration

```
Priority (highest to lowest):
1. Environment variables (.env) — secrets, overrides
2. Config file (YAML/JSON) — domain settings, tunables
3. Typed model defaults — sensible fallbacks
4. Code defaults — last resort
```

### Directory Structure

**Python:**
```
project/
├── config/
│   ├── settings.py          # Pydantic models + get_config()
│   └── app_config.yaml      # Domain settings
├── .env                     # Secrets (gitignored)
└── .env.example             # Template for required vars
```

**TypeScript:**
```
project/
├── src/
│   └── config/
│       ├── env.ts           # Zod schema + validated env export
│       └── app-config.ts    # Domain settings loader
├── config/
│   └── app-config.json      # Domain settings (or .yaml with a loader)
├── .env                     # Secrets (gitignored)
└── .env.example             # Template for required vars
```

### Typed Config Models with Defaults

**Python (Pydantic):**
```python
from pydantic import BaseModel, Field

class FetchSettings(BaseModel):
    rate_limit_seconds: float = 0.5
    request_timeout: int = 30
    connect_timeout: int = 10
    max_retries: int = 3
    retry_backoff_factor: float = 2.0

class DatabaseSettings(BaseModel):
    database_name: str = "my_database"
    collections: dict = Field(default_factory=lambda: {
        "items": "items",
        "logs": "logs"
    })

class Config(BaseModel):
    fetch: FetchSettings = Field(default_factory=FetchSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
```

**TypeScript (Zod):**
```typescript
import { z } from "zod";

const FetchSettingsSchema = z.object({
  rateLimitSeconds: z.number().default(0.5),
  requestTimeout: z.number().default(30),
  connectTimeout: z.number().default(10),
  maxRetries: z.number().default(3),
  retryBackoffFactor: z.number().default(2.0),
});

const DatabaseSettingsSchema = z.object({
  databaseName: z.string().default("my_database"),
  collections: z.record(z.string()).default({ items: "items", logs: "logs" }),
});

const ConfigSchema = z.object({
  fetch: FetchSettingsSchema.default({}),
  database: DatabaseSettingsSchema.default({}),
});
type Config = z.infer<typeof ConfigSchema>;
```

### Singleton Config Loading

**Python:**
```python
from functools import lru_cache
from pydantic import BaseModel
import yaml
import os
from dotenv import load_dotenv

load_dotenv()  # Once at module load

@lru_cache
def get_config() -> Config:
    """Load and cache configuration from YAML."""
    config_path = CONFIG_DIR / "app_config.yaml"

    if not config_path.exists():
        return Config()  # Defaults if no config file

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Config(**data)
```

**TypeScript:**
```typescript
import { readFileSync, existsSync } from "fs";
import { ConfigSchema } from "./config-schema";

let _config: Config | null = null;

export function getConfig(): Config {
  if (_config) return _config;

  const configPath = "./config/app-config.json";
  if (!existsSync(configPath)) {
    _config = ConfigSchema.parse({});  // Defaults
    return _config;
  }

  const data = JSON.parse(readFileSync(configPath, "utf-8"));
  _config = ConfigSchema.parse(data);
  return _config;
}
```

### Environment Variable Validation

**Python:**
```python
class MongoDBSettings(BaseModel):
    """Settings loaded from environment."""

    @property
    def uri(self) -> Optional[str]:
        return os.getenv("MONGODB_URI")

    @property
    def db_name_override(self) -> Optional[str]:
        return os.getenv("MONGODB_DB_NAME")
```

**TypeScript:**
```typescript
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  API_KEY: z.string().min(1),
  PORT: z.coerce.number().default(3000),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
});

// Validate at startup — fails fast with clear error if missing
export const env = envSchema.parse(process.env);
```

### Startup Validation (Production)

**Python:**
```python
def validate_required_config():
    """Call at application startup. Fails fast with clear message."""
    required = {
        "MONGODB_URI": os.getenv("MONGODB_URI"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }

    missing = [k for k, v in required.items() if not v]

    if missing:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"See .env.example for required configuration."
        )
```

**TypeScript:**

In TypeScript, the Zod `envSchema.parse(process.env)` pattern above already handles startup validation — if a required variable is missing, it throws a `ZodError` with details. For a friendlier message:

```typescript
import { envSchema } from "./env";

export function validateConfig(): void {
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    const missing = result.error.issues.map((i) => i.path.join(".")).join(", ");
    throw new Error(
      `Missing or invalid environment variables: ${missing}\nSee .env.example for required configuration.`
    );
  }
}
```

### Injectable Service Clients

Create service clients from validated config and pass them to consumers — don't hardcode connection details:

**Python:**
```python
# Good: client created from config, injectable
def create_db_client(config: DatabaseSettings):
    return MongoClient(config.uri)

# Bad: module-level singleton with hardcoded URL
db = MongoClient("mongodb://prod.example.com")
```

**TypeScript:**
```typescript
// Good: client created from config, injectable
export function createDbClient(config: { url: string }) {
  return createClient(config.url);
}

// Bad: module-level singleton with hardcoded URL
export const db = createClient("https://prod.example.com");
```

---

## What Goes Where

| Type of Config | Location | Example |
|----------------|----------|---------|
| **Secrets** | `.env` (environment) | API keys, database passwords |
| **Tunables** | Config file (YAML/JSON) | Rate limits, batch sizes, timeouts |
| **Structural** | Typed model defaults | Collection names, URL patterns |
| **Constants** | Code | Magic numbers that never change |

---

## YAML Config Example

```yaml
# config/parser_config.yaml

fetch:
  rate_limit_seconds: 0.5
  request_timeout: 30
  max_retries: 3

chunking:
  batch_size: 100
  checkpoint_interval: 100

database:
  database_name: "my_app"
  collections:
    items: "items"
    logs: "process_logs"

logging:
  level: "INFO"
  max_file_size_mb: 10
  backup_count: 5
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Scatter env loading across files (`load_dotenv()` in Python, `dotenv.config()` in TypeScript) | Single call at entry point |
| Hardcode secrets in code | Use environment variables |
| Use raw env access everywhere (`os.getenv()` in Python, `process.env.X` in TypeScript) | Centralize in a typed config module |
| Skip validation for "obvious" vars | Validate all required vars at startup |
| Mix secrets into config files | Config files for tunables, `.env` for secrets |
| Default to production URLs/credentials | Required credentials have no default — fail at startup if missing. Only provide defaults for genuinely safe values (localhost, dev ports) |
| Create service clients at module level with hardcoded config | Create clients at the application boundary and pass them to consumers. This enables testing and environment switching |
| Use `as` type assertions on `process.env` values (TypeScript) | Parse through a Zod schema — assertions skip validation |
| Scatter `z.string().parse(process.env.X)` across files (TypeScript) | Single `envSchema.parse(process.env)` in one config module |

---

## Tooling

| Language | Config Library | Validation |
|----------|----------------|------------|
| Python | `pydantic`, `python-dotenv`, `pyyaml` | Pydantic |
| TypeScript | `dotenv`, `zod` | Zod schemas |
| JavaScript | `dotenv`, `joi` | Joi schemas |

---

## Expand During Brainstorming

When starting a new project, discuss:

- What settings need to vary between environments?
- What's a secret vs a tunable?
- Are there environment-specific configs needed? (dev.yaml, prod.yaml)
- Feature flags requirements?
