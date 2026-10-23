# GitHub private review build storage

The owner chose to stay on GitHub and fix build distribution/storage. Main Windows builds now retain tested packages in draft GitHub Releases in the private product source repositories. This replaces Actions artifact storage for main build retention; it does not change the protected public distribution pipeline.

## Access and identity

Repository users with push/write access can see draft releases. They are not public releases and are not strictly owner-exclusive. Open the source repository's Releases page and select the **Review hub** or **Review genesis** draft. Its tag includes the full source commit, Actions run ID and run attempt. The draft contains review-build.json with asset sizes and SHA256 values. The storage step checks exact filenames/sizes and GitHub server-reported SHA256 values before reporting success. Checksums identify bytes; they are not publisher signatures.

- [Hub review-build instructions](https://github.com/SyedSU/EvidenceNeuterHub/blob/main/docs/REVIEW-BUILDS.md)
- [Genesis review-build instructions](https://github.com/SyedSU/EvidenceGenesis/blob/main/docs/REVIEW-BUILDS.md)

The first-party guard requires the exact private source repository, main branch, allowed push/manual event, complete immutable source/run identity, clean tracked build source and bounded regular outputs. Failed or interrupted uploads can leave a partial private draft; it is not reported as a successful stored build and is never silently overwritten/deleted. A new Actions run attempt gets a new tag. No historical cleanup or storage purchase is part of this mechanism.

## Permissions and gates

The main job runs the actual Windows build/test acceptance steps before storage. Its contents-write permission is scoped to that repository; GH_TOKEN is passed only to the storage step and checkout does not persist credentials. Feature/pull-request testing remains in a separate read-only job. No cross-repository PAT, production signing key or public-distribution environment is used.

Public prereleases, stable releases, website/Hub download enablement and promotion into EvidenceNeuter-Releases remain blocked by their existing gates. These private drafts retain engineering evidence for inspection; they do not waive signing/license, target-device, Android parity or protected-publication requirements. Old source/build locks retain their original identities.

To resume inspection, download the authenticated draft's assets into a separate workspace, compare the bytes to review-build.json, inspect package contents and required notices, and record acceptance against the exact source/run/archive. Back up saves and use isolated test profiles for development packages. No test build should replace a production installation by implication.
