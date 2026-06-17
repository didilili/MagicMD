from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

from magicmd.config import DocxConfig
from magicmd.exceptions import ConversionError

_IMAGE_LINE_RE = re.compile(r"^(\s*)!\[([^\]]*)\]\(([^)]*)\)\s*$")
_GENERIC_IMAGE_ALTS = {"", "image", "img", "图片", "图", "图像"}
_METADATA_QUOTE_PREFIXES = ("Source:", "Author:", "Original:")


def write_docx_from_markdown(
    markdown_path: str | Path,
    docx_path: str | Path,
    config: DocxConfig | None = None,
) -> Path:
    docx_config = config or DocxConfig()
    markdown = Path(markdown_path)
    output = Path(docx_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    working_dir = markdown.parent
    docx_markdown = _prepare_docx_markdown(
        markdown.read_text(encoding="utf-8"),
        working_dir,
    )

    try:
        output_arg = str(output.relative_to(working_dir))
    except ValueError:
        output_arg = str(output if output.is_absolute() else output.resolve())

    cmd = [
        docx_config.pandoc_path,
        "-",
        "-f",
        "markdown-implicit_figures",
        "-t",
        "docx",
        "-o",
        output_arg,
    ]
    if docx_config.reference_doc:
        reference_doc = Path(docx_config.reference_doc).expanduser().resolve()
        cmd.extend(["--reference-doc", str(reference_doc)])

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=markdown.parent,
            input=docx_markdown,
        )
    except FileNotFoundError as exc:
        raise ConversionError(
            "Pandoc not found. Install pandoc or set [docx].pandoc_path in .magicmd.toml.",
            stage="write",
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or str(exc)).strip()
        message = f"Pandoc DOCX export failed: {details}"
        raise ConversionError(message, stage="write") from exc

    return output


def _prepare_docx_markdown(markdown_text: str, base_dir: Path) -> str:
    front_matter, body = _split_front_matter(markdown_text)
    metadata = _parse_front_matter(front_matter)
    lines = body.splitlines()
    lines = _remove_duplicate_first_heading(lines, metadata.get("title", ""))
    lines = _remove_metadata_quote_blocks(lines)
    lines = _normalize_docx_images(lines, base_dir)
    body_text = _collapse_blank_lines(lines).strip()
    if front_matter:
        return f"{front_matter.rstrip()}\n\n{body_text}\n"
    return f"{body_text}\n"


def _split_front_matter(markdown_text: str) -> tuple[str, str]:
    if not markdown_text.startswith("---\n"):
        return "", markdown_text
    end = markdown_text.find("\n---", 4)
    if end == -1:
        return "", markdown_text
    closing_end = markdown_text.find("\n", end + 4)
    if closing_end == -1:
        return markdown_text, ""
    return markdown_text[:closing_end], markdown_text[closing_end + 1 :]


def _parse_front_matter(front_matter: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in front_matter.splitlines():
        if line.strip() == "---" or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _remove_duplicate_first_heading(lines: list[str], title: str) -> list[str]:
    if not title:
        return lines
    next_lines = list(lines)
    first_content_index = next((i for i, line in enumerate(next_lines) if line.strip()), None)
    if first_content_index is None:
        return next_lines
    match = re.match(r"^#\s+(.+?)\s*$", next_lines[first_content_index])
    if not match or _normalize_heading(match.group(1)) != _normalize_heading(title):
        return next_lines
    del next_lines[first_content_index]
    while first_content_index < len(next_lines) and not next_lines[first_content_index].strip():
        del next_lines[first_content_index]
    return next_lines


def _normalize_heading(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _remove_metadata_quote_blocks(lines: list[str]) -> list[str]:
    next_lines: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].lstrip().startswith(">"):
            block_start = index
            while index < len(lines) and lines[index].lstrip().startswith(">"):
                index += 1
            block = lines[block_start:index]
            if _is_metadata_quote_block(block):
                while index < len(lines) and not lines[index].strip():
                    index += 1
                if index < len(lines) and _is_horizontal_rule(lines[index]):
                    index += 1
                while index < len(lines) and not lines[index].strip():
                    index += 1
                continue
            next_lines.extend(block)
            continue
        next_lines.append(lines[index])
        index += 1
    return next_lines


def _is_metadata_quote_block(lines: list[str]) -> bool:
    if not lines:
        return False
    contents = [line.lstrip()[1:].strip() for line in lines]
    return all(content.startswith(_METADATA_QUOTE_PREFIXES) for content in contents)


def _is_horizontal_rule(line: str) -> bool:
    return line.strip() in {"---", "***", "___"}


def _normalize_docx_images(lines: list[str], base_dir: Path) -> list[str]:
    next_lines: list[str] = []
    for line in lines:
        match = _IMAGE_LINE_RE.match(line)
        if not match:
            next_lines.append(line)
            continue
        indent, alt, target = match.groups()
        target = target.strip()
        if _should_skip_docx_image(target, base_dir, alt):
            continue
        if _is_generic_image_alt(alt):
            next_lines.append(f"{indent}![]({target})")
            continue
        next_lines.append(line)
    return next_lines


def _is_generic_image_alt(alt: str) -> bool:
    return alt.strip().lower() in _GENERIC_IMAGE_ALTS


def _should_skip_docx_image(target: str, base_dir: Path, alt: str) -> bool:
    image_path = _local_image_path(target, base_dir)
    if image_path is None or image_path.suffix.lower() != ".gif":
        return False
    dimensions = _gif_dimensions(image_path)
    if dimensions is None or not _is_generic_image_alt(alt):
        return False
    width, height = dimensions
    return height <= 120 or width / max(height, 1) >= 4


def _local_image_path(target: str, base_dir: Path) -> Path | None:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None
    return base_dir / unquote(target)


def _gif_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        header = path.read_bytes()[:10]
    except OSError:
        return None
    if len(header) < 10 or header[:6] not in {b"GIF87a", b"GIF89a"}:
        return None
    return int.from_bytes(header[6:8], "little"), int.from_bytes(header[8:10], "little")


def _collapse_blank_lines(lines: list[str]) -> str:
    collapsed: list[str] = []
    blank_count = 0
    for line in lines:
        if line.strip():
            blank_count = 0
            collapsed.append(line)
            continue
        blank_count += 1
        if blank_count <= 1:
            collapsed.append("")
    return "\n".join(collapsed)
