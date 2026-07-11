# Hook Flow Documentation

Once `hupy init` has installed the stubs, the hooks are **fully automatic** — every `git commit` fires them in git's own order, and git hands each stage to the matching *HUPy* feature:

```mermaid
flowchart TD
    commit([git commit])

    %% pre-commit stage
    subgraph precommit [pre-commit stage]
        pre[/pre-commit hook/] --> bdc[[Ban Direct Commit]] --> ttg[[Triage Tag Gating]]
    end

    %% prepare-commit-msg stage
    subgraph preparemsg [prepare-commit-msg stage]
        prep[/prepare-commit-msg hook/] --> pch[[Prepend Commit Header]]
    end

    %% post-commit stage
    subgraph postcommit [post-commit stage]
        post[/post-commit hook/] --> reset[[reset one-time skip state]]
    end

    commit --> pre
    ttg --> prep
    pch --> created([commit created])
    created --> post
```

Each stub is a thin trampoline invoking `hupy hook <stage>`:

- **`pre-commit`** — runs [Ban Direct Commit](bdc_doc.md) then [Triage Tag Gating](ttg_doc.md)
- **`prepare-commit-msg`** — runs [Prepend Commit Header](pch_doc.md)
- **`post-commit`** — spends the round's one-time `skip-once` flags (`hupy-state.json`), so they apply once and then clear

Any stage's module can be skipped for the next commit with `hupy skip-once <module>` (undo with `-u`).
