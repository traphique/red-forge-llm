from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from redforge_app.library import LibraryError, SkillLibrary, find_library_root


class SkillLibraryTests(TestCase):
    def test_loads_nested_and_top_level_skills(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "skills" / "web" / "sqli"
            nested.mkdir(parents=True)
            (nested / "SKILL.md").write_text(
                "# SQL Specialist v1.1\n\n**Tags**: sql, web\n\nBody", encoding="utf-8"
            )
            top_level = root / "skills" / "recon"
            top_level.mkdir()
            (top_level / "SKILL.md").write_text("# Recon Specialist\n\nBody", encoding="utf-8")

            library = SkillLibrary.load(root)

            self.assertEqual(len(library.skills), 2)
            sql = library.get("skills/web/sqli/SKILL.md")
            self.assertEqual(sql.title, "SQL Specialist")
            self.assertEqual(sql.category, "web")
            self.assertEqual(sql.tags, ("sql", "web"))
            self.assertEqual(library.get("skills/recon/SKILL.md").category, "general")
            self.assertEqual(find_library_root(root / "skills"), root.resolve())

    def test_rejects_empty_library(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            with self.assertRaises(LibraryError):
                SkillLibrary.load(root)

    def test_parses_space_separated_hashtags(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "skills" / "recon"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "# Recon\n\n**Tags**: #osint #attack-surface #2026-recon\n",
                encoding="utf-8",
            )
            skill = SkillLibrary.load(root).get("skills/recon/SKILL.md")
            self.assertEqual(
                skill.tags,
                ("#osint", "#attack-surface", "#2026-recon"),
            )
