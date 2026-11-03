# Module Design

> **Calibrate to the context — but note the judgment itself is free.** Choosing a deep
> module over a shallow one costs nothing extra to build — it's the same code, organised
> behind a smaller surface. What *does* scale with need is seam ceremony: ports, adapters,
> and injected dependencies earn their keep only when something genuinely varies across
> the seam (a real second implementation, a test stand-in for a remote service). Default
> to deep modules everywhere; add seams reluctantly. Reference material, not a checklist.

## The Problem

When code gets split into modules, the split itself can create the complexity it was
supposed to manage. The most common failure looks *tidy*: many small files, each with one
small function, each individually "testable" — and understanding one behaviour means
bouncing between six of them, because the logic lives in how they're called, not in any
one of them. Nothing hides anything; every caller has to know everything.

The vocabulary for talking about this precisely comes from several sources.
*A Philosophy of Software Design* (John Ousterhout) gives module, interface, deep and
shallow, information leakage, "design it twice", and "somewhat general-purpose". *Working Effectively with
Legacy Code* (Michael Feathers) gives seam. Ports and adapters come from Alistair
Cockburn's hexagonal architecture. Leverage, locality, the deletion test, the one-adapter
rule, and the dependency categories are house terms that the `improve-codebase-architecture`
skill also uses; this chapter states them in the handbook's form:

- **Module** — anything with an interface and an implementation. Scale-agnostic: a
  function, class, package, or tier-spanning slice.
- **Interface** — everything a caller must know to use the module correctly. Not just the
  type signature: invariants, ordering constraints, error modes, required configuration,
  performance characteristics.
- **Depth** — leverage at the interface. A module is **deep** when a lot of behaviour
  sits behind a small interface; **shallow** when the interface is nearly as complex as
  the implementation it fronts. Depth is *not* a lines-of-implementation-per-line-of-
  interface ratio (that rewards padding) — it's how much a caller can get done per unit
  of interface they must learn.
- **Seam** — the place where an interface lives; a point where behaviour can vary without
  editing code at that point. (For a substitution point, prefer this over "boundary",
  which collides with domain-driven design's bounded context; "trust boundary" keeps its
  usual meaning.)
- **Adapter** — a concrete thing satisfying an interface at a seam. Describes *role*
  (what slot it fills), not substance.
- **Leverage** — what callers get from depth: more capability per unit of interface learned.
- **Locality** — what maintainers get from depth: change, bugs, knowledge, and
  verification concentrate in one place instead of spreading across callers.

**Depth is a property of the interface, not the implementation.** A deep module can be
internally composed of small, mockable, swappable parts — they just aren't part of the
interface. Deep does not mean monolithic; it means the *surface* is small relative to
what it delivers.

```typescript
// SHALLOW — the interface restates the implementation; callers learn nothing less
// than if they'd written the SQL themselves, and every caller repeats the assembly
function getUserRow(id: string): Promise<Row> { /* one query */ }
function rowToUser(row: Row): User { /* one mapping */ }
function getUserPrefs(id: string): Promise<Prefs> { /* one query */ }
// caller: fetch row, map it, fetch prefs, merge, handle each error case itself

// DEEP — one entry point hides fetching, mapping, merging, and the error model
function getUser(id: string): Promise<User>  // throws NotFoundError
```

---

## Before Proposing a Module

Answer these first — a module proposed without them is a shape looking for a purpose:

1. **What problem does it solve?** One sentence. If the sentence is "it wraps X", stop —
   that's a pass-through, not a module.
2. **Who are the callers?** Other modules, external users, tests. The interface is
   designed for them, not for the implementation's convenience.
3. **What are the key operations?** The handful of things callers actually do.
4. **What should be hidden?** The point of the module is what callers *don't* have to
   know. If nothing is hidden, there's no module — just a file boundary.
5. **What does it depend on?** This determines its testing shape — see *Structuring
   Around Dependencies* below.
6. **What constraints bind it?** Performance needs, compatibility, patterns the
   codebase already follows — a good module fits its surroundings.

