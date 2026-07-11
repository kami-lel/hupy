# Hook Bracket (HB) Documentation

**Hook Bracket (HB)** lets you run your own shell commands alongside *HUPy*'s git hooks, without writing a custom hook yourself.

## Lead And Trail

For each hook — `pre-commit`, `prepare-commit-msg`, and `post-commit` — you configure two lists of commands:

- **lead** commands run *before* HUPy's own checks
- **trail** commands run *after* HUPy's own checks

Slot in linting, formatting, notifications, or anything else your workflow needs, right around the checks HUPy already runs.
