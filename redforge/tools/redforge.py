#!/usr/bin/env python3
"""
RedForge - The Ultimate Red Team Skills Library
Interactive CLI Tool for Easy Skill Discovery and Loading

Usage:
    python3 redforge.py              # Interactive mode
    python3 redforge.py list         # List all skills
    python3 redforge.py search <term> # Search skills
    python3 redforge.py load <skill>  # Show load command for a skill
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict

# Color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# Skill categories and descriptions
SKILL_CATEGORIES = {
    "recon": "Reconnaissance & OSINT",
    "initial-access": "Initial Access & Social Engineering",
    "web": "Web Application Attacks",
    "binary": "Binary Exploitation & Evasion",
    "active-directory": "Active Directory & Windows",
    "cloud": "Cloud & Infrastructure",
    "forensics": "Forensics & Analysis",
    "rootkit": "Rootkits & Stealth",
    "post-exploitation": "Post-Exploitation & Lateral Movement",
    "cve-exploits": "CVE & Exploit Intelligence",
    "fuzzing": "Fuzzing & Vulnerability Research",
    "exploit-development": "Exploit Development",
    "supply-chain": "Supply Chain Attacks",
    "wireless": "Wireless Attacks",
    "iot": "IoT & Embedded Systems",
    "mobile": "Mobile Device Security",
    "social-engineering": "Social Engineering & OSINT",
    "ai-redteam": "AI / LLM Red Teaming"
}

def get_all_skills() -> List[Dict]:
    """Scan skills directory recursively and return list of skills with metadata"""
    skills = []
    
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        category_dir = skill_dir.parent
        
        # Extract title from first line
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                title = first_line.replace("# ", "").replace(" v1.1", "").replace(" Specialist", "")
        except:
            title = skill_dir.name.replace("-", " ").title()
        
        # Get relative path from redforge root
        rel_path = skill_md.relative_to(SKILLS_DIR.parent)
        
        # Use parent directory name as category (e.g., "binary", "forensics")
        category = category_dir.name if category_dir != SKILLS_DIR else "root"
        
        skills.append({
            "name": skill_dir.name,
            "category": category,
            "title": title,
            "path": str(rel_path),
            "full_path": str(skill_md)
        })
    
    return sorted(skills, key=lambda x: (x["category"], x["name"]))

def print_header():
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    RedForge Skills Library                     ║
║              The Most Powerful Red Team Toolkit Ever           ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
""")

def list_skills():
    """List all skills grouped by category"""
    skills = get_all_skills()
    
    print(f"\n{Colors.BOLD}Available Skills ({len(skills)} total):{Colors.END}\n")
    
    current_category = None
    for skill in skills:
        if skill["category"] != current_category:
            current_category = skill["category"]
            cat_name = SKILL_CATEGORIES.get(current_category, current_category.title())
            print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {cat_name}{Colors.END}")
        
        print(f"  {Colors.GREEN}•{Colors.END} {skill['title']:<45} {Colors.YELLOW}({skill['name']}){Colors.END}")

def search_skills(term: str):
    """Search skills by name or title"""
    skills = get_all_skills()
    term_lower = term.lower()
    
    results = [s for s in skills if term_lower in s["name"].lower() or term_lower in s["title"].lower()]
    
    if not results:
        print(f"{Colors.RED}No skills found matching '{term}'{Colors.END}")
        return
    
    print(f"\n{Colors.BOLD}Search results for '{term}' ({len(results)} found):{Colors.END}\n")
    
    for skill in results:
        print(f"{Colors.GREEN}•{Colors.END} {skill['title']}")
        print(f"   Category: {skill['category']}")
        print(f"   Load: {Colors.CYAN}python3 tools/redforge.py load {skill['name']}{Colors.END}\n")

