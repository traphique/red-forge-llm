#!/usr/bin/env python3
"""
RedForge Skill Validator & Scorer v1.0
Validates and scores SKILL.md files for quality, format compliance, and 2026 relevance.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class SkillValidator:
    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.content = ""
        self.score = 0
        self.max_score = 100
        self.issues = []
        self.strengths = []

    def load(self) -> bool:
        try:
            with open(self.skill_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except Exception as e:
            self.issues.append(f"Failed to read file: {e}")
            return False

    def check_required_sections(self) -> int:
        """Check for the 8 required sections (strict format)"""
        required_sections = [
            r"Your Persona & Non-Negotiable Rules",
            r"Core Knowledge Base",
            r"Decision Tree",
            r"2026",
            r"Blue Team|Purple Team",
            r"OPSEC",
            r"References|Tooling",
            r"END OF SKILL"
        ]
        
        score = 0
        for section in required_sections:
            if re.search(section, self.content, re.IGNORECASE):
                score += 8  # 8 points per section (64 total)
                self.strengths.append(f"✓ Contains required section: {section}")
            else:
                self.issues.append(f"✗ Missing required section: {section}")
        
        return score

    def check_version_and_date(self) -> int:
        """Check for version and recent update"""
        score = 0
        if re.search(r"\*?\*?Version\*?\*?:\s*1\.[0-9]", self.content):
            score += 5
            self.strengths.append("✓ Proper version number (v1.x)")
        else:
            self.issues.append("✗ Missing or invalid version number")
        
        if re.search(r"\*?\*?Last Updated\*?\*?:\s*2026", self.content):
            score += 5
            self.strengths.append("✓ Updated in 2026")
        else:
            self.issues.append("✗ Not updated in 2026")
        
        return score

    def check_2026_relevance(self) -> int:
        """Check for 2026-specific content"""
        score = 0
        keywords = [
            "2026", "AI-assisted", "LLM", "Entra ID", "hybrid", "serverless",
            "eBPF", "CET", "PAC", "Shadow Stack", "grammar-based", "coverage-guided",
            "living-off-the-land", "LOL", "BloodHound", "Kerberoasting", "Entra", "hybrid identity"
        ]
        
        found = 0
        for kw in keywords:
            if kw.lower() in self.content.lower():
                found += 1
        
        score = min(found * 2, 20)  # Up to 20 points
        
        if score >= 8:
            self.strengths.append(f"✓ Strong 2026 relevance ({found} modern keywords found)")
        else:
            self.issues.append(f"✗ Weak 2026 relevance (only {found} modern keywords)")
        
        return score

    def check_length_and_depth(self) -> int:
        """Check for appropriate length and depth"""
        word_count = len(self.content.split())
        score = 0
        
        if 1500 <= word_count <= 4000:
            score += 10
            self.strengths.append(f"✓ Good length ({word_count} words)")
        elif word_count < 1500:
            self.issues.append(f"✗ Too short ({word_count} words) — needs more depth")
        else:
            self.issues.append(f"✗ Too long ({word_count} words) — may exceed context limits")
        
        # Check for code examples, tables, decision trees
        if "```" in self.content:
            score += 5
            self.strengths.append("✓ Contains code examples")
        if "|" in self.content and "---" in self.content:
            score += 5
            self.strengths.append("✓ Contains tables")
        
        return score

    def check_purple_team(self) -> int:
        """Check for purple team / defensive content"""
        score = 0
        if re.search(r"Blue Team|Purple Team|Detection|Countermeasures", self.content, re.IGNORECASE):
            score += 10
            self.strengths.append("✓ Includes blue/purple team content")
        else:
            self.issues.append("✗ Missing blue/purple team recommendations")
        return score

    def check_cross_references(self) -> int:
        """Check for links to other RedForge skills"""
        score = 0
        if "Related RedForge Skills" in self.content or "use the " in self.content.lower():
            score += 5
            self.strengths.append("✓ Cross-references other skills")
        else:
            self.issues.append("✗ No cross-references to other RedForge skills")
        return score

    def validate(self) -> Dict:
        if not self.load():
            return {"valid": False, "score": 0, "issues": self.issues}
        
        self.score = 0
        self.score += self.check_required_sections()
        self.score += self.check_version_and_date()
        self.score += self.check_2026_relevance()
        self.score += self.check_length_and_depth()
        self.score += self.check_purple_team()
        self.score += self.check_cross_references()
        
        # Bonus for excellent structure
        if len(self.issues) == 0:
            self.score += 5
            self.strengths.append("✓ Perfect structure — no issues found")
        
        return {
            "valid": len(self.issues) == 0,
            "score": min(self.score, self.max_score),
            "issues": self.issues,
            "strengths": self.strengths,
            "word_count": len(self.content.split())
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_skill.py <path_to_SKILL.md> [or directory]")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    
    if target.is_dir():
        # Validate all SKILL.md files in directory
        skills = list(target.rglob("SKILL.md"))
        print(f"Found {len(skills)} skills to validate...\n")
        
        results = []
        for skill in skills:
            validator = SkillValidator(str(skill))
            result = validator.validate()
            results.append((skill, result))
            print(f"{skill.parent.name}: {result['score']}/100 {'✓' if result['valid'] else '✗'}")
        
        print("\n=== SUMMARY ===")
        avg_score = sum(r[1]['score'] for r in results) / len(results)
        print(f"Average Score: {avg_score:.1f}/100")
        print(f"Perfect Skills: {sum(1 for r in results if r[1]['valid'])}/{len(results)}")
        
    else:
        # Validate single skill
        validator = SkillValidator(str(target))
        result = validator.validate()
        
        print(f"\n=== RedForge Skill Validation Report ===")
        print(f"File: {target}")
        print(f"Score: {result['score']}/{validator.max_score}")
        print(f"Status: {'VALID ✓' if result['valid'] else 'NEEDS IMPROVEMENT ✗'}")
        print(f"Word Count: {result['word_count']}")
        
        if result['strengths']:
            print("\n--- Strengths ---")
            for s in result['strengths']:
                print(f"  {s}")
        
        if result['issues']:
            print("\n--- Issues to Fix ---")
            for i in result['issues']:
                print(f"  {i}")
        
        print("\nRecommendation:", end=" ")
        if result['score'] >= 90:
            print("Excellent — ready for production use.")
        elif result['score'] >= 75:
            print("Good — minor improvements recommended.")
        else:
            print("Needs significant work before release.")
        
        if result['valid']:
            print("Overall Status: VALID ✓")
        else:
            print("Overall Status: NEEDS IMPROVEMENT (but score is high)")

if __name__ == "__main__":
    main()
