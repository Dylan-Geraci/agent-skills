#!/usr/bin/env python3
"""env_check.py — diagnose why a project won't run on this machine.

Read-only. Inspects the repo + local environment and prints a JSON report of
findings: missing/old tools, uninstalled dependencies, env vars declared in an
example file but absent locally, and ports a config wants that are already busy.
It never installs, modifies, or starts anything — it only reports and lets the
env-doctor skill turn findings into suggested fix commands.

Usage:
    python env_check.py [ROOT]   # ROOT defaults to the current directory
"""
from __future__ import annotations

import json
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

# Manifest present -> tools we expect on PATH to build/run it.
TOOL_FOR_MANIFEST = {
    "package.json": ["node", "npm"],
    "pnpm-lock.yaml": ["pnpm"],
    "yarn.lock": ["yarn"],
    "requirements.txt": ["python"],
    "pyproject.toml": ["python"],
    "Pipfile": ["pipenv"],
    "go.mod": ["go"],
    "Cargo.toml": ["cargo"],
    "pom.xml": ["mvn", "java"],
    "build.gradle": ["gradle", "java"],
    "Gemfile": ["ruby", "bundle"],
    "composer.json": ["php", "composer"],
    "Dockerfile": ["docker"],
    "docker-compose.yml": ["docker"],
    "docker-compose.yaml": ["docker"],
}

VERSION_ARGS = {
    "java": ["-version"],  # java prints version to stderr with -version
}


def tool_version(tool: str) -> str | None:
    path = shutil.which(tool)
    if not path:
        return None
    args = VERSION_ARGS.get(tool, ["--version"])
    try:
        out = subprocess.run(
            [tool, *args], capture_output=True, text=True, timeout=8
        )
        text = (out.stdout or "") + (out.stderr or "")
        first = text.strip().splitlines()[0] if text.strip() else "(installed)"
        return first.strip()
    except (OSError, subprocess.SubprocessError):
        return "(installed, version unknown)"


def check_tools(present_manifests: list[str]) -> list[dict]:
    wanted: dict[str, None] = {}
    for m in present_manifests:
        for t in TOOL_FOR_MANIFEST.get(m, []):
            wanted.setdefault(t, None)
    findings = []
    for tool in wanted:
        ver = tool_version(tool)
        findings.append({
            "check": "tool",
            "name": tool,
            "ok": ver is not None,
            "detail": ver if ver else "not found on PATH",
            "severity": "ok" if ver else "error",
        })
    return findings


def check_deps_installed(root: Path, present_manifests: list[str]) -> list[dict]:
    findings = []
    if "package.json" in present_manifests:
        installed = (root / "node_modules").is_dir()
        findings.append({
            "check": "dependencies",
            "name": "node_modules",
            "ok": installed,
            "detail": "present" if installed else "missing — run your JS install",
            "severity": "ok" if installed else "warn",
            "suggest": None if installed else "npm install",
        })
    if any(m in present_manifests for m in ("requirements.txt", "pyproject.toml", "Pipfile")):
        venv = next((d for d in (".venv", "venv", "env") if (root / d).is_dir()), None)
        findings.append({
            "check": "dependencies",
            "name": "python venv",
            "ok": venv is not None,
            "detail": f"found {venv}" if venv else "no virtualenv detected",
            "severity": "ok" if venv else "warn",
            "suggest": None if venv else "python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt",
        })
    return findings


def check_env_vars(root: Path) -> list[dict]:
    example = next(
        (root / n for n in (".env.example", ".env.sample", ".env.template") if (root / n).exists()),
        None,
    )
    if not example:
        return []
    declared = _env_keys(example)
    actual = _env_keys(root / ".env") if (root / ".env").exists() else set()
    missing = sorted(declared - actual)
    has_env = (root / ".env").exists()
    return [{
        "check": "env_vars",
        "name": example.name,
        "ok": has_env and not missing,
        "detail": (
            f".env missing entirely (template has {len(declared)} vars)" if not has_env
            else f"missing {len(missing)}: {', '.join(missing)}" if missing
            else "all template vars present in .env"
        ),
        "severity": "error" if not has_env else ("warn" if missing else "ok"),
        "missing_keys": missing if has_env else sorted(declared),
        "suggest": None if (has_env and not missing) else f"cp {example.name} .env  # then fill in the values",
    }]


def _env_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            keys.add(line.split("=", 1)[0].strip())
    except OSError:
        pass
    return keys


def check_ports(root: Path) -> list[dict]:
    ports: set[int] = set()
    for name in ("docker-compose.yml", "docker-compose.yaml"):
        f = root / name
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Match "ports:" entries like "8080:80" or "- 3000:3000".
        for m in re.finditer(r'["\']?(\d{2,5})\s*:\s*\d{2,5}["\']?', text):
            ports.add(int(m.group(1)))

    findings = []
    for port in sorted(ports):
        busy = _port_busy(port)
        findings.append({
            "check": "port",
            "name": str(port),
            "ok": not busy,
            "detail": "in use by another process" if busy else "free",
            "severity": "warn" if busy else "ok",
        })
    return findings


def _port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {root}"}))
        return 1

    present = [m for m in TOOL_FOR_MANIFEST if (root / m).exists()]
    findings: list[dict] = []
    findings += check_tools(present)
    findings += check_deps_installed(root, present)
    findings += check_env_vars(root)
    findings += check_ports(root)

    summary = {
        "errors": sum(f["severity"] == "error" for f in findings),
        "warnings": sum(f["severity"] == "warn" for f in findings),
        "ok": sum(f["severity"] == "ok" for f in findings),
    }
    print(json.dumps({
        "root": str(root),
        "manifests_present": present,
        "summary": summary,
        "findings": findings,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
