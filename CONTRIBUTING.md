# Contributing to FinVerify

**Thank you for taking the time to contribute.** FinVerify is a stronger system
because people who care about correctness — and about getting it *provably*
right — are willing to poke holes in it.

This document covers everything you need to get from zero to a merged pull
request.

---

## 📑 Table of contents

1. [What we're looking for](#-what-were-looking-for)
2. [Legal ground rules](#-legal-ground-rules)
3. [Getting set up](#-getting-set-up)
4. [Making a change](#-making-a-change)
5. [Commit conventions](#-commit-conventions)
6. [Testing](#-testing)
7. [Opening a pull request](#-opening-a-pull-request)
8. [Review and merge policy](#-review-and-merge-policy)
9. [Code style](#-code-style)
10. [Project layout](#-project-layout)
11. [Areas that always need help](#-areas-that-always-need-help)
12. [Reporting bugs](#-reporting-bugs)
13. [Code of conduct](#-code-of-conduct)

---

## 🎯 What we're looking for

FinVerify exists to make financial LLM output **verifiable**. Contributions
that move that goal forward:

| ✅ High value | ⚠️ Low value | ❌ Not accepted |
|---|---|---|
| New deterministic operations in the DSL, with exact-arithmetic tests | Refactors with no behavioural change | Any change that introduces an LLM call into the verification path |
| New XBRL tag mappings with EDGAR-backed fixtures | Formatting-only churn across the whole tree | "Self-check" heuristics that ask a model to grade a model |
| New input formats or parser robustness | Dependency bumps with no security or feature rationale | Loosening the tolerance tiers without a benchmark to justify it |
| Tests that break the engine, the signer, or the ledger | | Removing or disabling existing tests |
| Reproductions of a real-world hallucination | | Hard-coded secrets, keys, or `.env` files |
| Better reviewer ergonomics and audit trails | | Bypassing the `unverifiable` → human-review path |
| Docs, diagrams, and explanations | | Contributions you do not have the right to license |

### The four non-negotiables

Every contribution must preserve these. If a change breaks one of them, it
will not be merged, regardless of how good it otherwise looks.

1. **No LLM performs verification arithmetic.** The engine stays pure
   SymPy/NumPy.
2. **Tolerance tiers are fixed**: `≤0.2% pass` · `0.2–1% pass_with_warning` ·
   `>1% fail`.
3. **`unverifiable` never becomes `fail`.** Unresolvable input routes to a
   human.
4. **The ledger stays append-only.** No `UPDATE`, no `DELETE` on certificates
   or reviewer decisions.

---

## ⚖️ Legal ground rules

FinVerify is **proprietary** — see [`LICENSE`](LICENSE). Please read §4 and §6
before you submit anything.

**By opening a pull request you agree that:**

- Your contribution is your **original work**, and you have the right to
  submit it under the terms below.
- You **grant the project a perpetual, irrevocable, worldwide, royalty-free,
  sublicensable, transferable licence** to use, reproduce, modify, distribute,
  and otherwise exploit your contribution as part of FinVerify — including the
  right to relicense FinVerify as a whole.
- You **retain copyright** in your contribution. We never claim ownership of
  your work.
- You understand that **we are under no obligation to merge** your pull
  request, and that we may close, re-scope, or decline it.
- Your contribution is provided **"as is", without warranty**.

If your employer requires a different agreement, or your contribution is
derived from work you are contractually barred from licensing, **do not open a
PR** — contact the maintainer first at the address in [`SECURITY.md`](SECURITY.md).

Contributions are merged and distributed under the
[FinVerify Proprietary License v1.0](LICENSE).

---

## 🛠️ Getting set up

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | 3.14 also works locally |
| Node.js | 20+ | For the dashboard |
| Docker | 24+ | For the full stack |
| Docker Compose | v2 | `docker compose`, not `docker-compose` |

### Clone and run

```bash
git clone https://github.com/<your-username>/finverify.git
cd finverify
git remote add upstream https://github.com/Meet6338-X/finverify.git

cp .env.example .env
# edit .env: set JWT_SECRET, POSTGRES_PASSWORD, and a real SEC_EDGAR_USER_AGENT

docker compose up --build -d
```

Verify the stack is alive:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/public-key
open http://localhost:3000
```

### Local development

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

uvicorn src.api.main:app --reload --port 8000   # API
python -m src.workflows.worker                   # worker, separate shell

cd frontend && npm install && npm run dev        # dashboard, third shell
```

### The fast loop — the validator

The `validator/` proof pack is the fastest way to know your change didn't break
the core guarantees. It is standalone, needs no Docker or database, and never
imports `src/`.

```bash
pip install -r validator/requirements.txt
python validator/run_all.py
# expect: PERFECT SCORE 100/100 — ALL PROOFS PASS
```

---

## ✏️ Making a change

### Branch naming

```
<type>/<short-description>
```

| Type | Use for |
|---|---|
| `feat/` | New capability (new DSL op, new parser format, new endpoint) |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `test/` | Tests only |
| `refactor/` | Behaviour-preserving restructuring |
| `ci/` | Pipelines, Docker, tooling |
| `perf/` | Performance work |
| `chore/` | Maintenance, dependency bumps |

Examples: `feat/engine/dividend-payout-ratio`, `fix/edgar/rate-limiter-drift`,
`docs/clarify-tolerance-tiers`.

### Keep your branch small

One logical change per pull request. A PR that touches the engine, the
dashboard, and the Dockerfiles is three PRs — and it will take three times as
long to review, which is the opposite of what you want.

### Update the docs with the code

If you change an endpoint, update the API table in `README.md`. If you add a
DSL operation, update the DSL table **and** `validator/engine_proof.py` — the
validator is the independent proof, and an operation without a proof is an
untested operation.

---

## 📝 Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

[optional body]
[optional footer]
```

- `type` — `feat`, `fix`, `docs`, `test`, `refactor`, `ci`, `perf`, `chore`, `build`
- `scope` — the module: `engine`, `crypto`, `edgar`, `parser`, `api`, `worker`, `frontend`, `docker`
- `subject` — imperative mood, no trailing period, ≤ 72 characters

Examples:

```
feat(engine): add dividend_payout_ratio operation
fix(crypto): preserve unicode in canonical JSON serialization
test(edgar): cover token bucket under burst traffic
docs(readme): document the unverifiable review path
```

Use `git commit -s` to add the `Signed-off-by` trailer.

---

## 🧪 Testing

Every pull request must have passing CI. Run the same three legs locally.

```bash
# 1 — backend suite
pytest tests/ -v

# 2 — validator proof pack
pip install -r validator/requirements.txt
python validator/run_all.py

# 3 — frontend build
cd frontend && npm ci && npm run build
```

### What a good test looks like

- **Deterministic.** No network, no clock dependence, no randomness without a
  fixed seed.
- **Independent.** Prove the property, not the implementation detail. Assert
  the *status* and the *tolerance boundary*, not that a helper was called.
- **Named for the behaviour.** `test_tolerance_boundary_at_0_2_percent_is_pass`
  beats `test_engine_3`.
- **Regression-tested.** Every bug fix ships with the test that would have
  caught it.

### Tolerance boundaries are sacred

If you touch the engine, add explicit boundary cases:

```python
def test_tolerance_boundary_exactly_at_limit():
    # 0.2% exactly → pass
    # 0.2% + epsilon → pass_with_warning
    # 1.0% exactly → pass_with_warning
    # 1.0% + epsilon → fail
    ...
```

---

## 🔀 Opening a pull request

1. **Sync** — `git fetch upstream && git rebase upstream/main`
2. **Branch** — `git checkout -b feat/your-change`
3. **Commit** — small, focused commits with Conventional Commit messages
4. **Test** — run all three CI legs locally
5. **Push** — `git push -u origin feat/your-change`
6. **Open the PR** from your fork, filling in the template
7. **Watch CI** — push again to re-trigger if a flake appears

### PR description checklist

- [ ] **What** — one paragraph: what changed and why.
- [ ] **Why** — the problem this solves, or the bug it fixes.
- [ ] **How** — the approach, and anything a reviewer should know.
- [ ] **Testing** — what you ran, and what the results were.
- [ ] **Guarantees** — confirm the four non-negotiables still hold.
- [ ] **Screenshots** — for dashboard changes.
- [ ] **Docs** — README/API docs updated where relevant.
- [ ] **Contributor terms** — you have read the legal section above and your
      contribution is your original work.

### PR titles

```
<type>(<scope>): <subject>
```

Same as commits. Keep it under 72 characters.

### Labels

| Label | Meaning |
|---|---|
| `good first issue` | Small, well-scoped entry point |
| `engine` / `crypto` / `edgar` / `parser` / `api` / `worker` / `frontend` | Area |
| `documentation` | Docs |
| `bug` / `enhancement` | Type |
| `needs-review` | Awaiting maintainer eyes |
| `blocked` | Waiting on something else |

---

## 🔍 Review and merge policy

### How review works

1. **CI must be green.** No exceptions for "I'll fix it in the next PR".
2. **A maintainer reviews** every PR. Expect one round of comments; a good
   reply addresses the point, not just the symptom.
3. **We prefer asking questions over closing PRs.** If something is unclear,
   we will ask. If it turns out to be not the right direction, we will explain
   why and often point you at a better-scoped change.
4. **We may ask for changes** — style, naming, test coverage, or an
   architectural concern. These are not rejections.

### Merge criteria

A PR is merged when **all** of the following hold:

- [ ] CI is green (backend tests, validator proof pack, frontend build).
- [ ] The four non-negotiable guarantees are intact.
- [ ] Tests cover the new behaviour, including boundary cases.
- [ ] Documentation is updated where the change is user-visible.
- [ ] The diff is focused — no unrelated churn.
- [ ] A maintainer has approved it.

### How we merge

- **Squash** by default — a clean, single-commit history on `main`.
- The PR title becomes the commit subject, so use Conventional Commits.
- Branch is deleted after merge.
- `main` is the protected, canonical branch. We do not maintain a `develop`
  branch.

### What we will not merge

- Changes that call an LLM inside the verification path.
- Changes that loosen the tolerance tiers without benchmark evidence.
- Changes that turn `unverifiable` into `fail`.
- Changes that add `UPDATE`/`DELETE` paths to the ledger.
- Large auto-generated diffs with no explanatory narrative.
- Anything you do not have the right to license under the terms above.
- Dependencies with known critical vulnerabilities and no mitigation plan.

### Response time

We aim to acknowledge a new PR within **7 days**. We are a small project with
day jobs; a slow response is not a rejection. Feel free to ping the PR after
a week.

---

## 🎨 Code style

There is no linter config in the repo yet, so match the surrounding code.

### Python

- PEP 8, 4-space indent, ~100-character lines.
- Type hints on public functions.
- Docstrings on modules and non-obvious functions. Explain *why*, not *what*.
- `from __future__ import annotations` is not used here; match the file.
- Prefer `pathlib.Path` over string paths.
- No bare `except:` — catch `Exception` and log, or catch the specific error.

### React / JavaScript

- Functional components with hooks.
- Tailwind utility classes; avoid inline styles except for computed values.
- Keep API calls in `frontend/src/api/client.js`.
- `tweetnacl` handles verification in the browser — never send a public key
  to the server for verification.

### Secrets

Never commit `.env`, `keys/`, or `*.pem`. They are already git-ignored — keep
it that way.

---

## 🗂️ Project layout

```
src/
├── api/           FastAPI app, routes, schemas
├── crypto/        Ed25519 signer, canonical JSON, QR
├── db/            Models, async connection, init.sql
├── extractor/     Claim extraction
├── ingestion/     SEC EDGAR client
├── parsers/       Document parsers
├── reexecutor/    ★ Deterministic engine
├── reports/       PDF generation
└── workflows/     Temporal workflow, activities, worker
frontend/          React dashboard
tests/             Test suite
validator/         Standalone proof pack
```

---

## 🧭 Areas that always need help

| Area | Why it's useful |
|---|---|
| **DSL operations** | New financial ratios, with exact-arithmetic tests and validator proofs |
| **XBRL tag coverage** | More `us-gaap:*` mappings = more claims verifiable automatically |
| **Parser formats** | Tables, markdown, HTML, messy PDF layouts |
| **Benchmark datasets** | Real-world error-injection sets beyond FinQA |
| **Dashboard UX** | Reviewer queue ergonomics, trace visualisation, keyboard flows |
| **Docs & diagrams** | Architecture docs, a hosted demo, onboarding guides |
| **CI hardening** | Coverage gates, dependency scanning, matrix testing |

---

## 🐛 Reporting bugs

Open an issue with:

- What you did, what you expected, what happened instead.
- The smallest reproduction you can manage.
- Environment: OS, Python/Node version, Docker or local.
- Relevant log output — **redact secrets and `.env` values**.

For anything that looks like a **security vulnerability**, do **not** open a
public issue. Follow [`SECURITY.md`](SECURITY.md).

---

## 📜 Code of conduct

Participation is governed by the
[Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating you agree to
uphold it. Report unacceptable behaviour to the address in
[`SECURITY.md`](SECURITY.md).

---

## 💬 Questions?

Open a **Discussion** on the repository. No question is too basic — everyone
started somewhere.

<div align="center">

**Happy hacking.** 🛡️

</div>
