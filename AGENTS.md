# FAST_PATH

Default to FAST_PATH. Continue from the current branch/checkpoint; do not reconstruct prior conversations or re-audit accepted decisions unless current artifacts are insufficient. Read `CODEX_CHECKPOINT.md` if present, `git status/diff`, then only task-relevant files.

Loop: minimum inspect -> coherent implementation -> focused verification -> safe commit/checkpoint -> <=5-line report. Avoid broad scans, long plans, extra agents/reviews/worktrees, and full TDD/regression unless a specific risk requires them.

Before budget runs low, stop scope expansion, finish a runnable atomic milestone, verify it, commit if safe, and update `CODEX_CHECKPOINT.md` (<=40 lines: branch/HEAD, done, remaining, exact next files/commands, failures). Resume from it.

Use high assurance only for security/secrets, irreversible migrations, production/release, cross-repo invariants, or lottery future-data/frozen-ledger/provenance/commit-reveal-score/parser integrity. Never weaken correctness/safety invariants. Games/exploration: playable prototype first.
