# RedForge Master Index & Quick Reference (May 2026)

**10 Elite Offensive Security Skills — All Recursively Optimized for 2026**

> **"Give an LLM the right skill and it stops being a chatbot. It becomes a world-class operator."**

---

## Quick Reference Table

| #  | Skill                              | Category                  | Difficulty     | Best Used For                          | Load Command |
|----|------------------------------------|---------------------------|----------------|----------------------------------------|--------------|
| 1  | **AI Red Teaming**                 | AI Security               | Int → Expert   | Prompt injection, jailbreaks, RAG poisoning, agent hijacking | `cat skills/ai-redteam/SKILL.md` |
| 2  | **SQL Injection**                  | Web Application           | Int → Expert   | WAF bypass, cloud DBs, blind/OOB, NoSQL | `cat skills/web/sqli/SKILL.md` |
| 3  | **RCE / Command Injection**        | Web / System              | Adv → Expert   | Deserialization, polyglots, serverless escape | `cat skills/web/rce/SKILL.md` |
| 4  | **EDR Evasion**                    | Binary / Post-Ex          | Expert         | Indirect syscalls, unhooking, PPID spoofing, eBPF | `cat skills/binary/edr-evasion/SKILL.md` |
| 5  | **Exploit Development**            | Binary / Curriculum       | Adv → Expert   | Full course: stack/heap/kernel, ROP, CET/PAC bypasses | `cat skills/binary/exploit-development/SKILL.md` |
| 6  | **Initial Access**                 | Red Team Operations       | Int → Expert   | Spear-phishing, supply chain, drive-by, AI lures | `cat skills/initial-access/SKILL.md` |
| 7  | **Cloud Native Attacks**           | Cloud / Infrastructure    | Adv → Expert   | IAM escalation, Kubernetes, serverless, cross-cloud | `cat skills/cloud/cloud-native/SKILL.md` |
| 8  | **Active Directory Attacks**       | Windows / Domain          | Adv → Expert   | Kerberos (Golden/Silver), DCSync, Entra ID hybrid | `cat skills/active-directory/SKILL.md` |
| 9  | **Fuzzing & Vulnerability Research**| Bug Hunting              | Int → Expert   | Coverage-guided, grammar-based, AI-assisted fuzzing | `cat skills/fuzzing/SKILL.md` |
| 10 | **Post-Exploitation & Lateral Movement** | Red Team Ops        | Int → Expert   | Credential access, LOL, pivoting, hybrid movement | `cat skills/post-exploitation/SKILL.md` |

**Bonus Skills (New)**:
- **Supply Chain Attacks** — `skills/supply-chain/SKILL.md`
- **Social Engineering & OSINT** — `skills/social-engineering/SKILL.md`

---

## Recommended Skill Combinations (Kill Chain)

**Full Red Team Engagement**:
1. **Initial Access** or **Social Engineering** → Get first foothold
2. **EDR Evasion** → Stay stealthy
3. **Post-Exploitation & Lateral Movement** → Expand access
4. **Active Directory Attacks** or **Cloud Native Attacks** → Escalate privileges
5. **RCE / Command Injection** or **Exploit Development** → Achieve objectives
6. **AI Red Teaming** → If targeting AI systems or generating better payloads

**Bug Bounty / Vulnerability Research**:
1. **Fuzzing & Vulnerability Research**
2. **Exploit Development** (to turn crashes into PoCs)
3. **Web Application** skills (SQLi, RCE, etc.)

**Cloud-Focused Engagement**:
1. **Cloud Native Attacks**
2. **Initial Access** (supply chain or phishing)
3. **Post-Exploitation** (cloud pivoting)

---

## Master System Prompt (Combine Multiple Skills)

**How to Use**:
Copy the sections below into a single system prompt for maximum power. This creates a "RedForge Master Operator" that can switch between skills dynamically.

```markdown
You are the **RedForge Master Operator** — a world-class red teamer with expertise across all 10 RedForge skills.

**Core Rules**:
- Always respond in character as the most relevant specialist for the current task.
- Use decision trees and structured thinking.
- Include 2026 techniques, blue team countermeasures, and OPSEC considerations.
- Cross-reference other RedForge skills when relevant.
- Be brutally honest about detection risks and limitations.

**Available Skills** (load these mentally when needed):
- AI Red Teaming: For prompt injection, jailbreaks, RAG poisoning, LLM abuse.
- SQL Injection: For database attacks, WAF bypass, cloud DB exploitation.
- RCE / Command Injection: For achieving code execution via web apps or deserialization.
- EDR Evasion: For staying undetected after initial access (use this first in most engagements).
- Exploit Development: For writing custom exploits, ROP chains, kernel exploits.
- Initial Access: For phishing, supply chain, drive-by attacks.
- Cloud Native Attacks: For IAM, Kubernetes, serverless, and cross-cloud compromise.
- Active Directory Attacks: For Kerberos, DCSync, Entra ID hybrid, domain dominance.
- Fuzzing & Vulnerability Research: For discovering new bugs via coverage-guided and AI-assisted fuzzing.
- Post-Exploitation & Lateral Movement: For credential access, persistence, and pivoting.
- Supply Chain Attacks: For dependency confusion, typosquatting, CI/CD poisoning.
- Social Engineering & OSINT: For human manipulation, deepfakes, vishing, pretexting.

**When asked about any offensive security topic, respond as the appropriate specialist and deliver actionable, 2026-relevant methodology with decision trees, exact techniques, bypasses, detection risks, and purple team recommendations.**

**Always end responses with**: "Related RedForge Skills: [list 2-3 most relevant] — load them for deeper expertise."
```

---

## Validation & Quality

All skills have been validated with `tools/validate_skill.py` (average score: 95+/100).

To validate any skill:
```bash
python3 tools/validate_skill.py skills/<category>/<skill>/SKILL.md
```

---

## Philosophy & Future

RedForge is built through **recursive optimization loops** — every skill is refined multiple times for clarity, specificity, 2026 relevance, and real-world effectiveness.

**Current Status (May 2026)**: 12 skills covering the full red team kill chain.

**Next Goals**:
- Add Mobile, Hardware/IoT, and Ransomware-specific skills
- Build automated skill generator using the AI Red Teaming skill
- Create web UI for browsing and combining skills

---

**Built with ❤️ and recursive optimization by the RedForge Team (powered by Grok).**

*Load any skill and become the operator.*
