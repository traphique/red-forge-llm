#!/usr/bin/env python3
"""
RedForge Web UI — local dashboard for browsing skills.
Run from the redforge directory: streamlit run tools/redforge_ui.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

# Repo root (directory that contains skills/, tools/, etc.)
REDFORGE_ROOT = Path(__file__).resolve().parent.parent

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="RedForge",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — tuned for dark Streamlit theme + cards
st.markdown(
    """
<style>
    .rf-brand {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #ff4b4b, #ff8c00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }
    .rf-tagline {
        color: rgba(250, 250, 250, 0.72);
        font-size: 0.95rem;
        margin-top: 0;
    }
    .skill-card {
        background: linear-gradient(145deg, #1a1d24 0%, #14161c 100%);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 75, 75, 0.25);
        border-left: 4px solid #ff4b4b;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
    }
    .skill-card-title {
        font-weight: 600;
        font-size: 1.05rem;
        margin: 0 0 0.35rem 0;
        color: #fafafa;
    }
    .skill-card-meta {
        font-size: 0.85rem;
        color: rgba(250, 250, 250, 0.55);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    div[data-testid="stSidebarContent"] .rf-sidebar-brand {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        color: #fafafa;
    }
</style>
""",
    unsafe_allow_html=True,
)


def _toast(message: str, icon: str | None = None) -> None:
    fn = getattr(st, "toast", None)
    if callable(fn):
        fn(message, icon=icon)


def copy_if_supported(text: str) -> bool:
    """Copy to clipboard when Streamlit exposes st.clipboard (newer versions)."""
    clip = getattr(st, "clipboard", None)
    if callable(clip):
        clip(text)
        return True
    return False


def load_command_for_skill(relative_path: str) -> str:
    return f"cat {relative_path} | claude --system-file -"


@st.cache_data(show_spinner=False)
def load_skills(repo_root: str) -> tuple[list[dict], list[str]]:
    """Load skill metadata. Returns (skills, warnings for skipped files)."""
    root = Path(repo_root)
    skills_dir = root / "skills"
    skills: list[dict] = []
    warnings: list[str] = []

    if not skills_dir.is_dir():
        return [], [f"Skills directory not found: {skills_dir}"]

    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError as e:
            warnings.append(f"{skill_md}: {e}")
            continue
        first = text.split("\n", 1)[0]
        title = first.replace("# ", "").replace(" v1.1", "").strip() or skill_md.parent.name
        try:
            rel = str(skill_md.relative_to(root))
        except ValueError:
            warnings.append(f"{skill_md}: outside repo root")
            continue
        category = skill_md.parent.parent.name
        skills.append(
            {
                "name": skill_md.parent.name,
                "title": title,
                "category": category,
                "path": rel,
            }
        )
    return skills, warnings


skills, load_warnings = load_skills(str(REDFORGE_ROOT))
skills_by_name = {s["name"]: s for s in skills}

# Sidebar
st.sidebar.markdown('<p class="rf-sidebar-brand">RedForge</p>', unsafe_allow_html=True)
st.sidebar.caption(f"{len(skills)} skills • {REDFORGE_ROOT.name}/")

page = st.sidebar.radio(
    "Section",
    [
        "Dashboard",
        "Semantic search",
        "All skills",
        "Quick actions",
        "Documentation",
    ],
    label_visibility="collapsed",
)

# Compact header (full hero only on Dashboard)
if page == "Dashboard":
    st.markdown(
        '<p class="rf-brand">🛡️ RedForge</p><p class="rf-tagline">Red team skills library for LLM agents — offline & local</p>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(f'<p class="rf-brand" style="font-size:1.35rem;">{page}</p>', unsafe_allow_html=True)

if load_warnings:
    with st.sidebar.expander("Load notices", expanded=False):
        for w in load_warnings:
            st.caption(w)

# --- Dashboard ---
if page == "Dashboard":
    st.markdown("")

    if not skills:
        st.warning(
            f"No skills found. Run the UI from the **redforge** folder "
            f"(expected `{REDFORGE_ROOT / 'skills'}`)."
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Skills indexed", len(skills))
        with c2:
            st.metric("Categories", len({s["category"] for s in skills}))
        with c3:
            st.metric("Repo", REDFORGE_ROOT.name)

    st.divider()

    st.subheader("Quick start")
    cli_cmd = "python3 tools/redforge.py"
    st.code(cli_cmd, language="bash")
    st.caption("Run from the `redforge` directory for CLI and search tools to resolve paths correctly.")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Copy CLI command", key="dash_copy_cli"):
            if copy_if_supported(cli_cmd):
                _toast("Copied", icon="✅")
            else:
                _toast("Select the command above and copy manually", icon="📋")
    with col_b:
        web_cmd = "streamlit run tools/redforge_ui.py"
        if st.button("Copy web UI command", key="dash_copy_ui"):
            if copy_if_supported(web_cmd):
                _toast("Copied", icon="✅")
            else:
                _toast("Select the command in Quick actions", icon="📋")

    st.subheader("Featured skills")
    featured_order = ["rootkit", "edr-evasion", "active-directory", "cve-exploits"]
    for name in featured_order:
        s = skills_by_name.get(name)
        if not s:
            continue
        st.markdown(
            f"""
<div class="skill-card">
  <p class="skill-card-title">{s["title"]}</p>
  <p class="skill-card-meta">{s["category"]} · {s["path"]}</p>
</div>
""",
            unsafe_allow_html=True,
        )
        cmd = load_command_for_skill(s["path"])
        with st.expander(f"Load command — {s['name']}", expanded=False):
            st.code(cmd, language="bash")
            if st.button("Copy load command", key=f"feat_copy_{name}"):
                if copy_if_supported(cmd):
                    _toast("Copied to clipboard", icon="✅")
                else:
                    st.caption("Use the copy control on the code block (Streamlit) or select the text.")

# --- Semantic search ---
elif page == "Semantic search":
    st.caption("Plain-English search via the offline semantic index.")

    query = st.text_input(
        "What do you need help with?",
        placeholder="e.g. how do I stay hidden after getting a shell?",
    )
    run = st.button("Search", type="primary", use_container_width=False)

    if run:
        q = (query or "").strip()
        if not q:
            st.warning("Enter a search query first.")
        else:
            with st.spinner("Searching…"):
                try:
                    proc = subprocess.run(
                        [sys.executable, "tools/semantic_search.py", q],
                        capture_output=True,
                        text=True,
                        cwd=str(REDFORGE_ROOT),
                    )
                except OSError as e:
                    st.error(f"Could not run semantic search: {e}")
                else:
                    if proc.returncode != 0:
                        st.error(f"Search exited with code {proc.returncode}.")
                    if proc.stderr.strip():
                        st.code(proc.stderr, language="text")
                    out = proc.stdout.strip()
                    if out:
                        st.code(out, language="text")
                    elif proc.returncode == 0:
                        st.info("No stdout from search (empty result).")

# --- All skills ---
elif page == "All skills":
    if not skills:
        st.warning("No skills loaded. Check that `skills/` exists under the redforge repo.")
    else:
        categories = sorted({s["category"] for s in skills})
        selected_cat = st.selectbox("Category", ["All"] + categories)

        q_filter = st.text_input("Filter by title or path", placeholder="type to filter…")
        q_lower = (q_filter or "").strip().lower()

        filtered = skills if selected_cat == "All" else [s for s in skills if s["category"] == selected_cat]
        if q_lower:
            filtered = [
                s
                for s in filtered
                if q_lower in s["title"].lower() or q_lower in s["path"].lower() or q_lower in s["name"].lower()
            ]

        st.caption(f"Showing {len(filtered)} skill(s).")

        for s in filtered:
            cmd = load_command_for_skill(s["path"])
            with st.expander(f"{s['title']} · {s['category']}"):
                st.markdown(f"**Path:** `{s['path']}`")
                st.code(cmd, language="bash")
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Copy load command", key=f"all_copy_{s['name']}"):
                        if copy_if_supported(cmd):
                            _toast("Copied", icon="✅")
                        else:
                            st.caption("Use the copy icon on the code block.")
                with b2:
                    if st.button("Copy path only", key=f"path_copy_{s['name']}"):
                        if copy_if_supported(s["path"]):
                            _toast("Path copied", icon="✅")

# --- Quick actions ---
elif page == "Quick actions":
    popular = ["edr-evasion", "rootkit", "active-directory", "cve-exploits"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Popular skills — load commands")
        for p in popular:
            s = skills_by_name.get(p)
            if s:
                cmd = load_command_for_skill(s["path"])
                st.markdown(f"**{s['title']}**")
                st.code(cmd, language="bash")
                if st.button("Copy", key=f"qa_copy_{p}"):
                    if copy_if_supported(cmd):
                        _toast("Copied", icon="✅")
            else:
                st.caption(f"`{p}` — not found in this checkout.")

    with col2:
        st.subheader("Commands")
        st.markdown("Run these from the **`redforge`** directory.")
        cli = "python3 tools/redforge.py"
        sem = 'python3 tools/semantic_search.py "your question here"'
        ui = "streamlit run tools/redforge_ui.py"

        st.markdown("**Interactive CLI**")
        st.code(cli, language="bash")
        if st.button("Copy CLI", key="qa_cli"):
            ok = copy_if_supported(cli)
            _toast("Copied" if ok else "Select and copy the command above", icon="✅" if ok else "📋")

        st.markdown("**Semantic search (example)**")
        st.code(sem, language="bash")
        if st.button("Copy search example", key="qa_sem"):
            if copy_if_supported(sem):
                _toast("Copied", icon="✅")

        st.markdown("**This dashboard**")
        st.code(ui, language="bash")
        if st.button("Copy Streamlit command", key="qa_ui"):
            if copy_if_supported(ui):
                _toast("Copied", icon="✅")

# --- Documentation ---
else:
    st.caption("These files live next to `tools/` in your clone.")

    docs = [
        ("START_HERE.md", "Onboarding and quick start"),
        ("MASTER_INDEX.md", "Full index and master prompt"),
        ("README.md", "Project overview"),
    ]
    for fname, desc in docs:
        p = REDFORGE_ROOT / fname
        exists = p.is_file()
        st.markdown(f"**{fname}** — {desc}")
        st.code(str(p), language="text")
        if not exists:
            st.caption("File not found at the path above.")

    st.subheader("Highlights")
    st.markdown(
        """
- Skills are plain `SKILL.md` trees — load into your LLM workflow as documented.
- Semantic search and CLI assume your shell cwd is the **redforge** folder.
- Everything runs locally; no cloud required for this UI.
"""
    )

st.divider()
st.caption("RedForge • Local skills browser • 2026")
