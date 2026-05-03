#!/usr/bin/env python3
"""
RedForge Semantic Search (Offline TF-IDF Version)
Natural language search across all skills

Usage:
    python3 tools/semantic_search.py "how do I stay hidden after getting a shell?"
    python3 tools/semantic_search.py "escalate privileges in Active Directory"
"""

import os
import sys
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

SKILLS_DIR = Path(__file__).parent.parent / "skills"

def extract_rich_content(skill_md_path: Path) -> str:
    """Extract rich content for better semantic matching"""
    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = []
        
        # Title
        title = re.search(r'^# (.+)', content, re.MULTILINE)
        if title:
            sections.append(title.group(1))
        
        # Tags (very important for matching)
        tags = re.search(r'\*\*Tags\*\*:\s*(.+)', content)
        if tags:
            sections.append(tags.group(1))
        
        # Core Identity (most important)
        core = re.search(r'## Your Persona & Non-Negotiable Rules\n(.+?)(?=\n## |$)', content, re.DOTALL)
        if core:
            sections.append(core.group(1)[:1000])
        
        # 2026 section
        modern = re.search(r'## .*2026.*\n(.+?)(?=\n## |$)', content, re.IGNORECASE | re.DOTALL)
        if modern:
            sections.append(modern.group(1)[:800])
        
        # Decision Tree
        dt = re.search(r'## .*Decision Tree.*\n(.+?)(?=\n## |$)', content, re.IGNORECASE | re.DOTALL)
        if dt:
            sections.append(dt.group(1)[:600])
        
        # Primary Techniques
        primary = re.search(r'## Primary.*\n(.+?)(?=\n## |$)', content, re.IGNORECASE | re.DOTALL)
        if primary:
            sections.append(primary.group(1)[:700])
        
        # Advanced Techniques
        advanced = re.search(r'## .*Advanced.*\n(.+?)(?=\n## |$)', content, re.IGNORECASE | re.DOTALL)
        if advanced:
            sections.append(advanced.group(1)[:600])
        
        return ' '.join(sections)
    except:
        return str(skill_md_path.parent.name)

def load_skills():
    skills = []
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        category = skill_dir.parent.name
        
        content = extract_rich_content(skill_md)
        
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                title = f.readline().strip().replace("# ", "").replace(" v1.1", "")
        except:
            title = skill_dir.name.replace("-", " ").title()
        
        skills.append({
            "name": skill_dir.name,
            "category": category,
            "title": title,
            "content": content,
            "path": str(skill_md.relative_to(SKILLS_DIR.parent))
        })
    return skills

def search(query, top_k=6):
    skills = load_skills()
    
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=8000,
        ngram_range=(1, 3),
        min_df=1
    )
    
    docs = [s["content"] for s in skills]
    tfidf = vectorizer.fit_transform(docs)
    qvec = vectorizer.transform([query])
    
    sims = cosine_similarity(qvec, tfidf).flatten()
    top_idx = np.argsort(sims)[::-1][:top_k]
    
    results = []
    for i in top_idx:
        if sims[i] > 0.08:
            s = skills[i]
            results.append({
                "name": s["name"],
                "title": s["title"],
                "category": s["category"],
                "score": round(float(sims[i]), 3),
                "path": s["path"]
            })
    return results

def main():
    if len(sys.argv) < 2:
        print('Usage: python3 tools/semantic_search.py "your query in natural language"')
        print('\nExamples:')
        print('  python3 tools/semantic_search.py "how do I stay hidden after getting a shell?"')
        print('  python3 tools/semantic_search.py "escalate privileges in Active Directory"')
        print('  python3 tools/semantic_search.py "attack IoT devices"')
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    results = search(query)
    
    print(f'\n🔍 RedForge Semantic Search: "{query}"\n')
    
    if not results:
        print("No strong matches. Try broadening your query or use the CLI menu.")
        return
    
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   Category: {r['category'].title()}")
        print(f"   Relevance: {r['score']:.1%}")
        print(f"   Load: cat {r['path']} | claude --system-file -\n")

if __name__ == "__main__":
    main()
