# RedForge — Curated Offensive Security Skills for LLMs (2026)

**Structured `SKILL.md` libraries for Claude, Grok, GPT, and other capable models** — decision trees, 2026-relevant techniques, and purple-team context in one place.

---

## What is RedForge?

Each skill is a self-contained expert prompt: domain methodology, escalation logic, modern bypasses, detection notes, and consistent response structure.

**Highlights:** recursive optimization process, 2026+ threats (agentic systems, RAG, hybrid cloud/AD), multi-LLM friendly, tool-aware where it matters.

---

## Repository layout

```
redforge/
├── README.md                 # This file
├── MASTER_INDEX.md           # Full skill index, kill chains, master system prompt
├── templates/
│   └── SKILL_TEMPLATE.md     # Template for new skills
├── skills/
│   ├── ai-redteam/
│   ├── web/{sqli,rce}/
│   ├── binary/{edr-evasion,exploit-development}/
│   ├── cloud/cloud-native/
│   ├── forensics/memory/
│   └── …                     # see MASTER_INDEX.md or `tools/redforge.py list`
├── tools/
│   ├── redforge.py           # CLI: list, search, load hints
│   ├── semantic_search.py    # TF-IDF search across skills
│   ├── redforge_ui.py        # Optional Streamlit browser (`streamlit run …`)
│   └── validate_skill.py     # Skill lint / scoring
└── requirements.txt          # Dependencies for tools above
```

---

## Quick start

Install tool dependencies (once):

```bash
cd redforge
python3 -m pip install -r requirements.txt
```

**CLI (recommended):**

```bash
python3 tools/redforge.py              # Interactive menu
python3 tools/redforge.py list       # All skills and paths
python3 tools/redforge.py search wifi
python3 tools/redforge.py load rootkit
```

**Semantic search (offline TF-IDF):**

```bash
python3 tools/semantic_search.py "stay hidden after shell"
python3 tools/semantic_search.py "Active Directory privilege escalation"
```

**Optional web UI:**

```bash
streamlit run tools/redforge_ui.py
```

**Use a skill as a system prompt:**

```bash
cat skills/ai-redteam/SKILL.md | claude --system-file -
```

Or copy `SKILL.md` into a project’s system instructions / custom GPT.

**Full index, kill-chain combos, and combined “master operator” prompt:** [`MASTER_INDEX.md`](MASTER_INDEX.md).

---

## Skill library

There are **19** topic skills under `skills/`. Paths and one-line reference live in [`MASTER_INDEX.md`](MASTER_INDEX.md). From the repo root:

```bash
python3 tools/redforge.py list
```

Validate locally:

```bash
python3 tools/validate_skill.py skills/
```

---

## Contributing

1. Copy `templates/SKILL_TEMPLATE.md` and fill it out.
2. Run `python3 tools/validate_skill.py` on your new `SKILL.md`.
3. Open a PR with concise optimization notes.

**Quality bar:** follow the template’s response format; include modern techniques and defensive countermeasures; keep loaded size reasonable for LLM context.

---

## License & disclaimer

**License:** MIT

**Use only on systems you own or are explicitly authorized to test.** Misuse may be illegal; authors are not responsible for unauthorized use.

---

*Built with iterative refinement — documentation last aligned with repo layout May 2026.*
