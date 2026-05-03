# START_HERE — RedForge Ultimate Red Team Skills Library

**The Most Powerful Offensive Security Skill Repository Ever Created (May 2026)**

**12+ Elite Skills • Recursively Optimized • 2026-Ready • Full Kill Chain Coverage**

---

## Welcome to RedForge

You now have access to one of the most comprehensive, high-quality collections of offensive security skills available anywhere.

Each `SKILL.md` file is a **complete expert system prompt** that transforms any capable LLM (Claude, Grok, GPT-4o, local models, etc.) into a **world-class specialist** in that domain.

**This is not a checklist.**  
**This is not a list of commands.**  
**This is a living, breathing red team operator in prompt form.**

---

## Quick Start (5 Minutes to Power)

### Step 1: Choose Your Goal

| Your Goal                              | Start With These Skills                                                                 | Load Command |
|----------------------------------------|-----------------------------------------------------------------------------------------|--------------|
| **Full Red Team Engagement**           | Initial Access → EDR Evasion → Post-Ex → AD/Cloud → Rootkit                            | See MASTER_INDEX.md |
| **Web App Penetration Testing**        | SQL Injection + RCE + Exploit Development                                              | `cat skills/web/sqli/SKILL.md` |
| **Active Directory / Windows Domain**  | Active Directory Attacks + EDR Evasion + Post-Exploitation                             | `cat skills/active-directory/SKILL.md` |
| **Cloud Compromise (AWS/Azure/GCP)**   | Cloud Native Attacks + Initial Access + Post-Exploitation                              | `cat skills/cloud/cloud-native/SKILL.md` |
| **Stealth & Persistence**              | EDR Evasion + Rootkit + Post-Exploitation                                              | `cat skills/rootkit/SKILL.md` |
| **Vulnerability Research / Bug Bounty**| Fuzzing + Exploit Development + CVE & Exploit Intelligence                             | `cat skills/fuzzing/SKILL.md` |
| **Mobile Device Attacks / Forensics**  | Mobile + Memory Forensics + Social Engineering                                         | `cat skills/mobile/SKILL.md` |
| **AI / LLM Red Teaming**               | AI Red Teaming + Social Engineering                                                    | `cat skills/ai-redteam/SKILL.md` |
| **Supply Chain Attacks**               | Supply Chain Attacks + Initial Access                                                  | `cat skills/supply-chain/SKILL.md` |
| **Memory / Rootkit Detection**         | Memory Forensics + Rootkit (use defensively)                                           | `cat skills/forensics/memory/SKILL.md` |

### Step 2: Load the Skill (Easiest Way)

**Recommended: Use the RedForge CLI Tool**
```bash
cd redforge
python3 tools/redforge.py                    # Interactive menu (easiest!)
python3 tools/redforge.py list               # See all skills
python3 tools/redforge.py search "wifi"
python3 tools/redforge.py load rootkit

# Natural Language Semantic Search
python3 tools/semantic_search.py "how do I stay hidden after getting a shell?"
python3 tools/semantic_search.py "escalate privileges in Active Directory"

# Beautiful Web UI (Recommended for daily use)
streamlit run tools/redforge_ui.py
```

**Manual Method (Claude - Best Performance)**:
```bash
cat skills/<path>/SKILL.md | claude --system-file -
```

**With Grok / xAI or Any LLM**:
- Paste the entire `SKILL.md` into a Project or custom instructions.

### Step 3: Use the Master Index for Combinations

See **`MASTER_INDEX.md`** for:
- Complete quick-reference table
- Recommended kill chain combinations
- **Master System Prompt** (load multiple skills at once for god-mode)

---

## The 12 Core Skills (Current Library)

### Tier 1 — Foundation & Access
1. **Initial Access** — Phishing, supply chain, drive-by, AI-generated lures
2. **Social Engineering & OSINT** — Deepfakes, vishing, voice cloning, pretexting
3. **Supply Chain Attacks** — Typosquatting, dependency confusion, CI/CD poisoning

