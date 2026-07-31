from unittest import TestCase

from redforge_app.diffing import (
    compare_markdown,
    compare_markdown_section,
    diff_to_html,
    markdown_section_choices,
    split_markdown_sections,
    wrap_diff_markdown,
)


ORIGINAL = """# Skill

## Objectives

Keep this objective.

## Steps

1. Old step

## Detection Notes

Watch this event.
"""

OPTIMIZED = """# Skill

## Objectives

Keep this objective.

## Steps

1. Better step
2. Validate the result

## Detection Notes

Watch this event.
"""


class MarkdownDiffTests(TestCase):
    def test_splits_level_two_sections(self):
        sections = split_markdown_sections(ORIGINAL)
        self.assertEqual(
            [section.name for section in sections],
            ["Document preamble", "Objectives", "Steps", "Detection Notes"],
        )

    def test_changed_sections_only_omits_unchanged_sections(self):
        comparison = compare_markdown(ORIGINAL, OPTIMIZED, changed_sections_only=True)
        self.assertEqual(comparison.changed_sections, ("Steps",))
        self.assertIn("Better step", comparison.right_text)
        self.assertNotIn("Keep this objective", comparison.left_text)
        self.assertNotIn("Watch this event", comparison.right_text)
        self.assertIn("+1. Better step", comparison.unified_diff)

    def test_full_document_mode_keeps_context(self):
        comparison = compare_markdown(ORIGINAL, OPTIMIZED, changed_sections_only=False)
        self.assertIn("Keep this objective", comparison.left_text)
        self.assertIn("Watch this event", comparison.right_text)

    def test_identical_documents_report_no_differences(self):
        comparison = compare_markdown(ORIGINAL, ORIGINAL)
        self.assertEqual(comparison.changed_sections, ())
        self.assertEqual(comparison.unified_diff, "No differences.")

    def test_diff_html_marks_added_and_removed_lines(self):
        rendered = diff_to_html("-old\n+new")
        self.assertIn("#3b1c22", rendered)
        self.assertIn("#173321", rendered)

    def test_diff_html_accepts_larger_text(self):
        rendered = diff_to_html("+new", font_size=18)
        self.assertIn("font-size:18px", rendered)

    def test_compares_one_chosen_section(self):
        choices = dict(markdown_section_choices(ORIGINAL, OPTIMIZED))
        steps_key = next(key for key, label in choices.items() if label == "Steps")
        comparison = compare_markdown_section(ORIGINAL, OPTIMIZED, steps_key)
        self.assertEqual(comparison.changed_sections, ("Steps",))
        self.assertIn("Better step", comparison.unified_diff)
        self.assertNotIn("Keep this objective", comparison.unified_diff)

    def test_markdown_wrapper_names_sources_and_handles_inner_fences(self):
        wrapped = wrap_diff_markdown("+```shell", "Original Skill", "Optimized Skill")
        self.assertTrue(wrapped.startswith("### Original Skill → Optimized Skill"))
        self.assertIn("````diff", wrapped)
        self.assertTrue(wrapped.endswith("````\n"))
