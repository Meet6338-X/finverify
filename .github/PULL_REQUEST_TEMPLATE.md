<!--
Thanks for contributing to FinVerify! 🛡️
Keep this template filled in — it makes review dramatically faster.

Every PR must have green CI:
  • pytest tests/ -v
  • python validator/run_all.py
  • cd frontend && npm run build
-->

## What this PR does

<!-- One paragraph. What changed and why it matters. -->

Closes #

## Why

<!-- The problem, the bug, or the gap this closes. Link the issue. -->

## How

<!-- The approach. Anything a reviewer needs to know to evaluate it. -->

## Type of change

- [ ] 🐛 Bug fix (non-breaking)
- [ ] ✨ New feature (non-breaking)
- [ ] 💥 Breaking change
- [ ] 📚 Documentation
- [ ] ♻️ Refactor (no behaviour change)
- [ ] ⚙️ Build / CI / tooling
- [ ] 🔐 Security

## Checklist

- [ ] CI is green
- [ ] Tests added or updated for this change
- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Validator proof pack still passes (`python validator/run_all.py` → `PERFECT SCORE 100/100`)
- [ ] The four non-negotiable guarantees are intact:
  - [ ] No LLM performs verification arithmetic
  - [ ] Tolerance tiers unchanged (`≤0.2% pass` · `0.2–1% pass_with_warning` · `>1% fail`)
  - [ ] `unverifiable` is never converted to `fail`
  - [ ] The ledger remains append-only (`INSERT`-only)
- [ ] Documentation updated (README / API table / DSL table) where user-visible
- [ ] `validator/` proofs updated if the engine or crypto layer changed
- [ ] No secrets, `.env` files, or key material in the diff
- [ ] No unrelated refactors or formatting churn

## Testing

<!-- What you ran, and the results. Paste relevant output. -->

```
$ pytest tests/ -v
...

$ python validator/run_all.py
...
```

## Screenshots

<!-- Required for dashboard changes. Remove this section otherwise. -->

| Before | After |
|---|---|
|  |  |

## Additional notes

<!-- Anything else: trade-offs, follow-ups, areas needing a second opinion. -->

---

**Contributor terms.** By opening this PR I confirm that this contribution is
my original work, that I have the right to license it, and that I agree to the
contribution terms in [`CONTRIBUTING.md`](../CONTRIBUTING.md) and §4 and §6 of
the [`LICENSE`](../LICENSE).
