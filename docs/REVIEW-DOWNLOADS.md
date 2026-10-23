# Download availability — 2026-10-23

These are private Windows development/review builds, not completed production releases. Sign in to GitHub with source-repository write access, open the linked draft, expand Assets, and download the named executable or ZIP. Anonymous users and read-only collaborators cannot download private drafts. Source ZIPs are not installers. No public download gate has been enabled.

| Product | Windows PC | Android mobile |
|---|---|---|
| Hub | [Inspected private draft](https://github.com/SyedSU/EvidenceNeuterHub/releases/tag/untagged-7b20d5c95fcb89605e63), `EvidenceNeuterHub-Setup-0.3.0.exe` | No APK available |
| Genesis | [Inspected private draft](https://github.com/SyedSU/EvidenceGenesis/releases/tag/untagged-00f34a49e1704f991789), `EvidenceGenesis-Windows-v0.5.0.zip` | No APK available |
| Flow | [Download page](https://github.com/SyedSU/EvidenceFlow/releases/tag/untagged-56d7b98fb9d5032dadfd), `EvidenceFlow-Windows-x64-review.zip` | No APK available |
| Council | [Download page](https://github.com/SyedSU/EvidenceCouncil/releases/tag/untagged-5f31fe0f7b4e0e799a6c), `EvidenceCouncil-Windows-x64-review.zip` | No APK available |
| Academy | [Download page](https://github.com/SyedSU/EvidenceAcademy/releases/tag/untagged-d4829b31c9d2479645e4), `EvidenceAcademy-Windows-x64-review.zip` | No APK available |
| Lab | [Download page](https://github.com/SyedSU/EvidenceLab/releases/tag/untagged-23a3a4fb3c2c7fa62eed), `EvidenceLab-Windows-x64-review.zip` | No APK available |
| Bot | [Download page](https://github.com/SyedSU/EvidenceBot/releases/tag/untagged-d097c6b74fdaa1780b18), `EvidenceBot-Windows-x64-review.zip` | No APK available |

For portable ZIPs, extract the complete folder before opening the product executable. Do not run an executable directly inside the ZIP or discard the native DLL. The five new apps do not bundle an AI model/server; their local AI features require a separately configured loopback server. Genesis's complete Windows ZIP includes its pinned runtime/model. Hub's production trust/metadata configuration remains gated; its review installer is not proof that approved product installation is enabled.

These packages are unsigned. Checksums verify retained bytes, not a production publisher identity. No advice to disable operating-system security protections is given. Use isolated review profiles and preserve existing work; physical-target acceptance and full release testing remain open.

Android requires more engineering, exports/model delivery, owner-controlled signing and genuine device/lifecycle/inference acceptance. Hub's WinForms UI is Windows-only; a mobile implementation remains required. Bot voice/accessibility and Lab neural speech/cloning remain incomplete. No fake APK links, debug signing identity or Android parity is provided.

The [website](https://evidence-neuter.vercel.app) can be visited in a browser; it is not an APK or PC installer. [EvidenceNeuter-Releases](https://github.com/SyedSU/EvidenceNeuter-Releases) holds release contracts/evidence rather than an installable application. See RELEASE-STATE.md for current scope and gates.

All five portable builds passed actual Windows CI, PE0.1.0.0 readback, extracted-ZIP native save/read and main-scene smoke; server SHA256/size match the locally tested package. [Exact source/run/asset hashes](evidence/2026-10-23-windows-portables/results.json). All five also passed [independent re-download inspection](evidence/2026-10-23-windows-portables/redownload-inspection.json): four exact asset hashes, receipt/source identity, archive/manifest parity, native persistence and headless UI initialization. This does not establish rendered UI or physical target acceptance.