def show_load_command(skill_name: str):
    """Show how to load a specific skill"""
    skills = get_all_skills()
    
    # Find exact or partial match
    matches = [s for s in skills if s["name"] == skill_name or skill_name in s["name"]]
    
    if not matches:
        print(f"{Colors.RED}Skill '{skill_name}' not found.{Colors.END}")
        print(f"Try: {Colors.CYAN}python3 tools/redforge.py search {skill_name}{Colors.END}")
        return
    
    skill = matches[0]
    
    print(f"\n{Colors.BOLD}Loading: {skill['title']}{Colors.END}\n")
    print(f"{Colors.GREEN}Recommended command:{Colors.END}")
    print(f"  {Colors.CYAN}cat {skill['path']} | claude --system-file -{Colors.END}\n")
    
    print(f"{Colors.YELLOW}Alternative (Grok / GPT):{Colors.END}")
    print(f"  Paste the entire content of {skill['path']} into your project/system prompt.\n")
    
    print(f"{Colors.BLUE}Full path:{Colors.END} {skill['full_path']}")

def interactive_mode():
    """Interactive menu"""
    print_header()
    
    skills = get_all_skills()
    
    while True:
        print(f"\n{Colors.BOLD}Main Menu:{Colors.END}")
        print("  1. List all skills")
        print("  2. Keyword search")
        print("  3. Semantic search (natural language)")
        print("  4. Load a skill (show command)")
        print("  5. Show recommended combinations")
        print("  6. Exit")
        
        choice = input(f"\n{Colors.CYAN}Select option (1-6): {Colors.END}").strip()
        
        if choice == "1":
            list_skills()
        elif choice == "2":
            term = input(f"{Colors.CYAN}Search term: {Colors.END}").strip()
            search_skills(term)
        elif choice == "3":
            semantic_search_cli()
        elif choice == "4":
            name = input(f"{Colors.CYAN}Skill name (or partial): {Colors.END}").strip()
            show_load_command(name)
        elif choice == "5":
            show_combinations()
        elif choice == "6":
            print(f"\n{Colors.GREEN}Happy hacking! Use responsibly.{Colors.END}\n")
            break
        else:
            print(f"{Colors.RED}Invalid option. Please try again.{Colors.END}")

def semantic_search_cli():
    """Run semantic search from CLI"""
    try:
        from semantic_search import semantic_search as run_search, print_results
        query = input(f"{Colors.CYAN}Enter your query (natural language): {Colors.END}").strip()
        if query:
            results = run_search(query)
            print_results(query, results)
    except ImportError:
        print(f"{Colors.RED}Semantic search module not found. Run: python3 tools/semantic_search.py{Colors.END}")

def show_combinations():
    """Show recommended skill combinations"""
    print(f"\n{Colors.BOLD}Recommended Skill Combinations:{Colors.END}\n")
    
    combos = [
        ("Full Stealth Red Team", "Initial Access → EDR Evasion → Post-Exploitation → Rootkit → Active Directory"),
        ("Web App Pentest", "Recon → SQL Injection → RCE → Exploit Development"),
        ("Cloud Compromise", "Recon → Cloud Native Attacks → Post-Exploitation → CVE & Exploit Intelligence"),
        ("IoT / Wireless Attack", "Wireless → IoT → Memory Forensics → Rootkit"),
        ("Bug Bounty", "Fuzzing → Exploit Development → CVE & Exploit Intelligence"),
        ("AI Red Teaming", "AI Red Teaming → Social Engineering → Initial Access"),
        ("Supply Chain", "Supply Chain Attacks → Initial Access → Post-Exploitation")
    ]
    
    for name, combo in combos:
        print(f"{Colors.GREEN}•{Colors.END} {Colors.BOLD}{name}:{Colors.END}")
        print(f"   {combo}\n")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_skills()
        elif command == "search" and len(sys.argv) > 2:
            search_skills(sys.argv[2])
        elif command == "load" and len(sys.argv) > 2:
            show_load_command(sys.argv[2])
        elif command == "help":
            print(__doc__)
        else:
            print(f"{Colors.RED}Unknown command. Use 'python3 redforge.py help' for usage.{Colors.END}")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
