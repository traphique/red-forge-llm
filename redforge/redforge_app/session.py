"""Minimal purple-team skill chaining."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .library import Skill

MAX_SAVED_SESSIONS = 5


class SessionError(ValueError):
    """Raised when a skill chain cannot produce a session prompt."""


class SessionHistoryError(RuntimeError):
    """Raised when the local saved-session file cannot be read or written."""


@dataclass(frozen=True)
class SavedSession:
    skills: tuple[str, ...]
    saved_at: str
    pinned: bool = False


def _valid_skill_paths(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not 2 <= len(value) <= 3:
        return None
    if not all(isinstance(path, str) and path for path in value):
        return None
    paths = tuple(value)
    if len(paths) != len(set(paths)):
        return None
    return paths


def load_session_history(path: Path) -> list[SavedSession]:
    """Read up to five valid session records from a local JSON list."""

    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SessionHistoryError(f"Could not read saved sessions: {exc}") from exc
    if not isinstance(payload, list):
        raise SessionHistoryError("Saved sessions must be a JSON list.")

    records: list[SavedSession] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        skills = _valid_skill_paths(item.get("skills"))
        saved_at = item.get("saved_at")
        if skills is None or not isinstance(saved_at, str):
            continue
        records.append(
            SavedSession(
                skills=skills,
                saved_at=saved_at,
                pinned=item.get("pinned") is True,
            )
        )
    return records[:MAX_SAVED_SESSIONS]


def _write_session_history(path: Path, records: Sequence[SavedSession]) -> None:
    payload = [
        {
            "skills": list(record.skills),
            "saved_at": record.saved_at,
            "pinned": record.pinned,
        }
        for record in records
    ]
    temporary = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        raise SessionHistoryError(f"Could not save session history: {exc}") from exc


def _trim_history(records: list[SavedSession]) -> list[SavedSession]:
    while len(records) > MAX_SAVED_SESSIONS:
        removable = next(
            (index for index in range(len(records) - 1, -1, -1) if not records[index].pinned),
            None,
        )
        if removable is None:
            # The UI permits one pin, but this also keeps malformed hand-edited
            # files bounded if several records were marked pinned.
            removable = len(records) - 1
        records.pop(removable)
    return records


def save_session_history(path: Path, skill_paths: Sequence[str]) -> list[SavedSession]:
    """Move an ordered chain to the front of an atomic five-record history."""

    paths = _valid_skill_paths(list(skill_paths))
    if paths is None:
        raise SessionHistoryError("A saved chain must contain two or three different skills.")

    existing = load_session_history(path)
    previous = next((record for record in existing if record.skills == paths), None)
    saved_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    records = [
        SavedSession(
            skills=paths,
            saved_at=saved_at,
            pinned=previous.pinned if previous else False,
        )
    ]
    records.extend(record for record in existing if record.skills != paths)
    records = _trim_history(records)
    _write_session_history(path, records)
    return records


def set_session_pinned(
    path: Path,
    skill_paths: Sequence[str],
    pinned: bool,
) -> list[SavedSession]:
    """Pin or unpin a saved chain, allowing at most one pinned record."""

    paths = tuple(skill_paths)
    records = load_session_history(path)
    if not any(record.skills == paths for record in records):
        raise SessionHistoryError("The chain must be saved before it can be pinned.")
    updated = [
        replace(
            record,
            pinned=(record.skills == paths and pinned),
        )
        for record in records
    ]
    _write_session_history(path, updated)
    return updated


def build_session_prompt(skills: Sequence[Skill]) -> str:
    """Combine two or three ordered skills into one system prompt."""

    if not 2 <= len(skills) <= 3:
        raise SessionError("Choose two or three skills.")
    paths = [skill.relative_path for skill in skills]
    if len(paths) != len(set(paths)):
        raise SessionError("Each position in the chain must use a different skill.")

    chain = "\n".join(f"{index}. {skill.title}" for index, skill in enumerate(skills, 1))
    modules = []
    for index, skill in enumerate(skills, 1):
        modules.append(
            "\n".join(
                [
                    f"## Skill module {index}: {skill.title}",
                    f"Source: `{skill.relative_path}`",
                    "",
                    skill.content.strip(),
                ]
            )
        )

    return "\n\n".join(
        [
            "# RedForge Purple-Team Session",
            (
                "You are supporting an authorized purple-team exercise. Work only within the "
                "operator's stated scope and authorization. Apply the following RedForge skill "
                "modules in order as one coordinated workflow."
            ),
            "## Chain order\n\n" + chain,
            (
                "## Session rules\n\n"
                "- Use each module at the stage where it appears in the chain.\n"
                "- Preserve defensive, detection, validation, and OPSEC guidance from every module.\n"
                "- Call out assumptions, scope limits, handoffs, and observable evidence.\n"
                "- If module instructions conflict, prefer authorization, safety, and the narrower scope.\n"
                "- Produce one coherent response instead of separate unrelated answers."
            ),
            *modules,
        ]
    ) + "\n"


def build_session_markdown(skills: Sequence[Skill]) -> str:
    """Create a standalone Markdown export for one current chain."""

    prompt = build_session_prompt(skills)
    names = " → ".join(skill.short_name for skill in skills)
    exported_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return (
        "# RedForge Chain Export\n\n"
        f"**Skills:** {names}\n\n"
        f"**Exported:** {exported_at}\n\n"
        "---\n\n"
        f"{prompt}"
    )


def _natural_list(items: Sequence[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _skill_purpose(skill: Skill) -> str:
    topics = []
    for tag in skill.tags:
        topic = tag.lstrip("#").replace("-", " ").replace("_", " ").strip()
        if topic and topic.casefold() not in {item.casefold() for item in topics}:
            topics.append(topic)
        if len(topics) == 3:
            break
    if topics:
        return f"Apply {skill.short_name} guidance focused on {_natural_list(topics)}."
    return (
        f"Apply {skill.short_name} guidance during this stage of the authorized "
        "purple-team workflow."
    )


def build_operator_brief(skills: Sequence[Skill]) -> str:
    """Create a compact, ready-to-paste Markdown handoff for one chain."""

    prompt = build_session_prompt(skills)
    names = " → ".join(skill.short_name for skill in skills)
    purposes = "\n".join(
        f"{index}. **{skill.short_name}** — {_skill_purpose(skill)}"
        for index, skill in enumerate(skills, 1)
    )
    return (
        "## RedForge Operator Brief\n\n"
        f"**Chain:** {names}\n\n"
        f"{purposes}\n\n"
        f"**Combined prompt:** {len(prompt.split()):,} words · "
        f"{len(prompt):,} characters\n"
    )


def format_relative_time(when: datetime, now: datetime | None = None) -> str:
    """Format a short stable relative time for the status bar."""

    current = now or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    elapsed = max(0, int((current - when).total_seconds()))
    if elapsed < 60:
        return "just now"
    minutes = elapsed // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"
