# cht-best-skill

> Version **V0.0.2** · Global skill `cht-best-skill`

A system in two halves: **the tactics tell the agent how to take direction, the three files tell it how to remember.**

> The tactics decide how well it works; the files decide how long it remembers.

---

## What it is

This skill is for working with AI agents (CodeBuddy / Claude / Copilot-style agents) on tasks that are **multi-step, long-running, or need to survive a context reset**. It does two things:

1. **Sets up a durable three-file memory system** on disk — `task_plan.md`, `findings.md`, `progress.md` — so the agent keeps its state even after `/clear`, context compaction, or a new session.
2. **Applies 10 collaboration tactics** that turn vague "AI tips" into concrete, executable behavior for the agent.

The 10 tactics come from Thorsten Ball (AMPCode engineering lead) and are reframed here as actions the agent should take, not slogans for the human to read.

The skill is itself a product of the meta-skill system (M3 domain-load generation). V0.0.2 grafts three more meta-skill lenses onto it: an **enablement gate** (M1), an **IPO primitive-chain constraint** (M2), and a **six-operation action lexicon** (M4) — sharpening *when to use it* and *how to decompose*, without bloating it into a meta-skill.

---

## When to use

Enable this skill if any of these is true:

- The task needs 3+ steps, or produces multiple files / chapters
- The task will span multiple conversations, multiple days, or get interrupted by `/clear` or context compression
- The task involves research, data, or comparing multiple options where facts must accumulate
- The user explicitly asks to "make a plan", "write this down", "don't forget", or "continue from last time"
- The user mentions tactics / "getting the most out of agents" / planning with files

For small questions, single-turn Q&A, or pure chit-chat — **do not** enable this. Don't pile process on simple tasks.

---

## Enablement gate: three tiers (from M1 domain assessment)

> Grafted from the meta-skill system's M1 — "eliminate rather than refactor". Turn "should I even enable this" from a hunch into a deterministic three-tier switch.

| Tier | Trigger | Action |
|---|---|---|
| **Eliminate** (don't use this skill) | single-turn Q&A, pure chit-chat, trivial confirmation | skip entirely, zero files, don't pile process |
| **Light** (only `progress.md`) | 2–3 steps, finishes same day, no fact accumulation | minimal version (see end of memory-protocol) |
| **Full** (all three files) | cross-session / multi-step / needs fact accumulation | run init script, build task_plan + findings + progress |

**Decision basis** (any one unmet downgrades): boundary clarity · step count · cross-session? · needs fact accumulation. Default to the lighter tier — don't enable if you can avoid it, don't go full if light suffices.

---

## Step 1: Drop memory onto disk

```bash
python3 ~/.codebuddy/skills/cht-best-skill/scripts/init_task.py "<task name>" [--dir <working dir>]
```

By default it creates `agent-tasks/<date>-<task-name>/` in the current directory and seeds the three files. The directory is not the point — **the three files must exist.**

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

## Execution loop: IPO primitive chain (≤5 primitives, from M2)

> Grafted from the meta-skill system's M2 — restructure the task into an end-to-end IPO (Input→Process→Output) primitive chain, cutting the "human-limitation compensation layer".

1. **Pick up the task**: restate goal + acceptance criteria (02); if materials are thin, ask first (03), don't guess.
2. **Persist**: run the init script, write the phases in `task_plan.md`.
3. **Work**: advance one phase at a time, writing into `findings.md` / `progress.md` as you go.
4. **Change phase**: update plan's "current phase" first, then act; write the phase conclusion into progress's decision log.
5. **Deliver**: give evidence (05); mark parts that need human sign-off (10); finally update progress's next steps.

**Two hard constraints**
- **≤5 primitives**: any task breaks into at most 5 primitives; more means a compensation layer is still untrimmed — loop back with M2 thinking and keep cutting.
- **Minimize cross-primitive handoff**: intermediate artifacts may stay as calibration anchors, but don't pile docs between primitives or hand off repeatedly.

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

---

## Files

- `scripts/init_task.py` — one command to seed the three-file skeleton
- `assets/templates/` — blank templates for the three files
- `references/tactics.md` — deep dive on the 10 tactics (for human and agent to read together)
- `references/memory-protocol.md` — three-file protocol and recovery flow
- `references/communication.md` — Grice's four maxims (communication layer, with a copy-paste prompt snippet)

---

## Quick self-check (for the human)

1. Am I giving a **goal** or a **procedure**? (02)
2. Did I get **evidence** or just **claims**? (05)
3. Is this memory on **disk** or only in the **conversation**? (09)

---

## License

MIT — use it, fork it, make your agents less forgetful.
