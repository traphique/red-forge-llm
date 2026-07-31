# RedForge Desktop — `forgepuddle` Summary

RedForge now has a native, offline-first PySide6 desktop app around the existing
`SKILL.md` library. This snapshot is the smallest complete desktop workflow:
find a skill, assemble a short purple-team chain, compare Markdown versions,
and hand the result to someone else without sending content to a service.

## What shipped

### Skill browser

- Loads the existing RedForge `skills/**/SKILL.md` tree and `MASTER_INDEX.md`.
- Uses an in-memory SQLite FTS5 index with BM25 ranking; no model download,
  API key, or network request is required.
- Supports category filtering, rendered Markdown preview, clipboard actions,
  CLI load-command copy, and standalone Markdown export.
- Can switch to another compatible local skill tree and remember that library.

### Purple-team runner

- Chains two or three different skills into one ordered system prompt.
- Copies the prompt or exports a standalone Markdown chain.
- Creates a compact operator brief with the ordered skill names, a local
  metadata-derived purpose for each skill, and the final prompt length.
- Keeps the five most recent chains in a local JSON file, supports one pinned
  chain, and shows the last-loaded chain with relative time.
- Shares and remembers the last skill-category filter with the Diff tab.

### Skill Diff

- Compares two live skills, reconstructed saved chains, or external Markdown
  files.
- Defaults to changed H2 sections only, with unified, rendered side-by-side,
  and single-section views.
- Lets either side be the baseline so additions and removals keep a stable
  meaning.
- Copies a raw unified diff or a ready-to-paste fenced Markdown diff.
- Offers Normal, Larger, and Largest text sizes for only the diff and Markdown
  panes.

### Packaging

- Uses PyInstaller with bundled Qt, the skill tree, and `MASTER_INDEX.md`.
- Builds native macOS, Windows, and Linux artifacts on their respective
  operating systems.
- Runs packaged resource and UI-launch smoke tests after every local build.
- Produces a shareable archive, SHA-256 checksum, and `VERIFY.txt`.
- Includes a three-platform GitHub Actions build workflow.

## One-command build

From the repository root:

```bash
cd redforge
python3 tools/build_desktop.py
```

The script finds Python 3.10+, creates or reuses `redforge/.build-venv`,
installs the pinned desktop/build extras when needed, runs PyInstaller, smoke
tests the packaged executable, and writes the handoff files under
`redforge/dist/`.

On macOS the useful handoff files are:

- `dist/RedForge.app`
- `dist/RedForge-macOS.zip`
- `dist/RedForge-macOS.zip.sha256`
- `dist/VERIFY.txt`

## Commit and local-state boundary

The `forgepuddle` commit contains the desktop source, shared core, tests,
packaging spec, build workflow, build script, and documentation described
above. After that commit, no desktop source changes from this work are expected
to remain uncommitted.

Generated or machine-local state remains intentionally outside Git:

- `.build-venv/`, `build/`, and `dist/`
- saved chains and last-loaded status in the platform application-data folder
- Qt settings such as the selected library and picker category

The latest local validation completed with 24 passing unit tests, a native UI
launch check, packaged smoke tests, SHA-256 verification, and strict macOS
bundle-signature verification.

## Not shipped yet

- Developer ID signing, notarization, and a production application icon
- Recursive skill optimization/editing and recovery history
- Structured multi-agent execution beyond deterministic prompt chaining
- Optional ONNX embeddings or hybrid semantic reranking
- Direct model execution; the desktop app remains an offline prompt workbench

Those are follow-on milestones, not hidden dependencies for the current app.
