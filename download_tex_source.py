#!/usr/bin/env python3
"""Download and extract TeX source archives from a URL."""

from __future__ import annotations

import argparse
import html
import shutil
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path


class _ArxivTitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self._in_title_h1 = False
        self._h1_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "meta":
            attrs_dict = {k.lower(): v for k, v in attrs if k}
            name_value = attrs_dict.get("name") or ""
            if name_value.lower() == "citation_title":
                content = attrs_dict.get("content")
                if content:
                    self.title = content.strip()
        elif tag.lower() == "h1":
            attrs_dict = {k.lower(): v for k, v in attrs if k}
            class_attr = (attrs_dict.get("class") or "").split()
            if "title" in class_attr:
                self._in_title_h1 = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "h1" and self._in_title_h1:
            self._in_title_h1 = False

    def handle_data(self, data: str) -> None:
        if self._in_title_h1:
            self._h1_chunks.append(data)

    def get_title(self) -> str | None:
        if self.title:
            return self.title
        if self._h1_chunks:
            text = " ".join(self._h1_chunks)
            text = text.replace("Title:", "")
            return " ".join(text.split())
        return None


def _extract_arxiv_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in {"arxiv.org", "www.arxiv.org"}:
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return None

    if parts[0] in {"abs", "e-print", "pdf"}:
        if len(parts) < 2:
            return None
        paper_id = "/".join(parts[1:])
        if parts[0] == "pdf" and paper_id.endswith(".pdf"):
            paper_id = paper_id[:-4]
        return paper_id

    return None


def _normalize_arxiv_download_url(url: str) -> str:
    arxiv_id = _extract_arxiv_id(url)
    if not arxiv_id:
        return url

    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[0] == "e-print":
        return url
    return f"https://arxiv.org/e-print/{arxiv_id}"


def _fetch_arxiv_title(arxiv_id: str) -> str | None:
    url = f"https://arxiv.org/abs/{arxiv_id}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "tex-source-downloader/1.0"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            content = response.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    parser = _ArxivTitleParser()
    parser.feed(content)
    title = parser.get_title()
    if not title:
        return None
    return html.unescape(title).strip()


def _sanitize_title(title: str) -> str:
    ascii_title = title.encode("ascii", "ignore").decode("ascii")
    cleaned = []
    for ch in ascii_title:
        if ch.isalnum() or ch in {" ", "-", "_", "."}:
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    collapsed = " ".join("".join(cleaned).split())
    return collapsed or "tex_source"


def _default_output_dir(url: str) -> Path:
    arxiv_id = _extract_arxiv_id(url)
    if arxiv_id:
        title = _fetch_arxiv_title(arxiv_id)
        if title:
            return Path(_sanitize_title(title))

    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name
    if not name:
        return Path("tex_source")

    stem = name
    for ext in (".tar.gz", ".tgz", ".tar", ".zip", ".gz"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break

    if not stem:
        stem = "tex_source"

    return Path(f"{stem}_tex")


def _download_archive(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "tex-source-downloader/1.0"},
    )
    with urllib.request.urlopen(request) as response, destination.open("wb") as file:
        shutil.copyfileobj(response, file)


def _validate_members(output_dir: Path, members: list[str]) -> None:
    base = output_dir.resolve()
    for member in members:
        target = (output_dir / member).resolve(strict=False)
        if base != target and base not in target.parents:
            raise RuntimeError(f"Unsafe path in archive: {member}")


def _extract_archive(archive_path: Path, output_dir: Path) -> None:
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as zip_file:
            _validate_members(output_dir, [m.filename for m in zip_file.infolist()])
            zip_file.extractall(output_dir)
        return

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as tar_file:
            _validate_members(output_dir, [m.name for m in tar_file.getmembers()])
            tar_file.extractall(output_dir)
        return

    raise ValueError(
        "Unsupported archive type; expected .zip, .tar, .tar.gz, or .tgz"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download an archive and extract TeX source files."
    )
    parser.add_argument(
        "url",
        help="URL to a source archive or arXiv abs/pdf link",
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        help="Directory to extract files into (defaults to paper title when available)",
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Keep the downloaded archive in the output directory",
    )

    args = parser.parse_args()
    download_url = _normalize_arxiv_download_url(args.url)
    output_dir = (
        Path(args.output_dir) if args.output_dir else _default_output_dir(args.url)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_name = Path(urllib.parse.urlparse(download_url).path).name or "archive"
    suffix = "".join(Path(archive_name).suffixes)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_file.name)
    temp_file.close()

    try:
        _download_archive(download_url, temp_path)
        _extract_archive(temp_path, output_dir)

        if args.keep_archive:
            archive_dest = output_dir / archive_name
            shutil.move(str(temp_path), archive_dest)
            temp_path = None

        tex_files = sorted(output_dir.rglob("*.tex"))
        print(f"Extracted into: {output_dir}")
        if tex_files:
            print("TeX files found:")
            for path in tex_files:
                print(f"- {path}")
        else:
            print("No .tex files found.")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
