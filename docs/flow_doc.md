# Hook Flow Documentation

Once `hupy init` has installed the stubs, the hooks are **fully automatic** — every `git commit` fires them in git's own order, and git hands each stage to the matching *HUPy* feature. Each stage's own logic is wrapped by a [Hook Bracket](hb_doc.md) — configured *lead* commands run before it, *trail* commands after:

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
        post[/post-commit hook/] --> lead3[[Hook Bracket - lead]]
        lead3 --> trail3[[Hook Bracket - trail]]
    end

    commit --> pre
    trail1 --> prep
    trail2 --> created([commit created])
    created --> post
```

See the per-feature docs for what each stage does: [Ban Direct Commit](bdc_doc.md), [Triage Tag Gating](ttg_doc.md), and [Prepend Commit Header](pch_doc.md). Both BDC and PCH decide their behavior from the branch and merge classification in [Commit, Branch & Merge](cbm_doc.md).
