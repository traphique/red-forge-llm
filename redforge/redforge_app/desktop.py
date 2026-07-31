"""Native RedForge desktop application using Qt Widgets."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from .diffing import (
    compare_markdown,
    compare_markdown_section,
    diff_to_html,
    markdown_section_choices,
    wrap_diff_markdown,
)
from .library import LibraryError, Skill, SkillLibrary
from .search import SearchIndex
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RedForge offline desktop skill browser")
    parser.add_argument(
        "--library",
        type=Path,
        help="RedForge root (or its skills directory); overrides the saved library",
    )
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--launch-test", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.smoke_test:
        try:
            from PySide6.QtCore import qVersion

            library = SkillLibrary.load(args.library)
            index = SearchIndex(library.skills)
            if not index.search("purple team"):
                raise RuntimeError("bundled search returned no results")
        except Exception as exc:
            print(f"RedForge smoke test failed: {exc}", file=sys.stderr)
            return 1
        print(
            f"RedForge smoke test passed: Qt {qVersion()}, "
            f"{len(library.skills)} skills, {index.backend}"
        )
        return 0

    try:
        from PySide6.QtCore import QSettings, QStandardPaths, QTimer, Qt
        from PySide6.QtGui import QAction, QFont, QKeySequence, QShortcut
        from PySide6.QtWidgets import (
            QApplication,
            QButtonGroup,
            QCheckBox,
            QComboBox,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QMessageBox,
            QPlainTextEdit,
            QPushButton,
            QSplitter,
            QTabWidget,
            QTextBrowser,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print(
            'PySide6 is required for the desktop app. Install it with:\n'
            '  python -m pip install -e ".[desktop]"',
            file=sys.stderr,
        )
        return 2

    class MainWindow(QMainWindow):
        def __init__(
            self,
            requested_root: Optional[Path] = None,
            use_saved_library: bool = True,
        ):
            super().__init__()
            self.settings = QSettings("RedForge", "RedForge Desktop")
            self.library: Optional[SkillLibrary] = None
            self.index: Optional[SearchIndex] = None
            self.current_skill: Optional[Skill] = None
            self.session_prompt = ""
            self.session_history: list[SavedSession] = []
            self.last_loaded_paths: tuple[str, ...] = ()
            self.last_loaded_at: Optional[datetime] = None
            self.diff_external: dict[str, Optional[tuple[str, str]]] = {
                "left": None,
                "right": None,
            }
            self.current_diff_text = ""
            self.current_diff_labels = ("", "")
            self.current_diff_documents: Optional[tuple[str, str, str, str]] = None
            self.diff_font_size = 12
            app_data = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
            self.session_history_path = Path(app_data) / "sessions.json"

            self.setWindowTitle("RedForge")
            self.resize(1180, 760)
            self.setMinimumSize(880, 580)
            self._build_ui()
            self._build_menu()

            saved = self.settings.value("library_root", "", type=str) if use_saved_library else ""
            initial = requested_root or (Path(saved) if saved else None)
            self._load_library(initial, allow_picker=True)
            self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
            self.search_shortcut.activated.connect(self._focus_search)
            self.last_loaded_timer = QTimer(self)
            self.last_loaded_timer.timeout.connect(self._refresh_last_loaded_label)
            self.last_loaded_timer.start(30_000)

        def _build_ui(self) -> None:
            root = QWidget()
            root_layout = QVBoxLayout(root)
            root_layout.setContentsMargins(18, 16, 18, 16)

            brand_row = QHBoxLayout()
            brand = QLabel("REDFORGE")
            brand.setObjectName("brand")
            subtitle = QLabel("offline skill library")
            subtitle.setObjectName("muted")
            brand_row.addWidget(brand)
            brand_row.addWidget(subtitle)
            brand_row.addStretch()
            root_layout.addLayout(brand_row)

            tabs = QTabWidget()
            root_layout.addWidget(tabs, 1)

            browser = QWidget()
            browser_layout = QVBoxLayout(browser)
            browser_layout.setContentsMargins(0, 0, 0, 0)
            splitter = QSplitter(Qt.Orientation.Horizontal)
            splitter.setChildrenCollapsible(False)

            left = QWidget()
            left_layout = QVBoxLayout(left)
            left_layout.setContentsMargins(0, 8, 8, 0)
            self.search_box = QLineEdit()
            self.search_box.setPlaceholderText("Search titles, tags, and skill content…")
            self.search_box.setClearButtonEnabled(True)
            self.search_box.textChanged.connect(self._refresh_results)
            left_layout.addWidget(self.search_box)

            self.category_box = QComboBox()
            self.category_box.currentTextChanged.connect(self._refresh_results)
            left_layout.addWidget(self.category_box)

            self.result_count = QLabel("")
            self.result_count.setObjectName("muted")
            left_layout.addWidget(self.result_count)

            self.skill_list = QListWidget()
            self.skill_list.currentItemChanged.connect(self._select_item)
            left_layout.addWidget(self.skill_list, 1)

            right = QWidget()
            right_layout = QVBoxLayout(right)
            right_layout.setContentsMargins(12, 8, 0, 0)
            self.skill_title = QLabel("Select a skill")
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            self.skill_title.setFont(title_font)
            self.skill_title.setWordWrap(True)
            right_layout.addWidget(self.skill_title)

            self.skill_meta = QLabel("")
            self.skill_meta.setObjectName("muted")
            right_layout.addWidget(self.skill_meta)

            self.preview = QTextBrowser()
            self.preview.setOpenExternalLinks(True)
            self.preview.setPlaceholderText("Choose a skill to preview its SKILL.md.")
            right_layout.addWidget(self.preview, 1)

            actions = QHBoxLayout()
            self.copy_button = QPushButton("Copy skill")
            self.copy_button.clicked.connect(self._copy_skill)
            self.command_button = QPushButton("Copy load command")
            self.command_button.clicked.connect(self._copy_command)
            self.export_button = QPushButton("Export…")
            self.export_button.clicked.connect(self._export_skill)
            for button in (self.copy_button, self.command_button, self.export_button):
                button.setEnabled(False)
                actions.addWidget(button)
            actions.addStretch()
            right_layout.addLayout(actions)

            splitter.addWidget(left)
            splitter.addWidget(right)
            splitter.setSizes([340, 820])
            browser_layout.addWidget(splitter)
            tabs.addTab(browser, "Skill browser")

            session = QWidget()
            session_layout = QVBoxLayout(session)
            session_layout.setContentsMargins(8, 12, 8, 4)
            session_title = QLabel("Purple-team session")
            session_title.setFont(title_font)
            session_layout.addWidget(session_title)
            session_help = QLabel(
                "Choose two required skills and an optional third. The order below is the chain order."
            )
            session_help.setObjectName("muted")
            session_layout.addWidget(session_help)

            session_category_row = QHBoxLayout()
            session_category_row.addWidget(QLabel("Skill category"))
            self.session_category_box = QComboBox()
            self.session_category_box.currentIndexChanged.connect(
                lambda _index: self._set_picker_category(
                    self.session_category_box.currentData()
                )
            )
            session_category_row.addWidget(self.session_category_box)
            session_category_row.addStretch()
            session_layout.addLayout(session_category_row)

            recent_row = QHBoxLayout()
            recent_row.addWidget(QLabel("Recent chains"))
            self.recent_session_box = QComboBox()
            self.recent_session_box.setToolTip(str(self.session_history_path))
            self.recent_session_box.currentIndexChanged.connect(self._update_load_button)
            recent_row.addWidget(self.recent_session_box, 1)
            self.load_session_button = QPushButton("Load")
            self.load_session_button.setEnabled(False)
            self.load_session_button.clicked.connect(self._load_recent_session)
            recent_row.addWidget(self.load_session_button)
            self.pin_session_button = QPushButton("Pin")
            self.pin_session_button.setEnabled(False)
            self.pin_session_button.clicked.connect(self._toggle_pinned_session)
            recent_row.addWidget(self.pin_session_button)
            session_layout.addLayout(recent_row)

            selectors = QHBoxLayout()
            self.session_boxes = []
            for position in range(3):
                column = QVBoxLayout()
                label = QLabel(f"{position + 1}. {'Required' if position < 2 else 'Optional'}")
                box = QComboBox()
                box.currentIndexChanged.connect(self._refresh_session_prompt)
                self.session_boxes.append(box)
                column.addWidget(label)
                column.addWidget(box)
                selectors.addLayout(column)
            session_layout.addLayout(selectors)

            self.session_notice = QLabel("")
            self.session_notice.setObjectName("muted")
            session_layout.addWidget(self.session_notice)
            self.session_preview = QPlainTextEdit()
            self.session_preview.setReadOnly(True)
            self.session_preview.setPlaceholderText(
                "The combined system prompt will appear after the library loads."
            )
            session_layout.addWidget(self.session_preview, 1)

            session_actions = QHBoxLayout()
            self.save_session_button = QPushButton("Save chain")
            self.save_session_button.setEnabled(False)
            self.save_session_button.clicked.connect(self._save_current_session)
            session_actions.addWidget(self.save_session_button)
            self.copy_session_button = QPushButton("Copy combined system prompt")
            self.copy_session_button.setEnabled(False)
            self.copy_session_button.clicked.connect(self._copy_session_prompt)
            session_actions.addWidget(self.copy_session_button)
            self.export_session_button = QPushButton("Export chain…")
            self.export_session_button.setEnabled(False)
            self.export_session_button.clicked.connect(self._export_session)
            session_actions.addWidget(self.export_session_button)
            self.copy_brief_button = QPushButton("Copy operator brief")
            self.copy_brief_button.setEnabled(False)
            self.copy_brief_button.clicked.connect(self._copy_operator_brief)
            session_actions.addWidget(self.copy_brief_button)
            self.export_brief_button = QPushButton("Export brief…")
            self.export_brief_button.setEnabled(False)
            self.export_brief_button.clicked.connect(self._export_operator_brief)
            session_actions.addWidget(self.export_brief_button)
            session_actions.addStretch()
            session_layout.addLayout(session_actions)
            tabs.addTab(session, "Purple-team session")

            diff_page = QWidget()
            diff_layout = QVBoxLayout(diff_page)
            diff_layout.setContentsMargins(8, 12, 8, 4)
            diff_title = QLabel("Skill diff")
            diff_title.setFont(title_font)
            diff_layout.addWidget(diff_title)
            diff_help = QLabel(
                "Compare library skills, reconstructed saved chains, or external Markdown files."
            )
            diff_help.setObjectName("muted")
            diff_layout.addWidget(diff_help)

            diff_category_row = QHBoxLayout()
            diff_category_row.addWidget(QLabel("Skill category"))
            self.diff_category_box = QComboBox()
            self.diff_category_box.currentIndexChanged.connect(
                lambda _index: self._set_picker_category(
                    self.diff_category_box.currentData()
                )
            )
            diff_category_row.addWidget(self.diff_category_box)
            diff_category_row.addStretch()
            diff_layout.addLayout(diff_category_row)

            source_row = QHBoxLayout()
            self.diff_source_boxes = {}
            for side, label_text in (
                ("left", "Original / left"),
                ("right", "Optimized / right"),
            ):
                column = QVBoxLayout()
                column.addWidget(QLabel(label_text))
                picker_row = QHBoxLayout()
                box = QComboBox()
                box.currentIndexChanged.connect(self._refresh_diff)
                self.diff_source_boxes[side] = box
                picker_row.addWidget(box, 1)
                open_button = QPushButton("Open .md…")
                open_button.clicked.connect(
                    lambda _checked=False, selected_side=side: self._open_diff_file(
                        selected_side
                    )
                )
                picker_row.addWidget(open_button)
                column.addLayout(picker_row)
                source_row.addLayout(column)
            diff_layout.addLayout(source_row)

            diff_options = QHBoxLayout()
            self.diff_changed_only = QCheckBox("Show changed H2 sections only")
            self.diff_changed_only.setChecked(True)
            self.diff_changed_only.toggled.connect(self._refresh_diff)
            diff_options.addWidget(self.diff_changed_only)
            diff_options.addWidget(QLabel("Baseline"))
            self.diff_baseline_box = QComboBox()
            self.diff_baseline_box.addItem("Left", "left")
            self.diff_baseline_box.addItem("Right", "right")
            self.diff_baseline_box.currentIndexChanged.connect(self._refresh_diff)
            diff_options.addWidget(self.diff_baseline_box)
            self.diff_summary = QLabel("")
            self.diff_summary.setObjectName("muted")
            diff_options.addWidget(self.diff_summary)
            diff_options.addStretch()
            self.diff_copy_wrapped = QCheckBox("Wrap for Markdown")
            diff_options.addWidget(self.diff_copy_wrapped)
            self.copy_diff_button = QPushButton("Copy unified diff")
            self.copy_diff_button.setEnabled(False)
            self.copy_diff_button.clicked.connect(self._copy_diff)
            diff_options.addWidget(self.copy_diff_button)
            diff_layout.addLayout(diff_options)

            diff_font_row = QHBoxLayout()
            diff_font_row.addWidget(QLabel("Diff text"))
            self.diff_font_buttons = QButtonGroup(self)
            for label, font_size in (
                ("Normal", 12),
                ("Larger", 15),
                ("Largest", 18),
            ):
                button = QPushButton(label)
                button.setCheckable(True)
                button.setChecked(font_size == self.diff_font_size)
                button.clicked.connect(
                    lambda _checked=False, selected_size=font_size: (
                        self._set_diff_font_size(selected_size)
                    )
                )
                self.diff_font_buttons.addButton(button, font_size)
                diff_font_row.addWidget(button)
            diff_font_row.addStretch()
            diff_layout.addLayout(diff_font_row)

            diff_views = QTabWidget()
            self.unified_diff_preview = QTextBrowser()
            self.unified_diff_preview.setPlaceholderText("Choose two sources to compare.")
            diff_views.addTab(self.unified_diff_preview, "Unified diff")

            rendered_split = QSplitter(Qt.Orientation.Horizontal)
            self.left_diff_preview = QTextBrowser()
            self.right_diff_preview = QTextBrowser()
            for preview in (self.left_diff_preview, self.right_diff_preview):
                preview.setOpenExternalLinks(True)
                rendered_split.addWidget(preview)
            rendered_split.setSizes([580, 580])
            diff_views.addTab(rendered_split, "Rendered side by side")

            section_page = QWidget()
            section_layout = QVBoxLayout(section_page)
            section_layout.setContentsMargins(0, 8, 0, 0)
            section_row = QHBoxLayout()
            section_row.addWidget(QLabel("Section"))
            self.diff_section_box = QComboBox()
            self.diff_section_box.currentIndexChanged.connect(
                self._refresh_section_diff
            )
            section_row.addWidget(self.diff_section_box, 1)
            self.diff_section_summary = QLabel("")
            self.diff_section_summary.setObjectName("muted")
            section_row.addWidget(self.diff_section_summary)
            section_layout.addLayout(section_row)
            self.section_diff_preview = QTextBrowser()
            self.section_diff_preview.setPlaceholderText(
                "Choose a section to compare."
            )
            section_layout.addWidget(self.section_diff_preview, 1)
            diff_views.addTab(section_page, "Single section")

            diff_layout.addWidget(diff_views, 1)
            tabs.addTab(diff_page, "Skill diff")

            self.setCentralWidget(root)
            self.statusBar().showMessage("Local only — no network requests")
            self.last_loaded_label = QLabel("Last loaded: —")
            self.last_loaded_label.setObjectName("muted")
            self.statusBar().addPermanentWidget(self.last_loaded_label)
            self.setStyleSheet(_STYLE)

        def _build_menu(self) -> None:
            file_menu = self.menuBar().addMenu("&File")
            open_action = QAction("Open skill library…", self)
            open_action.setShortcut(QKeySequence.StandardKey.Open)
            open_action.triggered.connect(self._choose_library)
            file_menu.addAction(open_action)

            reload_action = QAction("Reload library", self)
            reload_action.setShortcut(QKeySequence.StandardKey.Refresh)
            reload_action.triggered.connect(self._reload_library)
            file_menu.addAction(reload_action)
            file_menu.addSeparator()

            quit_action = QAction("Quit", self)
            quit_action.setShortcut(QKeySequence.StandardKey.Quit)
            quit_action.triggered.connect(self.close)
            file_menu.addAction(quit_action)

        def _focus_search(self) -> None:
            self.search_box.setFocus()
            self.search_box.selectAll()

        def _load_library(self, root: Optional[Path], allow_picker: bool = False) -> None:
            try:
                library = SkillLibrary.load(root)
            except LibraryError as exc:
                if allow_picker:
                    QMessageBox.warning(
                        self,
                        "Choose a RedForge library",
                        f"{exc}\n\nSelect the folder that contains skills/.",
                    )
                    self._choose_library()
                    return
                QMessageBox.critical(self, "Could not load library", str(exc))
                return

            self.library = library
            self.index = SearchIndex(library.skills)
            self.settings.setValue("library_root", str(library.root))
            self.category_box.blockSignals(True)
            self.category_box.clear()
            self.category_box.addItems(["All", *library.categories])
            self.category_box.blockSignals(False)
            self._refresh_results()
            self._populate_picker_categories()
            self._populate_session_boxes()
            self._load_session_history()
            self._restore_last_loaded_status()
            warning_note = f" · {len(library.warnings)} skipped" if library.warnings else ""
            self.statusBar().showMessage(
                f"{len(library.skills)} skills · {self.index.backend}{warning_note} · local only"
            )

        def _choose_library(self) -> None:
            start = str(self.library.root if self.library else Path.home())
            selected = QFileDialog.getExistingDirectory(
                self,
                "Choose RedForge folder",
                start,
                QFileDialog.Option.ShowDirsOnly,
            )
            if selected:
                self._load_library(Path(selected))

        def _reload_library(self) -> None:
            self._load_library(self.library.root if self.library else None)

        def _refresh_results(self) -> None:
            if self.index is None:
                return
            results = self.index.search(
                self.search_box.text(),
                self.category_box.currentText() or "All",
            )
            selected_path = self.current_skill.relative_path if self.current_skill else None
            self.skill_list.blockSignals(True)
            self.skill_list.clear()
            selected_row = -1
            for row, result in enumerate(results):
                skill = result.skill
                item = QListWidgetItem(f"{skill.title}\n{skill.category}  ·  {skill.name}")
                item.setData(Qt.ItemDataRole.UserRole, skill.relative_path)
                item.setToolTip(skill.relative_path)
                self.skill_list.addItem(item)
                if skill.relative_path == selected_path:
                    selected_row = row
            self.skill_list.blockSignals(False)
            self.result_count.setText(f"{len(results)} result{'s' if len(results) != 1 else ''}")
            if results:
                self.skill_list.setCurrentRow(selected_row if selected_row >= 0 else 0)
                self._select_item(self.skill_list.currentItem())
            else:
                self._show_skill(None)

        def _select_item(self, current: Optional[QListWidgetItem], _previous=None) -> None:
            if current is None or self.library is None:
                self._show_skill(None)
                return
            self._show_skill(self.library.get(current.data(Qt.ItemDataRole.UserRole)))

        def _show_skill(self, skill: Optional[Skill]) -> None:
            self.current_skill = skill
            enabled = skill is not None
            for button in (self.copy_button, self.command_button, self.export_button):
                button.setEnabled(enabled)
            if skill is None:
                self.skill_title.setText("No matching skill")
                self.skill_meta.setText("")
                self.preview.clear()
                return
            self.skill_title.setText(skill.title)
            tags = f" · {', '.join(skill.tags)}" if skill.tags else ""
            self.skill_meta.setText(
                f"{skill.category} · {skill.relative_path} · {skill.word_count:,} words{tags}"
            )
            self.preview.setMarkdown(skill.content)

        def _populate_session_boxes(self) -> None:
            if self.library is None:
                return
            previous = [box.currentData() for box in self.session_boxes]
            visible = self._picker_skills()
            for position, box in enumerate(self.session_boxes):
                box.blockSignals(True)
                box.clear()
                if position == 2:
                    box.addItem("No third skill", None)
                wanted = previous[position] if position < len(previous) else None
                ordered = list(visible)
                if wanted:
                    try:
                        selected_skill = self.library.get(wanted)
                    except LibraryError:
                        wanted = None
                    else:
                        if selected_skill not in ordered:
                            ordered.insert(0, selected_skill)
                for skill in ordered:
                    box.addItem(skill.title, skill.relative_path)
                if wanted:
                    selected = box.findData(wanted)
                    if selected >= 0:
                        box.setCurrentIndex(selected)
                elif position < 2 and box.count() > position:
                    box.setCurrentIndex(position)
                box.blockSignals(False)
            self._refresh_session_prompt()

        def _populate_picker_categories(self) -> None:
            if self.library is None:
                return
            saved = self.settings.value("skill_picker_category", "All", type=str)
            available = {"All", *self.library.categories}
            selected = saved if saved in available else "All"
            for box in (self.session_category_box, self.diff_category_box):
                box.blockSignals(True)
                box.clear()
                box.addItem("All", "All")
                for category in self.library.categories:
                    box.addItem(category.title(), category)
                box.setCurrentIndex(box.findData(selected))
                box.blockSignals(False)
            self.settings.setValue("skill_picker_category", selected)

        def _set_picker_category(self, category) -> None:
            if self.library is None or not isinstance(category, str):
                return
            available = {"All", *self.library.categories}
            selected = category if category in available else "All"
            self.settings.setValue("skill_picker_category", selected)
            for box in (self.session_category_box, self.diff_category_box):
                index = box.findData(selected)
                if index >= 0 and box.currentIndex() != index:
                    box.blockSignals(True)
                    box.setCurrentIndex(index)
                    box.blockSignals(False)
            self._populate_session_boxes()
            self._populate_diff_sources()

        def _picker_skills(self) -> list[Skill]:
            if self.library is None:
                return []
            category = self.session_category_box.currentData()
            return sorted(
                (
                    skill
                    for skill in self.library.skills
                    if category == "All" or skill.category == category
                ),
                key=lambda skill: skill.title.casefold(),
            )

        def _refresh_session_prompt(self, _index=None) -> None:
            if self.library is None or not hasattr(self, "session_boxes"):
                return
            paths = [box.currentData() for box in self.session_boxes]
            selected = [self.library.get(path) for path in paths if path]
            try:
                prompt = build_session_prompt(selected)
            except SessionError as exc:
                self.session_prompt = ""
                self.session_preview.setPlainText("")
                self.session_notice.setText(str(exc))
                self.copy_session_button.setEnabled(False)
                self.save_session_button.setEnabled(False)
                self.export_session_button.setEnabled(False)
                self.copy_brief_button.setEnabled(False)
                self.export_brief_button.setEnabled(False)
                return
            self.session_prompt = prompt
            self.session_preview.setPlainText(prompt)
            self.session_notice.setText(
                f"{len(selected)} skills · {len(prompt.split()):,} words · {len(prompt):,} characters"
            )
            self.copy_session_button.setEnabled(True)
            self.save_session_button.setEnabled(True)
            self.export_session_button.setEnabled(True)
            self.copy_brief_button.setEnabled(True)
            self.export_brief_button.setEnabled(True)

        def _current_session_paths(self) -> tuple[str, ...]:
            return tuple(path for path in (box.currentData() for box in self.session_boxes) if path)

        def _current_session_skills(self) -> list[Skill]:
            if self.library is None:
                return []
            return [self.library.get(path) for path in self._current_session_paths()]

        def _history_label(self, record: SavedSession) -> tuple[str, bool]:
            if self.library is None:
                return "Unavailable", False
            titles = []
            complete = True
            for path in record.skills:
                try:
                    titles.append(self.library.get(path).title)
                except LibraryError:
                    titles.append(f"{Path(path).parent.name} (missing)")
                    complete = False
            return " → ".join(titles), complete

        def _load_session_history(self) -> None:
            try:
                self.session_history = load_session_history(self.session_history_path)
            except SessionHistoryError as exc:
                self.session_history = []
                self.statusBar().showMessage(str(exc), 6000)
            self._refresh_recent_sessions()

        def _refresh_recent_sessions(self) -> None:
            self.recent_session_box.blockSignals(True)
            self.recent_session_box.clear()
            any_loadable = False
            if not self.session_history:
                self.recent_session_box.addItem("No saved chains", None)
            else:
                for index, record in enumerate(self.session_history):
                    label, complete = self._history_label(record)
                    if record.pinned:
                        label = f"📌 {label}"
                    self.recent_session_box.addItem(label, index if complete else None)
                    any_loadable = any_loadable or complete
            self.recent_session_box.blockSignals(False)
            current_loadable = self.recent_session_box.currentData() is not None
            self.load_session_button.setEnabled(any_loadable and current_loadable)
            self._update_recent_buttons()
            self._populate_diff_sources()

        def _selected_saved_session(self) -> Optional[SavedSession]:
            record_index = self.recent_session_box.currentData()
            if record_index is None or record_index >= len(self.session_history):
                return None
            return self.session_history[record_index]

        def _update_load_button(self, _index=None) -> None:
            self._update_recent_buttons()

        def _update_recent_buttons(self) -> None:
            record = self._selected_saved_session()
            self.load_session_button.setEnabled(record is not None)
            self.pin_session_button.setEnabled(record is not None)
            self.pin_session_button.setText("Unpin" if record and record.pinned else "Pin")

        def _save_current_session(self) -> None:
            try:
                self.session_history = save_session_history(
                    self.session_history_path,
                    self._current_session_paths(),
                )
            except SessionHistoryError as exc:
                QMessageBox.critical(self, "Could not save chain", str(exc))
                return
            self._refresh_recent_sessions()
            self.recent_session_box.setCurrentIndex(0)
            self.statusBar().showMessage(
                f"Chain saved · {self.session_history_path}",
                4000,
            )

        def _toggle_pinned_session(self) -> None:
            record = self._selected_saved_session()
            if record is None:
                return
            try:
                self.session_history = set_session_pinned(
                    self.session_history_path,
                    record.skills,
                    not record.pinned,
                )
            except SessionHistoryError as exc:
                QMessageBox.critical(self, "Could not update pin", str(exc))
                return
            target_paths = record.skills
            self._refresh_recent_sessions()
            for index, candidate in enumerate(self.session_history):
                if candidate.skills == target_paths:
                    self.recent_session_box.setCurrentIndex(index)
                    break
            state = "Pinned" if not record.pinned else "Unpinned"
            self.statusBar().showMessage(f"{state} chain", 3000)

        def _load_recent_session(self) -> None:
            record = self._selected_saved_session()
            if record is None:
                return
            if self.library is None:
                return
            try:
                for path in record.skills:
                    self.library.get(path)
            except LibraryError as exc:
                QMessageBox.warning(self, "Could not load chain", str(exc))
                return

            for box in self.session_boxes:
                box.blockSignals(True)
            try:
                for position, box in enumerate(self.session_boxes):
                    path = record.skills[position] if position < len(record.skills) else None
                    selected = box.findData(path)
                    if selected < 0:
                        raise LibraryError(f"Skill is no longer available: {path}")
                    box.setCurrentIndex(selected)
            except LibraryError as exc:
                QMessageBox.warning(self, "Could not load chain", str(exc))
                return
            finally:
                for box in self.session_boxes:
                    box.blockSignals(False)
            self._refresh_session_prompt()
            self._remember_last_loaded(record.skills)
            self.statusBar().showMessage("Saved chain loaded", 3000)

        def _populate_diff_sources(self) -> None:
            if self.library is None or not hasattr(self, "diff_source_boxes"):
                return
            previous = {
                side: box.currentData() for side, box in self.diff_source_boxes.items()
            }
            visible_skills = self._picker_skills()
            for side, box in self.diff_source_boxes.items():
                box.blockSignals(True)
                box.clear()
                ordered_skills = list(visible_skills)
                wanted = previous[side]
                if isinstance(wanted, str) and wanted.startswith("skill::"):
                    try:
                        selected_skill = self.library.get(
                            wanted.removeprefix("skill::")
                        )
                    except LibraryError:
                        wanted = None
                    else:
                        if selected_skill not in ordered_skills:
                            ordered_skills.insert(0, selected_skill)
                for skill in ordered_skills:
                    box.addItem(
                        f"Skill · {skill.title}",
                        f"skill::{skill.relative_path}",
                    )
                if self.session_history:
                    box.insertSeparator(box.count())
                    for record in self.session_history:
                        label, complete = self._history_label(record)
                        if not complete:
                            continue
                        prefix = "📌 " if record.pinned else ""
                        encoded = json.dumps(list(record.skills), separators=(",", ":"))
                        box.addItem(
                            f"{prefix}Chain · {label}",
                            f"chain::{encoded}",
                        )
                external = self.diff_external[side]
                if external is not None:
                    box.insertSeparator(box.count())
                    box.addItem(f"File · {external[0]}", f"external::{side}")

                selected = box.findData(wanted) if wanted else -1
                if selected >= 0:
                    box.setCurrentIndex(selected)
                elif side == "right" and box.count() > 1:
                    box.setCurrentIndex(1)
                else:
                    box.setCurrentIndex(0)
                box.blockSignals(False)
            self._refresh_diff()

        def _resolve_diff_source(self, side: str) -> tuple[str, str]:
            if self.library is None:
                raise LibraryError("No skill library is loaded.")
            key = self.diff_source_boxes[side].currentData()
            if not isinstance(key, str):
                raise LibraryError("Choose a comparison source.")
            if key.startswith("skill::"):
                skill = self.library.get(key.removeprefix("skill::"))
                return skill.title, skill.content
            if key.startswith("chain::"):
                paths = json.loads(key.removeprefix("chain::"))
                skills = [self.library.get(path) for path in paths]
                label = " → ".join(skill.short_name for skill in skills)
                return label, build_session_prompt(skills)
            if key == f"external::{side}" and self.diff_external[side] is not None:
                return self.diff_external[side]
            raise LibraryError("The selected comparison source is unavailable.")

        def _open_diff_file(self, side: str) -> None:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Open Markdown version",
                str(self.library.root if self.library else Path.home()),
                "Markdown (*.md *.markdown);;Text files (*.txt);;All files (*)",
            )
            if not filename:
                return
            try:
                content = Path(filename).read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                QMessageBox.critical(self, "Could not open Markdown", str(exc))
                return
            self.diff_external[side] = (Path(filename).name, content)
            self._populate_diff_sources()
            box = self.diff_source_boxes[side]
            selected = box.findData(f"external::{side}")
            if selected >= 0:
                box.setCurrentIndex(selected)

        def _refresh_diff(self, _value=None) -> None:
            if not hasattr(self, "diff_source_boxes"):
                return
            try:
                left_label, left = self._resolve_diff_source("left")
                right_label, right = self._resolve_diff_source("right")
            except (LibraryError, SessionError, json.JSONDecodeError) as exc:
                self.current_diff_text = ""
                self.current_diff_labels = ("", "")
                self.current_diff_documents = None
                self.diff_summary.setText(str(exc))
                self.unified_diff_preview.clear()
                self.left_diff_preview.clear()
                self.right_diff_preview.clear()
                self.diff_section_box.clear()
                self.diff_section_summary.clear()
                self.section_diff_preview.clear()
                self.copy_diff_button.setEnabled(False)
                return

            if self.diff_baseline_box.currentData() == "right":
                baseline_label, baseline = right_label, right
                comparison_label, comparison_text = left_label, left
            else:
                baseline_label, baseline = left_label, left
                comparison_label, comparison_text = right_label, right

            comparison = compare_markdown(
                baseline,
                comparison_text,
                left_label=baseline_label,
                right_label=comparison_label,
                changed_sections_only=self.diff_changed_only.isChecked(),
            )
            rendered = compare_markdown(
                left,
                right,
                left_label=left_label,
                right_label=right_label,
                changed_sections_only=self.diff_changed_only.isChecked(),
            )
            self.current_diff_text = comparison.unified_diff
            self.current_diff_labels = (baseline_label, comparison_label)
            self.current_diff_documents = (
                baseline_label,
                baseline,
                comparison_label,
                comparison_text,
            )
            self.unified_diff_preview.setHtml(
                diff_to_html(comparison.unified_diff, self.diff_font_size)
            )
            self.left_diff_preview.setMarkdown(
                rendered.left_text or "_No changed content on this side._"
            )
            self.right_diff_preview.setMarkdown(
                rendered.right_text or "_No changed content on this side._"
            )
            count = len(comparison.changed_sections)
            if count:
                names = ", ".join(comparison.changed_sections[:4])
                if count > 4:
                    names += f", +{count - 4} more"
                self.diff_summary.setText(
                    f"{count} changed section{'s' if count != 1 else ''}: {names}"
                )
            else:
                self.diff_summary.setText("No differences")
            self.copy_diff_button.setEnabled(comparison.unified_diff != "No differences.")
            self._populate_diff_sections(comparison.changed_section_keys)

        def _set_diff_font_size(self, font_size: int) -> None:
            if font_size not in {12, 15, 18}:
                return
            self.diff_font_size = font_size
            for preview in (self.left_diff_preview, self.right_diff_preview):
                font = preview.document().defaultFont()
                font.setPixelSize(font_size)
                preview.document().setDefaultFont(font)
            self._refresh_diff()
            labels = {12: "Normal", 15: "Larger", 18: "Largest"}
            self.statusBar().showMessage(
                f"Diff text size: {labels[font_size]}",
                2000,
            )

        def _populate_diff_sections(self, changed_keys: tuple[str, ...]) -> None:
            if self.current_diff_documents is None:
                return
            _, baseline, _, comparison = self.current_diff_documents
            previous = self.diff_section_box.currentData()
            choices = markdown_section_choices(baseline, comparison)
            self.diff_section_box.blockSignals(True)
            self.diff_section_box.clear()
            for key, label in choices:
                self.diff_section_box.addItem(label, key)
            wanted = previous if previous in {key for key, _ in choices} else None
            if wanted is None and changed_keys:
                wanted = changed_keys[0]
            selected = self.diff_section_box.findData(wanted) if wanted else -1
            if selected < 0 and self.diff_section_box.count():
                selected = 0
            self.diff_section_box.setCurrentIndex(selected)
            self.diff_section_box.blockSignals(False)
            self._refresh_section_diff()

        def _refresh_section_diff(self, _value=None) -> None:
            if (
                not hasattr(self, "diff_section_box")
                or self.current_diff_documents is None
            ):
                return
            section_key = self.diff_section_box.currentData()
            if not isinstance(section_key, str):
                self.diff_section_summary.clear()
                self.section_diff_preview.clear()
                return
            baseline_label, baseline, comparison_label, comparison = (
                self.current_diff_documents
            )
            result = compare_markdown_section(
                baseline,
                comparison,
                section_key,
                left_label=baseline_label,
                right_label=comparison_label,
            )
            self.section_diff_preview.setHtml(
                diff_to_html(result.unified_diff, self.diff_font_size)
            )
            section_name = self.diff_section_box.currentText()
            if result.changed_sections:
                self.diff_section_summary.setText(f"Changes in {section_name}")
            else:
                self.diff_section_summary.setText(f"No differences in {section_name}")

        def _copy_diff(self) -> None:
            if self.current_diff_text and self.current_diff_text != "No differences.":
                output = self.current_diff_text
                if self.diff_copy_wrapped.isChecked():
                    output = wrap_diff_markdown(
                        output,
                        *self.current_diff_labels,
                    )
                QApplication.clipboard().setText(output)
                message = (
                    "Markdown-wrapped diff copied"
                    if self.diff_copy_wrapped.isChecked()
                    else "Unified diff copied"
                )
                self.statusBar().showMessage(message, 3000)

        def _remember_last_loaded(self, paths: tuple[str, ...]) -> None:
            self.last_loaded_paths = paths
            self.last_loaded_at = datetime.now(timezone.utc)
            self.settings.setValue("last_loaded_paths", json.dumps(list(paths)))
            self.settings.setValue(
                "last_loaded_at",
                self.last_loaded_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
            )
            self._refresh_last_loaded_label()

        def _restore_last_loaded_status(self) -> None:
            encoded_paths = self.settings.value("last_loaded_paths", "", type=str)
            encoded_time = self.settings.value("last_loaded_at", "", type=str)
            try:
                paths = tuple(json.loads(encoded_paths))
                loaded_at = datetime.fromisoformat(encoded_time.replace("Z", "+00:00"))
                if not 2 <= len(paths) <= 3 or not all(isinstance(path, str) for path in paths):
                    raise ValueError
                if self.library is None:
                    raise ValueError
                for path in paths:
                    self.library.get(path)
            except (ValueError, TypeError, json.JSONDecodeError, LibraryError):
                self.last_loaded_paths = ()
                self.last_loaded_at = None
            else:
                self.last_loaded_paths = paths
                self.last_loaded_at = loaded_at
            self._refresh_last_loaded_label()

        def _refresh_last_loaded_label(self) -> None:
            if (
                not self.last_loaded_paths
                or self.last_loaded_at is None
                or self.library is None
            ):
                self.last_loaded_label.setText("Last loaded: —")
                return
            try:
                names = " → ".join(
                    self.library.get(path).short_name for path in self.last_loaded_paths
                )
            except LibraryError:
                self.last_loaded_label.setText("Last loaded: unavailable")
                return
            relative = format_relative_time(self.last_loaded_at)
            self.last_loaded_label.setText(f"Last loaded: {names} ({relative})")

        def _export_session(self) -> None:
            try:
                skills = self._current_session_skills()
                markdown = build_session_markdown(skills)
            except (LibraryError, SessionError) as exc:
                QMessageBox.warning(self, "Could not export chain", str(exc))
                return
            slug = "-".join(skill.name for skill in skills)
            destination, _ = QFileDialog.getSaveFileName(
                self,
                "Export current chain",
                f"redforge-{slug}.md",
                "Markdown (*.md);;All files (*)",
            )
            if not destination:
                return
            try:
                Path(destination).write_text(markdown, encoding="utf-8")
            except OSError as exc:
                QMessageBox.critical(self, "Export failed", str(exc))
                return
            self.statusBar().showMessage(f"Chain exported · {destination}", 4000)

        def _copy_operator_brief(self) -> None:
            try:
                brief = build_operator_brief(self._current_session_skills())
            except SessionError as exc:
                QMessageBox.warning(self, "Could not build operator brief", str(exc))
                return
            QApplication.clipboard().setText(brief)
            self.statusBar().showMessage("Operator brief copied", 3000)

        def _export_operator_brief(self) -> None:
            try:
                skills = self._current_session_skills()
                brief = build_operator_brief(skills)
            except SessionError as exc:
                QMessageBox.warning(self, "Could not export operator brief", str(exc))
                return
            slug = "-".join(skill.name for skill in skills)
            destination, _ = QFileDialog.getSaveFileName(
                self,
                "Export operator brief",
                f"redforge-{slug}-operator-brief.md",
                "Markdown (*.md);;All files (*)",
            )
            if not destination:
                return
            try:
                Path(destination).write_text(brief, encoding="utf-8")
            except OSError as exc:
                QMessageBox.critical(self, "Export failed", str(exc))
                return
            self.statusBar().showMessage(
                f"Operator brief exported · {destination}",
                4000,
            )

        def _copy_session_prompt(self) -> None:
            if self.session_prompt:
                QApplication.clipboard().setText(self.session_prompt)
                self.statusBar().showMessage("Combined system prompt copied", 3000)

        def _copy_skill(self) -> None:
            if self.current_skill:
                QApplication.clipboard().setText(self.current_skill.content)
                self.statusBar().showMessage(f"Copied {self.current_skill.title}", 3000)

        def _copy_command(self) -> None:
            if self.current_skill:
                QApplication.clipboard().setText(self.current_skill.load_command)
                self.statusBar().showMessage("Load command copied", 3000)

        def _export_skill(self) -> None:
            if not self.current_skill:
                return
            destination, _ = QFileDialog.getSaveFileName(
                self,
                "Export skill",
                f"{self.current_skill.name}.md",
                "Markdown (*.md);;All files (*)",
            )
            if not destination:
                return
            try:
                shutil.copyfile(self.current_skill.source_path, destination)
            except OSError as exc:
                QMessageBox.critical(self, "Export failed", str(exc))
                return
            self.statusBar().showMessage(f"Exported to {destination}", 4000)

    app = QApplication([sys.argv[0], *(argv or [])])
    app.setApplicationName("RedForge")
    app.setOrganizationName("RedForge")
    window = MainWindow(args.library, use_saved_library=not args.launch_test)
    window.show()
    if args.launch_test:
        QTimer.singleShot(750, app.quit)
    return app.exec()


_STYLE = """
QMainWindow, QWidget {
    background: #111318;
    color: #e8e9ed;
}
QLabel#brand {
    color: #ff4d4d;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 2px;
}
QLabel#muted {
    color: #8e94a3;
}
QLineEdit, QComboBox, QListWidget, QTextBrowser, QPlainTextEdit {
    background: #191c23;
    border: 1px solid #2b303b;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #8e2d35;
}
QLineEdit:focus, QComboBox:focus, QListWidget:focus, QTextBrowser:focus, QPlainTextEdit:focus {
    border-color: #e54b55;
}
QListWidget::item {
    border-bottom: 1px solid #262a33;
    padding: 9px 7px;
}
QListWidget::item:selected {
    background: #392127;
    color: #ffffff;
}
QPushButton {
    background: #262a33;
    border: 1px solid #3b414d;
    border-radius: 7px;
    padding: 8px 14px;
}
QPushButton:hover {
    background: #303540;
    border-color: #e54b55;
}
QPushButton:checked {
    background: #59242b;
    border-color: #e54b55;
}
QPushButton:disabled {
    color: #666b76;
}
QSplitter::handle {
    background: #262a33;
    width: 1px;
}
QMenuBar, QMenu, QStatusBar {
    background: #15181e;
}
"""
