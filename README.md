# cht-best-skill

> Version **V0.0.7** · Global skill `cht-best-skill`

A system in seven layers: **tactics** govern how the agent takes direction, **three files** how it remembers, the **communication layer** how it speaks, the **debate layer** how claims get verified, the **ambition layer** how bold a result you dare to ask for, the **Emperor Team layer** how a *team of AIs* actually gets the work done, and the **ask-first / council double gate** how you stop it from drifting at the start or shipping a broken answer at the end.

> Tactics decide how well it works; files decide how long it remembers; communication how precise it speaks; debate how trustworthy it is; ambition whether you dare ask for a real outcome — **organization decides whether anyone actually goes and does it, and the double gate decides whether it drifted or shipped a broken answer**.

> There is also **one on-demand decision gate** (V0.0.7): **not an eighth layer**, fired only at high-stakes forks — surface the question you have been avoiding, then arbitrate the decision and monitor its reversal conditions.

---

## What it is

This skill is for working with AI agents (CodeBuddy / Claude / Copilot-style agents) on tasks that are **multi-step, long-running, or need to survive a context reset**. It does two things:

1. **Sets up a durable three-file memory system** on disk — `task_plan.md`, `findings.md`, `progress.md` — so the agent keeps its state even after `/clear`, context compaction, or a new session.
2. **Applies 10 collaboration tactics** that turn vague "AI tips" into concrete, executable behavior for the agent.

The 10 tactics come from Thorsten Ball (AMPCode engineering lead) and are reframed here as actions the agent should take, not slogans for the human to read.

The skill is itself a product of the meta-skill system (M3 domain-load generation). V0.0.2 grafted three meta-skill lenses onto it: an **enablement gate** (M1), an **IPO primitive-chain constraint** (M2), and a **six-operation action lexicon** (M4). V0.0.3 added the **debate layer**. V0.0.4 added the **ambition layer** as a hard, script-enforced gate. **V0.0.5 adds the Emperor Team layer — an executable orchestration engine (`pstack.py`), not another essay**: team state on disk, handoffs by command, boundaries by a hard gate. **V0.0.6 adds the ask-first / council double gate** — two prompt assets baked into the three-file templates and enforced by `gates.py`, so ambiguities get closed before work starts and conclusions get red-teamed before delivery. **V0.0.7 merges two more high-value prompts into a single on-demand decision gate** (`decision.py`): a meta-level reframe of the avoided root question, three-stage adversarial arbitration, and observable reversal conditions — deliberately off by default.

---

## When to use

Enable this skill if any of these is true:

- The task needs 3+ steps, or produces multiple files / chapters
- The task will span multiple conversations, multiple days, or get interrupted by `/clear` or context compression
- The task involves research, data, or comparing multiple options where facts must accumulate
- The user explicitly asks to "make a plan", "write this down", "don't forget", or "continue from last time"
- The user mentions tactics / "getting the most out of agents" / planning with files
- The user wants to "hire AI employees / build a team / Emperor Team / pstack / let AIs recruit and delegate" — **enable the organization layer**
- The user wants to "ask about ambiguities first / don't invent context / reverse questioning / a council of advisors / five perspectives / internal red-teaming" — **enable the double gate**
- The user faces a high-stakes fork (should we do it / which path / irreversible cost), or says "I'm torn / something feels off / we're going in circles" — **fire the decision gate on demand**

For small questions, single-turn Q&A, or pure chit-chat — **do not** enable this. Don't pile process on simple tasks.

---

## Enablement gate: three tiers (from M1 domain assessment)

> Grafted from the meta-skill system's M1 — "eliminate rather than refactor". Turn "should I even enable this" from a hunch into a deterministic three-tier switch.

