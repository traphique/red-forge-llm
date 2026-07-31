# RedForge Desktop Rewrite

## Stack decision

The first desktop release uses **PySide6 with Qt Widgets**.

- It reuses the existing Python skill tooling instead of introducing a Rust or
  Node bridge.
- Qt's Python wheels include the Qt runtime, so contributors do not need a
  separate system Qt installation.
- Qt Widgets is mature, native, keyboard-friendly, and enough for a skill
  browser. RedForge does not need a browser engine.
- The UI and the application core are separate. A Tauri shell can replace the
  UI later without rewriting library discovery, search, chaining, or export.

Tauri is a good candidate after the workflows settle and if binary size or a
web-native interaction model becomes more valuable than a single-language
codebase. Electron is not justified for a local 19-document browser. Flet and
Dear PyGui are useful prototypes but offer less control over a conventional
document-oriented desktop UI and distribution.

## Search plan

Phase 1 replaces per-query TF-IDF fitting with an in-memory SQLite FTS5 index
ranked by BM25. It is fast, ships with normal Python builds, requires no model,
and never performs a network request.

Phase 2 can add a `SemanticReranker` behind the same `SearchIndex` boundary:

1. bundle a small quantized ONNX embedding model in release artifacts;
2. embed sections, not whole `SKILL.md` files;
3. persist vectors and content hashes in the user data directory;
4. combine vector score with FTS5 score;
5. keep FTS5 as the fallback on unsupported machines.

`sqlite-vec` is preferable to the older `sqlite-vss`, but loading SQLite
extensions varies by Python and operating system. Do not make it a hard
dependency until release builds prove it works on macOS, Windows, and Linux.

## Milestones

### 0.1 — useful desktop shell (started)

- shared skill discovery and metadata parser;
- FTS5/BM25 search;
- category filtering and Markdown preview;
- copy full skill, copy CLI load command, and export Markdown;
- two/three-skill prompt chains with full Markdown and compact operator-brief
  exports, five recent chains, single-pin retention, and last-loaded status;
- Markdown-aware skill/chain comparison with changed-H2 filtering, unified,
  rendered side-by-side, and single-section previews, explicit baseline
  direction, and Markdown-wrapped copy;
- choose/reload an external `skills/` tree;
- PyInstaller build that bundles the current library.

### 0.2 — production packaging

- application icon and signed/notarized artifacts;
- platform builds in GitHub Actions;
- version/about dialog and crash-safe logging;
- persist window state and recent libraries;
- packaging smoke test on all three operating systems.

### 0.3 — skill workbench

- validator results beside the preview;
- editable clone/draft flow (never mutate source without confirmation);
- recursive optimization history and diff review;
- atomic writes and backup/recovery.

### 0.4 — purple-team sessions

- local session schema with explicit steps and outputs;
- drag-to-chain skill builder;
- deterministic combined-system-prompt preview;
- token/character budget and conflict warnings;
- export only at first; model execution remains an optional adapter.

### 0.5 — optional local semantics

- bundled quantized ONNX model;
- section-level embeddings and hybrid reranking;
- index health/rebuild UI;
- no first-launch download.

## Local development

Use Python 3.10 or newer in an isolated environment:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[desktop]"
.venv/bin/python -m redforge_app
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

You can point the app at another library:

```bash
.venv/bin/python -m redforge_app --library /path/to/redforge
```

## Build

Build on each target operating system; desktop bundles are not cross-compiled:

```bash
python3 tools/build_desktop.py
```

The command finds Python 3.10+, creates an isolated `.build-venv` when needed,
installs the desktop build dependencies, builds the app, and runs resource and
UI launch smoke tests. Later builds reuse that environment. Output is under
`dist/RedForge`; on macOS there is also `dist/RedForge.app`. The spec bundles
`skills/` and `MASTER_INDEX.md`, so the released application remains useful
with no checkout and no network.
