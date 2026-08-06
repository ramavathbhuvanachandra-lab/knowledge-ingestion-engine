from pathlib import Path
import json

from models.page import PageData

def save_page(
    page: PageData,
    domain: str,
    category: str,
    filename: str,
    ) -> None:

    
    output_dir = (
    Path("storage")
    / "output"
    / domain
    / category
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save Markdown
    markdown_file = output_dir / f"{filename}.md"
    markdown_file.write_text(page.markdown, encoding="utf-8")

    # Save Metadata
    metadata = {
        "title": page.title,
        "url": page.url,
        "success": page.success
    }

    metadata_file = output_dir / f"{filename}.json"

    metadata_file.write_text(
        json.dumps(metadata, indent=4),
        encoding="utf-8"
    )

    print(f"\n✅ Saved Markdown : {markdown_file}")
    print(f"✅ Saved Metadata : {metadata_file}")