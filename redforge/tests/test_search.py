from pathlib import Path
from unittest import TestCase

from redforge_app.library import Skill
from redforge_app.search import SearchIndex


def _skill(name, title, category, content, tags=()):
    return Skill(
        name=name,
        title=title,
        category=category,
        relative_path=f"skills/{category}/{name}/SKILL.md",
        source_path=Path(f"/tmp/{name}/SKILL.md"),
        content=content,
        tags=tags,
    )


class SearchIndexTests(TestCase):
    def setUp(self):
        self.skills = [
            _skill(
                "edr-evasion",
                "EDR Evasion Specialist",
                "binary",
                "endpoint detection stealth process injection",
                ("opsec", "windows"),
            ),
            _skill(
                "sqli",
                "SQL Injection Specialist",
                "web",
                "database queries parameters injection web application",
                ("sql",),
            ),
        ]
        self.index = SearchIndex(self.skills)

    def test_searches_content_and_metadata(self):
        results = self.index.search("stay stealthy around endpoint detection")
        self.assertTrue(results)
        self.assertEqual(results[0].skill.name, "edr-evasion")

    def test_filters_by_category(self):
        self.assertEqual(self.index.search("injection", category="binary")[0].skill.name, "edr-evasion")
        self.assertEqual(self.index.search("injection", category="web")[0].skill.name, "sqli")

    def test_empty_query_lists_skills(self):
        self.assertEqual(len(self.index.search("")), 2)

