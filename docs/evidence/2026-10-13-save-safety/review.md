# C save-safety review and verification

Independent read-only static reviewer: save_review. Important finding: an unnecessary backup rollback could erase the sole valid backup after failed primary replacement; backup restore/rollback results were unchecked. Five newly failing assertions reproduced the loss. Correction pre-stages the prior backup, skips backup rollback when no primary existed, checks rollback results and preserves/reports verified recovery stages on failure. All resulting regressions passed, including failed active replacement, failed backup replacement/rollback and partial recovery adapter.

Review limits: Windows, physical power loss, concurrency, symlink behavior and target device were not independently tested. No claim of disk fsync or atomic Windows overwrite is made. Pinned engine source confirms Unix fflush and Windows delete-before-move. Added malformed UTF8 regression separately went RED→GREEN; raw invalid bytes are preserved/quarantined, valid Urdu/emoji round trips and eight malformed encoding vectors pass.

Original regression13 failures→GREEN; settings failure assertion→GREEN; recovery finding5 failures→GREEN. Final67 save assertions,8 actual process kills and state/startup/panel checks passed on exact4.7.2. Python14/14, JavaScript6/6 plus syntax passed. Initial mutation4/5 showed first-write coverage gap; missing first-write test killed the survivor. Final source rerun killed5/5 targeted mutants (reward mutation caused the expected assertion/timeout). No parse-error mutant is counted as killed. Formal third-party mutation/framework adoption remains unapproved.

No AI/packaging/catalog/source-lock/signing change. No new screenshots, installer/package/APK, signature or genuine local model execution. Logs contain isolated fixtures only; binaries/model weights/personal saves are not committed.

Exact engine interruption banners/npm syntax stdout (including terminal blank lines) are retained in exact-interruption-and-syntax-output.json with original byte lengths/digests; separate uncommitted duplicate .log copies were omitted. Original work/ captures are unchanged.
