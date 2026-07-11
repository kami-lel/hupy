# Prepend Commit Header (PCH) Documentation

**Prepend Commit Header (PCH)** adds a short header line to the top of the
commit message so the history reads clearly at a glance, when you make a **merge commit**.

PCH looks at the kind of merge you're making — landing a feature, cutting a release, backporting a fix, and so on — and writes a matching header that names the source branch, target branch, or version involved. A regular, non-merge commit is left completely untouched.

PCH runs in the prepare-commit-msg stage — see the [Hook Flow](flow_doc.md) for where it fits. The merge types it recognizes are defined in [Commit, Branch & Merge](cbm_doc.md).
