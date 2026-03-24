from __future__ import annotations

import glob as glob_module
import re
import subprocess
from pathlib import Path

import requests
from langchain_core.tools import tool


def _resolve_path(workspace_root: Path, path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (workspace_root / candidate).resolve()

    root_resolved = workspace_root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError("Path escapes workspace root")
    return resolved


def build_tools(workspace_root: Path):
    @tool
    def run_bash(command: str, timeout_ms: int = 120000) -> str:
        """Run a shell command in the workspace root."""

        completed = subprocess.run(
            command,
            cwd=workspace_root,
            shell=True,
            capture_output=True,
            text=True,
            timeout=max(1, timeout_ms) / 1000,
        )
        output = []
        output.append(f"exit_code={completed.returncode}")
        if completed.stdout:
            output.append("stdout:\n" + completed.stdout)
        if completed.stderr:
            output.append("stderr:\n" + completed.stderr)
        return "\n".join(output).strip()

    @tool
    def read_file(path: str) -> str:
        """Read a UTF-8 text file in the workspace."""

        file_path = _resolve_path(workspace_root, path)
        return file_path.read_text(encoding="utf-8")

    @tool
    def write_file(path: str, content: str) -> str:
        """Write UTF-8 text content to a file in the workspace."""

        file_path = _resolve_path(workspace_root, path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    @tool
    def glob_files(pattern: str, base: str = ".") -> list[str]:
        """Glob files under a base directory in the workspace."""

        base_path = _resolve_path(workspace_root, base)
        search = str(base_path / pattern)
        matches = glob_module.glob(search, recursive=True)
        return sorted(str(Path(match)) for match in matches)

    @tool
    def grep_files(pattern: str, include_glob: str = "**/*") -> list[str]:
        """Find lines matching a regex and return path:line:content."""

        regex = re.compile(pattern)
        lines: list[str] = []
        for file_name in workspace_root.glob(include_glob):
            if not file_name.is_file():
                continue
            try:
                content = file_name.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for idx, line in enumerate(content.splitlines(), start=1):
                if regex.search(line):
                    lines.append(f"{file_name}:{idx}:{line}")
        return lines

    @tool
    def web_fetch(url: str, timeout_s: int = 120) -> str:
        """Fetch web content from a URL."""

        response = requests.get(url, timeout=max(1, timeout_s))
        response.raise_for_status()
        return response.text

    return [run_bash, read_file, write_file, glob_files, grep_files, web_fetch]
