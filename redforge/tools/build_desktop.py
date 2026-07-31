#!/usr/bin/env python3
"""One-command, cross-platform RedForge desktop build and smoke test."""

from __future__ import print_function

import os
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_VENV = PROJECT_ROOT / ".build-venv"
MINIMUM_PYTHON = (3, 10)
DEPENDENCY_STAMP = BUILD_VENV / ".redforge-dependencies"


def _python_version(executable):
    result = subprocess.run(
        [str(executable), "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None
    try:
        major, minor = result.stdout.strip().split(".", 1)
        return int(major), int(minor)
    except ValueError:
        return None


def _find_build_python():
    candidates = [Path(sys.executable)]
    for name in ("python3.14", "python3.13", "python3.12", "python3.11", "python3.10"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    homebrew = Path("/opt/homebrew/bin/python3")
    if homebrew.exists():
        candidates.append(homebrew)

    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        version = _python_version(resolved)
        if version and version >= MINIMUM_PYTHON:
            return resolved
    raise RuntimeError(
        "Python 3.10 or newer was not found. Install a current Python, then rerun this command."
    )


def _venv_python():
    if os.name == "nt":
        return BUILD_VENV / "Scripts" / "python.exe"
    return BUILD_VENV / "bin" / "python"


def _dependencies_ready(python):
    result = subprocess.run(
        [str(python), "-c", "import PyInstaller, PySide6"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _prepare_python():
    build_python = _find_build_python()
    if Path(build_python).resolve() == Path(sys.executable).resolve() and _dependencies_ready(
        build_python
    ):
        return build_python

    venv_python = _venv_python()
    if not venv_python.exists():
        print(f"Creating isolated build environment with {build_python}…")
        subprocess.run([str(build_python), "-m", "venv", str(BUILD_VENV)], check=True)
    dependency_signature = hashlib.sha256(
        (PROJECT_ROOT / "pyproject.toml").read_bytes()
    ).hexdigest()
    installed_signature = (
        DEPENDENCY_STAMP.read_text(encoding="utf-8").strip()
        if DEPENDENCY_STAMP.is_file()
        else ""
    )
    if not _dependencies_ready(venv_python) or installed_signature != dependency_signature:
        print("Installing desktop build dependencies…")
        subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "-e",
                f"{PROJECT_ROOT}[desktop,build]",
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )
        DEPENDENCY_STAMP.write_text(dependency_signature + "\n", encoding="utf-8")
    return venv_python


def _artifact_executable():
    if sys.platform == "darwin":
        return PROJECT_ROOT / "dist" / "RedForge.app" / "Contents" / "MacOS" / "RedForge"
    suffix = ".exe" if os.name == "nt" else ""
    return PROJECT_ROOT / "dist" / "RedForge" / f"RedForge{suffix}"


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive_artifact():
    dist = PROJECT_ROOT / "dist"
    if sys.platform == "darwin":
        archive = dist / "RedForge-macOS.zip"
        if archive.exists():
            archive.unlink()
        subprocess.run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                "RedForge.app",
                archive.name,
            ],
            cwd=dist,
            check=True,
        )
        verify_command = f"shasum -a 256 -c {archive.name}.sha256"
    elif os.name == "nt":
        archive = Path(
            shutil.make_archive(
                str(dist / "RedForge-Windows"),
                "zip",
                root_dir=dist,
                base_dir="RedForge",
            )
        )
        verify_command = (
            "powershell -Command "
            f"\"$e=(Get-Content {archive.name}.sha256).Split()[0];"
            f"$a=(Get-FileHash {archive.name} -Algorithm SHA256).Hash.ToLower();"
            "if($a -ne $e){exit 1}\""
        )
    else:
        archive = Path(
            shutil.make_archive(
                str(dist / "RedForge-Linux"),
                "gztar",
                root_dir=dist,
                base_dir="RedForge",
            )
        )
        verify_command = f"sha256sum -c {archive.name}.sha256"

    checksum = archive.with_name(archive.name + ".sha256")
    checksum.write_text(f"{_sha256(archive)}  {archive.name}\n", encoding="utf-8")
    note = dist / "VERIFY.txt"
    note.write_text(verify_command + "\n", encoding="utf-8")
    return archive, checksum, note


def main():
    try:
        python = _prepare_python()
        print("Building RedForge…")
        subprocess.run(
            [
                str(python),
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "packaging/redforge.spec",
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )

        executable = _artifact_executable()
        if not executable.is_file():
            raise RuntimeError(f"Build finished but the application was not found at {executable}")

        for label, flag in (
            ("resource smoke test", "--smoke-test"),
            ("UI launch test", "--launch-test"),
        ):
            print(f"Running packaged {label}…")
            result = subprocess.run(
                [str(executable), flag],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode:
                details = (result.stderr or result.stdout).strip()
                raise RuntimeError(f"Packaged {label} failed: {details}")
        print("Creating handoff archive and checksum…")
        archive, checksum, note = _archive_artifact()
    except (RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"\nBuild failed: {exc}", file=sys.stderr)
        return 1

    print(f"\nBuild passed: {executable}")
    print(f"Share: {archive}")
    print(f"Checksum: {checksum}")
    print(f"Verify note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
