# Hook Stub Documentation

A HUPy **hook stub** is a hook file in Git's hook folder (`core.hooksPath` if configured, otherwise `.git/hooks/`). It's a `bash` script that calls the HUPy CLI (`python3 -m hupy hook ...`). It carries no HUPy logic of its own — it just invokes the CLI. Each Git hook may have one corresponding stub file.

Once `hupy init` installs the stubs, the hooks run **fully automatically**. Relevant `git` commands fire them in git's own order, and git hands each stage to the matching *HUPy* feature. Q.v. [Hook Chain Documentation](chain_doc.md) for the full stage-by-stage diagram.

### stub by demand

`hupy` doesn't install a stub for every git hook name that exists. It only installs one for hooks it actually needs. A hook stub is **demanded** when the hook either owns a dedicated *HUPy* feature, or has an active [Hook Bracket](hb_doc.md) configured for it.

A hook meeting neither condition is skipped — no stub gets installed for it. This is why [Standalone Hooks](chain_doc.md#standalone-hooks) like `pre-auto-gc` or `pre-push` only get a stub once the user sets up a Hook Bracket for them.


































## Managing Stubs

### `hupy init`

`hupy init` writes a hook stub for every demanded hook into the repository's hook folder, filling in whichever ones are missing. It also creates a default `.hupy.config.jsonc` alongside them.

Use it the **first time** HUPy is adopted in a repository (eg right after cloning one that uses HUPy).

Q.v. `hupy init -h` for the full flag reference and exactly how it behaves.













### `hupy verify`

`hupy verify` **compares the stubs** in the repository's hook folder against current demand. It flags any demanded hook still missing its stub, and any installed stub that's no longer needed. Use it whenever demand may have drifted — for example after editing `.hupy.config.jsonc` (e.g. toggling a Hook Bracket) or upgrading `hupy`.

By default it only reports this drift (**missing hook stub** / **hook stub no longer demanded** warnings). Pass `-u` to have it perform the update instead.

Q.v. `hupy verify -h` for the full flag reference and exactly how it behaves.
