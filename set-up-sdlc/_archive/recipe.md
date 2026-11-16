# The recipe: what we worked out

A record of what Kasey decided on 11 Nov 2026 about how a repo and its software lifecycle should
be set up, why, and what is still open. **This is not the recipe itself.** It is the source a
later agent turns into step-by-step instructions. It is written as findings and decisions, not as
instructions to an agent.

Each chapter has three parts: **Decided**, **Why** (the evidence), **Open**.
"ADR" means an architecture decision record: a file under `docs/adr/` recording one decision.

Chapters: 1 how the recipe runs · 2 look before you ask · 3 the context files · 4 the agents file ·
5 git workflow · 6 CI/CD and environments · 7 the tracker · 8 checks that guard the context files ·
9 reviews and wrap-ups · 10 what every agent loads.

---

## 1. How the recipe runs

**Decided**
- The setup skill is renamed `set-up-sdlc`. It becomes the lifecycle recipe as well as the setup procedure, and any agent can read it as a reference at any time.
- It is scripted like a skill. At each step the agent looks, reports what it found, and asks before acting.
- It must not say "take what you need and leave the rest". That invites laziness.
- Kasey marked the context files (chapters 3 and 4) rigid; git workflow and CI/CD flexible; the tracker a one-liner; the checks mandated or strongly urged (chapter 8). The rest carry no mark.
- Each chapter says plainly what in it is not decided yet. There is no separate "not decided" chapter.
- There is no "changing it later" chapter. Kasey changes the lifecycle himself, in his own session. The rules for updating context files live in chapter 3.
- Not one big file in the end: one file per chapter behind a short front page. Kasey reviews each chapter as it is written.
- Existing repos are not changed by this work.
- No overlap with `dev-standards-handbook`. Direction agreed: the handbook holds general standards and options; the recipe records which one a repo takes. Exception (17:37): the three CI/CD subjects (stages, data, triggers) go in chapter 6.
- No hard numeric limits anywhere in the recipe. Agents follow them blindly and hack round them.
- The setup is tied to one agent tool no more than necessary, so Kasey can move away from it.
- Six mechanisms: instruction files, skills, git checks, scheduled runs, harness hooks, Linear. Built in that order, as Kasey expects, instruction files and skills first. No checks, hooks or scheduled runs are built now (16:35).

**Why**
- The old setup skill wrote the `## Agent skills` block and the domain file, and seeded the template's shared half when `AGENTS.md` was missing. For the repo's own half, its only instruction was "write the repo's own sections".
- Its upgrade notes told a re-run to copy three named pieces. Agents copied exactly those, so every repo's copy differs from the template in a different way.
- A bulk run across repos skipped every step that needed the human.

**Open**
- Whether a re-run of setup only reports what differs from the template and never overwrites. Proposed, not confirmed. A repo's own text may be worth keeping.

## 2. Look before you ask

**Decided**
- Setup looks at the organisation's other repos for its conventions before asking the human for everything.
- It may find those repos by itself. It then asks which ones it may read.
- The workflow must work in more than one organisation. Nothing that belongs to one organisation is stated as universal.

**Why**
- Kasey works in three organisations with three ways of working.
- Rules that were treated as universal turned out to be one organisation's: a branch that can be pushed only once; who may merge; whether worktrees are allowed at all; whether new markdown files are blocked; which file holds the agent instructions.

**Open**
- Taking on a repo that is already live: how far to change it to fit this layout, and how far to adapt to what is there. Needs thought.

## 3. The context files (rigid)

A context file is a markdown file that agents and people read to understand a project. Not code, not a ticket.

**Decided: the files and what each holds**
- `AGENTS.md`: what every session needs before any task. Chapter 4.
- `docs/agents/domain.md`, the domain file: the map of the context files, what each is for, and the tests for adding to each, in full. `AGENTS.md` carries a short map, the ask-first section (chapter 8) and a pointer here.
- `CONTEXT.md`: the vocabulary. Each term of the product's domain and what it means. Nothing about how things are built.
- `docs/adr/`: one ADR per ruling that is hard to reverse, surprising without context, and came from a real choice between options.
- `docs/decisions.md`: rulings the human made that no ADR covers, one line each.
- `docs/pitfalls.md`: traps in this repo that cost an agent time and will recur, one line each.
- The handbook's `environment.md`: traps in tools and machines every repo shares.
- The handbook's `pitfalls.md`: named mistakes in code that can happen in any repo.
- `README.md`: what the project is and how to get started, in the ordinary sense. Left alone. It is not a dumping ground: text moved out of `AGENTS.md`, such as how the code is built, does not go there.

**Decided: what is not a context file**
- A script's manual lives in the script: its header, help text and error messages.
- One-time work stays on its ticket once done.
- Task how-tos do not go in `AGENTS.md`.

**Decided: the rules**
- The rules for writing every context file are stated once, in one place, not scattered across skills.
- The rules for each context file cover changing and removing lines as well as adding them.
- The specific files take precedence over any catch-all. Something that fits an ADR, the vocabulary, decisions, pitfalls or a handbook chapter goes there first.
- An agent asks the human first, every time, with no exceptions: for every new context file or folder for them, every new ADR, every planning document, and every decisions or pitfalls line. Code files and folders are free. This binds agents working in a product repo, not sessions where the human is redesigning the rules.
- The ask-first rule is widened (12 Nov): it covers any change to any context file, not only new files and lines, and any idea for a new way of preserving context. The one exception is an ADR: a change whose exact wording is in a ticket or plan the human approved is landed without a second ask. No other context file may be changed that way (Kasey, 12 Nov).
- The first versions of these rules will not be perfect. They are still controlled centrally.

