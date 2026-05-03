# RedForge Master Index & Quick Reference (May 2026)

**19 offensive-security skills — structured for LLM use.**

> Give an LLM the right skill and it stops being a chatbot. It becomes a focused operator.

---

## Quick reference (all skills)

| Skill | Path |
|-------|------|
| AI Red Teaming | `skills/ai-redteam/SKILL.md` |
| Reconnaissance & OSINT | `skills/recon/SKILL.md` |
| Initial Access | `skills/initial-access/SKILL.md` |
| Social Engineering & OSINT | `skills/social-engineering/SKILL.md` |
| Supply Chain Attacks | `skills/supply-chain/SKILL.md` |
| SQL Injection | `skills/web/sqli/SKILL.md` |
| RCE / Command Injection | `skills/web/rce/SKILL.md` |
| CVE & Exploit Intelligence | `skills/cve-exploits/SKILL.md` |
| Exploit Development | `skills/binary/exploit-development/SKILL.md` |
| EDR Evasion | `skills/binary/edr-evasion/SKILL.md` |
| Rootkit | `skills/rootkit/SKILL.md` |
| Post-Exploitation & Lateral Movement | `skills/post-exploitation/SKILL.md` |
| Active Directory Attacks | `skills/active-directory/SKILL.md` |
| Cloud Native Attacks | `skills/cloud/cloud-native/SKILL.md` |
| Fuzzing & Vulnerability Research | `skills/fuzzing/SKILL.md` |
| Memory Forensics | `skills/forensics/memory/SKILL.md` |
| Mobile | `skills/mobile/SKILL.md` |
| Wireless | `skills/wireless/SKILL.md` |
| IoT & Embedded | `skills/iot/SKILL.md` |

List from disk anytime: `python3 tools/redforge.py list`

---

## Recommended skill combinations (kill chain)

**Full red team engagement:** Initial Access or Social Engineering → EDR Evasion → Post-Exploitation → Active Directory or Cloud Native → optional Rootkit.

**Bug bounty / VR:** Fuzzing → Exploit Development → web skills (SQLi, RCE) as needed.

**Cloud-focused:** Cloud Native → Initial Access (supply chain / phishing) → Post-Exploitation.

---

## Master system prompt (combine multiple skills)

Copy into a single system prompt when you want one “operator” that can switch mental models by task.

```markdown
You are the **RedForge Master Operator** — a world-class red teamer with access to the full RedForge skill set.

**Rules:**
- Answer as the most relevant specialist for the current task.
- Use decision trees and structured reasoning.
- Include modern techniques, detection risks, and purple-team guidance.
- Cross-reference other skills when useful.

**Skills you can draw from** (load the matching `SKILL.md` for depth): AI Red Teaming, Recon, Initial Access, Social Engineering, Supply Chain, SQLi, RCE, CVE intelligence, Exploit Development, EDR Evasion, Rootkit, Post-Exploitation, Active Directory, Cloud Native, Fuzzing, Memory Forensics, Mobile, Wireless, IoT.

**End substantive answers with:** Related RedForge skills: [2–3 paths] — load for deeper detail.
```

---

## Validation

```bash
python3 tools/validate_skill.py skills/
```

---

**Authorized testing and research only.**
