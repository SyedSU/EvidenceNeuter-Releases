# Distribution Contract Implementation Plan

**Goal:** Fail-closed shared distribution metadata and reproducible package tooling.
**Architecture:** Strict JSON schemas, Python validation/signing, protected manual publishing.
**Tech Stack:** Python, jsonschema, cryptography, GitHub Actions.
**Spec:** docs/CONTRACT.md

## Global Constraints
No production keys, releases, binaries or models committed. Genesis schema1 remains compatible.

## Review Focus
Expired/replayed metadata, tampered signatures, fabricated URLs, unsafe archive paths, mismatched source versions must reject.

### Task 1: Contract validation
- [x] Write catalog tests, observe missing validator failure.
- [x] Implement strict schemas and validation with authentication and gates.
- [x] Verify unsigned development catalog succeeds but public enabling fails.

### Task 2: Packaging and publication
- [x] Test deterministic packaging, traversal rejection, signing tamper/expiry and version lock.
- [x] Implement offline CLI tools and protected manual approval workflow.
- [x] Document metadata renewal/key recovery and production prerequisites.
- [x] Run entire test suite, commit, push, open PR without publishing.
