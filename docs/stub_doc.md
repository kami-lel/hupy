# Hook Stub Documentation

## Hooks & `hupy`

Once `hupy init` has installed the stubs, the hooks are **fully automatic** — every `git commit` fires them in git's own order, and git hands each stage to the matching *HUPy* feature. Each stage's own logic is wrapped by a [Hook Bracket](hb_doc.md) — configured *lead* commands run before it, *trail* commands after. See the [Hook Chain Documentation](chain_doc.md) for the end-to-end, stage-by-stage diagram of how each git operation runs.

### Hook Stub Auto-Determination

`hupy` doesn't install a stub for every git hook name that exists — it only installs one for hooks it actually needs. On each `init`/`verify` run, it walks every hook stage module under [`hupy/cli/hooks/`](../hupy/cli/hooks/) (`pre_commit.py`, `prepare_commit_msg.py`, `commit_msg.py`, and so on), each of which declares its git hook name via a `HOOK_NAME` constant (eg `HOOK_NAME = "pre-commit"`). A hook name is **demanded** — and so gets a stub — when at least one of the following holds:

- the module defines `run_core`, meaning it owns a dedicated *HUPy* feature (eg `pre_commit.py` wires up Ban Direct Commit and Triage Tag Gating)
- the module defines `run_after`
- its [Hook Bracket](hb_doc.md) is active — HB isn't disabled in `.hupy.config.jsonc`, and that hook's bracket has at least one configured *lead* or *trail* command

A module satisfying none of these is skipped, and no stub is installed for it. This is why the [Standalone Hooks](chain_doc.md#standalone-hooks) — like `pre-auto-gc` or `pre-push` — only get a stub once the user configures a Hook Bracket for them; per the note at the bottom of the [Hook Chain Documentation](chain_doc.md), they don't carry a dedicated *HUPy* feature yet.

Each installed stub is a thin generated shell script — no on-disk template, no placeholder substitution — that just shells out to `python -m hupy hook <hook-name> "$@"`. That `hook` subcommand is what actually runs the Hook Bracket *lead* → the stage's `run_core` → the Hook Bracket *trail* → `run_after`, for that hook name.

### Managing Stubs: `hupy init` & `hupy verify`

`hupy init` performs first-time setup for a repository — installing every demanded hook stub and creating a default `.hupy.config.jsonc`. Run `hupy init -h` for the full flag reference (eg `--hooks-dir`, `--install-hook-stubs`, `--create-config-file`, `-f`/`--force`).

`hupy verify` re-checks an already-initialized repository, including whether its installed stubs are still in sync with current demand — demand can drift after editing `.hupy.config.jsonc` (eg toggling a Hook Bracket) or upgrading `hupy` itself. By default it only reports drift (**missing hook stub** / **hook stub no longer demanded** warnings); run `hupy verify -h` for the full flag reference (eg `-u`/`--update-hook-stubs`, `-f`/`--force`) to turn reporting into action.

`verify` also confirms the config file loads and validates against its schema, and that a version string can be grepped per the VerGrep config, before reporting on hook stub sync.
