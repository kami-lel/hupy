# Ban Direct Commit (BDC) Documentation

**Ban Direct Commit (BDC)** protects certain branches — typically `main`, and optionally `dev` or any branch you name — from receiving direct commits.

Once a branch is protected, the only way to add changes to it is by **merging** (for example, landing a feature branch or a pull request). A plain `git commit` made while checked out on a protected branch is rejected.
