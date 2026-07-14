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

The vocabulary for talking about this precisely (from *A Philosophy of Software Design*,
Ousterhout, and Michael Feathers):

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
  editing code at that point. (Prefer this over "boundary", which collides with domain-
  driven design's bounded context.)
- **Adapter** — a concrete thing satisfying an interface at a seam. Describes *role*
  (what slot it fills), not substance: a thing can be a small adapter with a large
  implementation (a real Postgres repository) or a large adapter with a small one (an
  in-memory fake).
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
is where the insight is, and often the winner is a hybrid. Useful constraints to force
genuine difference between sketches:

- *Minimise the interface* — 1–3 entry points max; maximise leverage per entry point.
- *Optimise the most common caller* — make the default case trivial.
- *Maximise flexibility* — support many use cases and extension (then check it against
  the over-generalization warning below).
- *Design around ports & adapters* — when the module has cross-seam dependencies
  (remote or third-party — see the dependency table below).

Each sketch should be a **complete proposal**, not just a type signature: the interface
*including invariants and error modes*, a usage example showing how callers use it, what
the implementation hides behind the seam, the dependency strategy (which adapters), and
where its leverage is high vs thin. For a big decision this fans out well — one sub-agent
per constraint, designing in parallel — then compare the results by depth, locality, and
seam placement.

---

## Judging a Proposed Module

Five tests, applicable to your own proposals before anyone else has to review them:

- **The deletion test.** Imagine deleting the module. If complexity simply vanishes, it
  was a pass-through hiding nothing. If complexity reappears across N callers, the module
  was earning its keep. Propose only modules that pass.
- **The interface is the test surface.** Callers and tests cross the same seam. If you
  find yourself wanting to test *past* the interface — reaching into internals — the
  module is probably the wrong shape.
- **One adapter means a hypothetical seam; two means a real one.** Don't introduce a port
  or interface abstraction unless at least two adapters are justified (typically
  production + test). A single-adapter seam is indirection with no payoff.
- **Implementation efficiency.** Does the interface shape allow a clean implementation,
  or force awkward contortions inside? An interface that makes the implementation fight
  itself is the wrong interface, however pretty it looks to callers.
- **Ease of correct use vs ease of misuse.** A good interface makes the wrong call hard
  to write — wrong orderings unrepresentable, required steps unskippable. If correct use
  requires remembering to call things in a certain order, the order belongs inside.

A note on general-purpose vs specialized: general-purpose interfaces handle future cases
without change, but beware over-generalization — flexibility nobody uses is interface
cost everybody pays. Somewhat general-purpose, driven by real callers, is the sweet spot.

---

## Structuring Around Dependencies

What a module depends on determines how it's built and tested across its seam:

| Category | Example | Shape |
|----------|---------|-------|
| **In-process** | Pure computation, in-memory state | Merge freely into a deep module; test through the interface directly. No adapter needed |
| **Local-substitutable** | Postgres (PGLite), filesystem (in-memory) | Deepen and test with the stand-in running in the suite. The seam stays internal — no port in the external interface |
| **Remote but owned** | Your own service across a network | Define a **port** at the seam; production gets an HTTP/queue adapter, tests get an in-memory one. The logic sits in one deep module even though it's deployed across a network |
| **True external** | Stripe, Twilio — services you don't control | Injected port; tests provide a mock adapter (mocked at the HTTP layer — see [Testing](./testing.md)) |

Two disciplines around seams:

- **Internal seams stay internal.** A deep module can have private seams its own tests
  use. Don't expose them through the interface just because tests touch them.
- **Replace tests, don't layer them.** When shallow modules merge into a deep one, the
  old unit tests on the fragments become waste — delete them and write tests at the new
  interface. Tests assert observable outcomes through the interface and survive internal
  refactors; a test that breaks when the implementation changes was testing past the seam.

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
| Split modules by technical layer alone (all handlers / all validators / all mappers) | Split by concept, so one behaviour lives in one place | Layer-split scatters every behaviour across every layer — no locality |

---

## Deciding for Your Project

1. **Where does behaviour concentrate?** Aim for a handful of deep modules named after
   domain concepts (if a `CONTEXT.md` exists, its vocabulary names the good seams).
2. **Which dependencies cross a network or leave your control?** Those are the only ones
   that need ports and injected adapters. Everything else can be direct.
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

- **Testing through the interface** — see [Testing](./testing.md) for the real-database
  setup and HTTP-boundary mocking the dependency categories map onto
- **Error modes are part of the interface** — see [Error Handling](./error-handling.md);
  what a module throws is something every caller must know
- **API endpoints are interfaces too** — see [API Design](./api-design.md) for the same
  discipline applied at the HTTP seam
