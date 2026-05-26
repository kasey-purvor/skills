# Product Analytics

## The Problem

Observability (logging, metrics, traces) tells you whether the system is healthy. Product analytics tells you whether anyone is *using* it.

Without product analytics, you can't answer basic questions about your own product:

- How many users logged in this week?
- Which features are actually used vs. silently ignored?
- Did the feature we shipped last sprint change any behaviour?
- Which tenant is getting the most value? Which one might churn?

These questions matter for business decisions, client success conversations, and prioritising what to build next. You can extract some answers from database queries, but retroactively querying your production database for usage patterns is slow, error-prone, and misses the user's journey (the *sequence* of actions, not just the counts).

---

## Core Concepts

### Events

Product analytics tracks named events with properties. An event is "a user did something":

```typescript
// Event: what happened
// Properties: context about what happened
analytics.capture('dashboard_viewed', { role: 'rep' });
analytics.capture('pipeline_move', { from_stage: 'prospecting', to_stage: 'negotiation' });
analytics.capture('briefing_played');
```

Events should be **intentional** — track specific actions you care about, not everything. "User clicked button" is noise. "User completed onboarding" is signal.

### Identity

Anonymous sessions become useful when you link them to a real user:

```typescript
// On login — associate all future events with this user
analytics.identify(userId, { email: user.email, role: user.role });

// On logout — break the association
analytics.reset();
```

This lets you answer "what did user X do?" instead of just "what did someone do?"

### Groups

If your product has organisations, tenants, or teams, group users so you can filter analytics by account:

```typescript
// Associate this user's session with their tenant
analytics.group('company', tenantId, { name: 'Acme Corp', plan: 'enterprise' });
```

This lets you answer "how is Acme Corp using the product?" without querying individual users.

---

## Implementation Pattern

### 1. Centralise in a wrapper module

Don't scatter analytics calls through your codebase with direct library imports. Create a thin wrapper:

```typescript
// lib/analytics.ts
import posthog from 'posthog-js'; // or mixpanel, amplitude, etc.

export function initAnalytics(key: string | undefined): void {
  if (!key) return; // no-op without config — safe for dev
  posthog.init(key, { api_host: 'https://eu.i.posthog.com' });
}

export function identifyUser(userId: string, email: string): void {
  posthog.identify(userId, { email });
}

export function resetUser(): void {
  posthog.reset();
}

export function trackEvent(event: string, properties?: Record<string, unknown>): void {
  posthog.capture(event, properties);
}
```

Why a wrapper: you can swap the provider (PostHog to Mixpanel) by changing one file. You can add global properties (tenant, environment) in one place. You can disable tracking in tests without mocking the library itself.

### 2. Initialise at app boot, gated on config

```typescript
// main.tsx — alongside your error tracking init
initAnalytics(import.meta.env.VITE_POSTHOG_KEY);
```

If the key isn't set (local dev, CI), nothing happens. No conditional logic needed anywhere else.

### 3. Identify on auth state change

Put identity calls alongside your existing error-tracking identity (Sentry, Datadog, etc.):

```typescript
// In your auth context/provider
if (user) {
  Sentry.setUser({ id: user.id, email: user.email });
  identifyUser(user.id, user.email);
} else {
  Sentry.setUser(null);
  resetUser();
}
```

### 4. Track specific events, not pageviews

Automatic pageview tracking captures noise. Manual event tracking captures signal:

```typescript
// In the component or handler where the action happens
useEffect(() => { trackEvent('dashboard_viewed', { role }); }, []);

// In a mutation's onSuccess callback
onSuccess: () => { trackEvent('deal_closed', { value: deal.value }); }
```

### 5. Respect privacy boundaries

Don't track on admin/settings pages. Don't track PII beyond what's needed for identity. If you have EU users, use an EU-hosted region for GDPR data residency.

---

## What to Track

Start with 5-10 events that answer your most important product questions. You can always add more later.

| Category | Example Events | Why |
|----------|---------------|-----|
| **Activation** | `login`, `onboarding_completed` | Are users coming back? Did they finish setup? |
| **Core usage** | `dashboard_viewed`, `report_generated` | Are users engaging with the main value prop? |
| **Feature adoption** | `feature_x_used`, `export_downloaded` | Is a specific feature worth maintaining? |
| **Conversion** | `deal_closed`, `upgrade_started` | Business outcomes |

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Track everything ("track all clicks") | Track 5-10 intentional events that answer specific questions | Noise makes analytics dashboards useless — nobody looks at them |
| Import the analytics library directly in 30 files | Centralise in a wrapper module | Vendor lock-in, no single place to add global properties or disable |
| Auto-capture pageviews without filtering | Use manual event tracking or configure exclusion rules | Admin pages, settings, auth flows add noise and may leak sensitive paths |
| Track PII in event properties (full name, address, phone) | Track only identifiers and role/plan metadata | Privacy regulations (GDPR, CCPA) apply to analytics data too |
| Initialise analytics unconditionally | Gate on an env var so dev/CI/test environments don't pollute data | Test events mixed with real data ruins every dashboard |
| Skip the identify call | Always identify on login, reset on logout | Anonymous events can't be attributed to users or accounts |

---

## Deciding for Your Project

1. **Do you need product analytics at all?** If you have paying customers or stakeholders who ask "is anyone using X?" — yes.
2. **Which provider?** PostHog (open-source, self-hostable, EU region), Mixpanel, Amplitude, or a simple custom events table in your database.
3. **EU data residency?** If you have EU users, choose a provider with EU hosting or self-host.
4. **What 5-10 events answer your most pressing product questions?** Define these before instrumenting. Don't start with "track everything."
5. **Where do identity and group calls go?** Alongside your existing auth/error-tracking identity calls — same lifecycle hooks.

---

## Related Topics

- **Not the same as monitoring** — see [Monitoring](./monitoring.md) for system health (metrics, SLOs, alerting). Product analytics answers "are users doing what we hoped?" not "is the server up?"
- **Not the same as logging** — see [Logging](./logging.md) for operational debugging. Analytics events are business-level, not debug-level.
- **Configuration gating** — see [Configuration](./configuration.md) for the env-var gating pattern that keeps analytics out of dev/test.
- **Privacy and security** — see [Security](./security.md) for PII handling and data residency considerations.