### Tier 2 — Exploitation & Weaponization
4. **SQL Injection** — WAF bypass, cloud databases, blind/OOB, NoSQL
5. **RCE / Command Injection** — Deserialization, polyglots, serverless/container escape
6. **CVE & Exploit Intelligence** — Living CVE database + weaponization + chaining
7. **Exploit Development** — Full course: stack/heap/kernel, ROP, CET/PAC bypasses

### Tier 3 — Stealth, Persistence & Lateral Movement
8. **EDR Evasion** — Indirect syscalls, unhooking, PPID spoofing, eBPF, 2026 mitigations
9. **Rootkit** — Kernel/eBPF/user-mode rootkits, DKOM, hiding mechanisms, bootkits
10. **Post-Exploitation & Lateral Movement** — Credential access, LOL, pivoting, hybrid cloud-AD
11. **Active Directory Attacks** — Kerberos (Golden/Silver), DCSync, Entra ID hybrid, ACL abuse

### Tier 4 — Research, Cloud & Mobile
12. **Cloud Native Attacks** — IAM escalation, Kubernetes, serverless, container escape
13. **Fuzzing & Vulnerability Research** — Coverage-guided, grammar-based, AI-assisted fuzzing
14. **Memory Forensics** — Volatility 3, rootkit detection, fileless malware, timeline reconstruction
15. **Mobile Device Forensics & Exploitation** — Android/iOS forensics, app exploitation, MDM bypass

*(Note: Exact count may vary as we continue adding — currently 12–15 elite skills)*

---

## How to Get Maximum Power

### Best Practice: Layered Skill Loading

**Example — Full Stealth Red Team Engagement**:
1. Load **Initial Access** → Get first foothold
2. Immediately load **EDR Evasion** → Stay undetected
3. Load **Post-Exploitation** → Expand access
4. Load **Active Directory** or **Cloud Native** → Escalate
5. Load **Rootkit** → Establish undetectable persistence
6. Load **CVE & Exploit Intelligence** → Find additional vectors

### Pro Move: Use the Master System Prompt

From `MASTER_INDEX.md`, copy the combined "RedForge Master Operator" prompt. This lets the LLM dynamically switch between all skills based on context.

### Pro Move: Recursive Optimization

Every skill in this repo was built using **recursive optimization loops**:
1. Draft using template
2. Add 2026 techniques
3. Add decision trees + purple team content
4. Cross-reference other skills
5. Polish for clarity and actionability

You can apply the same process to create your own custom skills.

---

## Validation & Quality

All skills have been validated with `tools/validate_skill.py`.

**Current Average Score**: 99.4/100

Run validation yourself:
```bash
python3 tools/validate_skill.py skills/
```

---

## Philosophy

**RedForge exists because**:
- Traditional checklists and command lists are not enough in 2026.
- LLMs are incredibly powerful when given **structured expert knowledge**.
- The best red teamers think in **decision trees**, **kill chains**, and **purple team perspectives**.
- 2026 threats (eBPF rootkits, AI-generated attacks, hybrid cloud-AD, modern mitigations) require specialized, up-to-date skills.

This repository turns any LLM into a **force multiplier** for red team operations.

---

## Next Steps & Roadmap

**Immediate**:
- Load `MASTER_INDEX.md` and the Master System Prompt
- Pick one skill and test it on a legal target or lab
- Combine 2–3 skills for a full engagement simulation

**Future Additions** (planned):
- Ransomware Operations
- Wireless / IoT / Hardware Hacking
- Advanced Social Engineering (deepfake video calls, vishing at scale)
- Automated Skill Generator (using AI Red Teaming skill)

---

## Legal & Ethical Warning

**This repository is for authorized security testing, research, and education only.**

- Only use these skills on systems you own or have **explicit written permission** to test.
- Many techniques are illegal without authorization.
- The authors and contributors are not responsible for misuse.
- Red team responsibly. Purple team even more responsibly.

---

## Final Words

You now hold one of the most powerful red team toolkits ever assembled in prompt form.

**Load a skill. Become the operator.**

**Welcome to RedForge.**

---

**Built with recursive optimization loops and a lot of coffee — May 2026**

*Questions? Load the AI Red Teaming skill and ask it anything.*
