# Commit, Branch & Merge Documentation

<!-- FIXME rewrite cbm doc -->

Identify in-progress git commits and merges by branch patterns.

## CommitType

Categorizes in-progress commits by merge strategy and commit type. A
merge is further categorized by its source and target branches.

### Feature Landing
`feature -> dev`

A completed feature lands in the shared development line. Marks the integration of a feature branch into the main development branch.

### Version Release
`dev -> main`

A stable batch of features ships to production. Marks the promotion of development changes into the production-ready main branch.

### Sync Backport
`main -> dev`

Pulls a hotfix or main-only change back into dev, so dev doesn't drift behind main. Ensures the development branch stays in sync with production.

### Catch Up
`dev -> feature`

Brings a feature branch current with the latest dev, before continuing work or opening a PR. Ensures feature branches don't fall behind while in development.

### Hotfix Release
`hotfix -> main`

An urgent fix ships directly to production, bypassing the normal dev cycle. Used for critical production issues.

### Hotfix Backport
`hotfix -> dev`

The same urgent fix gets folded back into dev, so it isn't lost on the next release. Ensures hotfixes don't regress when the next version ships.

### Release Cut
`release/* -> main`

A release-candidate branch, after final testing/bugfixes, merges into main. Marks the finalization and tagging of a release version.

### Release Backport
`release/* -> dev`

Any last-minute fixes made on the release branch get synced back to dev. Prevents divergence between release fixes and ongoing development.

### Other Commit
A regular, non-merge commit. Represents standard development work.

### Other Merge
Any merge that doesn't fit the recognized patterns (e.g., pull merges, octopus merges, etc.).
