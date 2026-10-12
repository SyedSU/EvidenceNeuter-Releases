# Public download activation: main milestone

The owner authorizes publication and direct main updates. Existing feature work was preserved by fast-forwarding main to reviewed implementations. This document supersedes old statements that publication is unauthorized. Authorization alone does not provide private signing keys, a known Windows publisher or protected deployment configuration. All public download gates remain false until genuine checks pass.

## Exact observed blockers

- Hub and distribution configuration APIs returned403 for secrets/variables; those bindings are unknown.
- No protected Hub/Genesis/distribution environments existed at inspection. Required environments must not be created unprotected by workflow dispatch.
- This runtime has no secret/identity bindings. Do not paste secrets in chat or commit them.
- GitHub Actions artifact upload quota is exhausted. Hub7855306 and Genesis541cd71 built/tested successfully, but their artifact uploads failed. Preserve pinned historical artifacts. An administrator can remove selected superseded build artifacts after retaining required evidence, or adjust storage billing; quota recalculation can take6–12hours. No deletion/purchase is performed here.
- No public release currently exists. No direct installer URL, actual installer hash/size, accepted publisher certificate or signed public metadata has been verified. Old artifact wrapper hashes are not installer hashes.

## Configure securely

1. Provision the approved code-signing publisher certificate/private-key provider in the protected Windows runner certificate store/HSM. Public selectors: `HUB_SIGNING_CERT_SHA1` and independently reviewed uppercase SHA256 certificate-DER `HUB_PUBLISHER_SHA256`. No production self-signed/test certificate.
2. Configure independent RSA-PSS3072+ catalog, Genesis and Hub metadata signing roles; retain private keys offline/HSM/protected signing infrastructure. Public build pins: `CATALOG_RELEASE_PUBLIC_KEY_PEM`, `GENESIS_RELEASE_PUBLIC_KEY_PEM`, `HUB_RELEASE_PUBLIC_KEY_PEM`, `CATALOG_URL`. Distribution verifier variables: `DISTRIBUTION_PUBLIC_KEY_PEM`, `GENESIS_MANIFEST_PUBLIC_KEY_PEM`, `HUB_MANIFEST_PUBLIC_KEY_PEM`, same publisher pin.
3. Configure existing approved protected environments with human reviewers, no self-review/admin bypass and main-only branch policy: distribution-release, distribution-candidate, hub-signing; Genesis publication additionally needs genesis-build and genesis-release in Hub. Use environment metadata read permission for read-only guards. Do not relax website's existing Production/Preview approvals.
4. Private source reads across repositories require least-privilege GitHub App/fine-grained credentials scoped to the exact source repo. Distribution write credentials belong only in protected publication environment; a default GITHUB_TOKEN in another repository is insufficient. `GENESIS_SOURCE_READ_TOKEN` and `DISTRIBUTION_WRITE_TOKEN` are existing workflow bindings. No credentials are embedded in clients.

## Concrete publication order

1. Rebuild exact reviewed main commits with production public trust pins. Sign Hub executable and bootstrapper before NSIS packaging; then sign/timestamp/verify the installer against the approved publisher. Run Windows smoke and approved-publisher/bootstrap acceptance. Retain exact SHA256/size and acceptance logs.
2. Build Genesis0.5.0's separate game/runtime/model archives, real-model smoke and deterministic byte-parity report from its exact reviewed commit. Keep models/runtime independent; verify upstream revisions, hashes and license notices. Retain actual archives/report outside source control.
3. Obtain genuine same-epoch0.4→0.5 update/rollback and a newer genuine Hub installer for publisher self-update acceptance. Synthetic test packages are not proof of these public journeys.
4. Feed actual archives/report, reviewed immutable tags/URLs, fresh sequence/expiry, pins and Windows acceptance into `tools/prepare_release.py`; sign Hub and Genesis manifests with the real approved roles. No generated URL is evidence of an existing asset.
5. Publish immutable versioned assets/manifests to SyedSU/EvidenceNeuter-Releases through protected manual publication. Never clobber versioned assets. Verify anonymous HTTPS availability, sizes, hashes and independent envelope signatures.
6. Test genuine public fresh install, import/reuse, update, cancellation, interrupted transfer, save preservation, offline Play and compatible rollback. Verify self-update with the actual approved publisher. Record real evidence bound to each artifact.
7. Sign catalog last with every gate backed by evidence. Run `tools/verify_bundle.py`, stage exactly the signed catalog/Hub mirror/pins into website and rebuild pinned clients where needed. Push reviewed website main to the existing Vercel project and verify production HTTP/links. The website currently offers a truthful public-repository link, not a working installer download.

None of these steps is marked passed just because a workflow was prepared or an unsigned candidate built. Existing updater is deliberately limited single-role trust, not full TUF; root rotation/revocation and transactional Hub rollback remain documented gaps.
