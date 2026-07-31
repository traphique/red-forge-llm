"""Markdown-aware comparison helpers for skills and generated chains."""

from __future__ import annotations

import difflib
import html
import re
from dataclasses import dataclass

_H2_RE = re.compile(r"^##\s+(.+?)\s*$")
_KEY_RE = re.compile(r"[^\w]+", re.UNICODE)


@dataclass(frozen=True)
class MarkdownSection:
    key: str
    name: str
    text: str


@dataclass(frozen=True)
class MarkdownComparison:
    left_text: str
    right_text: str
    unified_diff: str
    changed_sections: tuple[str, ...]
    changed_section_keys: tuple[str, ...]


def _section_key(name: str) -> str:
    normalized = _KEY_RE.sub(" ", name.casefold()).strip()
    return normalized or "untitled"


def split_markdown_sections(markdown: str) -> list[MarkdownSection]:
    """Split a document at level-two headings while preserving Markdown."""

    sections: list[MarkdownSection] = []
    current_name = "Document preamble"
    current_key = "__preamble__"
    current_lines: list[str] = []
    key_counts: dict[str, int] = {}

    def finish() -> None:
        if current_lines:
            sections.append(
                MarkdownSection(
                    key=current_key,
                    name=current_name,
                    text="\n".join(current_lines).strip() + "\n",
                )
            )

    for line in markdown.splitlines():
        match = _H2_RE.match(line)
        if not match:
            current_lines.append(line)
            continue
        finish()
        current_name = match.group(1).strip()
        base_key = _section_key(current_name)
        occurrence = key_counts.get(base_key, 0) + 1
        key_counts[base_key] = occurrence
        current_key = f"{base_key}::{occurrence}"
        current_lines = [line]
    finish()
    return sections


def compare_markdown(
    left: str,
    right: str,
    left_label: str = "original",
    right_label: str = "optimized",
    changed_sections_only: bool = True,
) -> MarkdownComparison:
    """Compare Markdown, optionally removing unchanged level-two sections."""

    left_sections = split_markdown_sections(left)
    right_sections = split_markdown_sections(right)
    left_by_key = {section.key: section for section in left_sections}
    right_by_key = {section.key: section for section in right_sections}
    ordered_keys = list(left_by_key)
    ordered_keys.extend(key for key in right_by_key if key not in left_by_key)

    changed_keys = [
        key
        for key in ordered_keys
        if left_by_key.get(key, MarkdownSection(key, "", "")).text.strip()
        != right_by_key.get(key, MarkdownSection(key, "", "")).text.strip()
    ]
    changed_names = tuple(
        (right_by_key.get(key) or left_by_key[key]).name for key in changed_keys
    )

    if changed_sections_only:
        left_view = "\n\n".join(
            left_by_key[key].text.rstrip() for key in changed_keys if key in left_by_key
        )
        right_view = "\n\n".join(
            right_by_key[key].text.rstrip() for key in changed_keys if key in right_by_key
        )
    else:
        left_view = left.rstrip()
        right_view = right.rstrip()

    diff_lines = list(
        difflib.unified_diff(
            left_view.splitlines(),
            right_view.splitlines(),
            fromfile=left_label,
            tofile=right_label,
            lineterm="",
            n=3,
        )
    )
    unified = "\n".join(diff_lines) if diff_lines else "No differences."
    return MarkdownComparison(
        left_text=left_view,
        right_text=right_view,
        unified_diff=unified,
        changed_sections=changed_names,
        changed_section_keys=tuple(changed_keys),
    )


def markdown_section_choices(left: str, right: str) -> tuple[tuple[str, str], ...]:
    """Return the ordered union of selectable Markdown sections."""

    left_sections = split_markdown_sections(left)
    right_sections = split_markdown_sections(right)
    sections_by_key = {section.key: section for section in left_sections}
    ordered_keys = [section.key for section in left_sections]
    for section in right_sections:
        if section.key not in sections_by_key:
            sections_by_key[section.key] = section
            ordered_keys.append(section.key)

    name_counts: dict[str, int] = {}
    choices = []
    for key in ordered_keys:
        name = sections_by_key[key].name
        occurrence = name_counts.get(name, 0) + 1
        name_counts[name] = occurrence
        label = name if occurrence == 1 else f"{name} ({occurrence})"
        choices.append((key, label))
    return tuple(choices)


def compare_markdown_section(
    left: str,
    right: str,
    section_key: str,
    left_label: str = "baseline",
    right_label: str = "comparison",
) -> MarkdownComparison:
    """Compare one selected Markdown section, including added or removed sections."""

    left_by_key = {section.key: section for section in split_markdown_sections(left)}
    right_by_key = {section.key: section for section in split_markdown_sections(right)}
    left_section = left_by_key.get(section_key)
    right_section = right_by_key.get(section_key)
    left_view = left_section.text.rstrip() if left_section else ""
    right_view = right_section.text.rstrip() if right_section else ""
    name = (right_section or left_section).name if right_section or left_section else "Section"

    diff_lines = list(
        difflib.unified_diff(
            left_view.splitlines(),
            right_view.splitlines(),
            fromfile=left_label,
            tofile=right_label,
            lineterm="",
            n=3,
        )
    )
    unified = "\n".join(diff_lines) if diff_lines else "No differences."
    changed = left_view.strip() != right_view.strip()
    return MarkdownComparison(
        left_text=left_view,
        right_text=right_view,
        unified_diff=unified,
        changed_sections=(name,) if changed else (),
        changed_section_keys=(section_key,) if changed else (),
    )


def wrap_diff_markdown(unified_diff: str, baseline_label: str, comparison_label: str) -> str:
    """Wrap a diff for direct pasting into Markdown without breaking inner fences."""

    longest_fence = max((len(match) for match in re.findall(r"`+", unified_diff)), default=0)
    fence = "`" * max(4, longest_fence + 1)
    baseline = " ".join(baseline_label.split())
    comparison = " ".join(comparison_label.split())
    return (
        f"### {baseline} → {comparison}\n\n"
        f"{fence}diff\n"
        f"{unified_diff.rstrip()}\n"
        f"{fence}\n"
    )


def diff_to_html(unified_diff: str, font_size: int = 12) -> str:
    """Render a unified diff as compact, colored HTML."""

    rendered = []
    for line in unified_diff.splitlines() or [""]:
        escaped = html.escape(line)
        if line.startswith(("--- ", "+++ ")):
            color = "#aeb4c0"
            background = "#242832"
        elif line.startswith("@@"):
            color = "#8db7ff"
            background = "#1d2a3d"
        elif line.startswith("+"):
            color = "#b7f0c2"
            background = "#173321"
        elif line.startswith("-"):
            color = "#ffb4b8"
            background = "#3b1c22"
        else:
            color = "#d7d9df"
            background = "transparent"
        rendered.append(
            f'<span style="display:block;color:{color};background:{background};">'
            f"{escaped or ' '}</span>"
        )
    return (
        "<html><body style='background:#191c23;margin:0;'>"
        "<pre style='font-family:Menlo,Monaco,Consolas,monospace;"
        f"font-size:{font_size}px;white-space:pre-wrap;margin:10px;'>"
        + "".join(rendered)
        + "</pre></body></html>"
    )
