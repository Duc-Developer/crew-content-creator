from __future__ import annotations

import shutil
import uuid

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def create_section_workspace(prefix: str) -> tuple[str, Path]:
    section_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
    workspace = project_root() / ".runtime_sections" / section_id
    workspace.mkdir(parents=True, exist_ok=True)
    return section_id, workspace


def section_output_paths(workspace: Path) -> dict[str, str]:
    root = project_root()
    return {
        "draft_article": str((workspace / "draft_article.md").relative_to(root)),
        "final_article": str((workspace / "final_article.md").relative_to(root)),
    }


def resolve_output_path(relative_path: str) -> Path:
    return project_root() / relative_path


def cleanup_section_workspace(workspace: Path) -> None:
    if workspace.exists():
        shutil.rmtree(workspace, ignore_errors=True)
