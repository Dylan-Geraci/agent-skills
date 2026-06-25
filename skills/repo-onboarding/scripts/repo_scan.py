#!/usr/bin/env python3
"""repo_scan.py — gather objective signals about a repository for onboarding.

Read-only. Prints a JSON report of structure, languages, package managers,
entry points, scripts, tests, CI, and docs. The repo-onboarding skill feeds
this to Claude, which turns the raw signals into a human "start here" guide.

Usage:
    python repo_scan.py [ROOT]   # ROOT defaults to the current directory
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Directories we never want to descend into when sampling the tree.
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__",
    "dist", "build", "target", ".next", ".nuxt", "out", "vendor",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache", ".gradle",
    "coverage", ".tox", "bin", "obj", ".terraform",
}

# Marker file -> (ecosystem label, package-manager hint).
MANIFESTS = {
    "package.json": ("JavaScript/TypeScript", "npm/yarn/pnpm"),
    "pnpm-lock.yaml": ("JavaScript/TypeScript", "pnpm"),
    "yarn.lock": ("JavaScript/TypeScript", "yarn"),
    "requirements.txt": ("Python", "pip"),
    "pyproject.toml": ("Python", "pip/poetry/uv"),
    "Pipfile": ("Python", "pipenv"),
    "go.mod": ("Go", "go modules"),
    "Cargo.toml": ("Rust", "cargo"),
    "pom.xml": ("Java", "maven"),
    "build.gradle": ("Java/Kotlin", "gradle"),
    "build.gradle.kts": ("Java/Kotlin", "gradle"),
    "Gemfile": ("Ruby", "bundler"),
    "composer.json": ("PHP", "composer"),
    "pubspec.yaml": ("Dart/Flutter", "pub"),
    "mix.exs": ("Elixir", "mix"),
    "*.csproj": (".NET", "dotnet"),
    "Dockerfile": ("Container", "docker"),
    "docker-compose.yml": ("Container", "docker compose"),
    "docker-compose.yaml": ("Container", "docker compose"),
}

# Extensions counted toward the language histogram.
LANG_EXT = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".c": "C", ".h": "C/C++",
    ".swift": "Swift", ".dart": "Dart", ".ex": "Elixir", ".scala": "Scala",
    ".sh": "Shell", ".sql": "SQL", ".vue": "Vue", ".svelte": "Svelte",
}

# Common entry-point filenames worth surfacing if present.
ENTRY_HINTS = [
    "main.py", "__main__.py", "app.py", "manage.py", "wsgi.py", "asgi.py",
    "index.js", "index.ts", "main.js", "main.ts", "server.js", "server.ts",
    "main.go", "main.rs", "Main.java", "Program.cs", "index.php",
]

CONFIG_HINTS = [
    "tsconfig.json", "vite.config.ts", "vite.config.js", "webpack.config.js",
    "next.config.js", "tailwind.config.js", ".eslintrc", ".prettierrc",
    "ruff.toml", "setup.cfg", "tox.ini", "Makefile", "justfile",
    ".env.example", ".env.sample", "alembic.ini",
]


def is_text(p: Path) -> bool:
    try:
        with p.open("rb") as fh:
            return b"\x00" not in fh.read(2048)
    except OSError:
        return False


def scan(root: Path) -> dict:
    manifests: list[dict] = []
    lang_counts: dict[str, int] = {}
    entry_points: list[str] = []
    configs: list[str] = []
    test_dirs: set[str] = set()
    ci_files: list[str] = []
    docs: list[str] = []
    file_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = Path(dirpath).relative_to(root)

        if ".github" in rel_dir.parts or "workflows" in rel_dir.parts:
            for f in filenames:
                if f.endswith((".yml", ".yaml")):
                    ci_files.append(str((rel_dir / f).as_posix()))

        low_dir = rel_dir.as_posix().lower()
        if any(seg in ("test", "tests", "__tests__", "spec") for seg in low_dir.split("/")):
            test_dirs.add(rel_dir.as_posix())

        for f in filenames:
            file_count += 1
            rel = (rel_dir / f).as_posix()
            ext = Path(f).suffix.lower()

            if ext in LANG_EXT:
                lang_counts[LANG_EXT[ext]] = lang_counts.get(LANG_EXT[ext], 0) + 1

            for marker, (eco, pm) in MANIFESTS.items():
                hit = f == marker or (marker.startswith("*") and f.endswith(marker[1:]))
                if hit:
                    manifests.append({"file": rel, "ecosystem": eco, "package_manager": pm})

            if f in ENTRY_HINTS:
                entry_points.append(rel)
            if any(f == c or f.startswith(c) for c in CONFIG_HINTS):
                configs.append(rel)
            if f.lower() in ("readme.md", "contributing.md", "architecture.md") or (
                low_dir.startswith("docs") and ext in (".md", ".rst")
            ):
                docs.append(rel)

    langs = sorted(lang_counts.items(), key=lambda kv: -kv[1])

    # package.json scripts are the single highest-signal "how do I run this".
    scripts = {}
    pkg = root / "package.json"
    if pkg.exists() and is_text(pkg):
        try:
            scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
        except (ValueError, OSError):
            pass

    return {
        "root": str(root),
        "total_files_scanned": file_count,
        "languages": [{"language": l, "files": c} for l, c in langs],
        "primary_language": langs[0][0] if langs else None,
        "manifests": manifests,
        "package_json_scripts": scripts,
        "entry_points": sorted(set(entry_points)),
        "config_files": sorted(set(configs)),
        "test_dirs": sorted(test_dirs),
        "ci_files": sorted(set(ci_files)),
        "docs": sorted(set(docs))[:25],
    }


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {root}"}))
        return 1
    print(json.dumps(scan(root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