| Tier | Trigger | Action |
|---|---|---|
| **Eliminate** (don't use this skill) | single-turn Q&A, pure chit-chat, trivial confirmation | skip entirely, zero files, don't pile process |
| **Light** (only `progress.md`) | 2–3 steps, finishes same day, no fact accumulation | minimal version (see end of memory-protocol) |
| **Full** (all three files) | cross-session / multi-step / needs fact accumulation | run init script, build task_plan + findings + progress |
| **Org tier** (Full + Emperor Team) | needs multiple roles, recursive hiring, auto handoff, skill capture, periodic review | additionally run `pstack.py init` and dispatch via the seven practices |

**Decision basis** (any one unmet downgrades): boundary clarity · step count · cross-session? · needs fact accumulation. Default to the lighter tier — don't enable if you can avoid it, don't go full if light suffices. **The org tier is an optional add-on; never spin up a team for trivial tasks** (process heavier than the work). **The double gate applies to Full / Org tiers** — Eliminate and Light skip both, so single-turn Q&A never gets buried in process. **The decision gate is not one of these tiers**: it is an on-demand trigger stacked on Full / Org, fired only at a high-stakes fork and skipped entirely for Eliminate / Light.

---

## Ambition upgrade (pre-flight · mandatory every run · hard gate)

> Source: Claude's technical lead, *How to be more ambitious: A tutorial for humans with models* — most people underuse AI not because the model is weak, but because **the goal they hand it is too timid**. Once this skill is enabled (except the Eliminate tier), **this gate must pass before any work starts.**

Three dimensions: **height reframes the goal, depth forces rigor, breadth closes blind spots.**

| Dimension | One-liner | Weak → Ambitious |
|---|---|---|
| **Height** | change the goal, not the task; anchor the final outcome and make the agent fully accountable for it | "fix these 3 bugs" → "keep this app crash-free, connect to the crash-reporting system, follow through and fix everything" |
| **Depth** | hold the agent to top-expert standards: upload raw data/logs, name the professional method and an **external validation standard** (no self-grading) | "analyze churn" → raw data + statistical model verification, actively challenge existing assumptions, mine data blind spots |
| **Breadth** | turn nouns into verbs (who achieves what decision, in how long) + cross-review from multiple independent angles, surface risks | "make a quarterly-review deck" → "let a busy exec understand business causality and decide within 30 minutes" |

**Why a hard gate**: written as advice, this gets ignored — agents drift back to shallow execution on long tasks. So the three dimensions are baked into `task_plan.md` as a fixed "0. Ambition upgrade" block (generated by **every** `init_task.py` run) and enforced by a checker:

```bash
python3 ~/.codebuddy/skills/cht-best-skill/scripts/verify_ambition.py "<task dir>"
# exit 0 = pass; exit 1 = dimensions incomplete, blocks start and delivery
```

**Three red lines**: ① **no role-playing** ("you are an expert" raises sycophancy — multiple angles come from cross-verification, not personas); ② no self-grading — require data source + method + external validation standard; ③ no entering phase 1 until all three dimensions are filled.

> **Reconciling with the debate layer**: this tutorial says "invite analysts, auditors, senior editors", while Jensen Huang's method says "never assign roles". No conflict — the tutorial itself demands *actionable verification steps, not role-play lines*. The "virtual brain trust" is **multiple independent perspectives cross-examining** (the higher-order form of debate-layer cross-examination), each producing a risk list and rebuttals, not expert-toned commentary.

Full breakdown, three paste-ready templates, five depth tactics, mapping table and anti-patterns: `references/ambition.md`.

---

## Emperor Team layer: the organization layer (make a team of AIs actually work)

> Prototype: Lauren Tan (SpaceX / Grok Bot engineering lead) — "don't use AI as a tool, build an agent team; humans own the goal, AIs deliver" — seven practices + a three-tier architecture + the open-source `pstack` orchestrator. Reframed here as **imperial governance**: Liu Bang (the human) only sets direction and staffs the team; Zhang Liang (genius) thinks, Han Xin (talent) fights, Xiao He (steward) runs the rear, and each of the three recruits their own people.
> **This layer is the answer to "not just a shell"**: earlier layers govern how a *single* agent thinks / speaks / remembers / verifies / aims. This one is `scripts/pstack.py` — team state on disk, handoffs by command, boundaries by a hard gate. **It runs.**

**Three tiers / three talents**

| Imperial seat | Talent | Duty |
|---|---|---|
| **Liu Bang** (human) | Director | sets direction, staffs the team, reviews results; does no work, is no relay, is no strategist |
| **Zhang Liang** | Genius · decision tier | understand, decompose into dispatchable subtasks, set acceptance, track progress; writes no deliverables |
| **Han Xin** | Field talent · execution tier | actually produces openable evidence; may recruit 10–20 temporary specialist instances |
| **Xiao He** | Steward · orchestration tier | three-file memory, skill library, verification guardrails, logistics; may recruit bookkeepers / validators |

**Seven practices → executable actions**: ① AI-HR creates roles (`init` / `hire` / `onboard` five questions / `review`) → ② **hard cap of 3–5 standing roles** (a 6th `hire` is refused) → ③ introduce yourself before asking "how should we collaborate" (`ONBOARDING.md`; dispatch is blocked until filled) → ④ `capture` a method the moment a job succeeds, `reuse` it later → ⑤ independent `outbox/` + `inbox/` per role → ⑥ `handoff` **actually copies upstream artifacts into the downstream inbox**, killing manual relay → ⑦ speak the context, then "restate it in your own words" (restate gate).

**Why it isn't a shell**: `manifest.json` is the machine-readable single source of truth (roster / task ledger / skill library / handoff log / review log); `verify_team.py` is a hard gate (3–5 roles, all three talents present, five duty-contract fields, isolated outbox, valid schedule, onboarding confirmed, `done` requires evidence). A failing gate returns exit 1 and blocks dispatch and delivery.

```bash
P=~/.codebuddy/skills/cht-best-skill/scripts
python3 $P/pstack.py init                      # staff the three talents + isolated output areas
python3 $P/pstack.py onboard                   # introduce yourself + collaboration + restate gate
python3 $P/verify_team.py ./agent-team || exit 1
python3 $P/pstack.py dispatch --to hanxin --task "..." --acceptance "..."
python3 $P/pstack.py handoff --from hanxin --to xiaohe   # auto relay, never manual
python3 $P/pstack.py capture --name "workflow" --from-task T001 --method "1... 2..."
python3 $P/pstack.py review                    # periodic performance review
```

> **Duty contract ≠ persona** (reconciling with the debate layer's "never assign roles" and the ambition layer's "no role-play"): `PROFILE.md` holds **interface fields** (inputs / outputs / acceptance / reports-to / schedule / up-downstream); "Zhang Liang" is only a slot ID. Adjectives like "you are a genius strategist" are forbidden. We hire posts, not actors — the checker validates field completeness and never asks "does it sound like Zhang Liang".

Full breakdown (three-tier architecture, seven-practice mapping, recursive delegation, 3–5 standing roles vs temporary instances, mapping to all seven layers, agent-executable protocol, anti-patterns): `references/emperor-team.md`.

---

## Ask-first & Council layer: two hard gates at the entrance and exit (V0.0.6 · every run)

> Two high-leverage prompts, one at the **entrance** (clarify every ambiguity before starting so the agent doesn't invent context) and one at the **exit** (red-team the answer through five lenses before concluding). Like V0.0.4 / V0.0.5, **this is a gate, not an essay**: two blocks baked into the existing three-file templates (no fourth file), every item checked by `scripts/gates.py`, exit code 1 on anything unclosed.

**Entrance · Reverse questioning**: the agent asks about every vague or missing piece of information *before* doing the work.

> **Reconciling with tactic 06** ("ask only on real blockers, don't interrupt with trivial confirmations"): this is not "ask more", it's "**ask the right things, once**". Self-check first (resolve anything readable / queryable / inferable yourself) → keep only high-leverage ambiguities that would derail the result → **ask them all in one batch** → finish the whole job in one go → write down explicit default assumptions tagged `[hypothesis]` for anything unanswered. What's forbidden is asking while working and firing off twenty questions up front.

**Exit · Council red-team**: before giving the conclusion, five independent perspectives sweep the answer for problems.

| Lens | What it must produce |
|---|---|
| L1 Fault-finding | factual / arithmetic / logical errors, unsupported assertions |
| L2 First principles | the real goal under the surface request; is the plan solving the wrong problem |
| L3 Counter-example | at least one concrete scenario or boundary condition that breaks the conclusion |
| L4 Evidence check | source and reproducible path for every key claim; missing ones tagged `[to verify]` |
| L5 Landing | who does what, when; blockers, dependencies, rollback |

> **Reconciling with "never assign roles"** (same logic as V0.0.3 / V0.0.4 / V0.0.5): the five advisors are **five review lenses**, not "you are a senior consultant" persona lines. Each item is `problem + evidence/verification action + disposition`, followed by an **arbitration & revisions** entry. We fill slots, not cast actors — the checker validates item completeness and never asks "does it sound like an advisor".

**Why a hard gate**: `task_plan.md` "0.1 Reverse questioning" and `progress.md` "Council red-team" are generated by **every** `init_task.py` run. `gates.py clarify` checks A self-resolved / B high-leverage ambiguities / C one batched question set / D per-question closure (**every Q in C must have an answer in D**); `gates.py council` checks ≥1 three-part item in each of the five lenses plus ≥1 arbitration entry. Any gap, numbering skip, or leftover `【待填】` placeholder blocks.

```bash
P=~/.codebuddy/skills/cht-best-skill/scripts
python3 $P/gates.py clarify "<task dir>" || exit 1   # before starting: unclosed questions block
python3 $P/gates.py council "<task dir>" || exit 1   # before delivery: missing lens / no arbitration blocks
python3 $P/gates.py verify  "<task dir>" || exit 1   # delivery check: both gates at once
python3 $P/gates.py seed    "<old task dir>"         # backfill blocks, never overwrite
```

> **Two boundaries**: ① a red-team is the agent checking itself — it **cannot replace the external validation standard** required by the ambition layer (self-grading ≠ external validation); ② the debate layer makes multiple answers fight, the council sweeps one answer through five lenses — they stack: `council` → cross-examine → human arbitration. Eliminate / Light tiers skip both gates.

Full breakdown: `references/clarify-council.md`. Paste-ready prompts: `assets/prompts/reverse-questions.md` and `assets/prompts/council.md`.

## Decision gate: an on-demand trigger, not an eighth layer (V0.0.7)

> Two high-value prompts merged into one landing point: first surface the question you've been avoiding (**pick the right problem**), then arbitrate the decision and monitor its reversal conditions (**make the right call**).
> **This is not an eighth layer, nor a sixth gate you must pass every run** — it's a decision gate fired only at high-stakes forks, at steps 0.3 / 4.5 of the execution loop, not counted toward ≤5 primitives. **Off by default; err on the side of using it less.**

**The two original prompts**: ① "Across all the problems we've discussed repeatedly, is there a deeper question I've been circling but never actually asked?" ② "Fully embody the devil's advocate, the decision-flaw auditor and the neutral judge: phase 1, supporting me is forbidden — prove the decision wrong as strongly as possible, finding missing facts, over-optimistic assumptions, irreversible costs, opportunity costs, worst-case risk, and emotional cognitive biases; phase 2, switch to the supporting view and list the core reasons it could hold; phase 3, as neutral judge, compare the key evidence and tell me directly which side prevails, the largest unknown risk, and under which conditions the conclusion would flip — don't force a 50/50 balance."

**The merged five beats**:

| Beat | What it does | Lands in |
|---|---|---|
| **S0 Meta-level reframe** | `decision.py scan` sweeps `agent-tasks/*/` decision logs and `[hypothesis]` entries across directories for repeatedly rejected options / rework / recurring assumptions → answers "is there a question I never asked?" | If the real question changed, rule **continue / reframe the goal / stop** and write back to `task_plan.md` "3. Boundaries / 6. Change log" |
| **S1 Devil's advocate** | Supporting is forbidden; six items: missing facts / over-optimistic assumptions / irreversible costs / opportunity costs / worst-case risk / emotional cognitive bias | Rebuttal items only; the checker blocks supportive phrasing |
| **S2 Supporting view** | Core reasons the decision could hold, with evidence | ≥1 item |
| **S3 Neutral judge** | Compare key evidence, state clearly which side's **evidence prevails** (against / for / needs evidence / defer) + largest unknown risk | Bans "50/50 / both have a point / too close to call", and requires an explicit stance |
| **R Reversal conditions** | "When X appears, the conclusion should flip to Y" + monitoring method / threshold | Feeds tactic 07 scheduled checks; notify when a condition hits |

**Why merge them**: separately they'd become a 5th and 6th gate — six in total with the existing four — making the process heavier than the work (violates M1 and tactic 06). Merged, it's **one trigger that fires on demand**, wiring together three existing capabilities: the three-file memory, the debate layer, and scheduled tasks. A full-repo search confirmed the seven layers previously had **no** notion of irreversible cost, opportunity cost, cognitive bias, reversal conditions, or an avoided root question.

**Two reconciliations**:

> ① **Argument slots ≠ personas** (fourth reuse of the V0.0.3 → V0.0.6 logic): "devil's advocate expert" is an **output contract**, not an authority-inflating adjective. This prompt ships with its own anti-sycophancy constraints — "supporting me is forbidden", "refuse a forced 50/50" — so it *suppresses* sycophancy, on the same side as Jensen Huang's method. We fill slots, not cast actors.
> ② **Evidence-prevails judgment ≠ deciding for the human**: V0.0.3 has the human arbitrate and stay impartial; this gate makes the AI **say which side prevails**. The difference is real — the AI supplies an evidence-prevails judgment + largest unknown risk + reversal conditions; tactic 10 keeps the final call with the human.

**Trigger threshold** (any one; Eliminate / Light tiers skip entirely): high irreversible cost (external commitment / release / spend / data deletion / signing) · discussed across ≥2 sessions or reworked ≥2 times · the user says "I'm torn / should I / something feels off / we're going in circles" · a directional choice rather than an execution detail.

```bash
P=~/.codebuddy/skills/cht-best-skill/scripts
python3 $P/decision.py scan "<parent of agent-tasks>"     # S0 material: cross-session signals
python3 $P/decision.py init "<task dir>"                  # idempotent append of the S0–R block (not baked into the template → zero cost when unused)
python3 $P/decision.py verify "<task dir>" --required || exit 1
```

> When the block is absent, `verify` passes by default (treated as not enabled); `--required` explicitly declares "this is high-stakes", and a missing block then blocks. **Only trigger it when needed — but once triggered, it must be filled in completely.**

Full breakdown: `references/decision-gate.md`. Paste-ready merged prompt: `assets/prompts/decision.md`.

## Step 1: Drop memory onto disk

```bash
python3 ~/.codebuddy/skills/cht-best-skill/scripts/init_task.py "<task name>" [--dir <working dir>]
```

By default it creates `agent-tasks/<date>-<task-name>/` in the current directory and seeds the three files; the script reports the ambition-upgrade status and prints the exact checker command. The directory is not the point — **the three files must exist.**

| File | Who writes / when | Must contain |
|---|---|---|
| `task_plan.md` | written at start, updated before each phase change | one-line goal, verifiable acceptance criteria, phases + current phase, what's explicitly out of scope |
| `findings.md` | written the moment each fact is found | fact + **source** + confidence; speculation must be tagged `[hypothesis]` |
| `progress.md` | appended after each step | status snapshot, actions + results (with evidence paths), decision log, next steps |

The relationship: **plan is the map, findings is the fact base, progress is the dashcam.**

Full protocol (update timing, field spec, recovery flow) is in `references/memory-protocol.md`.

---

## The 10 tactics (what the human directs, what the agent does)

| # | Tactic | Agent-side action |
|---|---|---|
| 01 | Always use the newest, strongest model | never downgrade for critical judgment or long chains; use lightweight models only for mechanical batch work |
| 02 | Say "what", not "how" | restate goal + acceptance criteria before starting; design the steps yourself, but never invent requirements |
| 03 | What the AI can't see, it will invent | fetch / read / look up missing context first; **never fabricate numbers or citations** |
| 04 | Don't edit one-by-one; offer several options | on disagreement, produce 2–3 options + a comparison table; let the human judge, don't re-do the same version repeatedly |
| 05 | Demand evidence | reports must include file paths, command output, before/after diffs; "done" needs an artifact |
| 06 | Don't stare at the screen waiting | dispatch a whole chunk at once, ask only on real blockers; don't interrupt the human with trivial confirmations |
| 07 | Scheduled tasks | hand periodic work to timers/automation; proactively notify when something lands |
| 08 | One conversation, one job | one task = one set of files; if it drifts, write back to plan first, then decide whether to split |
| 09 | Chat history is working memory | chat gets lost, files don't — write memory into findings/progress, not the conversation |
| 10 | Write important outward text yourself | apologies, key reports, external copy: give a draft and mark "needs human sign-off"; don't make the call for the human |

The test is always the same: **does this need "human heart", or just "information"?**

Full breakdown and counter-examples are in `references/tactics.md`.

---

## How tactics map to files

| Tactic | Lands in |
|---|---|
| 02 Say what | `task_plan.md` goal + acceptance criteria |
| 03 Give real context | `findings.md` facts + sources |
| 05 Demand evidence | `progress.md` outputs + evidence paths |
| 06 Let go | the three files — state survives without the human present |
| 08 One task one context | one task one directory, naturally isolated |
| 09 Record as memory | three files replace volatile chat history |
| Reverse questioning (V0.0.6 entrance) | `task_plan.md` "0.1" four-part closure |
| Council red-team (V0.0.6 exit) | `progress.md` "Council red-team" five lenses + arbitration |
| Decision gate (V0.0.7 on demand) | `progress.md` decision log + S0–R block; `task_plan.md` boundaries / change log |

---

## Action primitives: the six-operation lexicon (from M4 execution axis)

> Grafted from the meta-skill system's M4 — every action classifies into 6 meta-operations (S/C/A/O/I/G). Aligning the 10 tactics to this table gives the agent's actions a shared grammar for self-check.

| Meta-op | Meaning | Maps to tactics |
|---|---|---|
| S Perceive / G Guard | acquire & verify info, hold boundaries | 03 what it can't see, 05 demand evidence |
| C Cognize | judge & design options | 02 say what, 04 offer options |
| A Act | execute & automate | 06 let go, 07 scheduled tasks |
| O Organize | structure & memory management | 08 one job per conversation, 09 chat is memory |
| I Interact | outward human collaboration | 10 write outward text yourself |

---

## Communication layer: Grice's Cooperative Principle

> The 10 tactics govern *how to direct and remember*; this layer governs *how to talk*. It ports philosopher Paul Grice's **Cooperative Principle** into hard communication constraints for the agent. Paste it into a prompt and the fluff, fabricated data, tangents, and rambling disappear.

Four sentences: **say neither too much nor too little · be truthful and evidenced · stay on topic · be clear and concise.**

| Maxim | One-liner | Agent-side action |
|---|---|---|
| Quantity (just enough) | information neither too much nor too little | give only what the task needs: stop when sufficient, don't pad background, don't repeat, don't pre-enumerate every branch |
| Quality (truthful) | content truthful and evidenced | write "to confirm" / tag source / tag confidence when unsure; **never fabricate numbers, citations, or filenames** |
| Relation (relevant) | stay on topic, don't drift | every paragraph must serve the current goal; don't mix unrelated topics or multiple tasks into one reply |
| Manner (clear) | express clearly and concisely | use short sentences, lists, tables; lead with the conclusion; cut the pleasantries and padding |

Before emitting each sentence, ask: **Is this what the user asked, or am I adding it?** (Quantity) · **Does this have a source?** (Quality) · **Is this relevant to the current task?** (Relation) · **Can this be shorter?** (Manner)

This doesn't duplicate the 10 tactics: those are about direction and memory, these are about expression and communication. Quality ↔ 03/05, Relation ↔ 08, Quantity ↔ 02/04, Manner is an independent boost. Full breakdown and a copy-paste prompt snippet are in `references/communication.md`.

---

## Debate layer: adversarial verification (three gates for every answer)

> Source: Jensen Huang's AI usage — he never assigns roles to AI and never trusts ready-made answers. AI has built-in sycophancy: ask along its own logic and you get errors that agree with you. Swap "believe one answer" for "make answers fight each other" — the human keeps **questioning and decision rights**.

**Three steps**: ① **Self-check** — push back on the first answer, force it to find its own holes; ② **Cross-examine** — hand the conclusion to two other AIs (or fresh sessions) to pick faults and expose hard flaws; ③ **Arbitrate** — compare both sides' strengths and hard flaws; the human filters and distills.

**Two taboos**: no role-playing ("you are an expert in X" raises sycophancy); never trust ready-made answers (high-stakes conclusions must pass all three gates).

**Three ready-to-paste prompts**:
1. Are you sure this is the best answer you can give? Check yourself carefully; find the holes, errors, and logical flaws in your response.
2. Please review the following AI conclusion; itemize the factual errors and logical blind spots and rebut them: [paste the AI answer]
3. Compare the two AI positions; objectively lay out each side's strengths and hard flaws; stay neutral, no favoritism.

How it meshes: 03 governs **input** (give real context), debate governs **output** (adversarial verification); the hard-flaw list from cross-examination is the strongest form of 05's evidence; arbitration stays human (10). Full breakdown in `references/debate.md`.

---

## Execution loop: IPO primitive chain (≤5 primitives, from M2)

> Grafted from the meta-skill system's M2 — restructure the task into an end-to-end IPO (Input→Process→Output) primitive chain, cutting the "human-limitation compensation layer".

0. **Ambition upgrade (pre-flight)**: rewrite the shallow request into height / depth / breadth, fill them into `task_plan.md` "0. Ambition upgrade", and pass `verify_ambition.py` (exit 0) before proceeding. Eliminate-tier tasks skip this step.
0.2. **Reverse questioning (entrance · every run)**: follow `assets/prompts/reverse-questions.md` — self-check first, ask only high-leverage ambiguities in one batch, close every question (unanswered ones tagged `[hypothesis]`), fill `task_plan.md` "0.1", and pass `gates.py clarify`. Eliminate / Light tiers skip this.
0.3. **Decision gate (on demand)**: only at a high-stakes fork — `decision.py scan` → `init` → fill S0–R → `verify --required`; if S0 rules "reframe the goal / stop", write back to `task_plan.md` and loop back with M2 thinking. Eliminate / Light tiers skip it; never for trivial tasks. May also run at 4.5 when a phase change hits a fork.
0.5. **Staff the team (org tier only)**: `pstack.py init` → fill `ONBOARDING.md` → pass `verify_team.py` → Zhang Liang decomposes and dispatches → `handoff` auto-relays → `capture` distills → `review` audits. Never for trivial tasks.
1. **Pick up the task**: restate goal + acceptance criteria (02); if materials are thin, ask first (03), don't guess.
2. **Persist**: run the init script, write the phases in `task_plan.md`.
3. **Work**: advance one phase at a time, writing into `findings.md` / `progress.md` as you go.
4. **Change phase**: update plan's "current phase" first, then act; write the phase conclusion into progress's decision log.
5. **Deliver**: first red-team the answer through the five lenses per `assets/prompts/council.md` and write it into `progress.md`, making sure arbitration actually changes the conclusion; then give evidence (05), mark parts needing human sign-off (10), update progress's next steps. **Before delivery run `gates.py verify` (both gates) + `verify_ambition.py`; for org tier also `verify_team.py`.**

**Two hard constraints**
- **≤5 primitives**: any task breaks into at most 5 primitives (steps 0 / 0.2 / 0.3 / 0.5 are pre-flight or fork gates, not counted); more means a compensation layer is still untrimmed — loop back with M2 thinking and keep cutting.
- **Minimize cross-primitive handoff**: intermediate artifacts may stay as calibration anchors, but don't pile docs between primitives or hand off repeatedly; in the org tier always use `handoff` — **never manual relay**.

---

## Resuming after an interruption

If context is lost or the session changed, recover in this order — **don't start over**:

1. Read `progress.md` status snapshot + last log entry → know where it stopped
2. Read `task_plan.md` current phase → know what to do next
3. Read `findings.md` → reuse existing facts, don't re-research
4. Fill only the gaps, then keep writing progress

---

## Anti-patterns

- Filling in a placeholder number when data is missing (violates 03)
- Asking "is this OK?" after every step (violates 06)
- Saying "done" with no path or output (violates 05)
- Writing weekly report, budget, and code in one chat window (violates 08)
- Rebuilding from scratch instead of small fixes (violates 04)
- Skipping progress, restarting from zero after interruption (violates 09)
- Sending un-finalized sensitive text outward (violates 10)
- Rephrasing without raising accountability ("professionally fix these 3 bugs") — fake height
- Letting the AI judge whether its own analysis is "deep enough" — violates external validation
- Writing an expert-toned paragraph instead of a risk list — role-play, not breadth
- Starting before all three ambition dimensions are filled, or skipping `verify_ambition.py` at delivery — bypassing the hard gate
- Stuffing a dozen half-baked AIs into the roster (org-tier cap refuses them; "few well-tuned, not many mediocre")
- Dispatching immediately without `ONBOARDING.md` or the restate check (blocked)
- Copy-pasting A's output to B yourself (being a relay — should use `handoff`)
- Never `capture`-ing a finished job, re-teaching next time; all AIs sharing one output dir (no traceability)
- Writing persona adjectives like "you are a genius strategist" (role-play, red line of the duty-contract layer)
- Spinning up a team for a trivial task (violates the M1 enablement gate — process heavier than the work)
- Firing off twenty questions up front, or asking "is this OK?" after every step (turning reverse questioning into a confirmation machine — violates 06)
- Leaving the self-check section empty, or listing questions without closing every Q (inventing context — violates 03)
- Writing "as a senior consultant, I think…" instead of itemized faults (persona red line)
- Filling only two of the five lenses, or writing "no issues found" in each (box-ticking red-team)
- Finding faults but recording no arbitration/revision, shipping the conclusion unchanged; passing a red-team table off as external validation (self-grading ≠ external validation)
- Firing the decision gate for a trivial task or single-turn Q&A (violates M1 and tactic 06 — process heavier than the work)
- Inventing a "deep question" in S0 when the scan found no recurring pattern (fabrication — violates 03)
- Baking the decision block into the template, turning an on-demand trigger into a sixth every-run gate
- Slipping "but overall it's still worth doing" into the devil's-advocate phase, or writing "both sides have a point" in the judgment (sycophancy / forced 50/50)
- Letting the AI decide for the human ("so you should do X") — crosses tactic 10
- Writing unobservable reversal conditions like "depends on the situation / if risk grows" (can't be scheduled or monitored)

---

## Files

- `scripts/init_task.py` — one command to seed the three-file skeleton (includes the ambition block + checker hint)
- `scripts/verify_ambition.py` — ambition hard gate: exit 1 when any dimension is incomplete
- `scripts/pstack.py` — **Emperor Team orchestration engine** (executable org-layer kernel: init / hire / onboard / dispatch / handoff / capture / reuse / review / verify / status)
- `scripts/verify_team.py` — team hard gate (3–5 roles, three talents, duty contracts, identity isolation, restate confirmation)
- `scripts/gates.py` — **V0.0.6 double gate** (clarify entrance four-part closure / council exit five lenses + arbitration / verify / seed)
- `scripts/decision.py` — **V0.0.7 decision gate** (scan cross-session signals / init idempotent append / verify five-section hard gate, off by default)
- `assets/templates/decision-block.md` — S0–R block template (appended on demand; three-file structure unchanged)
- `assets/templates/` — blank templates for the three files (task_plan carries "0. Ambition upgrade" + "0.1 Reverse questioning"; progress carries "Council red-team")
- `assets/prompts/reverse-questions.md` — ask-first prompt (full + short form, reconciling with tactic 06)
- `assets/prompts/council.md` — five-lens council prompt (full + short form, "review lens ≠ persona" red line)
- `assets/prompts/decision.md` — **merged version** of the two high-value prompts (full + short form, trigger threshold, two red lines)
- `references/tactics.md` — deep dive on the 10 tactics (for human and agent to read together)
- `references/memory-protocol.md` — three-file protocol and recovery flow
- `references/communication.md` — Grice's four maxims (communication layer, with a copy-paste prompt snippet)
- `references/debate.md` — Jensen Huang's AI debate verification (debate layer: self-check → cross-examine → arbitrate, with three ready-to-paste prompts)
- `references/ambition.md` — height / depth / breadth deep dive (ambition layer, with three paste-ready templates and the role-conflict reconciliation)
- `references/emperor-team.md` — Emperor Team deep dive (org layer: three tiers / three talents, seven-practice mapping, recursive delegation, duty contract ≠ persona, agent-executable protocol)
- `references/clarify-council.md` — V0.0.6 double-gate deep dive (two conflict reconciliations, field spec, mapping to all seven layers, agent protocol, anti-patterns)
- `references/decision-gate.md` — V0.0.7 decision-gate deep dive (two reconciliations, cross-directory scan, field spec, mapping to all seven layers, anti-patterns)

---

## Quick self-check (for the human)

1. Am I giving a **goal** or a **procedure**? (02)
2. Did I get **evidence** or just **claims**? (05)
3. Is this memory on **disk** or only in the **conversation**? (09)
4. Did I ask for a **real outcome**, or just a surface task? (ambition · height)
5. Before starting, did I ask the **right** ambiguities once — and close every one of them? (reverse questioning)
6. Before delivering, did all **five lenses** produce verifiable items, and did the arbitration actually change the conclusion? (council)
7. At a high-stakes fork, did I look for the question I've been avoiding — and did I state which side's evidence prevails plus what would flip it? (decision gate)

---

## License

MIT — use it, fork it, make your agents less forgetful.
