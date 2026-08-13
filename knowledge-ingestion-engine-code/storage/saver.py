from pathlib import Path
import hashlib
import json

from models.page import PageData


HASH_LENGTH = 8


def save_page(
    page: PageData,
    domain: str,
    category: str,
    filename: str,
    base_path: str | Path = "storage/output",
) -> str:
    """
    Save page markdown and metadata.

    Filename policy:

    1. Use the readable filename when available.
    2. If the filename already belongs to the same URL,
       overwrite it safely.
    3. If the filename belongs to another URL, append a
       deterministic URL hash.

    Returns:
        Final filename without extension.
    """

    output_dir = (
        Path(base_path)
        / domain
        / category
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_filename = _resolve_filename(
        output_dir=output_dir,
        filename=filename,
        page=page,
    )

    markdown_file = (
        output_dir
        / f"{final_filename}.md"
    )

    metadata_file = (
        output_dir
        / f"{final_filename}.json"
    )

    markdown_file.write_text(
        page.markdown or "",
        encoding="utf-8",
    )

    metadata = {
        "title": page.title,
        "url": page.url,
        "success": page.success,
    }

    metadata_file.write_text(
        json.dumps(
            metadata,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"\nSaved Markdown : {markdown_file}"
    )

    print(
        f"Saved Metadata : {metadata_file}"
    )

    return final_filename


def _resolve_filename(
    output_dir: Path,
    filename: str,
    page: PageData,
) -> str:
    """
    Resolve filename collisions deterministically.
    """

    filename = _clean_filename(filename)

    metadata_file = (
        output_dir
        / f"{filename}.json"
    )

    # No collision.
    if not metadata_file.exists():
        return filename

    existing_url = _read_existing_url(
        metadata_file
    )

    current_url = (
        page.url or ""
    ).strip()

    # Same URL -> safe overwrite.
    if existing_url == current_url:
        return filename

    # Different URL -> deterministic suffix.
    url_hash = hashlib.sha256(
        current_url.encode("utf-8")
    ).hexdigest()[:HASH_LENGTH]

    candidate = (
        f"{filename}__{url_hash}"
    )

    candidate_metadata = (
        output_dir
        / f"{candidate}.json"
    )

    # Extremely unlikely hash collision,
    # but handle it safely.
    if candidate_metadata.exists():
        candidate_url = _read_existing_url(
            candidate_metadata
        )

        if candidate_url != current_url:
            raise RuntimeError(
                "Filename hash collision detected "
                f"for URL: {current_url}"
            )

    return candidate


def _read_existing_url(
    metadata_file: Path,
) -> str:
    """
    Read URL from an existing metadata file.
    """

    try:
        data = json.loads(
            metadata_file.read_text(
                encoding="utf-8"
            )
        )

        return str(
            data.get("url", "")
        ).strip()

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return ""


def _clean_filename(filename: str) -> str:
    """
    Final defensive filesystem sanitization.
    """

    import re

    filename = (
        filename or ""
    ).strip().lower()

    filename = re.sub(
        r"[^a-z0-9_-]+",
        "_",
        filename,
    )

    filename = re.sub(
        r"_+",
        "_",
        filename,
    )

    filename = re.sub(
        r"-+",
        "-",
        filename,
    )

    filename = filename.strip("_-")

    return filename or "page"