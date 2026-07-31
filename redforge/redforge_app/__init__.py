"""Shared application core for RedForge."""

from .library import LibraryError, Skill, SkillLibrary, find_library_root
from .search import SearchIndex, SearchResult
from .session import (
    SavedSession,
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

__all__ = [
    "LibraryError",
    "SearchIndex",
    "SearchResult",
    "SavedSession",
    "SessionError",
    "SessionHistoryError",
    "Skill",
    "SkillLibrary",
    "build_operator_brief",
    "build_session_markdown",
    "build_session_prompt",
    "find_library_root",
    "format_relative_time",
    "load_session_history",
    "save_session_history",
    "set_session_pinned",
]

__version__ = "0.1.0"
