# Phase 1 Release State Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this documentation phase inline. Owner has already authorized execution/main updates; no extra design approval or product implementation is requested.

**Goal:** Install one canonical, evidence-based release state and owner brief with pointers in all four repositories.
**Architecture:** Releases owns RELEASE-STATE.md, docs/RELEASE-BRIEF.md, docs/DEPENDENCY-LOG.md and durable dated evidence. Each consumer has root AGENTS/state and docs/brief pointers; Genesis guidance stays intact. Existing product source, trust/catalogs, source locks and workflows stay unchanged.
**Tech Stack:** Markdown/JSON evidence, existing Git and Python for document verification; no dependencies added.
**Spec:** docs/RELEASE-BRIEF.md §7.2 and the owner command `/BUILD PHASE 1 STATE`.

## Global Constraints

- One phase only; no product fixes, publication, signing or download activation.
- Exactly one A/B/C/D class per requirement family; PASS/FAIL/UNRUN kept distinct.
- Actual source/build identities and historical evidence preserved; no new artifact hashes claimed.
- No credentials, private keys, personal saves, model weights or binaries committed.
- Direct main execution owner-authorized; fetch/rebase before push, no force push or protection bypass.

## Review Focus

- Local synthetic/older-engine tests incorrectly promoted to signed Windows/device acceptance.
- Missing requirement families or duplicate/ambiguous A/B/C/D classifications.
- Broken consumer pointers, conflicting duplicated state, or lost Genesis instructions.
- Invented vetting/source pins or credentials/production settings treated as known.
- Documentation commits falsely relabeling old build artifacts/source locks.

## Task 1: Canonical ledger, dependencies and durable evidence

**Files:** RELEASE-STATE.md; docs/RELEASE-BRIEF.md; docs/DEPENDENCY-LOG.md; docs/evidence/2026-10-13/*.
**Interfaces:** Consumes owner-uploaded sections1–9/AppendixR and actual Phase0 outputs; produces the canonical state/dependency/evidence targets consumed by Task2.

- [x] Refresh environment, fetch exact remote mains and preserve starting SHAs; capture command outputs.
- [x] Write feature/acceptance matrix, blockers/owner steps, decisions, five evidence layers, proposed budgets/design/recovery notes.
- [x] Record existing dependencies with unverified fields pending; preserve selected exact audit logs and digests.
- [x] Verify unique46 requirement IDs/classes, all local evidence links/digests, required brief sections and unchanged locks/gates; expected PASS for document integrity, existing consumer validation still FAIL K02.
- [ ] Commit the complete canonical documentation after review.

## Task 2: Consumer guidance and coordinated handoff

**Files:** All four AGENTS.md; three consumer RELEASE-STATE.md/docs/RELEASE-BRIEF.md pointers.
**Interfaces:** Consumes Task1 canonical paths, produces durable session entry points with existing Genesis guidance retained.

- [x] Add short canonical guidance and pointers; preserve original Genesis instructions byte-for-byte after preface.
- [x] Verify canonical GitHub/sibling paths, documentation-only changed paths, source SHA identities and disabled catalog gates; run existing distribution49 tests as a provenance/regression check.
- [ ] Review whole documentation change, resolve material findings, commit each clean main; fetch/rebase and repeat verification before non-force push.
- [ ] Report actual commit/push results, tests and unchanged release blockers; stop at Phase1.

Documentation-only verification replaces implementation TDD here: no product behavior or runtime feature is added, and the owner requests a state ledger. Native/UI/model/installer checks are retained as historical scoped evidence, not rerun or promoted by this phase. No skill automation scripts/new test dependencies are adopted.
