#!/usr/bin/env python3
"""Render Mermaid code to PNG files using mermaid.ink."""

from __future__ import annotations

import argparse
import base64
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "mermaid-png-renderer/1.0"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_mermaid_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    in_block = False
    buffer: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not in_block:
            if stripped.lower().startswith("```mermaid"):
                in_block = True
                buffer = []
            continue

        if stripped.startswith("```"):
            block = "\n".join(buffer).strip()
            if block:
                blocks.append(block)
            in_block = False
            buffer = []
        else:
            buffer.append(line)

    if in_block:
        raise ValueError("Unterminated Mermaid code block in markdown input")

    return blocks


def _mermaid_ink_url(
    code: str,
    theme: str | None,
    scale: float | None,
    background: str | None,
) -> str:
    payload = code.encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii")
    url = f"https://mermaid.ink/img/{encoded}"

    params: dict[str, str] = {}
    if theme:
        params["theme"] = theme
    if scale is not None:
        params["scale"] = str(scale)
    if background:
        params["bgColor"] = background
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    return url


def _download_png(url: str, output_path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type", "")
        if "image/png" not in content_type and "image/jpeg" not in content_type:
            raise RuntimeError(f"Unexpected content type: {content_type or 'unknown'}")
        with output_path.open("wb") as file:
            shutil.copyfileobj(response, file)


def _output_names(input_path: Path, count: int, is_markdown: bool) -> list[str]:
    stem = input_path.stem
    if is_markdown:
        if count == 1:
            return [f"{stem}-mermaid.png"]
        return [f"{stem}-mermaid-{index}.png" for index in range(1, count + 1)]
    return [f"{stem}.png"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render Mermaid code to PNG files via mermaid.ink."
    )
    parser.add_argument(
        "input",
        help="Path to a .mmd file or a Markdown file with ```mermaid blocks",
    )
    parser.add_argument(
        "--out-dir",
        dest="out_dir",
        help="Directory to write PNG files (defaults to input directory)",
    )
    parser.add_argument("--theme", help="Mermaid theme (default, neutral, dark)")
    parser.add_argument("--scale", type=float, help="Scale factor for rendering")
    parser.add_argument(
        "--background",
        dest="background",
        help="Background color for mermaid.ink (example: transparent or #FFFFFF)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PNG files",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    output_dir = Path(args.out_dir) if args.out_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    is_markdown = input_path.suffix.lower() in {".md", ".markdown"}
    try:
        content = _read_text(input_path)
        if is_markdown:
            blocks = _extract_mermaid_blocks(content)
            if not blocks:
                print(
                    "Error: no Mermaid code blocks found in markdown file",
                    file=sys.stderr,
                )
                return 1
        else:
            block = content.strip()
            if not block:
                print("Error: Mermaid input file is empty", file=sys.stderr)
                return 1
            blocks = [block]

        output_names = _output_names(input_path, len(blocks), is_markdown)
        for index, code in enumerate(blocks):
            output_path = output_dir / output_names[index]
            if output_path.exists() and not args.overwrite:
                print(
                    f"Error: output file exists: {output_path}",
                    file=sys.stderr,
                )
                return 1
            url = _mermaid_ink_url(code, args.theme, args.scale, args.background)
            _download_png(url, output_path)
            print(f"Generated: {output_path}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
