# Front-end Development

> **Calibrate to the context.** Start with the application's existing conventions and
> the simplest structure that keeps a user journey understandable and changeable.
> A small screen does not need a state library, component framework, or new layer by
> default. What earns its keep as the product grows is shared structure: one set of
> accessible primitives and design tokens, a query cache with deliberate invalidation,
> and browser journeys that cover each role. Accessibility, truthful feedback, and
> server-enforced permissions hold at any size. The chapter names React mechanisms
> where they decide a design; it is not a framework manual. Reference material, not a
> checklist.

## The Problem

A screen can look correct while its state goes stale, its controls lose keyboard
focus, or a change requires edits across unrelated components. Equally, tidy code
does not prove that a person can find or complete their task. Front-end engineering
has to preserve both the user journey and the boundaries that make it maintainable.

Use this chapter when building or reviewing front-end code. The observable faults a
browser reviewer looks for are catalogued separately, by review lens, in
[Front-end Patterns](./frontend-patterns.md).

**Read selectively:**

| Working on | Start with |
|---|---|
| Components or feature organisation | Component Boundaries and Composition |
| Interactive behaviour | State Ownership; Effects and External Systems |
| Loading, saving, or editing data | Data Loading and Changes; Forms and Recovery |
| Navigation, styling, or shared controls | Navigation and Accessible Interaction; Layout and Visual Consistency |
| Rendering or deployment choices | Framework-Specific Decisions |
| Verification or an existing fault | Testing Front-end Behaviour; Anti-Patterns; the relevant [Front-end Patterns](./frontend-patterns.md) group |

## Component Boundaries and Composition

Group a feature's UI, behaviour, and tests so a change to one user task is local.
Promote a component to a shared location when its meaning and behaviour really are
shared. Similar markup alone does not establish a common abstraction. Follow the
repo's naming and layer conventions; this chapter does not prescribe a directory tree.

A component or custom hook earns its boundary by hiding a coherent responsibility,
owning a meaningful interaction, or providing reuse with a clear contract. A long
file is a reason to investigate, not a rule to split it by line count. Conversely,
many short files are not evidence of good architecture. [Module Design](./module-design.md)
applies directly: a component's props and a hook's return value are its interface, so
judge depth by how much they hide from the caller. The data client or network boundary
is the test seam; control responses there rather than mocking a feature's own hooks.

Separate substantial domain calculations from framework lifecycle when they are
hard to reason about or verify there. Keep trivial rendering expressions local; a
transformation repeated across screens, such as mapping a transport record to what the
screens display, gets one home in the feature or data layer.
Do not manufacture a hook, mapper, service, and presentation component for every
screen just to make each fragment independently mockable. Test the resulting
behaviour through the feature's public interface.

Compose controls with clear responsibilities. Prefer named content slots or small
compositions over a shared component with dozens of interacting mode flags. Start
with the project's existing primitives before creating another dialog, selector,
or form control; a bespoke control inherits keyboard and accessibility obligations.

## State Ownership

Give each piece of information one authoritative owner. Distinguish:

| Kind of information | Usual owner | Decision to make |
|---|---|---|
| Temporary interaction, such as an open menu | Nearest relevant component | Does anyone else actually need to control it? |
| A filter or selected record that must survive sharing and navigation | Route or query parameters | What should Back, refresh, and a copied link restore? |
| Data returned by the application programming interface (API) | Framework data layer or the established query cache | When is it stale, and what invalidates it? |
| An unsaved edit | The form or editing feature | When do newer server values replace, conflict with, or leave the draft alone? |
| A value calculated from other values | Derive from those values | Is storing another copy necessary? |

