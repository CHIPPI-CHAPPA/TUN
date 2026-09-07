# Codex Execution Policy

Default mode is **FAST_PATH**. Optimize for verified useful progress per token and per turn. Prefer finishing an atomic milestone over process ceremony.

## Context budget
- Read this file, then only task-relevant code, state, tests, and docs.
- Search/navigate before opening broad trees. Do not scan the whole repository or history unless the task truly requires it.
- Reuse committed decisions and invariants; do not repeatedly re-derive approved architecture.
- Keep planning compact. Do not create long plan/review documents unless the work is genuinely multi-stage or high-risk.

## Default execution loop
1. Inspect the smallest relevant surface.
2. Implement one coherent batch.
3. Run the smallest focused check that can falsify the change.
4. Fix observed failures; do not invent extra review stages.
5. Commit a working milestone when repository policy permits.
6. Report briefly: changed, verified, remaining/blocker.

## Avoid by default
- Separate brainstorming/design/reviewer subagents for routine work.
- Worktrees for single-threaded changes that do not need isolation.
- Full TDD for UI, prototypes, docs, simple glue, or low-risk refactors.
- Full-suite regression after every small edit.
- Repeated Git lineage/status/history checks when state is already known.
- Long reports that duplicate code, tests, or committed documentation.

Use focused TDD, broader regression, independent review, or extra isolation only when they materially reduce risk.

## HIGH_ASSURANCE triggers
Escalate only for security/auth/secrets, irreversible or data migrations, production/release boundaries, cross-repository contracts, or explicit user request. Lottery work also escalates when prediction integrity, future-data leakage, frozen evidence/ledger/provenance, commit-reveal-score semantics, scoring logic, or official-result parsing can change.

High assurance is targeted: add only the checks/reviewers needed for the specific risk; do not automatically enable every ceremony.

## Continuity before limits
- Structure large work as independently useful atomic milestones.
- If usage/context/turn budget becomes constrained, stop expanding scope and finish the current milestone first.
- Make it runnable, run the focused check, and commit if safe. Never trade a recoverable checkpoint for a long report.
- If meaningful work remains, create/update `CODEX_CHECKPOINT.md` (keep it under ~40 lines) with: current HEAD/branch, completed work, remaining work, exact next files/command, and any known failing check.
- A resumed session should read `AGENTS.md`, then `CODEX_CHECKPOINT.md` if present, then only the relevant files. Do not reconstruct the full prior conversation.
- Remove the task checkpoint when the task is fully completed and its state is already represented by code/tests/docs.

## Prototype mode
For games and exploratory product work, default to a playable/testable prototype with placeholders and minimal architecture. Do not future-proof or productionize mechanics before they are accepted.

When instructions conflict, direct system/developer/user instructions and more-specific nested `AGENTS.md` files take precedence.