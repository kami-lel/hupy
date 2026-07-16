# Hook Chain Documentation

Running a single `git` command can trigger a sequence of hooks, with *HUPy* running its matching features at each one according to your settings. This project's term for that full sequence — every hook stage a given git operation triggers, start to finish — is a **chain**.

Within each hook **stage**, execution always opens with *Leading Hook Bracket* and closes with *Trailing Hook Bracket*; q.v. [Hook Bracket](hb_doc.md) for details.
































































## Commit Chain

Triggered by a **non-merge** `git commit` (a merge commit follows the [Merge Chain](#merge-chain) instead), or by `git rebase`:

```mermaid
flowchart TD
    A([<pre><code>git commit</code></pre>])
    R([<pre><code>git rebase</code></pre>])

    A --> B{<pre><code>--no-verify</code></pre>?}

    subgraph precommit [pre-commit stage]
        C[[pre-commit hook]] --> C1{{Leading Hook Bracket}}
        C1 --> E1[Ban Direct Commit]
        E1 --> E2[Triage Tag Gating]
        E2 --> C2{{Trailing Hook Bracket}}
    end
    B -->|F| C

    subgraph preparemsg [prepare-commit-msg stage]
        F[[prepare-commit-msg hook]] --> F1{{Leading Hook Bracket}}
        F1 --> G[Prepend Commit Header]
        G --> F2{{Trailing Hook Bracket}}
    end
    B -->|T| F
    C2 --> F

    F2 --> H{<pre><code>--no-verify</code></pre>?}

    subgraph commitmsg [commit-msg stage]
        I[[commit-msg hook]] --> I1{{Leading Hook Bracket}}
        I1 --> I2{{Trailing Hook Bracket}}
    end
    H -->|F| I

    subgraph postcommit [post-commit stage]
        L[[post-commit hook]] --> L1{{Leading Hook Bracket}}
        L1 --> L2{{Trailing Hook Bracket}}
    end
    H -->|T| L
    I2 --> L

    L2 --> N{<pre><code>--amend</code></pre>?}

    subgraph prerebase [pre-rebase stage]
        prb[[pre-rebase hook]] --> lead0{{Leading Hook Bracket}}
        lead0 --> trail0{{Trailing Hook Bracket}}
    end
    R --> prb

    subgraph postrewrite [post-rewrite stage]
        O[[post-rewrite hook]] --> O1{{Leading Hook Bracket}}
        O1 --> O2{{Trailing Hook Bracket}}
    end
    N -->|T| O
    trail0 --> O

    N -->|F| P([End])
    O2 --> P
```

[Ban Direct Commit](bdc_doc.md) blocks direct commits to protected branches, [Triage Tag Gating](ttg_doc.md) blocks merges that still carry unresolved triage tags, and [Prepend Commit Header](pch_doc.md) adds a header line to merge commit messages — see each doc for the full behavior.


































## Merge Chain

Triggered by `git merge`, or by `git pull` (which runs a merge under the hood):

```mermaid
flowchart TD
    A1([<pre><code>git merge</code></pre>])
    A2([<pre><code>git pull</code></pre>])

    B{fast-forward? or <pre><code>--squash</code></pre>?}

    A1 --> B
    A2 --> B

    B -->|F| CF{merge
            conflicts?}

    CF -->|T| Z4

    CF -->|F| G{<pre><code>--no-verify</code></pre>?}

    subgraph premerge [pre-merge-commit stage]
        C[[pre-merge-commit hook]] --> C1{{Leading Hook Bracket}}
        C1 --> C2{{Trailing Hook Bracket}}
    end
    G -->|F| C

    subgraph preparemsg [prepare-commit-msg stage]
        F[[prepare-commit-msg hook]] --> F1{{Leading Hook Bracket}}
        F1 --> Fmsg[Prepend Commit Header]
        Fmsg --> F2{{Trailing Hook Bracket}}
    end
    G -->|T| F
    C2 --> F

    F2 --> EditStep[/user edits commit message/]
    EditStep --> H{<pre><code>--no-verify</code></pre>?}

    subgraph commitmsg [commit-msg stage]
        I[[commit-msg hook]] --> I1{{Leading Hook Bracket}}
        I1 --> I2{{Trailing Hook Bracket}}
    end
    H -->|F| I

    subgraph postcommit [post-commit stage]
        L[[post-commit hook]] --> L1{{Leading Hook Bracket}}
        L1 --> L2{{Trailing Hook Bracket}}
    end
    H -->|T| L
    I2 --> L

    subgraph postmerge [post-merge stage]
        PM3[[post-merge hook]] --> PM1{{Leading Hook Bracket}}
        PM1 --> PM2{{Trailing Hook Bracket}}
    end
    L2 --> PM3
    B -->|T| PM3
    PM2 --> Z4([End])
```

See [Prepend Commit Header](pch_doc.md) for its merge-commit header logic.






























































## Patch Apply Chain

Triggered by `git am`.

```mermaid
flowchart TD
    A([<pre><code>git am</code></pre>])

    subgraph B [applypatch-msg stage]
        amsg[[applypatch-msg hook]] --> lead4{{Leading Hook Bracket}}
        lead4 --> trail4{{Trailing Hook Bracket}}
    end

    A --> amsg

    subgraph preapplypatch [pre-applypatch stage]
        preap[[pre-applypatch hook]] --> lead5{{Leading Hook Bracket}}
        lead5 --> trail5{{Trailing Hook Bracket}}
    end
    trail4 --> preap

    trail5 --> applied[Patch Applied]

    subgraph postapplypatch [post-applypatch stage]
        postap[[post-applypatch hook]] --> lead6{{Leading Hook Bracket}}
        lead6 --> trail6{{Trailing Hook Bracket}}
    end
    applied --> postap
```
































































## Standalone Hooks

<!-- FIXME FIXME clean up chain doc -->

Each of these fires on its own, unrelated trigger — none of them join the Chains above, and they don't chain into each other either.

- `pre-auto-gc`
- `post-index-change`
- `sendemail-validate`
- `fsmonitor-watchman`
- `post-checkout`
- `pre-push`

----

> [!NOTE]
> `applypatch-msg`, `pre-applypatch`, `post-applypatch`, `pre-merge-commit`, `commit-msg`, `post-rewrite`, `pre-rebase`, `pre-auto-gc`, `post-index-change`, `sendemail-validate`, `fsmonitor-watchman`, `post-checkout`, `post-merge`, and `pre-push` currently run only their [Hook Bracket](hb_doc.md) *lead*/*trail* commands — no dedicated *HUPy* feature is wired into them yet.