In React, lift state only as far as its consumers require. Context can carry
genuinely shared state; it does not automatically make every value global.
Store an entity's identifier when selection can be derived from the authoritative
collection. Avoid combinations of booleans that permit impossible states; a small
explicit status such as `editing | saving | failed | saved` can make transitions clearer.
An editing draft is a legitimate separate value when its reset and save behaviour
are deliberate. To start a fresh draft when the edited record changes, give the editing
component the record's identifier as its `key` instead of copying props into state with
an effect. See [React's state guidance](https://react.dev/learn/choosing-the-state-structure).

## Effects and External Systems

Keep rendering free of external side effects. In React, use effects to synchronise
with external systems such as a subscription or browser integration. Derive display
values during rendering; handle an action caused by a user in its event flow.
An effect chain that copies state into more state usually obscures the owner.

When an effect is needed, account for changed inputs and teardown. A slow old
request must not overwrite a newer result. Clean up subscriptions and timers.
Prefer the project's data-loading facilities when they already solve cancellation,
deduplication, and invalidation. Do not suppress dependency checks to conceal an
unclear lifecycle. When part of an effect is really an event the external system fires,
such as a connection callback that reads the current theme, move that part into
`useEffectEvent` (stable from React 19.2). It reads the latest values without re-running
the effect. It is not a way to drop a dependency the effect's own logic needs.
See [React's effect guidance](https://react.dev/learn/you-might-not-need-an-effect).

A custom hook is useful for a named, coherent piece of React behaviour. Extracting
one does not make its state shared between callers, or justify hiding unrelated
network work inside it. See [custom hook guidance](https://react.dev/learn/reusing-logic-with-custom-hooks).

## Data Loading and Changes

Choose the loading boundary to suit the existing router and rendering model. Avoid
forcing every component to fetch for itself or every application to fetch only in
page components; an established repository may deliberately choose either convention.
Keep transport details behind the existing client or data layer and validate
untrusted responses at the appropriate boundary; [Data Integrity](./data-integrity.md)
and [API Design](./api-design.md) own those contracts.

Model initial loading, a background refresh, no matching records, denied access,
and failure as different outcomes. Preserve useful content during a refresh when
safe, and indicate staleness where it affects a decision. A failed request is not
an empty result. Compute a total over the whole dataset on the server; a count taken in
the browser from fetched rows silently stops at the query's row limit. Parallelise
independent work where useful and avoid request chains created only by component nesting.

For a change sent to the server, define pending feedback, repeated submission,
success, failure, and which views need refreshing. An optimistic update—showing
the expected result before the server confirms it—needs recovery and conflict
handling appropriate to the action. It is optional, not the default for every form.
Disabling a button helps the person; it is not the server's duplicate-write protection.
See [Resilience](./resilience.md) for retry and idempotency decisions.

User-specific caches need identity and tenant scoping (put both in the query key), with
a deliberate reset on sign-out or account changes. Hiding a control is not an authorisation check: the
server validates every protected operation. Use server-projected capabilities when
available instead of independently reconstructing permission rules in the browser.
See [Authentication and Authorization](./authentication-authorization.md#enforcement-layers) and
[Multi-tenant Isolation](./multi-tenant-isolation.md).

## Forms and Recovery

Make draft, saved, and saving states distinguishable. Preserve entered values after
a recoverable failure. Put useful validation near the affected field and provide a
way to locate errors in a long form. Client validation helps the person; server
validation remains authoritative. Explain disabled actions where the reason is not apparent.
Web Content Accessibility Guidelines (WCAG) 2.2 criterion 3.3.7 Redundant Entry asks
that, within one process, information the person already gave is offered again or
pre-filled rather than requested twice. Criterion 3.3.8 Accessible Authentication
(Minimum) asks that sign-in not rely only on remembering or transcribing; allow paste
and password managers in credential and code fields.

In React 19, Actions hold much of this state: `useActionState` carries the pending flag
and the last result, `useFormStatus` lets a submit control inside the form read the
pending state to block a duplicate submit, and `useOptimistic` shows the expected result
until the action settles. A `<form action>` resets its uncontrolled fields after every
action, including one that returned validation errors through `useActionState`, which
silently discards the entered values. Return the submitted values from the action and
render them through `defaultValue`, or submit through `onSubmit` inside a transition.

Choose explicit save or autosave deliberately. For autosave, communicate pending,
failed, and confirmed saves and handle edits made while a save is in flight. For
explicit save, keep the action discoverable and handle navigation away from meaningful
unsaved work. Do not warn on every departure from an untouched form.

Decide cancellation and retry behaviour before implementing a success toast.
Expected validation and request errors belong in the interaction. Unexpected render
failures need an appropriate fallback; see [Error Handling](./error-handling.md) for
React error boundaries and framework-specific mechanics. An error boundary does not
replace handling an ordinary failed submission.

## Navigation and Accessible Interaction

Use links for navigation and buttons for actions, with names that describe their
actual result. Support direct entry, refresh, Back, and Forward for meaningful routes.
Preserve relevant filters or selection when returning to a list. Avoid making the
only path to an important view depend on transient state from another screen.
After a client-side route change, move focus to the new view's main heading or announce
its title; the browser does this on a full page load but not on a client-side transition.
Next.js ships a route announcer; React Router does not, so supply one where it is in use.

Prefer native controls or established accessible primitives. Ensure labels, visible
focus, keyboard operation, and status feedback survive composition and responsive
changes. Colour and hover cannot be the only ways to convey essential information.
Do not nest interactive controls inside other interactive controls. A sticky header or
pinned bar, such as a pinned Save or navigation from [Front-end Patterns](./frontend-patterns.md),
must not hide the element that has focus entirely. WCAG 2.2 criterion 2.4.11 Focus Not Obscured
(Minimum), level AA, covers this; keeping it wholly unobscured is 2.4.12, level AAA.

Match focus handling to the interaction: a modal needs managed entry, containment,
Escape to close, and return; a simple disclosure normally leaves focus on its trigger.
A dialog needs an accessible name; a description is optional, and a complex body
announced as one description can be worse.
Follow the [dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) rather
than treating every expandable region as a modal.

For charts, make the metric, unit, time range, population, and active filters
understandable. Provide a usable alternative to essential hover-only information.
An accessible label alone does not make an interactive chart operable.

## Layout and Visual Consistency

Use the existing tokens for spacing, type, colour, and shared layout; agree a small
convention before adding another scale. Keep local feature variation local until
there is a real shared pattern. A reusable component should preserve semantics as
well as appearance.

Let content and supported devices determine breakpoints. Check long labels, meaningful
data volumes, zoom, and short viewports; a desktop screenshot does not prove a layout
fits. At 320 Cascading Style Sheets (CSS) pixels wide, the width in WCAG 2.2 criterion
1.4.10 Reflow (level AA), content must reflow without loss of information or functionality
and without scrolling in two directions, except parts such as a data table that need a
two-dimensional layout. Size full-height panels and sheets with `svh` (or `dvh` when it
must track the bars, at the cost of resizing while the user scrolls) rather than `100vh`.
On a phone, `100vh` is the height with the browser's bars hidden, so the bottom of the
panel sits under them. Preserve relationships when adapting a table: people must still
know which entity a value or action belongs to. Sometimes a scrollable table is the right answer.

A 44-pixel touch target is a design target (WCAG 2.2 criterion 2.5.5, level AAA), not
the level AA threshold, which criterion 2.5.8 sets at 24 by 24 CSS pixels with exceptions
including spacing; see [target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

## Framework-Specific Decisions

Identify the installed framework version and routing mode before applying its
conventions. These notes choose where behaviour belongs; official documentation
supplies version-specific syntax and defaults.

| Environment | What changes the design |
|---|---|
| React | Components render from inputs and state; hooks organise lifecycle behaviour. Do not introduce a global store or custom hook for every concern. |
| Next.js App Router | Choose server/client boundaries deliberately. Keep credentials and privileged access on the server, and mark server modules with `import 'server-only'` so a client import fails the build; pass only intended, serializable data into client components. Interactive state belongs in client code. Client components may also be pre-rendered, so browser-only assumptions during rendering can cause problems. Server Functions (Server Actions) are publicly reachable POST endpoints: each must authenticate, authorise, and validate its arguments, regardless of which page renders the button. |
| Next.js Pages Router | Follow its existing page data-loading and routing conventions. App Router server-component instructions do not apply unchanged. |
| Vite-based React app | Vite supplies development and build tooling; it does not by itself decide routing, caching, or authorisation. Follow the router and data layer actually installed. |
| React Router v7 | Remix merged into it. Identify the mode first: data and framework modes load through route loaders and change data through actions, after which loaded data revalidates; declarative mode has neither, so loading and invalidation belong to components or the query layer. |
| TanStack Router / Start | The router provides route loaders with their own cache and search parameters validated as typed route state; decide whether that cache or a query cache owns server data. Start adds server rendering and server functions, which are public endpoints like Next.js Server Functions. |
| Single-page application (SPA) | Plan direct-link hosting, route restoration, sign-in transitions, and client-cache lifetime. This deployment/rendering choice is not synonymous with Vite. |

In Next.js, check the installed version's fetching, caching, and revalidation
behaviour rather than relying on remembered defaults. See [server and client components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
and [fetching data](https://nextjs.org/docs/app/getting-started/fetching-data).
In Vite, exposed client environment values are built into client code; the default
`VITE_` prefix does not make a value secret. See [environment variables](https://vite.dev/guide/env-and-mode).
Next.js inlines `NEXT_PUBLIC_` values at `next build`, so an image promoted from staging
to production still carries the values it was built with; read a per-environment public
value on the server at request time and pass it down. [Configuration](./configuration.md#build-time-vs-runtime-configuration) owns
build-time versus runtime configuration, and [Deployment](./deployment.md#environment-promotion) the promotion.

## Testing Front-end Behaviour

Test through the interface that matters. A component test can verify labels, keyboard
interaction, validation, and state transitions; a browser journey verifies routing,
layout, session integration, and completion across screens. Test substantial pure
calculations directly when useful, without making every render expression an exported
utility. See [Testing](./testing.md) for suite organisation and dependency handling.

Run an automated accessibility scan as the cheap baseline: `@axe-core/playwright` inside
browser journeys, and an axe matcher at component level in a jsdom environment
(`jest-axe`, or its Vitest fork `vitest-axe`, whose README warns it does not work under
happy-dom). A component scan under jsdom skips colour contrast, which only the browser
scan measures. No clean scan covers focus order, whether accessible names are accurate,
or keyboard operation, so those still need a keyboard pass.

Prefer queries by role and accessible name, and wait for observable state instead
of fixed delays. Exercise the failure and recovery paths the change actually touches.
Use controlled network responses where appropriate in automated tests, but keep that
distinct from a browser-only review of the deployed product. Screenshots prove a
visible state; behaviour needs an action and an observed outcome. See
[Playwright's testing guidance](https://playwright.dev/docs/best-practices).

Check performance when evidence warrants it: rendering cost, request waterfalls,
large lists, and unnecessary client code affect different things. Measure before
adding memoization or virtualization, and verify that the change preserves keyboard
access, focus, and understandable navigation. Measuring includes checking whether React
Compiler is enabled: with Compiler 1.0 it memoizes components and hooks automatically,
so new code needs no manual `useMemo`, `useCallback` or `memo` for performance. Keep
existing ones unless removing them is tested, and keep them where a value is an effect
dependency.

## Anti-Patterns

| Don't | Do instead | Why |
|---|---|---|
| Split every screen into mandatory hook/mapper/service/view files | Introduce boundaries for coherent responsibilities and real reuse | File count does not measure maintainability |
| Copy server data, selection objects, and computed values into multiple states | Choose an owner and derive the rest; model drafts deliberately | Copies drift and obscure which value wins |
| Chain effects to implement user actions or derived values | Keep the action in its event flow and calculations in rendering | Each link renders a stale intermediate value, and an effect re-runs on remount or a dependency change, so the action can fire twice |
| Treat failed reads as empty lists | Distinguish failure, loading, denial, and empty results | Users need different recovery actions |
| Consider a hidden button sufficient permission enforcement | Enforce access on the server and use capabilities for presentation | The browser is not the authority |
| Build another generic control before checking existing primitives | Reuse or compose the established accessible control | Behaviour and accessibility are part of reuse |
| Apply App Router conventions to every React application | Identify the project's actual framework, router, and version | Similar-looking projects can have different execution models |
| File a visual defect solely from a pattern checklist | Observe the actual state and consequence | A heuristic is a lead, not a verdict |

## Deciding for Your Project

1. Which user journeys and devices matter, and what conventions are already settled? (Follow the settled conventions; probe the sizes in [Front-end Patterns](./frontend-patterns.md).)
2. Which rendering model and router are in use? Where does trusted data access belong? (Identify the installed version first; credentials and privileged access stay on the server. See Framework-Specific Decisions.)
3. Who owns each interaction, route state, server value, and editable draft? (One owner each, by the State Ownership table; derive the rest.)
4. Which components genuinely share meaning, and which only share appearance? (Share meaning and behaviour, not markup; see Component Boundaries and Composition.)
5. How do loading, saving, failure, cancellation, and return navigation behave? (Each is a distinct designed outcome; see Data Loading and Changes and Forms and Recovery.)
6. Which accessibility and realistic-data states must be verified for this change? (An automated scan plus a keyboard pass over changed controls, and the empty, one, many, and failure states.)
7. What observable tests and browser evidence would reveal a regression? (A component test for the interaction and a browser journey for anything that crosses screens; see Testing Front-end Behaviour.)

## Related Topics

- [Front-end Patterns](./frontend-patterns.md) — observable interface faults by review lens, with browser checks and probe sizes.
- [Module Design](./module-design.md) — responsibility, interface depth, and useful extraction.
- [API Design](./api-design.md) and [Data Integrity](./data-integrity.md) — contracts and validation boundaries.
- [Authentication and Authorization](./authentication-authorization.md) and [Security](./security.md) — permission enforcement, server-projected capabilities, and protection of sensitive data.
- [Multi-tenant Isolation](./multi-tenant-isolation.md) — the tenant boundary the server enforces, which client cache keys must mirror.
- [Resilience](./resilience.md) — retries and idempotency behind a repeated submission.
- [Error Handling](./error-handling.md) — expected failures and unexpected render failures.
- [Logging](./logging.md) — its front-end section: reporting browser errors to an error tracker rather than the console.
- [Product Analytics](./product-analytics.md) — client events and pageviews in a single-page application.
- [Testing](./testing.md) — verification strategy and test organisation.
- [Configuration](./configuration.md) and [Deployment](./deployment.md) — public client configuration and deployed behaviour.
