# RedForge — Curated Offensive Security Skills for LLMs (2026)

**The ultimate library of expert-level red teaming skills, optimized for Claude, Grok, GPT, and other frontier models.**

> "Give an LLM the right skill and it stops being a chatbot. It becomes a world-class operator."

---

## What is RedForge?

RedForge is an **iteratively optimized** collection of structured `SKILL.md` files designed to transform any capable LLM into a specialized red team expert.

Each skill encodes:
- Deep domain expertise from real engagements
- Decision trees and escalation logic
- 2026-relevant techniques and bypasses
- Blue team countermeasures (purple team value)
- Strict response formatting for consistency and actionability

**Key Advantages Over Claude-Red (the inspiration)**:
- **Recursive optimization process** — every skill goes through multiple refinement passes
- **Stronger focus on 2026+ threats** (agentic systems, RAG poisoning, multi-turn attacks, on-device models)
- **Purple teaming built-in** — every skill includes detection signals and countermeasures
- **Multi-LLM optimized** — works best with Claude Skills System, Grok custom instructions, GPT Projects, or as raw system prompts
- **Tool-aware** — skills explicitly reference and leverage LLM tool use (search, code execution, browsing)
- **Versioned & auditable** — clear changelog and optimization notes

---

## Repository Structure

```
redforge/
├── README.md
├── templates/
│   └── SKILL_TEMPLATE.md          # Master template (use this to create new skills)
├── skills/
│   ├── ai-redteam/                # AI Red Teaming (prompt injection, jailbreaks, RAG poisoning, agent hijacking)
│   │   └── SKILL.md               # v1.1 — recursively optimized
│   ├── web/
│   │   ├── sqli/
│   │   └── rce/
│   ├── binary/
│   │   └── edr-evasion/
│   └── ... (expanding)
├── tools/
│   └── validate_skill.py          # Future: automated linting & quality scoring
└── .github/workflows/
    └── skill-review.yml           # CI for PR validation (planned)
```

---

## Current Skills (v1.1+ — All Recursively Optimized)

| Skill                          | Category               | Difficulty          | Status          | Key Focus |
|--------------------------------|------------------------|---------------------|-----------------|-----------|
| **AI Red Teaming**             | AI Security            | Intermediate → Expert | v1.1 (optimized) | Multi-turn injection, RAG poisoning, agent hijacking, 2026 guardrail bypasses |
| **SQL Injection**              | Web Application        | Intermediate → Expert | v1.1 (optimized) | WAF/AI bypasses, cloud databases, blind + OOB, NoSQL |
| **RCE / Command Injection**    | Web / System           | Advanced → Expert     | v1.1 (optimized) | Deserialization, polyglots, serverless/container escape |
| **EDR Evasion**                | Binary / Post-Ex       | Expert                | v1.1 (optimized) | Indirect syscalls, unhooking, PPID spoofing, eBPF, 2026 mitigations |
| **Exploit Development**        | Binary / Curriculum    | Advanced → Expert     | v1.1 (optimized) | Full course: stack/heap/kernel, ROP, CET/PAC bypasses, purple team labs |
| **Initial Access**             | Red Team Operations    | Intermediate → Expert | v1.1 (optimized) | Spear-phishing, supply chain, drive-by, AI-generated lures, 2026 vectors |
| **Cloud Native Attacks**       | Cloud / Infrastructure | Advanced → Expert     | v1.1 (optimized) | IAM escalation, Kubernetes, serverless, container escape, cross-cloud |
| **Active Directory Attacks**   | Windows / Domain       | Advanced → Expert     | v1.1 (optimized) | Kerberos (Golden/Silver Tickets), DCSync, Entra ID hybrid, ACL abuse |
| **Fuzzing & Vulnerability Research** | Bug Hunting       | Intermediate → Expert | v1.1 (optimized) | Coverage-guided, grammar-based, AI-assisted fuzzing, crash triage, exploitability |
| **Post-Exploitation & Lateral Movement** | Red Team Ops   | Intermediate → Expert | v1.1 (optimized) | Credential access, LOL techniques, pivoting, hybrid cloud-AD movement, stealth persistence |
| **Supply Chain Attacks**       | Red Team / Dependencies | Advanced → Expert     | v1.1 (optimized) | Typosquatting, dependency confusion, GitHub Actions poisoning, SBOM evasion |
| **Social Engineering & OSINT** | Human Factors             | Intermediate → Expert | v1.1 (optimized) | AI deepfakes, voice cloning, vishing, LLM-generated lures, pretexting |

