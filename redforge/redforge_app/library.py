"""Skill discovery and metadata parsing with no GUI dependencies."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_TAGS_RE = re.compile(r"^\s*\*\*Tags\*\*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_VERSION_SUFFIX_RE = re.compile(r"\s+v\d+(?:\.\d+)*\s*$", re.IGNORECASE)
_SHORT_NAMES = {
    "ai-redteam": "AI Red Team",
    "cve-exploits": "CVE Exploits",
    "edr-evasion": "EDR Evasion",
    "iot": "IoT",
    "rce": "RCE",
    "sqli": "SQLi",
}


class LibraryError(RuntimeError):
    """Raised when a directory is not a readable RedForge library."""


@dataclass(frozen=True)
class Skill:
    name: str
    title: str
    category: str
    relative_path: str
    source_path: Path
    content: str
    tags: tuple[str, ...] = ()

    @property
    def word_count(self) -> int:
        return len(self.content.split())

    @property
    def load_command(self) -> str:
        return f"cat {self.relative_path} | claude --system-file -"

    @property
    def short_name(self) -> str:
        return _SHORT_NAMES.get(self.name, self.name.replace("-", " ").title())


def _candidate_roots(explicit: Optional[Path] = None) -> Iterable[Path]:
    if explicit is not None:
        yield explicit

    configured = os.environ.get("REDFORGE_LIBRARY")
    if configured:
        yield Path(configured).expanduser()

    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        yield Path(bundle_root)

    module_root = Path(__file__).resolve().parent.parent
    yield module_root
    yield Path.cwd()
    yield Path.cwd() / "redforge"


def _normalize_library_root(candidate: Path) -> Optional[Path]:
    candidate = candidate.expanduser().resolve()
    if candidate.name == "skills" and candidate.is_dir():
        return candidate.parent
    if (candidate / "skills").is_dir():
        return candidate
    return None


def find_library_root(explicit: Optional[Path] = None) -> Path:
    """Find a directory containing ``skills/``.

    Packaged application resources, source checkouts, an environment override,
    and an explicitly selected directory all use the same lookup path.
    """

    checked: list[str] = []
    for candidate in _candidate_roots(explicit):
        checked.append(str(candidate))
        root = _normalize_library_root(candidate)
        if root is not None:
            return root
    raise LibraryError("Could not find a RedForge skills/ directory. Checked: " + ", ".join(checked))


def _parse_title(content: str, fallback: str) -> str:
    match = _TITLE_RE.search(content)
    if not match:
        return fallback.replace("-", " ").title()
    return _VERSION_SUFFIX_RE.sub("", match.group(1)).strip()


def _parse_tags(content: str) -> tuple[str, ...]:
    match = _TAGS_RE.search(content)
    if not match:
        return ()
    value = match.group(1)
    hashtags = tuple(re.findall(r"#[^\s,#]+", value))
    if hashtags:
        return hashtags
    return tuple(tag.strip() for tag in value.split(",") if tag.strip())


class SkillLibrary:
    """A snapshot of one RedForge ``skills/`` tree."""

    def __init__(self, root: Path, skills: Sequence[Skill], warnings: Sequence[str] = ()):
        self.root = root
        self.skills = tuple(skills)
        self.warnings = tuple(warnings)
        self._by_path = {skill.relative_path: skill for skill in self.skills}

    @classmethod
    def load(cls, root: Optional[Path] = None) -> "SkillLibrary":
        library_root = find_library_root(root)
        skills_dir = library_root / "skills"
        skills: list[Skill] = []
        warnings: list[str] = []

        for skill_path in sorted(skills_dir.rglob("SKILL.md")):
            try:
                content = skill_path.read_text(encoding="utf-8")
                relative = skill_path.relative_to(library_root)
            except (OSError, UnicodeError, ValueError) as exc:
                warnings.append(f"{skill_path}: {exc}")
                continue

            within_skills = relative.relative_to("skills")
            parts = within_skills.parts
            category = parts[0] if len(parts) > 2 else "general"
            name = skill_path.parent.name
            skills.append(
                Skill(
                    name=name,
                    title=_parse_title(content, name),
                    category=category,
                    relative_path=relative.as_posix(),
                    source_path=skill_path,
                    content=content,
                    tags=_parse_tags(content),
                )
            )

        if not skills:
            raise LibraryError(f"No SKILL.md files found under {skills_dir}")
        return cls(library_root, skills, warnings)

    @property
    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({skill.category for skill in self.skills}))

    def get(self, relative_path: str) -> Skill:
        try:
            return self._by_path[relative_path]
        except KeyError as exc:
            raise LibraryError(f"Skill is no longer in the library: {relative_path}") from exc
