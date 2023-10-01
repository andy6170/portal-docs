import os
import json
import pathlib
import shutil

from .libs.helper import CleanDoc, project_dir, project_root
from loguru import logger

BUILD_DIR = project_root / "docs" / "portal_blocks"
BUILD_DIR.mkdir(exist_ok=True)


def delete_existing_official_docs():
    """Delete all existing official docs"""
    REGEN_DOCS_DIR = os.getenv("REGEN_DOCS_DIR", "False").lower() == 'true'
    if REGEN_DOCS_DIR:
        logger.warning(f"REGEN_DOCS_DIR is Set to {REGEN_DOCS_DIR}, Document directories will be regenerated")

    for f in BUILD_DIR.iterdir():
        if f.is_dir():
            shutil.rmtree(f) if REGEN_DOCS_DIR else (f / "docs" / "official.md").unlink(missing_ok=True)


def ensure_doc_dir(block_name: str):
    self_docs = BUILD_DIR / block_name / "docs"
    self_docs.mkdir(exist_ok=True, parents=True)


def ensure_index_md(block_name: str):
    root_doc = BUILD_DIR / block_name / "_index.md"
    if not root_doc.exists():
        doc_header = [
            "---",
            f"title: {block_name}",
            "draft: false",
            "geekdocFilePath: false",
            "---"
            f"# {block_name}"
        ]
        root_doc.write_text('\n'.join(doc_header))

    self_docs_index = BUILD_DIR / block_name / "docs" / "_index.md"
    if not self_docs_index.exists():
        header = [
            "---",
            "geekdocHidden: true",
            "---"
        ]
        self_docs_index.write_text('\n'.join(header))


def ensure_index_extra_docs_file(block_name: str):
    extra_doc = BUILD_DIR / block_name / "docs" / "extra.md"
    if not extra_doc.exists():
        extra_doc.write_text(f"<!-- Add extra documentation for {block_name} in this file -->")


def write_official_doc(doc_json_file: pathlib.Path, block_name: str):
    with doc_json_file.open("r") as JSON_FILE:
        doc_json: CleanDoc = json.loads(JSON_FILE.read())

    doc = [f"{doc_json['summary']}"]

    if doc_json.get("inputs", False):
        doc.extend([
                "### Inputs",
                "\n".join(doc_json["inputs"])
        ])

    if doc_json.get("output", False):
        doc.extend([
            "### Output",
            "\n".join(doc_json["output"])
        ])

    block_image_url = (f"https://raw.githubusercontent.com/battlefield-portal-community/"
                       f"Image-CDN/main/portal_blocks/{block_name}.png")

    doc.append(f"\n![{block_name}]({block_image_url})")

    doc_file = BUILD_DIR / block_name / "docs" / "official.md"
    doc_file.write_text("\n".join(doc))


def generate():

    # geekdocFilePath: portal_blocks/blocks/{file.stem}.md

    delete_existing_official_docs()
    for file in (project_dir / "docs_json").glob("*.json"):

        block_name = file.stem

        # need to ensure as delete_existing_official_docs may delete the doc dir
        # because of REGEN_DOCS_DIR
        ensure_doc_dir(block_name)
        ensure_index_md(block_name)
        ensure_index_extra_docs_file(block_name)

        write_official_doc(file, block_name)
        logger.info(f"Built {file.stem}")
