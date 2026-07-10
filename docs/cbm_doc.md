# Commit, Branch & Merge Documentation

## Concepts

### Branch Type

| Branch Type | Default Name | Config File Field | Remarks |
| --- | --- | --- | --- |
| main | `main` | `main_branch_name` | the production-ready branch |
| dev | `dev` | `dev_branch_name` | the shared development branch |
| hotfix | `hotfix/*`, eg `hotfix/crash`| `hotfix_branch_prefix` | urgent fix |
| release | `release/*`, eg `release/1.2` | `release_branch_prefix` | release candidate |
| user | eg `alice/x`  | n/a  | any owned branch |
| feature | eg `add-user-sing-in` | n/a | fallback for a plain feature branch |













### Merge Type

| Merge Type | Direction | Remarks |
| --- | --- | --- |
| Stable Release | dev → main | a stable batch ships to production |
| Feature Landing | feature → dev | a finished feature lands on the shared dev line |
| Sync Backport | main → dev | pull a main-only change back so dev doesn't drift |
| Catch Up | dev → feature | bring a feature branch current with dev |
| Hotfix Release | hotfix → main | an urgent fix ships straight to production |
| Hotfix Backport | hotfix → dev | fold that same fix back into dev |
| Release Cut | release → main | finalize and tag a release |
| Release Backport | release → dev | sync last-minute release fixes back to dev |
| Other Merge | any other pair | recognized as a merge, but no known pattern |

**feature ↔ dev ↔ main**: Feature Landing, Catch Up, Stable Release, Sync Backport

```mermaid
%%{init: { 'gitGraph': {'showCommitLabel': false} } }%%
gitGraph
  commit
  branch dev
  checkout dev
  commit
  branch feature
  checkout feature
  commit
  checkout dev
  commit
  checkout feature
  merge dev tag: "Catch Up"
  commit
  checkout dev
  merge feature tag: "Feature Landing"
  checkout main
  merge dev tag: "Stable Release"
  checkout main
  commit
  checkout dev
  merge main tag: "Sync Backport"
```

**hotfix, release → main, dev**: Hotfix Release, Hotfix Backport, Release Cut, Release Backport

```mermaid
%%{init: { 'gitGraph': {'showCommitLabel': false} } }%%
gitGraph
  commit
  branch dev
  checkout dev
  commit
  branch release
  checkout release
  commit
  checkout main
  merge release tag: "Release Cut"
  checkout dev
  merge release tag: "Release Backport"
  checkout main
  branch hotfix
  checkout hotfix
  commit
  checkout main
  merge hotfix tag: "Hotfix Release"
  checkout dev
  merge hotfix tag: "Hotfix Backport"
```
































## `hupy.cbm` Module

### `get_current_commit_type(repo_path)`

The main entry point of the module. Call it during an in-progress commit (e.g. from a `commit-msg` or `prepare-commit-msg` hook) to find out whether the commit is a plain commit or a merge, and if it's a merge, which of the recognized types it belongs to.

```python
from hupy.cbm import get_current_commit_type, CommitType

commit_type = get_current_commit_type(".")

if commit_type is CommitType.FEATURE_LANDING:
    ...
```

Here the first branch runs when a feature is landing on `dev`, the
second runs for any other kind of merge, and the final `else` runs for
a plain, non-merge commit.

`repo_path` may be the repo root or any path inside it — the repo is
located by walking up from there. Raises
`git.InvalidGitRepositoryError` / `git.NoSuchPathError` if no repo is
found.













### `get_source_branch(repo)` / `get_target_branch(repo)`

Lower-level helpers used internally by `get_current_commit_type`, also useful on their own when only the branch names are needed rather than a full `CommitType`. Both expect an already-open `git.Repo` and only make sense while a merge is in progress (i.e. `MERGE_HEAD` exists):

`get_source_branch` reads the branch being merged *from*, `get_target_branch` reports the currently checked-out branch being merged *into*.

```python
import git
from hupy.cbm import get_source_branch, get_target_branch

repo = git.Repo(".", search_parent_directories=True)
get_source_branch(repo)
get_target_branch(repo)
```

For a feature branch being merged into `dev`, `get_source_branch`
returns something like `"add-login"` and `get_target_branch` returns
`"dev"`.

`get_target_branch` returns `None` on a detached `HEAD`, since there is
no named branch to report.
