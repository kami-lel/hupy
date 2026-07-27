# Version Grep (VG) Documentation

**Version Grep (VG)** extracts a repo's canonical version string by regex-matching a line in a configured file, at a given git ref — the source [Prepend Commit Header](pch_doc.md) stamps into merge commit messages, and the source [Version Uniformity](#version-uniformity) checks every other occurrence against.

### `version_occurrences`

A list of `{file, glob, remark}` entries, each naming a place the version string appears:

| Field | Required | Meaning |
|---|---|---|
| `file` | yes | file path, relative to repo root |
| `glob` | yes | regex matched line-by-line against `file`; its first capture group `( )` is the version on that line |
| `remark` | no | description/name of the entry, used only in logger output |

**The first entry is canonical** — the version VG greps and every other entry is checked against.

### Version Uniformity

Beyond the first entry, every configured occurrence is checked for **Version Uniformity**: the same version string must appear, unchanged, in each one — a `pyproject.toml` version bumped without also updating a shipped config asset, a README badge, or a doc header no longer slips through unnoticed.

| Config Field | Effect |
|---|---|
| `disable_version_uniformity` | turn the check off; VG itself keeps running |
| `allow_version_uniformity_failure` | downgrade a drifted occurrence to a warning instead of blocking the commit |

Version Uniformity runs in the pre-commit, pre-merge-commit, and pre-applypatch stages — see the [Hook Chain](chain_doc.md) for where each fits — and is also reported (never enforced) by `hupy verify`.
