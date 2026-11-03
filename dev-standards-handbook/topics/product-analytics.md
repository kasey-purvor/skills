# Product Analytics

> **First, does this apply at all?** Product analytics is opt-in: it earns its keep
> when you have paying customers or stakeholders asking "is anyone using X?". If
> neither exists — an internal tool whose handful of users you can just ask — skip
> this chapter. When you do adopt it, start small (5-10 intentional events); the
> privacy rules (no PII in event properties, consent where the law requires it) are
> firm whatever the scale. A product that promises its users anonymity limits what you
> may capture at all: read Identity before adding any call.

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
analytics.capture('deal_stage_changed', { from_stage: 'prospecting', to_stage: 'negotiation' });
analytics.capture('briefing_played');
```

Events should be **intentional** — track specific actions you care about, not everything. "User clicked button" is noise. "User completed onboarding" is signal.

**Name events by one convention, and never rename one.** This chapter uses `object_action`: snake_case, the object first, the verb in the past tense (`report_exported`, `onboarding_completed`). An event's name is effectively permanent, because renaming it splits its history into two events that no chart joins up. So the events live in one typed catalogue (the wrapper below), reviewed like any other code.

### Identity

Anonymous sessions become useful when you link them to a real user:

```typescript
// posthog-js 1.x
// On login — associate all future events with this user
analytics.identify(userId, { role: user.role });

// On logout — break the association
analytics.reset();
```

This lets you answer "what did user X do?" instead of just "what did someone do?" Identify by your internal user ID, not an email: join it to your own user table when you need to know who someone is, and the analytics vendor never holds the address.

**Not where the product promises anonymity.** Anonymous surveys, whistleblowing channels and some health products tell users that what they do there cannot be traced to them. Identifying those users in analytics breaks that promise, and so do properties fine enough to single someone out, such as a small team's group ID or an exact timestamp next to a known submission. On such a surface, never identify the user; capture only coarse, aggregate events around the protected action, or none. People outside the promise, such as the admin who builds the survey, can still be identified.

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
// lib/analytics.ts: posthog-js 1.x
import posthog from 'posthog-js'; // or mixpanel, amplitude, etc.

// The tracking plan: every event and its properties, reviewed like any other code
type AnalyticsEvents = {
  report_exported: { format: 'csv' | 'pdf' };
  filter_applied: { filter: 'stage' | 'owner' };
};

export function initAnalytics(key: string | undefined): void {
  if (!key) return; // no-op without config — safe for dev
  posthog.init(key, {
    api_host: 'https://eu.i.posthog.com',
    capture_pageview: 'history_change', // SPA: count client-side navigations, not just the first load
  });
}

export function identifyUser(userId: string, role: string, tenantId: string): void {
  posthog.identify(userId, { role });
  posthog.group('company', tenantId);  // attach this session's events to the tenant
}

export function resetUser(): void {
  posthog.reset();
}

export function trackEvent<E extends keyof AnalyticsEvents>(event: E, properties: AnalyticsEvents[E]): void {
  posthog.capture(event, properties);
}
```

Why a wrapper: you can swap the provider (PostHog to Mixpanel) by changing one file. You can add global properties (tenant, environment) in one place. You can disable tracking in tests without mocking the library itself. And the event type turns a misspelt name or a missing property into a compile error, instead of a new event in the dashboard.

### 2. Initialise at app boot, gated on config

```typescript
// main.tsx — alongside your error tracking init
initAnalytics(import.meta.env.VITE_POSTHOG_KEY);
```

If the key isn't set (local dev, CI), nothing happens. No conditional logic needed anywhere else.

### 3. Identify on auth state change

Put identity calls alongside your existing error-tracking identity (Sentry, Datadog, etc.):

```typescript
// @sentry/react 8+, posthog-js 1.x
// In your auth context/provider. Skip identifyUser on surfaces that promise anonymity (see Identity)
if (user) {
  Sentry.setUser({ id: user.id });
  identifyUser(user.id, user.role, user.tenantId);
} else {
  Sentry.setUser(null);
  resetUser();
}
```

### 4. Track specific events on top of pageviews

Pageviews are the cheap baseline that weekly-active and retention charts are built from, so keep them, and make sure a single-page app counts client-side navigations (the `capture_pageview: 'history_change'` option in the wrapper). The noise comes from click **autocapture**, which records every click; turn it off or filter it, and capture the actions you care about by name where they happen. A `useEffect` that tracks "dashboard viewed" is a hand-rolled pageview, and it fires twice in development under React StrictMode:

```typescript
// posthog-js 1.x
// In the handler where the action happens
onClick={() => { exportReport(); trackEvent('report_exported', { format }); }}

// A business outcome such as `deal_closed` is captured on the server after commit (step 5)
```

### 5. Capture business outcomes on the server

Views and clicks are captured in the browser, but a business outcome (an order paid, an invitation accepted) is captured on the server after its transaction commits, with the server SDK (`posthog-node`, `posthog-python`). Ad blockers drop a share of browser events, a client can forge them, and a browser event can fire for a write that was rolled back. In a serverless function, `await` the client's `flush()` (or `shutdown()`) before returning, or queued events die with the instance. For what stays in the browser, a reverse proxy on your own domain recovers much of what ad blockers drop.

### 6. Respect privacy boundaries

Don't track on admin/settings pages. Don't track PII beyond what's needed for identity. If you have EU or UK users, data residency is not the GDPR obligation. You need a lawful basis, a data processing agreement with the vendor, and consent before setting non-essential cookies or device storage, which in the EU includes analytics (ePrivacy Directive). UK PECR has exempted analytics used only to improve your own service, by you or a processor, since February 2026, provided users get clear information and a simple, free way to object. The exemption covers aggregate statistics only: tracking individual users, or using the data for anything else such as ad attribution, still needs consent. In code, that means opt-in capture (PostHog's `opt_out_capturing_by_default: true`, then `opt_in_capturing()` once the user consents) or cookieless tracking (`cookieless_mode: 'always'`, or `'on_reject'` behind a banner; it must also be enabled in the project settings). An EU-hosted region is optional: it simplifies international transfers but satisfies none of the above.

---

## What to Track

Start with 5-10 events that answer your most important product questions. You can always add more later.

| Category | Example Events | Why |
|----------|---------------|-----|
| **Activation** | `user_logged_in`, `onboarding_completed` | Are users coming back? Did they finish setup? |
| **Core usage** | `dashboard_viewed`, `report_generated` | Are users engaging with the main value prop? |
| **Feature adoption** | `feature_x_used`, `export_downloaded` | Is a specific feature worth maintaining? |
| **Conversion** | `deal_closed`, `upgrade_started` | Business outcomes |

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Track everything ("track all clicks") | Track 5-10 intentional events that answer specific questions | Noise makes analytics dashboards useless — nobody looks at them |
| Import the analytics library directly in 30 files | Centralise in a wrapper module | Vendor lock-in, no single place to add global properties or disable |
| Auto-capture every click and page without filtering | Track intentional product events; let the SDK own pageviews, and avoid click autocapture noise | Click noise buries the signal, and admin, settings and auth pages may leak sensitive paths, so exclude them |
| Track PII in event properties (full name, address, phone) | Track only identifiers and role/plan metadata | Privacy regulations (GDPR, CCPA) apply to analytics data too |
| Initialise analytics unconditionally | Gate on an env var so dev/CI/test environments don't pollute data, and give staging its own project | Test events mixed with real data ruins every dashboard |
| Skip the identify call | Identify on login and reset on logout, except on surfaces that promise anonymity | Anonymous events can't be attributed to users or accounts; where anonymity is the promise, identifying breaks it |

---

## Deciding for Your Project

1. **Do you need product analytics at all?** If you have paying customers or stakeholders who ask "is anyone using X?" — yes.
2. **Which provider?** PostHog (open-source, self-hostable, EU region), Mixpanel, Amplitude, or a simple custom events table in your database.
3. **Consent and lawful basis?** If you have EU or UK users, decide how capture waits for consent (opt-in or cookieless) and whether the UK exemption covers you, and sign the vendor's processing agreement. EU hosting or self-hosting is optional; it simplifies international transfers.
4. **What 5-10 events answer your most pressing product questions?** Define these before instrumenting. Don't start with "track everything."
5. **Client or server capture?** The browser for interface behaviour (views, clicks); the server, after commit, for business outcomes that must be counted exactly.
6. **Where do identity and group calls go?** Alongside your existing auth/error-tracking identity calls — same lifecycle hooks. If any surface promises anonymity, first decide what may be captured there at all.

---

## Related Topics

- **Not the same as monitoring** — see [Monitoring](./monitoring.md) for system health (metrics, SLOs, alerting). Product analytics answers "are users doing what we hoped?" not "is the server up?"
- **Not the same as logging** — see [Logging](./logging.md) for operational debugging. Analytics events are business-level, not debug-level.
- **Configuration gating** — see [Configuration](./configuration.md#environment-variable-validation) for validating the variable that gates analytics (the gate itself is step 2 above).
- **Personal data** — see the "Don't Log" rules in [Logging](./logging.md#dont-log), which apply to event properties too.
