# Hook Flow Documentation

Once `hupy init` has installed the stubs, the hooks are **fully automatic** — every `git commit` fires them in git's own order, and git hands each stage to the matching *HUPy* feature. Each stage's own logic is wrapped by a **Hook Bracket** — configured *lead* commands run before it, *trail* commands after:

```mermaid
flowchart TD
    commit([git commit])

    %% pre-commit stage
    subgraph precommit [pre-commit stage]
        pre[/pre-commit hook/] --> lead1[[Hook Bracket - lead]]
        lead1 --> bdc[[Ban Direct Commit]] --> ttg[[Triage Tag Gating]]
        ttg --> trail1[[Hook Bracket - trail]]
    end

    %% prepare-commit-msg stage
    subgraph preparemsg [prepare-commit-msg stage]
        prep[/prepare-commit-msg hook/] --> lead2[[Hook Bracket - lead]]
        lead2 --> pch[[Prepend Commit Header]]
        pch --> trail2[[Hook Bracket - trail]]
    end

    %% post-commit stage
    subgraph postcommit [post-commit stage]
        post[/post-commit hook/]
    end

    commit --> pre
    trail1 --> prep
    trail2 --> created([commit created])
    created --> post
```

Each stub is a thin trampoline invoking `hupy hook <stage>`:

- **`pre-commit`** — [Hook Bracket](hb_doc.md) lead → [Ban Direct Commit](bdc_doc.md) → [Triage Tag Gating](ttg_doc.md) → Hook Bracket trail
- **`prepare-commit-msg`** — [Hook Bracket](hb_doc.md) lead → [Prepend Commit Header](pch_doc.md) → Hook Bracket trail
- **`post-commit`** — runs after the commit is created

Any stage's module can be skipped for the next commit with `hupy skip-once <module>` (undo with `-u`).
