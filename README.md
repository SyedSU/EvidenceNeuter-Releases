# EvidenceNeuter distribution contract

Public metadata/tooling only. No production keys, downloadable releases, runtime/model binaries or installers exist in this change. Development catalog intentionally disables downloads.

Install tooling with `python -m pip install -r requirements.txt`; run `python -m unittest discover -s tests -v` and `python tools/distribution.py validate-catalog catalog/development.json`.

Canonical strict JSON schemas are in `schemas/`; website and Hub share `catalog/development.json` and [contract](docs/CONTRACT.md). Signed Genesis schema1 stays compatible with Hub0.2; new catalog and signed Hub installer manifest use separate locators. Target Hub0.3.0, Genesis0.4.0, save compatibility schema4.

[Protected release operations](docs/RELEASE-OPERATIONS.md) covers packaging, source locks, signature verification, metadata renewal and key recovery. `catalog/source-lock.json` pins reviewed Hub0.3.0 and Genesis0.4.0 with saveSchema4 after matching Windows candidate builds; signing CLI refuses missing/mismatched provenance. Compatible source locks do not supply production trust or signed artifact acceptance. Runtime/model versions come from actual approved build evidence.

The optional manual publication workflow requires protected human review and independently configured trust. This task never invokes it, creates public releases or enables download gates.

Production preparation is reviewable through [blocked configuration](release/preparation.json), [candidate provenance](release/reviewed-candidates.json), and `tools/prepare_release.py`. Actual archives and externally reviewed acceptance evidence remain outside Git. `tools/verify_bundle.py` provides real anonymous signed-bundle verification with explicit role trust and replay floors; its output never authorizes publication.