**Design it twice.** Your first interface idea is unlikely to be the best. Before
committing, sketch at least two *radically different* shapes and compare — the comparison
is where the insight is, and often the winner is a hybrid. The full exercise below pays
for an interface with many callers or one that is hard to reverse (a public API, a shared
library, a persisted format); for a private helper, weighing one alternative in your head
is enough. Useful constraints to force genuine difference between sketches:

- *Minimise the interface* — 1–3 entry points max; maximise leverage per entry point.
- *Optimise the most common caller* — make the default case trivial.
- *Maximise flexibility* — support many use cases and extension (then check it against
  the over-generalization warning below).
- *Design around ports & adapters* — when the module has cross-seam dependencies
  (remote or third-party — see the dependency table below).

Each sketch should be a **complete proposal**, not just a type signature: the interface
*including invariants and error modes*, a usage example showing how callers use it, what
the implementation hides behind the seam, the dependency strategy (which adapters), and
where its leverage is high vs thin. Compare the sketches by depth, locality, and seam
placement. When the user asks for a parallel exploration, the `improve-codebase-architecture`
skill's `INTERFACE-DESIGN.md` is the procedure.

---

## Judging a Proposed Module

Six tests, applicable to your own proposals before anyone else has to review them:

- **The deletion test.** Imagine deleting the module. If complexity simply vanishes, it
  was a pass-through hiding nothing. If complexity reappears in its callers, even one,
  the module was earning its keep. Propose only modules that pass.
- **The interface is the test surface.** Callers and tests cross the same seam. If you
  find yourself wanting to test *past* the interface — reaching into internals — the
  module is probably the wrong shape.
