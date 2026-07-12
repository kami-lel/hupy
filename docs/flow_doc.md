# Hook Flow Documentation

Once `hupy init` has installed the stubs, the hooks are **fully automatic** — every `git commit` fires them in git's own order, and git hands each stage to the matching *HUPy* feature. Each stage's own logic is wrapped by a [Hook Bracket](hb_doc.md) — configured *lead* commands run before it, *trail* commands after:


































## Commit Flow

Triggered by `git commit` for a **non-merge commit** (a merge commit follows [Merge Flow](#merge-flow) instead):

```mermaid
flowchart TD
    commit([git commit - non-merge])

    %% pre-commit stage
    subgraph precommit [pre-commit stage]
        pre[/pre-commit hook/] --> lead1[[Hook Bracket - lead]]
        lead1 --> bdc(Ban Direct Commit) --> ttg(Triage Tag Gating)
        ttg --> trail1[[Hook Bracket - trail]]
    end

    %% prepare-commit-msg stage
    subgraph preparemsg [prepare-commit-msg stage]
        prep[/prepare-commit-msg hook/] --> lead2[[Hook Bracket - lead]]
        lead2 --> pch(Prepend Commit Header)
        pch --> trail2[[Hook Bracket - trail]]
    end

    %% commit-msg stage
    subgraph commitmsg [commit-msg stage]
        cmsg[/commit-msg hook/] --> lead2b[[Hook Bracket - lead]]
        lead2b --> trail2b[[Hook Bracket - trail]]
    end

    %% post-commit stage
    subgraph postcommit [post-commit stage]
        post[/post-commit hook/] --> lead3[[Hook Bracket - lead]]
        lead3 --> trail3[[Hook Bracket - trail]]
    end

    commit --> pre
    trail1 --> prep
    trail2 --> cmsg
    trail2b --> created([commit created])
    created --> post
```

See the per-feature docs for what each stage does: [Ban Direct Commit](bdc_doc.md), [Triage Tag Gating](ttg_doc.md), and [Prepend Commit Header](pch_doc.md). Both BDC and PCH decide their behavior from the branch and merge classification in [Commit, Branch & Merge](cbm_doc.md).

## Merge Flow

Triggered by `git merge`. A non-fast-forward merge runs its own commit chain (`pre-merge-commit` → `prepare-commit-msg` → `commit-msg` → `post-commit`) and only fires `post-merge` once that finishes; a fast-forward merge creates no commit at all, so it skips straight to `post-merge`:

```mermaid
flowchart TD
    nonff([git merge - non-fast-forward])
    ff([git merge - fast-forward])

    %% pre-merge-commit stage
    subgraph premergecommit2 [pre-merge-commit stage]
        pmc[/pre-merge-commit hook/] --> lead1c[[Hook Bracket - lead]]
        lead1c --> trail1c[[Hook Bracket - trail]]
    end

    %% prepare-commit-msg stage
    subgraph preparemsg2 [prepare-commit-msg stage]
        prep2[/prepare-commit-msg hook/] --> lead2c[[Hook Bracket - lead]]
        lead2c --> pch2(Prepend Commit Header)
        pch2 --> trail2c[[Hook Bracket - trail]]
    end

    %% commit-msg stage
    subgraph commitmsg2 [commit-msg stage]
        cmsg2[/commit-msg hook/] --> lead2d[[Hook Bracket - lead]]
        lead2d --> trail2d[[Hook Bracket - trail]]
    end

    %% post-commit stage
    subgraph postcommit2 [post-commit stage]
        post2[/post-commit hook/] --> lead3c[[Hook Bracket - lead]]
        lead3c --> trail3c[[Hook Bracket - trail]]
    end

    %% post-merge stage
    subgraph postmerge2 [post-merge stage]
        pmg2[/post-merge hook/] --> lead12b[[Hook Bracket - lead]]
        lead12b --> trail12b[[Hook Bracket - trail]]
    end

    nonff --> pmc
    ff -. no commit created .-> pmg2
    trail1c --> prep2
    trail2c --> cmsg2
    trail2d --> created2([merge commit created])
    created2 --> post2
    trail3c --> pmg2
```

































## Rewrite Flow

Triggered by `git commit --amend` or `git rebase` — separate from, and does not follow, the commit flow above. `git rebase` also fires `pre-rebase` first, before it starts replaying commits:

```mermaid
flowchart TD
    amend([git commit --amend])
    rebase([git rebase])

    %% pre-rebase stage
    subgraph prerebase [pre-rebase stage]
        prb[/pre-rebase hook/] --> lead0[[Hook Bracket - lead]]
        lead0 --> trail0[[Hook Bracket - trail]]
    end

    %% post-rewrite stage
    subgraph postrewrite [post-rewrite stage]
        postrw[/post-rewrite hook/] --> lead3b[[Hook Bracket - lead]]
        lead3b --> trail3b[[Hook Bracket - trail]]
    end

    rebase --> prb
    trail0 --> postrw
    amend --> postrw
```


































## Patch Apply Flow

Triggered by `git am` — separate from, and does not follow, the commit flow above:

```mermaid
flowchart TD
    am([git am])

    %% applypatch-msg stage
    subgraph applypatchmsg [applypatch-msg stage]
        amsg[/applypatch-msg hook/] --> lead4[[Hook Bracket - lead]]
        lead4 --> trail4[[Hook Bracket - trail]]
    end

    %% pre-applypatch stage
    subgraph preapplypatch [pre-applypatch stage]
        preap[/pre-applypatch hook/] --> lead5[[Hook Bracket - lead]]
        lead5 --> trail5[[Hook Bracket - trail]]
    end

    %% post-applypatch stage
    subgraph postapplypatch [post-applypatch stage]
        postap[/post-applypatch hook/] --> lead6[[Hook Bracket - lead]]
        lead6 --> trail6[[Hook Bracket - trail]]
    end

    am --> amsg
    trail4 --> preap
    trail5 --> applied([patch applied])
    applied --> postap
```


































## Standalone Hooks

Each of these fires on its own, unrelated trigger — none of them chain into the flows above, or into each other.













### `pre-auto-gc`

Triggered before automatic garbage collection:

```mermaid
flowchart TD
    gc([automatic git gc])

    %% pre-auto-gc stage
    subgraph preautogc [pre-auto-gc stage]
        pgc[/pre-auto-gc hook/] --> lead7[[Hook Bracket - lead]]
        lead7 --> trail7[[Hook Bracket - trail]]
    end

    gc --> pgc
```













### `post-index-change`

Triggered when the index is written and the working tree is unchanged:

```mermaid
flowchart TD
    idx([index written, worktree unchanged])

    %% post-index-change stage
    subgraph postindexchange [post-index-change stage]
        pic[/post-index-change hook/] --> lead8[[Hook Bracket - lead]]
        lead8 --> trail8[[Hook Bracket - trail]]
    end

    idx --> pic
```













### `sendemail-validate`

Triggered by `git send-email`, once per outgoing message:

```mermaid
flowchart TD
    email([git send-email, per message])

    %% sendemail-validate stage
    subgraph sendemailvalidate [sendemail-validate stage]
        sev[/sendemail-validate hook/] --> lead9[[Hook Bracket - lead]]
        lead9 --> trail9[[Hook Bracket - trail]]
    end

    email --> sev
```













### `fsmonitor-watchman`

Triggered by `git status` and other commands querying the filesystem-monitor state:

```mermaid
flowchart TD
    fsm([git status / fsmonitor query])

    %% fsmonitor-watchman stage
    subgraph fsmonitorwatchman [fsmonitor-watchman stage]
        fsw[/fsmonitor-watchman hook/] --> lead10[[Hook Bracket - lead]]
        lead10 --> trail10[[Hook Bracket - trail]]
    end

    fsm --> fsw
```













### `post-checkout`

Triggered after `git checkout` or `git switch` updates the working tree:

```mermaid
flowchart TD
    checkout([git checkout / git switch])

    %% post-checkout stage
    subgraph postcheckout [post-checkout stage]
        pco[/post-checkout hook/] --> lead11[[Hook Bracket - lead]]
        lead11 --> trail11[[Hook Bracket - trail]]
    end

    checkout --> pco
```













### `pre-push`

Triggered before `git push` updates the remote's refs:

```mermaid
flowchart TD
    push([git push])

    %% pre-push stage
    subgraph prepush [pre-push stage]
        ppu[/pre-push hook/] --> lead13[[Hook Bracket - lead]]
        lead13 --> trail13[[Hook Bracket - trail]]
    end

    push --> ppu
```

> [!NOTE]
> `applypatch-msg`, `pre-applypatch`, `post-applypatch`, `pre-merge-commit`, `commit-msg`, `post-rewrite`, `pre-rebase`, `pre-auto-gc`, `post-index-change`, `sendemail-validate`, `fsmonitor-watchman`, `post-checkout`, `post-merge`, and `pre-push` currently run only their [Hook Bracket](hb_doc.md) *lead*/*trail* commands — no dedicated *HUPy* feature is wired into them yet.
