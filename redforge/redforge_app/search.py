"""Fast, local skill search backed by SQLite FTS5/BM25."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Optional, Sequence

from .library import Skill

_QUERY_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_QUERY_STOP_WORDS = {
    "a",
    "an",
    "and",
    "around",
    "do",
    "for",
    "from",
    "getting",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "the",
    "to",
    "what",
    "with",
}


@dataclass(frozen=True)
class SearchResult:
    skill: Skill
    score: float


class SearchIndex:
    """An in-memory index that never sends skill content off-device."""

    def __init__(self, skills: Sequence[Skill]):
        self.skills = tuple(skills)
        self._by_path = {skill.relative_path: skill for skill in self.skills}
        self._db: Optional[sqlite3.Connection] = None
        self.backend = "substring fallback"
        self._build()

    def _build(self) -> None:
        db = sqlite3.connect(":memory:")
        try:
            db.execute(
                """
                CREATE VIRTUAL TABLE skills_fts USING fts5(
                    title, name, category, tags, content, path UNINDEXED,
                    tokenize='porter unicode61'
                )
                """
            )
        except sqlite3.OperationalError:
            db.close()
            return

        db.executemany(
            """
            INSERT INTO skills_fts(title, name, category, tags, content, path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    skill.title,
                    skill.name,
                    skill.category,
                    " ".join(skill.tags),
                    skill.content,
                    skill.relative_path,
                )
                for skill in self.skills
            ],
        )
        self._db = db
        self.backend = f"SQLite FTS5 {sqlite3.sqlite_version} / BM25"

    @staticmethod
    def _fts_query(query: str) -> str:
        tokens = [
            token
            for token in _QUERY_TOKEN_RE.findall(query.casefold())
            if token not in _QUERY_STOP_WORDS
        ]
        # Prefix matching keeps partial skill names useful while quoting every
        # token prevents FTS operators in user input from changing the query.
        return " OR ".join(f'"{token}"*' for token in tokens[:24])

    def search(
        self,
        query: str = "",
        category: Optional[str] = None,
        limit: int = 50,
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            skills = [
                skill
                for skill in self.skills
                if not category or category == "All" or skill.category == category
            ]
            return [SearchResult(skill=skill, score=0.0) for skill in skills[:limit]]

        if self._db is None:
            return self._substring_search(query, category, limit)

        fts_query = self._fts_query(query)
        if not fts_query:
            return []

        sql = """
            SELECT path, bm25(skills_fts, 8.0, 7.0, 4.0, 5.0, 1.0, 0.0) AS rank
            FROM skills_fts
            WHERE skills_fts MATCH ?
        """
        parameters: list[object] = [fts_query]
        if category and category != "All":
            sql += " AND category = ?"
            parameters.append(category)
        sql += " ORDER BY rank LIMIT ?"
        parameters.append(limit)

        try:
            rows = self._db.execute(sql, parameters).fetchall()
        except sqlite3.OperationalError:
            return self._substring_search(query, category, limit)
        if not rows:
            return []
        relevance = [-float(rank) for _path, rank in rows]
        best = max(relevance)
        worst = min(relevance)
        spread = best - worst
        return [
            SearchResult(
                skill=self._by_path[path],
                score=(value - worst) / spread if spread else 1.0,
            )
            for (path, _rank), value in zip(rows, relevance)
        ]

    def _substring_search(
        self,
        query: str,
        category: Optional[str],
        limit: int,
    ) -> list[SearchResult]:
        tokens = _QUERY_TOKEN_RE.findall(query.casefold())
        ranked: list[SearchResult] = []
        for skill in self.skills:
            if category and category != "All" and skill.category != category:
                continue
            title = skill.title.casefold()
            metadata = f"{skill.name} {skill.category} {' '.join(skill.tags)}".casefold()
            content = skill.content.casefold()
            score = sum(
                (8 if token in title else 0)
                + (4 if token in metadata else 0)
                + (1 if token in content else 0)
                for token in tokens
            )
            if score:
                ranked.append(SearchResult(skill=skill, score=float(score)))
        ranked.sort(key=lambda item: (-item.score, item.skill.title.casefold()))
        return ranked[:limit]
