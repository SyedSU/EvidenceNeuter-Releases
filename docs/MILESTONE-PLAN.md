# Coordinated implementation plan

Execution: four repository owners in isolated worktrees, root coordinating shared contract first and independent review after implementations. User has explicitly authorized this method and unattended routine decisions.

1. D finalizes catalog/package/bootstrapper schemas, development blocked catalog, signing/publication/renewal tools and tests; public repository PR to main.
2. C implements menu/profiles/onboarding/task recovery/documents/settings and schema4, real native tests and screenshots, packaged Windows candidate; PR to feat/native-game, depends on existing PR2.
3. B implements catalog consumer, dark nativeUI/settings/storage/updater hardening and separate pinned selfupdate bootstrapper; Windows test installer/screenshots and security tests; PR to feat/hub-foundation, depends existingPR1 and D contract.
4. A implements static portal/catalog consumer with disabled blocked downloads, screenshots from C, usable animation fallback, responsive/keyboard/performance tests, preview attempt; PR to main, depends D catalog/C screenshots.
5. Root runs consumer-contract checks, inspects meaningful source/CI results, dispatches independent security+game/web review, routes required fixes to owningagents, reruns affected checks and captures artifact links.
6. Final perrepo handoff with exact user install/update steps, tested vs untested matrix, explicit no public/prod readiness absent authentic keys/assets/genuineWindowsacceptance, retained review branches/worktrees.

Review focus: unsigned catalog erroneously enabling download; malformed active state/paths deleting user content; selfupdate accepting caller-provided key/publisher/path; profile switch or crash duplicating task/reward; legacy save import overwriting original. Each owner adds relevant negative tests before claiming completion.