- **One adapter means a hypothetical seam; two means a real one.** Don't introduce a port
  or interface abstraction unless at least two adapters are justified. A test adapter
  counts as the second only for a dependency that cannot run in the suite (remote but
  owned, or truly external, in the table below); a database or filesystem that runs in
  the suite earns no port. Injecting a configured client (a connection pool, an SDK
  instance) is not a port: it avoids a module-level singleton and needs no second
  adapter (see [Configuration](./configuration.md#service-clients-are-built-in-the-composition-root)).
- **Implementation efficiency.** Does the interface shape allow a clean implementation,
  or force awkward contortions inside? An interface that makes the implementation fight
  itself is the wrong interface, however pretty it looks to callers.
- **Ease of correct use vs ease of misuse.** A good interface makes the wrong call hard
  to write — wrong orderings unrepresentable, required steps unskippable. If correct use
  requires remembering to call things in a certain order, the order belongs inside.
  Error modes are interface too: define one out of existence where the caller's goal
  already holds (removing a key that is already absent succeeds), and keep it an error
  where the caller must act differently (see [Error Handling](./error-handling.md)).
- **No information leakage.** One design decision (a file format, a protocol, an ordering
  rule) known by two modules means a change to it edits both. The usual cause is temporal
  decomposition: splitting code by the order things happen (read, then parse, then
  write) rather than by the knowledge each part hides. Move the decision behind one module.

A note on general-purpose vs specialized: Ousterhout's point is that a *somewhat*
general-purpose interface is usually simpler and deeper *now* than a special-purpose one.
His text-editor example replaces `backspace()`, `delete()`, and `deleteSelection()` with
one `delete(range)` that serves all three callers. The functionality stays limited to
current needs; only the interface is general. Beware over-generalization, the opposite
failure — flexibility nobody uses is interface cost everybody pays.

**Shared utilities.** Share a helper when it encodes a rule that must change together
everywhere it is used (a rounding rule, a currency or date format, a tenant check); search
for the existing one before writing another. Code that merely looks alike can stay local
until it proves to be the same rule: a premature shared helper couples callers whose needs
then diverge, and grows flags to serve them.

---

## Structuring Around Dependencies

What a module depends on determines how it's built and tested across its seam:

| Category | Example | Shape |
|----------|---------|-------|
| **In-process** | Pure computation, in-memory state | Merge freely into a deep module; test through the interface directly. No adapter needed |
| **Local-substitutable** | Postgres (in a container via Testcontainers, or PGlite), filesystem (in-memory) | Deepen and test with the stand-in running in the suite. Lead with a real Postgres in a container; PGlite starts faster but runs in JavaScript runtimes only and uses a single connection, so it has no real concurrency or locking. The seam stays internal — no port in the external interface |
| **Remote but owned** | Your own service across a network | Define a **port** at the seam; production gets an HTTP/queue adapter, tests get an in-memory one. The logic sits in one deep module even though it's deployed across a network. Run one interface suite against both adapters so the in-memory one cannot drift from the real one; [Testing](./testing.md) covers the same drift for hand-written HTTP mocks |
| **True external** | Stripe, Twilio — services you don't control | Usually an injected port. Test the production adapter once against HTTP-level mocks (MSW, respx — see [Testing](./testing.md)); modules that use the port may take an in-memory fake. Where the SDK is used in one module only, HTTP mocking alone is enough and no port is needed |

Two disciplines around seams:

- **Internal seams stay internal.** A deep module can have private seams its own tests
  use. Don't expose them through the interface just because tests touch them. Enforce
  it with a check, because a convention alone erodes: package `exports`, the linter's
  restricted-imports rule, dependency-cruiser (TypeScript) or import-linter (Python).
- **Replace tests, don't layer them.** When shallow modules merge into a deep one, the
  old unit tests on the fragments become waste — write tests at the new interface, then
  delete the fragment tests once those interface tests exist. Tests assert observable
  outcomes through the interface and survive internal refactors; a test that breaks when
  the implementation changes without a behaviour change was testing past the seam.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Create pass-through wrappers ("service" that calls the repo that calls the DB, adding nothing per layer) | Collapse layers that add no behaviour; apply the deletion test | Each pass-through layer is interface cost with zero hiding |
| Extract tiny pure functions everywhere "for testability" | Keep behaviour together in a deep module; test through its interface | The real bugs hide in how fragments are called — which nothing tests |
| Add an interface/port with a single implementation "in case we swap it" | Two adapters or no seam | Hypothetical seams are indirection debt; YAGNI applies to abstraction too |
| Design the interface around the implementation's structure | Design it around what callers need to do | Callers shouldn't have to learn your internals to use your surface |
| Expose internals so tests can reach them | Test through the interface; use internal (private) seams if the implementation needs them | Exposed internals become de-facto interface that callers couple to |
| Commit to the first interface idea | Sketch two radically different shapes and compare | The first idea is rarely the best; the comparison surfaces what matters |
| Split modules by technical layer alone (all handlers / all validators / all mappers), or by execution order | Split by concept, so one behaviour lives in one place | Layer-split scatters every behaviour across every layer — no locality; an execution-order split leaks each shared decision into every step |

---

## Deciding for Your Project

1. **Where does behaviour concentrate?** Aim for a handful of deep modules named after
   domain concepts (if a `CONTEXT.md` exists, its vocabulary names the good seams).
2. **Which dependencies cross a network or leave your control?** Those are the only ones
   that need ports. Everything else can be used directly, through an injected client
   rather than a module-level singleton.
3. **What's the test surface?** Decide it when you decide the interface — they're the
   same thing.
4. **Reshaping existing code?** Hunt by friction, not heuristics: where does
   understanding one behaviour mean bouncing between many small modules? Where were pure
   functions extracted just for testability while the real bugs hide in how they're
   called? Where do tightly-coupled modules leak details across their seams? What's
   untested because it's hard to test through its current interface? Apply the deletion
   test to each suspect, pick the candidate where complexity would concentrate most,
   then design its interface twice before touching anything.

---

## Related Topics

- **Front-end boundaries** — see [Front-end Development](./frontend-development.md) for
  applying responsibility and interface depth to components, hooks, and feature state
  without mandatory layers.
- **Testing through the interface** — see [Testing](./testing.md) for the real-database
  setup and HTTP-boundary mocking the dependency categories map onto.
- **Error modes are part of the interface** — see [Error Handling](./error-handling.md);
  what a module throws is something every caller must know.
- **API endpoints are interfaces too** — see [API Design](./api-design.md) for the same
  discipline applied at the HTTP seam.
- **Injected clients** — see [Configuration](./configuration.md) for building a client
  from validated config and passing it in, which is not a port.
- **Failure handling at the seam** — see [Resilience](./resilience.md) for the timeouts
  and retries an adapter wraps around each external call, so its callers need not.
