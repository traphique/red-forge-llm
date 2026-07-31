from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from redforge_app.library import Skill
from redforge_app.session import (
    SessionError,
    SessionHistoryError,
    build_operator_brief,
    build_session_markdown,
    build_session_prompt,
    format_relative_time,
    load_session_history,
    save_session_history,
    set_session_pinned,
)


def _skill(name, title):
    return Skill(
        name=name,
        title=title,
        category="test",
        relative_path=f"skills/{name}/SKILL.md",
        source_path=Path(f"/tmp/{name}/SKILL.md"),
        content=f"# {title}\n\nInstructions for {name}.",
    )


class SessionPromptTests(TestCase):
    def setUp(self):
        self.recon = _skill("recon", "Recon")
        self.web = _skill("web", "Web")
        self.forensics = _skill("forensics", "Forensics")

    def test_builds_ordered_two_skill_prompt(self):
        prompt = build_session_prompt([self.recon, self.web])
        self.assertIn("1. Recon\n2. Web", prompt)
        self.assertLess(prompt.index("Skill module 1: Recon"), prompt.index("Skill module 2: Web"))
        self.assertIn(self.recon.content, prompt)
        self.assertIn(self.web.content, prompt)

    def test_accepts_three_skills(self):
        prompt = build_session_prompt([self.recon, self.web, self.forensics])
        self.assertIn("3. Forensics", prompt)

    def test_markdown_export_names_skills_before_prompt(self):
        exported = build_session_markdown([self.recon, self.web])
        self.assertIn("**Skills:** Recon → Web", exported)
        self.assertLess(exported.index("**Skills:**"), exported.index("# RedForge Purple-Team Session"))

    def test_operator_brief_summarizes_order_purpose_and_prompt_length(self):
        tagged_recon = Skill(
            **{
                **self.recon.__dict__,
                "tags": ("#recon", "#attack-surface", "#osint"),
            }
        )
        skills = [tagged_recon, self.web]
        prompt = build_session_prompt(skills)
        brief = build_operator_brief(skills)
        self.assertIn("**Chain:** Recon → Web", brief)
        self.assertIn(
            "1. **Recon** — Apply Recon guidance focused on "
            "recon, attack surface, and osint.",
            brief,
        )
        self.assertIn(
            "2. **Web** — Apply Web guidance during this stage",
            brief,
        )
        self.assertIn(
            f"**Combined prompt:** {len(prompt.split()):,} words · "
            f"{len(prompt):,} characters",
            brief,
        )

    def test_rejects_wrong_size_or_duplicates(self):
        with self.assertRaises(SessionError):
            build_session_prompt([self.recon])
        with self.assertRaises(SessionError):
            build_session_prompt([self.recon, self.recon])

    def test_history_keeps_five_newest_unique_chains(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.json"
            for index in range(6):
                save_session_history(
                    path,
                    [f"skills/{index}/a/SKILL.md", f"skills/{index}/b/SKILL.md"],
                )

            records = load_session_history(path)
            self.assertEqual(len(records), 5)
            self.assertEqual(records[0].skills[0], "skills/5/a/SKILL.md")
            self.assertEqual(records[-1].skills[0], "skills/1/a/SKILL.md")

            save_session_history(path, records[-1].skills)
            moved = load_session_history(path)
            self.assertEqual(len(moved), 5)
            self.assertEqual(moved[0].skills, records[-1].skills)

    def test_pinned_chain_survives_eviction_and_only_one_can_be_pinned(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.json"
            pinned_paths = ("skills/pinned/a/SKILL.md", "skills/pinned/b/SKILL.md")
            other_pin = ("skills/other/a/SKILL.md", "skills/other/b/SKILL.md")
            save_session_history(path, pinned_paths)
            save_session_history(path, other_pin)
            set_session_pinned(path, pinned_paths, True)
            self.assertTrue(next(r for r in load_session_history(path) if r.skills == pinned_paths).pinned)

            set_session_pinned(path, other_pin, True)
            records = load_session_history(path)
            self.assertFalse(next(r for r in records if r.skills == pinned_paths).pinned)
            self.assertTrue(next(r for r in records if r.skills == other_pin).pinned)

            for index in range(6):
                save_session_history(
                    path,
                    [f"skills/{index}/a/SKILL.md", f"skills/{index}/b/SKILL.md"],
                )
            records = load_session_history(path)
            self.assertEqual(len(records), 5)
            self.assertIn(other_pin, [record.skills for record in records])
            self.assertTrue(next(r for r in records if r.skills == other_pin).pinned)

    def test_relative_time_is_short(self):
        now = datetime(2026, 7, 31, 6, 30, tzinfo=timezone.utc)
        self.assertEqual(format_relative_time(now - timedelta(seconds=20), now), "just now")
        self.assertEqual(format_relative_time(now - timedelta(minutes=2), now), "2 min ago")
        self.assertEqual(format_relative_time(now - timedelta(hours=3), now), "3 hr ago")

    def test_history_rejects_malformed_json(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(SessionHistoryError):
                load_session_history(path)

    def test_history_reads_records_saved_before_pinning_existed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.json"
            path.write_text(
                '[{"skills":["skills/recon/SKILL.md","skills/web/sqli/SKILL.md"],'
                '"saved_at":"2026-07-31T06:00:00Z"}]',
                encoding="utf-8",
            )
            self.assertFalse(load_session_history(path)[0].pinned)