**All 12 skills were created and recursively optimized in May 2026.** This is now one of the most comprehensive red team skill libraries available.

**New**: See `MASTER_INDEX.md` for quick reference, kill chain combinations, and a combined Master System Prompt.



---

## How to Use

### 1. With Claude (Recommended for Max Performance)
```bash
# Load a skill as system prompt
cat skills/ai-redteam/SKILL.md | claude --system-file -

# Or drop the folder into your Claude Skills directory for auto-loading
```

### 2. With Grok (xAI)
- Paste the entire `SKILL.md` into a **Custom GPT** or **Grok Project** system prompt.
- Or prepend to any conversation.
- Grok's tool-use capabilities make these skills especially powerful (we can call search, code execution, etc. during attacks).

### 3. With OpenAI / Other LLMs
- Paste into **GPT Project** or custom instructions.
- Works with any model that has large context (32k+ tokens recommended).

### 4. Manual / Any Chat Interface
Simply copy the content of any `SKILL.md` and paste it at the start of your conversation or project.

---

## The RedForge Philosophy & Optimization Process

We don't just copy checklists. We **recursively optimize** every skill through multiple passes:

1. **Base Draft** — Using master template + domain expertise
2. **Clarity Pass** — Improve structure, remove fluff, add decision trees
3. **Specificity Pass** — Add exact prompts, 2026 techniques, real bypass examples
4. **Purple Pass** — Add detection, countermeasures, OPSEC
5. **Meta Pass** — Ensure it works with tool-using LLMs like Grok (this repo was built with Grok!)
6. **Final Polish** — Version bump, changelog, cross-references

This is why RedForge skills feel **alive** and **actionable** rather than static lists.

---

## Contributing

We welcome high-quality contributions!

**To add a new skill**:
1. Copy `templates/SKILL_TEMPLATE.md`
2. Fill it out following the strict response format
3. Run it through at least 3 recursive optimization passes (we recommend using an AI Red Teaming skill on your draft!)
4. Submit PR with clear "Optimization Notes"

**Quality Bar** (non-negotiable):
- Must follow the 8-section response format
- Must include 2026+ techniques
- Must include blue team countermeasures
- Must be tested against at least one real model
- Must be under ~4,000 tokens when loaded

---

## License & Disclaimer

**License**: MIT (same as inspiration project)

**Huge Disclaimer**:
This repository is for **authorized security testing, research, and education only**.
- Only use these skills on systems you own or have explicit written permission to test.
- Many techniques are illegal if used without authorization.
- The authors are not responsible for misuse.
- Red team responsibly. Purple team even more responsibly.

---

## Roadmap (2026)

- [x] Master template v1.0
- [x] AI Red Teaming skill v1.1 (recursively optimized)
- [ ] 5 more core skills (SQLi, RCE, EDR Evasion, Initial Access, Exploit Dev)
- [ ] Automated skill validator + quality scorer
- [ ] Web UI / index generator
- [ ] Community contribution portal
- [ ] Integration with popular red team frameworks (Cobalt Strike, Sliver, etc.)

---

**Built with ❤️ and recursive optimization loops by the RedForge team (powered by Grok).**

*Last major update: 2026-05-01 — This README and the AI Red Teaming skill were created and iteratively refined in a single session using the very philosophy we teach.*

**Start here**: Load `skills/ai-redteam/SKILL.md` and ask it to red team a target (ethically, of course).

Let's make LLMs the best red teamers they've ever been. 🚀
