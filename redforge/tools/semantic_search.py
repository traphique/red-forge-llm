#!/usr/bin/env python3
"""
RedForge Local Search (Offline SQLite FTS5/BM25)
Natural-language relevance search across all skills

Usage:
    python3 tools/semantic_search.py "how do I stay hidden after getting a shell?"
    python3 tools/semantic_search.py "escalate privileges in Active Directory"
"""

import sys
from pathlib import Path

REDFORGE_ROOT = Path(__file__).resolve().parent.parent
if str(REDFORGE_ROOT) not in sys.path:
    sys.path.insert(0, str(REDFORGE_ROOT))

from redforge_app import SearchIndex, SkillLibrary


def search(query, top_k=6):
    library = SkillLibrary.load(REDFORGE_ROOT)
    index = SearchIndex(library.skills)
    return index.search(query, limit=top_k)


# Compatibility names used by the interactive CLI.
semantic_search = search


def print_results(query, results):
    print(f'\n🔍 RedForge Local Search: "{query}"\n')
    if not results:
        print("No matches. Try broadening your query or use the CLI menu.")
        return
    for i, result in enumerate(results, 1):
        skill = result.skill
        print(f"{i}. {skill.title}")
        print(f"   Category: {skill.category.title()}")
        print(f"   Relative rank: {result.score:.0%}")
        print(f"   Load: {skill.load_command}\n")


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
    print_results(query, results)

if __name__ == "__main__":
    main()
