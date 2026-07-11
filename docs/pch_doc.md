
<!-- TODO PCH doc -->


## `hupy.pch` Module

**Prepend Commit Header** is *HUPy*'s `prepare-commit-msg` hook. When you make a **merge commit**, it adds a short header line to the top of the commit message so the history reads clearly at a glance — you don't have to write it yourself.

It recognizes every merge type listed under [Merge Type](#merge-type) above and leaves every other commit (`REGULAR_COMMIT`, `OTHER_MERGE`) untouched. The header goes on the first line, followed by a blank line and then git's original message:

```
Feature Landing: add-user-auth

Merge branch 'add-user-auth' into dev
```

### Header Format

| Merge Type | Header |
|---|---|
| Feature Landing | `Feature Landing: <source-branch-name>` |
| Version Release | `<bump><release-type>: <version>`, eg `Minor Prototype Release: 0.4.0`, `Alpha Release: 1.3.0-alpha.1`, `Release Candidate: 1.3.0-rc.1` — see [Version Release Header](#version-release-header) below; falls back to `Version Release: <version>` when the version doesn't parse, or plain `Version Release` with no version at all |
| Sync Backport | `Sync Backport from: <version>` or plain `Sync Backport` |
| Catch Up | `Catch Up: <target-branch-name>` |
| Hotfix Release | `<bump>Hotfix Release: <version>` or plain `Hotfix Release` |
| Hotfix Backport | `Hotfix Backport from: <version>` or plain `Hotfix Backport` |
| Release Cut | `<bump>Release Cut: <version>` or plain `Release Cut` |
| Release Backport | `Release Backport from: <version>` or plain `Release Backport` |

`<bump>` is `Major `/`Minor `/`Patch `/*(none)*`, comparing the source and target branch versions via `ver_grep`; empty when no bump is detected or a version doesn't resolve.

#### Version Release Header

`<release-type>` is chosen by checking the resolved version against the `pch` config (see [`.hupy.config.json` Documentation](hupy_config_doc.md#pch)), in this order:

1. `alpha_tag`/`beta_tag`/`release_candidate_tag` found as a substring of the version → `Alpha Release`/`Beta Release`/`Release Candidate` (each check skipped if its tag is left empty)
2. `enable_pre_alpha` and a `0.9.z` core → `Pre-Alpha Release`
3. `enable_vertical_slice` and a `0.5.z`–`0.9.z` core → `Vertical Slice Release`
4. any other `0.x.z` core → `Prototype Release`
5. `>=1.0.0` core → `Stable Release`
6. otherwise → unparsable, falls back to the plain header above

`<bump>` is always empty for Alpha, Beta, and Release Candidate releases, even when a bump would otherwise be detected.













### `prepend_commit_header(repo)`

The main entry point of the module. Call it during an in-progress commit (e.g. from a `prepare-commit-msg` hook) to prepend the appropriate header to `COMMIT_EDITMSG`, based on the commit type reported by `get_current_commit_type`.

```python
import git
from hupy.pch import prepend_commit_header

repo = git.Repo(".", search_parent_directories=True)
prepend_commit_header(repo)
```

`repo` must be an already-open `git.Repo`.