**Decided: ADRs**
- An ADR holds three things: the ruling, the reason, and the options turned down.
- It does not describe the code, carry measurements or tell a ticket's story. Test for a sentence: would it still be true if the code were rewritten another way?
- The ruling sits at the top and is rewritten when it changes, never added to. Whoever changes an ADR updates the top in the same edit.
- The plan carries the exact new wording of a ruling. The builder lands it unchanged.
- Builders may change an ADR. Forbidding it would mean more questions for the human. Kasey: it depends how much the human wants to be in the loop.
- A ruling lives in one place. `docs/decisions.md` is for rulings that have no ADR; it may point at an ADR, but never extends one.
- No ADR rule depends on sorting ADRs by type. The review's privacy and security carve-out is rejected.


**Decided: made at setup (16 Nov)**
- Setup creates every context file and folder up front, in one shot, with a script (`set-up-sdlc/scripts/create-context-files.sh`): `CONTEXT.md`, `docs/adr/`, `docs/decisions.md`, `docs/pitfalls.md` and `docs/agents/domain.md`. It creates only what is missing and never overwrites. This replaces creating each file later, when an agent first has something to write, so that no agent needs to create a context file again.
- The rules file is rewritten in its new form at `set-up-sdlc/domain.md`, and the script copies it into the repo. It was drafted from this chapter. Where this chapter is still open it keeps the old rule: the line shapes for decisions and pitfalls, and `session-wrap-up` as the only route for those lines. Two old rules are gone: a pitfall no longer graduates into `AGENTS.md`, and the fifteen-minute threshold for a pitfall is dropped as a hard number. Kasey has not read it yet.
- Still pointing the old way: `grill-with-docs` says to create these files lazily.
**Why**
- In every place examined, the rule for creating something was fine and the rule for changing it was missing. So files only grew.
- ADRs in one repo: 34 files, about 154,000 tokens, the largest about 21,600 with 23 dated amendments. 167 commits changed an existing ADR, 113 of them alongside code. About half the added text describes how things were built.
- Of 135 changes that altered or extended a ruling: a human decided 84, a ticket or planning document scheduled 38, and 13 show no evidence of anyone deciding. One amendment credits the human with a decision an agent made.
- No skill says who may change an ADR. The habit came from planning documents that schedule an amendment inside a build step, tickets that list it as a deliverable, and orchestrators copying it into builders' instructions.
- The tops of large ADRs went stale: one title still gives a threshold the code changed.
- The other repo writes a short new ADR and marks the old one as replaced. Its ADRs stayed small: largest about 4,100 tokens.
- The rules for these files sat in at least six places (the assistant's own count, not from a report), and two copies of one rule already disagreed.
- The one place is for the human, who has to manage the rules. The domain file holds them so that `AGENTS.md` stops growing.
- When pitfalls were first seeded from old transcripts, the rules turned nothing away: 8 lines in two repos reduced to 1 line, 2 sentences of instructions and 2 tickets under a strict test.

**Open**
- Where the leftover goes when no file accepts it: the ticket, a Linear team document, or nowhere.
- Runbooks, meaning step-by-step procedures for rare, risky operations. Kasey leans against allowing them: he does not like context explosions, and runbooks record workarounds that good design would remove. Only 6% of one repo's runbook lines are true procedures. A small review of the genuinely useful ones comes first.
- Who writes decisions and pitfalls lines. Today only the session wrap-up proposes them.
- The tightening proposed for pitfalls: a line must be still true, likely to recur, not already said anywhere an agent reads, and not cheaper to fix at its source; and "an agent's word" stops counting as a source. The numeric caps in that proposal are dropped.
- The exact line shapes for decisions and pitfalls.
- For ADRs: the form of the ruling at the top (the review tested a short header at 300 to 410 tokens against 13,000 to 21,000 for the whole file); a one-line index of all ADRs (about 1,240 tokens); writing honestly who decided; and whether a reversal gets a new ADR.
- Whether every repo's domain file is identical.
- A review to find every place the context-file rules are stated today.

## 4. The agents file (rigid)

**Decided**
- `AGENTS.md` is the central place. It is not the only file agents can be made to load.
- It carries a map of the context files. People read it too.
- It was to be designed first (16:01). Its structure is now deferred, together with where the global git and CI rules go (chapter 5).
- First-draft test for its repo-specific part, to revisit: every session needs it; it is a short rule or fact; it will stay true; nothing else says it; the other homes were offered it first.
- First draft, agreed alongside that test: a ticket may add a never-do rule and a pointer, never a section. Overtaken on 12 Nov: only an ADR may be changed through a ticket or plan, so any change to this file is asked first (chapter 3).
- No line or size budget for any part of the file. The reviews' 150-line, 12 KB budget is rejected.
- The half copied identically into every repo goes away (12 Nov). The whole file belongs to the repo, in sections that setup fills by asking. General lifecycle procedure lives in skills, one copy. Kasey: the copied half no longer fits, because the point is a flexible git and CI/CD setup that opens a discussion.
- The file is a skeleton that works in any organisation, with the details guided at varying strictness (12 Nov).
- Its sections are split by whether they are rigid (the same in every repo) or flexible (filled by setup). Sections may be grouped under a heading; they need not sit at one level.
- Two rigid sections are agreed: the session-level skills this workflow uses (such as `linear`, `stream`, `grill-with-docs`, `to-prd`, `to-issues`, `handoff`, `session-wrap-up`; not the background ones a builder uses, such as test-driven development), and the context files.
- The flexible part covers how work is done (git, reviews, merging) and CI/CD. Whatever is left is reviewed after those and slotted into a section or given a new one.
- The file reads for a human (12 Nov): similar things grouped together, tables where they help, plain sentences. A first draft ordered by the path of one change and written as slots to fill was rejected as unreadable.
- Its sections, in order, as they stand in the worked example (16 Nov): house rules; the skills, in a table that says what each is for and who uses it; the subagents, in a table that says what each does and what it works from; the context files, in a table, with the ask-first rule; how work is done (tickets, worktrees, then the two flows, with a stream as an optional way to run several tickets); git and CI/CD (the environments, the picture of the route and its gates, why each gate exists, the grid of what each gate demands, the tests, test data and logins); and about this repo.
- How work is done has two modes, deciding what to build and building. It says who does the work (the agent, or subagents, which it names), that product work always has a ticket and the `linear` skill holds the rest, and how worktrees are used to run work in parallel. It does not describe a ticket's stages.
- References run one way: the agents file points at skills, and a skill does not point at a section of the agents file. Kasey: two-way references become spaghetti. The `linear` skill is re-reviewed against this at the end.
- A section of house rules is a compulsory part of the template, put into every repo's file unchanged (12 Nov). It opens with the old template's paragraph on quality ("This codebase will outlive you") and holds the rules for how agents are run: which model subagents use (Opus at extra-high effort for code work, or Sol at extra-high on Codex; Sonnet for research and non-code work, or Luna on Codex), that routine reviews start without asking, that each round of review fixes goes to a fresh agent, that nothing credits an AI, and that a credential is never printed. The ask-first rule stays in the context files section. Added 16 Nov: the check with other sessions before starting a ticket, moved out of the `stream` skill, where it had made every ticket load a skill that is otherwise about streams. The rules for review findings still live in `stream` and still apply to a lone ticket.
- The old template's check for resuming a worktree is dropped. Kasey: it is old, and that does not really happen.
- The last section, about the repo itself, holds the tech stack and the key facts every session needs that the repo does not show for itself. It is not forced into a fixed form to stop dumping: the ask-first rule, and later the checks on context file changes, are the protection (Kasey, 12 Nov). A map of the folders is left out.
- A worked example using one repo's current rules is at `set-up-sdlc/AGENTS-example.md`. It stays a demo of that one repo for now. Later the setup becomes a grilling-style skill that works from the demo (Kasey, 12 Nov).
- Each section is one of two kinds (16 Nov). **Fixed**: the same words in every repo, a few with one blank the repo fills (the product's one-line description; the Linear team and prefix; the worktree folder, branch pattern and install command; the stack table; where test logins and fixtures are). **Discussed**: a real decision made with the repo's creator, which changes as the project grows (the environments; the gates and what each demands; the tests and which gate runs each; the rules that hold across the code). Tickets is fixed: the team and prefix are its only blank, and the `linear` skill holds the rest. The building steps are fixed in shape, and the wording of three of them (when to push, who merges, where the change is proved) follows from the gate decisions, so they are written last and nothing new is asked.
- The template itself records which kind a section is, by how it is written: a fixed section is written out in full; a discussed section is only its heading and a line pointing at its guide. There is no separate list of kinds.
- The setup skill's files (16 Nov): `SKILL.md`, the steps the agent follows with the user; `AGENTS-template.md`, as above; `section-guide.md` (first called `discussed-sections.md`), which covers every section that is not a plain copy: how each blank is filled, and for each discussed section what must be decided and the shape of the answer, taking options from the handbook's git and CI/CD topic; `AGENTS-example.md`, the finished demo, for shape only. This record is not loaded by the skill. The old `AGENTS-portable-template.md` goes.
- The skill's steps, agreed in outline: look at the repo before asking; draft the fixed part and fill its blanks, asking only for one it could not find; discuss the discussed sections one at a time, each question with a recommendation; write the building steps last; show the whole file and wait for a yes before writing it.

- Keeping the file true is one general rule, not a rule for each case (Kasey, 16 Nov, late): "we are never going to be able to add specific rules for every scenario... why don't we just add a line somewhere? maybe a house rule? maybe even rely on the session wrap up a little bit?" Three changes. A new house rule, "This file": if something you learn or change makes a line untrue, or the setup stops fitting the project, tell the human, and do not change the file yourself. A fifth thing `session-wrap-up` looks for: lines in the repo's agent instructions that the session made untrue or out of date, proposed as edits, or as a suggestion to run setup again. And the table of triggers no longer goes into a repo's file, which keeps only its stage line; the table stays in `git-and-cicd.md` for setup when it is run again. This overtakes the stage block with triggers decided earlier the same day (chapter 6).
**Why**
- The repo-specific part is the main dumping ground. In two repos, about 80% and 85% of it is not needed by every session: 741 lines against about 140 needed, and 484 against about 70.
- It grows a paragraph per ticket and nothing comes out. One file grew seven times over in four months.
- Most of it copies a runbook, a script header or the handbook, and the copies now disagree. Each repo had about a dozen stale or wrong claims.
- Causes: the template's only guidance was a list of sections to write, with no test; planning documents listed "`AGENTS.md` gains a section" as a deliverable; code and error messages cite its sections by name, so they can only be added to; the pitfalls rule sent a graduated trap into it.
- Every Claude subagent loads it automatically, so every line is paid for by every agent on every task.
- The half meant to be identical in every repo is about three quarters git, pull request and CI rules that belong to one organisation. Every repo has drifted from the template, and one has 83 lines of its own text inside that half.

**Open**
- Its sections. The earlier three-part proposal (true everywhere, one organisation, one repo) is overtaken by dropping the copied half. Being worked out in a grilling session started 12 Nov.
- Where each piece of procedure in today's copied half goes once that half is dropped.
- What is written out and what is pointed at. Kasey: pointing is fine, but the file may become a mapping document; look at past cases first.
- Whether anything in the repos' own top halves is worth lifting into the template.

## 5. Git workflow (flexible)

**Decided**
- Every organisation differs, so this chapter offers options and asks. Setup discusses the workflow with the human and writes it down.
- Good textbook options should be on offer.
- What is flexible is narrower than first thought (12 Nov): the number of environments, how a change is promoted to production, and the git settings and restrictions a repo applies. Ticketing is not flexible (chapter 7).
- Setup covers creating the repo and putting its git rules in place. The same goes for CI/CD and environments (chapter 6).
- One organisation's git, CI/CD and merge rules come out of the global files. Code behaviour does not live there (standing since 3 Nov).
- What is in the global files is sorted three ways (12 Nov): a procedure goes in a skill, one copy; a repo's choices go in that repo's `AGENTS.md`, written by setup as short lines; what is about the person or their machine stays in their global file.
- Setup never changes anyone's global file. Someone else using this setup gets their version of these rules from the recipe and the repo.
- How the person runs subagents stays in Kasey's global file and is also written into the recipe as its default. The duplication is accepted. His defaults (12 Nov): never Fable for a subagent unless he asks; Opus at extra-high effort by default; Sonnet for research and other work that is not about code.
- Anything that is part of the software lifecycle does not stay global (12 Nov). The shared review workflow (routine reviews start without asking when work is ready for review) is lifecycle, so it leaves the global file.
- Leaves the global file and becomes a question setup asks and writes into the repo: whether agents may merge their own pull requests; branch and worktree naming; file and code naming conventions.
- Stays global and outside the recipe: communication style, approved acronyms, links to files, pane notes, notifications, visual previews, the test inbox, web search, browser driving, messaging between sessions, the shared docs folder and the machine file. Kasey considered adding some of these to the recipe and set it aside as scope creep.
- The approving review done under a colleague's token stays global. Kasey: it is a hack and not part of any lifecycle.
- The fresh-fixer rule (a new agent for each round of review fixes) leaves the global file, with the review workflow.
- "Never attribute work to the agent" stays global and is also written into the recipe as its default, like the subagent rules.

**Why**
- The global instruction files state one way of working for every organisation. They give agents standing permission to merge their own pull requests and say this overrides a repo's "never merge yourself"; the template and the repos say the opposite.
- The copies disagree on other points too: the worktree folder name, the number of reviewers, whether a full local check runs before a push.
- The global files cost about 9,850 tokens in every Claude session and subagent. About 53% is lifecycle process, session bookkeeping or tool how-tos that could load only when needed.

**Open**
- The wording of each line setup writes into the repo for the rules that left the global files, and which skill holds each procedure.
- The global-files review proposes that what stays global becomes a short shared file about Kasey plus a machine file.
- The actual content of the example's git section. Its format is agreed (12 Nov): rules a machine checks, then rules that rest on the agent. Kasey is planning a new git setup with another agent, and wants the two pieces of work brought together to record an ideal demo.
- Reversed 16 Nov, see chapter 6: the file below moved out of the handbook into this skill's folder. As first decided: Git and CI/CD practice lives in one topic file in the handbook, `dev-standards-handbook/topics/git-and-cicd.md`, listed in the handbook's router, and not in a separate git skill (16 Nov). A first draft was wrongly put inside this skill and moved the same day: Kasey had asked for a topic, not a skill. It holds the options, the reasons and the steps that install things, and it absorbs the `setup-pre-commit` skill. Kasey: related things stay in one place, which stops agents scattering them and lets people keep the whole thing in their heads. It is needed only when a repo is set up or its setup is reviewed. At the bottom it keeps a section on previous setups and the thinking behind them: his setups are similar, and the differences can be reasoned. A first draft exists and is not yet reviewed. The earlier ten-point outline for a handbook chapter (branching, branch names, pull requests, who merges, protection rules, merge methods, local checks versus CI, parallel work, commits, what to avoid) is material for it.
- Overlap with the skills-review session, which has moving team process out of the global file on its list.

## 6. CI/CD and environments (flexible)

**Decided**
- Flexible. A halfway house before a full production workflow is acceptable.
- Sensible starting points: a project that is not live does not need several environments.
- The chapter covers how data flows between development and production, and what runs on a pull request, on merge and on a schedule.
- Each of the three subjects is covered briefly. The patch below is material to draw on, not text to copy.
- This content goes in the recipe, not the handbook.
- The form of the CI/CD section in the agents file (12 Nov, from the worked example): a table of the environments, including what an agent may do in each; a picture of the route a change takes, drawn in D2 and stored as an image beside its source; a table of every test suite and what it proves; and a grid of which suite runs when. Kasey liked the tests table and the grid, which must flex to fit different setups. A list of gates was tried and dropped: it repeated the git section and mixed machine checks, human decisions and advice.
- The git section is absorbed into the CI/CD section (12 Nov, later the same day). Every check a change passes on its way to production sits in one numbered table (C1, C2 and so on), whether a hook, GitHub, the pipeline or the agent enforces it, with a column saying which. The picture carries the same numbers, beside the test numbers. Kasey: read as a list, the rules were unreadable.
- The unit that ties the section together is the gate (12 Nov). A change passes a few numbered gates (in the example: commit, pull request, merge, to the test environment, to production). The picture shows the route and the gates and nothing else. A short table gives, for each gate, why it exists: the document should build an understanding of why the process is used, for people as well as agents. One grid has the gates as columns and the tests and rules as rows, marked by whether a machine checks it or it rests on the agent. The table of tests stays as the reference for what each test proves. This replaces the separate checks table and the what-runs-when grid.
- The git checks in chapter 8 guard the context files. They are not general CI standards.

- Setup grills the whole of git and CI/CD as one conversation and builds every table at the end from its answers (16 Nov). Kasey: the environments, gates and tests cannot be grilled apart, because the grid joins them.
- The agent proposes a complete setup and the user changes what does not fit. It asks only for facts the user alone knows and for real trade-offs, each with a recommendation. Kasey's worry: an agent that interviews asks unhelpful questions.
- The one stage that counts is whether the product is live, meaning any real user's data exists (Kasey, 16 Nov). Every part of the setup is in one of three piles. **Day one, not live:** the commit hook; CI on every pull request; `main` protected; GitHub's own rules; whether an agent may push and who merges; the database built from the repo with made-up data (cheap now, very costly to add later). **Going live:** the environments beyond local; what data each holds; who deploys; only proved code deploys; a check after each deploy; what an agent may do in each; test logins. **Later, when it hurts:** an environment that takes every merge; running only the tests a change touches; keeping pull requests up to date automatically; scheduled runs; alerts that reach a person. Each of these has its own trigger. The agent decides the pile for the stage and names what is left for later; it does not discuss the later ones.
- The strong suggestion is the shape of Kasey's newest setup, sized by stage, without that setup's copy of production data in pre-production, which was inherited there and not chosen.
- GitHub's own rules are looked up before anything is asked: whether an approving review is required, who may merge, whether the rules bind administrators, and whether the account's plan allows such rules at all. The agent tells the user that GitHub never lets a pull request's author approve it.
- Past setups are kept as separate example files, each a finished git and CI/CD section, with no company or client names: not live; live with three environments; live at full size.
- Integration, the environment that takes every merge automatically (16 Nov). It must be a real deployment in the cloud or it is not worth having: a local container only repeats what CI did. One person on a project that is not live skips it. It is added at the first of two moments: someone else needs to see the merged work, or going live is near. Once live it is always there, because it is what lets agents merge fast: the work's flow ends at integration, where a change is proved and its ticket finished, and the two steps a person starts (promote, deploy) gate a release, not a ticket. So not live is local, with integration when one of those moments comes; live adds pre-production and production. This replaces "an environment that takes every merge" in the later pile above.
- The agents file's git and CI/CD section carries a stage line and a short fixed block, worded per stage, saying when to tell the human that the next set of decisions is due. The agent only raises it.
- The practice is kept free of any one tool (Kasey, 16 Nov). The database rule is: everything the database needs can be recreated from the repo with one command, and nothing is made by hand.
- The handbook topic holds all the practice: the principles, the suggested setup, what to decide when, the triggers, the options and usual choice at each gate, GitHub's own rules, the past setups. The setup skill's guide holds only the conversation: what to ask, in what order, and the form of the tables. Its first instruction is to load the topic. The topic was revised to match on 16 Nov; the three example files are not written yet, and its table of previous setups stays until they are.
- The practice file moved out of the handbook the same day, to `set-up-sdlc/git-and-cicd.md`, and its row left the handbook's router (Kasey, 16 Nov). His reason: it reads as tailored to setup, not as a textbook entry. It has one reader, the setup agent, at one moment; the handbook's other chapters are standards builders and reviewers use during any change, and a builder routed to it could take the suggested setup as a reason to change a repo. It is still one file and not a separate skill, the commit-hook steps stay in it, and practice stays apart from the conversation in `section-guide.md`. Where the paragraph above says "the handbook topic", read this file. Possibly for the handbook later: the four rules for changing a setup, which apply to anyone editing CI in any repo.
- A reviewer's report on the revised file is at `~/.local/state/memory-study/reviews-2026-11/git-topic-review-2026-11-16.md`.
- The practice file was then rewritten as rules only (Kasey, 16 Nov): "too detailed - it doesn't need code examples. It should just state rules in prose." Out went the step-by-step hook instructions, the tables of options at each gate, and the table of previous setups. The hook is now five rules about what it must do. The rewrite also took in the reviewer's findings that were about the rules: the stage and triggers are copied into the agents file; a deploy checks that the code passed, not the commit; where the demo-customer tests run when there is no integration; the emergency database route is a recorded workflow in the repo; whether GitHub's rules are enforced and not only present. One line in it is the assistant's own answer and is for Kasey to correct: what pre-production proves that integration does not (it holds one chosen release still while integration moves with every merge).
- `git-and-cicd.md` now holds the whole git and CI/CD part of setup in one file (Kasey, 16 Nov), because a file of practice alone was confusing with nothing around it and the handbook was no longer its home. Four parts: how to run the conversation, what to propose, what to write, what to build. This overtakes the split above between practice and conversation. `section-guide.md` keeps the small sections and points at it.
- Setup is one flow and builds on the spot (Kasey, 16 Nov): it makes the hook, CI and the rules on `main` that the section describes, and does not turn them into tickets. Creating the other context files and folders is a one-shot step that could be a script. Kasey will check the git part by using it and guiding it the first time, not by perfecting it on paper.
- A second reviewer walked the file through three made-up repos; its report is at `~/.local/state/memory-study/reviews-2026-11/git-setup-walkthrough-2026-11-16.md`. Kasey's rulings on it (16 Nov): anything decided at setup that cannot be built yet becomes a ticket under one parent ticket for infrastructure; "a review" in the merge rule means the repo's review subagents, said plainly, and not GitHub's approving review; the small fixes the assistant agreed with were made without discussion. His objection to the smaller findings: they forget how flexible agents are and assume the user is stupid, when the users are software engineers. So the file is not to be padded with instructions for every case.
- More rulings from Kasey on the walk-through review (16 Nov): the agent asks before filing those tickets; the database rule is stated twice on purpose, in full under the environments table and again in the never list; and a repo that is already built is handled flexibly, not by a fixed procedure: the agent describes the setup that exists and agrees each difference from the suggestion with the owner (leave, change now, or ticket), and builds the context files backwards from the app with the user (`section-guide.md`, "A repo that is already built"). This takes "taking on a live repo" off the parked list in outline.
- Dropped by Kasey (16 Nov): a publish gate and a separate stage for projects that are installed and not deployed, such as libraries and command-line tools. Setup is written for deployed apps.
- On whether an agent may push without being asked, setup recommends yes, whenever its branch is ready (Kasey, 16 Nov): a push to a branch can harm nothing, and the merge gate is what protects `main`. The owner is still asked. The recommendation on who merges is not settled.
**Why**
- The handbook's deployment chapter is a sound reference, but it describes one model: every merge deploys to a test environment and production is a gated promotion. It has nothing on the stages before that, on what data each environment holds, or one view of what runs when.
- A review of the runbooks found 14 manual steps that tooling should do, such as opening a database tunnel, collecting delivery evidence and running log queries (12 of them behind about 610 lines of the main test-environment runbook).

**Material to draw on** (reviewed twice, then set aside): `~/dev_wsl/projects/agent-context/context-retro/drafts/handbook-deployment-additions.patch`
- Stages: nobody depends on it yet; first real users; outages are costly. Each adds environments and pipeline when what they protect exists. An environment becomes production the day a real user's data lands in it.
- Data: what is in the repo moves up with the code; each environment keeps its own records, settings and secrets; test data comes from a script that refuses to run against production; production data comes down only as a masked copy; a test environment must not send real email or take real payments; a shared environment holds standing fixtures, listed in the repo's docs, and neither a listed fixture nor anything a script cannot rebuild may be deleted.
- Triggers: every pull request; merge; promotion to production; a schedule. A scheduled run is not a gate, so its failure, or its not running, has to reach a person.
- Its examples of reference data ("roles, plans or country codes") were made up. Kasey objected to them, and they are not carried over.

**Open**
- Where a repo's answers are recorded. This waits on chapter 4.
- Whether CI/CD gets a file of its own in the repo.
- How CI/CD grows with the project. Kasey (12 Nov): most people do not want to start with four environments.
- Kasey is redesigning CI in another session.

## 7. The tracker

**Decided**
- Linear, in every organisation Kasey works with. One line says another tracker needs a discussion.
- Ticketing is rigid (12 Nov). Linear, its labels, what makes a good ticket and how a ticket progresses are a carefully curated way of working that preserves hard lessons. Setup offers no options on them.
- The `linear` skill stays as it is, holding the ticket rules alongside the tool how-to (12 Nov). Kasey: naming a label means saying what it is for, so the two are intrinsically linked. The aim is balance, and no repetition elsewhere.
- A stream is optional (12 Nov). The agent offers one when the human plans several tickets as one piece of work or hands over several at once; its benefit is a place to coordinate and record the work. One ticket followed by another needs no stream. The rule lives in the `stream` skill, with a short version in the agents file's skills table.
- Decisions and pitfalls live in repo files, not in Linear documents.
- Routine progress comments on a stream ticket are fine. It is the tracking ticket.
- The Linear team document is considered last. It is the intended flexible place and may cover whatever this iteration cannot settle. Agents should read it with a pinch of salt.
- First-draft test for a team document entry: not settled yet; spans more than one ticket; has a way out.

**Why**
- The instructions for an ordinary ticket are already clear. The problem is what agents write elsewhere when a ticket finishes.
- Project status updates are used mostly as asked: 13 in one team, posted by 6 of the 8 streams closed since the rule arrived.
- No team document exists in either team, though the skills assume one. Agents wrote "N/A" and parked its content in stream tickets.
- The lesson written up to six times in Linear was one organisation's push-once rule. What Kasey took from it is that git rules vary by organisation (chapters 2 and 5).
- The `stream` skill says "Routine progress gets no comment", which is not what Kasey wants.
- The `linear` skill (325 lines) is about half lifecycle rules and half tool how-to. The rules: statuses and who moves them, labels, ten conventions, the ticket body, projects as epics, blocked and kickback. Kasey expected it to hold only how to use the tool. It also points back at the agents file's work lifecycle section, which goes when the copied half goes, and its kickback labels name one organisation's people.

**Open**
- Whether to have a team document at all.
- When its entries move into repo files. Kasey expects to use it for a while and then write rules from what agents do.

## 8. Checks that guard the context files

**Decided**
- A git check flags any pull request that adds a markdown file.
- A pull request that changes any named context file raises a warning, and the agent working with the human double-checks the change with him. Every such file, with no sorting by type: an agent cannot be trusted to classify which ones matter.
- Git does this, with a section in `AGENTS.md` to match. Not harness hooks, so the setup is not tied to one agent tool.
- The checks are mandated or strongly urged.
- They are not being built now. There is no repo to hand that wants them.

**Why**
- A runbook folder appeared in two repos through ticket work, and Kasey did not know.
- A check can show that a file was added or changed. It cannot prove the human said yes, because agents commit and open pull requests as him.
- A rule that a machine or a reviewer can check tends to hold. A rule that needs judgement drifts.
- About 40 ADR changes a month was the dumping, not normal use. Kasey wants to know about every change, so the warning is not narrowed to cut noise.

**Open**
- How the human's yes is recorded so a check or a reviewer can see it. Today the agent that writes the lines also writes the list vouching for them, and that list is read only if a review happens.
- Where the check lives: one shared script that setup installs, so copies do not drift. Kasey agreed in passing (16:35); not designed yet.
- The wording of the `AGENTS.md` section that goes with the checks.
- How Kasey reviews, or is made aware of, changes to the context files. He asked on 12 Nov for this to be kept on the list, then parked it the same day: it is a scheduled run of some kind (chapter 9) and comes after the skills, the context files and the build-to-deploy lifecycle are settled. Kasey expects agents always to try to break the ask-first rule, so he needs some way to be made aware of every change: the git check, a scheduled run over context file changes, or a check added to a reviewer subagent. To be taken up straight after the template and the grilling skill.
- The builder file says a builder reports pitfalls and decisions instead of writing them. It needs widening to every context file except an ADR change carried in its brief.

## 9. Reviews and wrap-ups

**Decided**
- Session wrap-up is the one place for tidying context as well as adding to it, with a router so it does not always do everything.
- It only proposes. The human says yes or no.
- It is offered whenever the human says he is wrapping up, in any session.
- Wrap-ups and reviews also run on a schedule, not only when a coding agent starts one: overnight, per pull request, per day's sessions, or since the last run. They take their time and produce a report. This is more impartial.
- The scheduled wrap-up is the safety net for ADR changes. It checks that each change traces to a plan or to the human's own words.
- Once its design (Open) is settled, the chapter says how to set the schedule up.
- Wrap-up needs one place holding the rules and definitions of every context file. That place is the domain file.
- A wrap-up's changes may go in their own pull request or ride with code. Both are allowed.

**Why**
- Four things trigger adding a line and nothing triggers removing one.
- A wrap-up run by the session that did the work is marking its own work, can be skipped, and runs after the change has merged.
- Rules that nobody checks get broken, including ones already written down.

**Open**
- A review of the `review-code-change` skill. Its split into two reviewers (one against the ticket, one hunting bugs) is new, and Kasey wants it verified as solid (12 Nov).
- The router's levels. Proposed: skip; quick (this session only); tidy (one subagent checks the context files against the rules and recent code); full audit (several subagents, only when asked).
- The scheduled run's design. Kasey's working assumption is a scheduled run on a virtual machine. A review of a pull request needs only the repo. A wrap-up needs the session transcripts, which live on the machine where the session ran.
- Deciding which skill owns which rule is no longer parked (12 Nov). Kasey: skills hold instructions about how the work is done, so where that context lives cannot be deferred. The session that was reviewing all the skills finished on 12 Nov and handed its open questions (what builders and reviewers do, and how they load context) to this work. They are listed in `~/dev_wsl/projects/agent-context/skills-review/to-do.md` and not started.

## 10. What every agent loads

**Decided**
- `AGENTS.md` alone is not enough. Agents, subagents included, need the vocabulary, probably the ADRs, and the pitfalls. Kasey's lean: "probably all of it".
- Everything cannot be loaded into every agent at today's sizes.
- Each kind of subagent will be gone through and decided separately.
- Hooks that force a file to load are possible. Kasey wants few of them, not a tangle.

**Why**
- Tested: a fresh Claude subagent has the repo's `AGENTS.md` and the global instruction files at start-up, and nothing else from the repo. It could not define a term from the vocabulary.
- Measured over 30 days in one repo: of 37 subagents that edited code, 64% opened the vocabulary, 48% opened an ADR, and 8% opened the domain file that tells them to read the others.
- Sizes in that repo: the vocabulary about 19,000 tokens, the ADRs about 154,000.
- The builder's instructions tell it to read these files first. The reviewer's instructions do not.
- Codex was not tested.
- Hooks stay possible because they can be exported.

**Open**
- How loading is done: a short index inside `AGENTS.md`, context placed in each subagent's instructions, or hooks.
- Kasey's idea: a short section in `AGENTS.md` naming the hooks (15:12).
- What each kind of agent gets.
- Whether stricter rules for context files shrink the problem enough in a new repo.

---

## Where things stand (16 Nov 2026)

**Where the files are (16 Nov, late):** Kasey had everything that is not part of the working skill moved into `set-up-sdlc/_archive/`: this record, the old `SKILL.md` (now `SKILL-old.md`) and the old `AGENTS-portable-template.md`. The skill folder has no `SKILL.md` until the new one is written, so the setup skill cannot be run until then. The working files are `section-guide.md`, `domain.md`, `git-and-cicd.md`, `AGENTS-example.md` with its picture, and `scripts/create-context-files.sh`. Still to write: the new `SKILL.md`, and the guide's entry for "About this repo" (the stack table and the rules across the code), which the template points at. Written since: `AGENTS-template.md`, built from the example's fixed sections with blanks in square brackets and "setup:" comments for the worked-out sections; and the example's git and CI/CD section, rewritten with integration, six gates, the stage line and the triggers, with its picture redrawn. Kasey: leave `SKILL.md` till last.

**All of the skill's files are now written (16 Nov, late):** the new `SKILL.md` (eight rules, ten steps, and what to do when it is run again) and the guide's "About this repo" entry (the stack table; the rules across the code, taken only if breaking one would do real harm and nothing in the code already stops it). None of it has been used on a real repo. Kasey's plan is to guide it by hand the first time and fix what that shows. Still unsettled inside it: the recommendation on who merges.

**Made so far**
- `set-up-sdlc/AGENTS-example.md`, with its picture `example_pipeline.png` and the picture's source `example_pipeline.d2`: a worked example of the new agents file, using one repo's rules. Kasey agreed its structure section by section. Its facts are illustrative.
- `set-up-sdlc/git-and-cicd.md`: the practice the setup agent proposes from. A first draft, revised and moved out of the handbook on 16 Nov, reviewed by a subagent, not reviewed by Kasey. He does not want to spend long reviewing it.
- The `setup-pre-commit` skill is archived (moved to the skills repo's `_archive` folder, 16 Nov). Its steps live on in the handbook topic.
- Skill changes made: `linear` (the four rules joining a ticket to its pull request, and three small fixes); `stream` (when to offer a stream; the check with other sessions moved out to house rules).
- Kasey's global file: the subagent default is now Opus at extra-high effort, with Sonnet for research and non-code work.
- This skill's `SKILL.md`, `domain.md` and `AGENTS-portable-template.md` are still the old setup skill's.

**Next, in the order Kasey gave**
1. Done 16 Nov: the sections are sorted into fixed and discussed (chapter 4).
2. In progress: the grilling-style skill that creates a repo's agents file with the user. Kasey wants it in small chunks: the template and `SKILL.md` first, starting with how `SKILL.md` directs the agent; then the guide for the discussed sections.
   Changed the same day: Kasey wants to be in the loop on how the agent handles each section that is not a plain copy, one at a time, and the agreed wording goes into `section-guide.md` as it is agreed. Agreed so far: the opening line. Worktrees needs no discussion (Kasey).
3. Straight after that: how Kasey is made aware of changes to context files.

**Skills brought into line (16 Nov, late).** On Kasey's instruction three subagents searched for places that had fallen out of step with the new agents file, and the mechanical fixes were made: 21 edits in `linear`, `to-issues`, `handoff`, `grill-with-docs`, `session-wrap-up` and `stream`, and about a dozen in `review-code-change`, `verify-frontend-change`, `improve-codebase-architecture`, `codex-dispatch`, the handbook's `environment.md`, and the two agent definitions in `~/.claude/agents/` (backups beside them). No skill now points at a section of the old agents file, creates a context file lazily, or sends the reader to the global file for when reviews start. Reports: `skill-pointers-workflow-2026-11-16.md`, `skill-pointers-subagents-2026-11-16.md` and `global-files-vs-new-agents-file-2026-11-16.md` in `~/.local/state/memory-study/reviews-2026-11/`. Not done, waiting on Kasey: the global files (nothing in them was changed), the team document, the two format files in `grill-with-docs` that are looser than `domain.md`, and the Codex model for research.

**Kasey's rulings on what the search found (16 Nov, late), all carried out.**
- Who merges: setup recommends that the agent merges its own pull request once the checks are green and the review is done with nothing blocking, and that the human saying "merge it" is enough by itself. This was already his standing rule in the global file. The owner is still asked.
- The global file `~/.claude/CLAUDE.md` lost five sections: the fresh agent for fix rounds, the shared review workflow, the merge permission (with its sentence overriding a repo's own rule), code naming conventions, and branch and worktree naming. It went from 316 lines to 262. The approving review with a colleague's token stays, under its own heading, reworded to depend on the repo's instructions. Backup: `~/.claude/CLAUDE.md.bak-2026-11-16`. Two details were dropped on purpose: "a missing check is not a pass" (test-driven development covers it) and resuming the original builder for a change of plan ("something I never really want done"); the same clause came out of `codex-dispatch`. The code naming conventions now exist only in the backup; where they should live is not decided.
- The Codex global file `~/.codex/AGENTS.md` had three references to those sections reworded. Backup beside it. Its line that Luna is used only when Kasey picks it is left as it is, and so is the house rule that says Luna for research (Kasey: "leave it - luna for research is fine").
- The team document is dropped, and tally lines with it: `stream/team-document.md` is in the skills repo's `_archive`, and a review finding left unfixed is now a ticket or dropped.
- The ADR format file in `grill-with-docs` now matches the context file rules: the ruling, why, and what was turned down; no "Consequences".
- A consequence to know: a repo that does not yet have the new agents file no longer gets the review workflow or the merge permission from the global file. Its own file governs.

**Builders and reviewers (Kasey, 16 Nov, late).** A builder that is still running can be told of a change of plan. Once a builder has stopped at the end of its work it is never resumed: later work goes to a new builder. Reviewers are different: the same reviewer is resumed to check the fix. The house rule "Fix rounds" now says this.

**Still open, none started**
- A re-review of `linear` at the end. Two rules from the old copied half are in no skill (comment on decisions as they happen; record unrecorded decisions before a handoff). Several skills point back at sections of the agents file, against the one-way rule: `linear`, `to-issues`, `stream` and its team document and builder files, `session-wrap-up`, `handoff`, and this skill's `domain.md`.
- A review of the two reviewer types in `review-code-change`.
- The rules for review findings still sit in `stream`, though they apply to a lone ticket too.
- The real content of the gates and the building flow, to be recorded as an ideal demo together with Kasey's newest git setup. Its design notes are in that repo at `docs/cicd-redesign/design-so-far.txt`. Two readers of the example raised questions about the flow (where the agent stops and waits, when a ticket is finished, who builds a lone ticket). Kasey set those reviews aside as picking at a demo; the questions belong to the ideal demo.
- The rules file for the context files is drafted (`set-up-sdlc/domain.md`) and not yet read by Kasey.
- The subagents: what builders and reviewers are told and what they load. The skills review's open questions are in `~/dev_wsl/projects/agent-context/skills-review/to-do.md`.
- Where the detail about a repo's test fixtures lives.
- Small and unanswered: whether `diagnose` and `prototype` join the skills table; Kasey's Codex file says Luna is used only when he picks it, where the house rules say Luna for research; the handbook's description line does not mention the new topic.
- Parked: scheduled runs, the Linear team document, runbooks, taking on a live repo.

---

## Where the evidence is

Reports in `~/.local/state/memory-study/reviews-2026-11/`:
`agents-md-review-connect-assist.md`, `agents-md-review-people-guard.md`, `runbooks-review.md`,
`linear-notes-review.md`, `adr-review.md` (with `adr-review-commits.md`), `global-files-review.md`,
`pitfalls-review-rules.md`, `pitfalls-review-connect-assist.md`, `pitfalls-review-people-guard.md`,
`deployment-additions-review.md`.

Working notes in `~/dev_wsl/projects/agent-context/context-retro/`: `decided.md`, `to-do.md`, `recipe-outline.md`.
