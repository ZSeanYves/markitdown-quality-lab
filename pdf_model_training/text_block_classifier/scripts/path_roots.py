#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_ROOT = SCRIPT_DIR.parent
PDF_MODEL_TRAINING_ROOT = MODEL_ROOT.parent
QUALITY_LAB_ROOT = PDF_MODEL_TRAINING_ROOT.parent
MAIN_REPO_ROOT = QUALITY_LAB_ROOT.parent
REPO_ROOT = MAIN_REPO_ROOT

MODEL_REL = "text_block_classifier"
LOCAL_ONLY_REL = "local_only"
LEGACY_CORPUS_PREFIX = ".external/quality_corpus/"
LEGACY_LAYOUT_LAB_PREFIX = "samples/pdf_layout_classifier/"
LEGACY_LAYOUT_MODEL_PREFIX = ".external/layout_model/"


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        out.append(path)
        seen.add(key)
    return out


def first_existing_dir(candidates: Iterable[Path | None]) -> Path | None:
    for candidate in candidates:
        if candidate is None:
            continue
        candidate = candidate.expanduser()
        if candidate.is_dir():
            return candidate.resolve()
    return None


def discover_quality_lab_root(repo_root: Path = REPO_ROOT) -> Path | None:
    return first_existing_dir(
        [
            _env_path("MARKITDOWN_QUALITY_LAB"),
            QUALITY_LAB_ROOT,
            repo_root / "markitdown-quality-lab",
            repo_root.parent / "markitdown-quality-lab",
        ]
    )


def discover_layout_lab_root(
    repo_root: Path = REPO_ROOT,
    override: str | None = None,
) -> Path | None:
    if override:
        override_root = Path(override).expanduser()
        if (override_root / "scripts").is_dir():
            return override_root.resolve()
        if (override_root / MODEL_REL / "scripts").is_dir():
            return (override_root / MODEL_REL).resolve()
        return first_existing_dir([override_root])

    env_root = _env_path("MARKITDOWN_LAYOUT_LAB")
    if env_root is not None:
        return first_existing_dir([env_root])
    if MODEL_ROOT.is_dir():
        return MODEL_ROOT.resolve()
    quality_lab_root = discover_quality_lab_root(repo_root)
    if quality_lab_root is not None:
        return first_existing_dir([quality_lab_root / "pdf_model_training" / MODEL_REL])
    return first_existing_dir(
        [
            repo_root / "markitdown-quality-lab" / "pdf_model_training" / MODEL_REL,
            repo_root.parent / "markitdown-quality-lab" / "pdf_model_training" / MODEL_REL,
        ]
    )


def discover_corpus_root(
    repo_root: Path = REPO_ROOT,
    override: str | None = None,
) -> Path | None:
    quality_lab_root = discover_quality_lab_root(repo_root)
    return first_existing_dir(
        [
            Path(override).expanduser() if override else None,
            _env_path("MARKITDOWN_QUALITY_CORPUS"),
            quality_lab_root / "external_quality" if quality_lab_root else None,
            repo_root / "markitdown-quality-lab" / "external_quality",
            repo_root.parent / "markitdown-quality-lab" / "external_quality",
            repo_root.parent / "markitdown-quality-corpus",
            repo_root / ".external" / "quality_corpus",
        ]
    )


def discover_model_root(
    repo_root: Path = REPO_ROOT,
    override: str | None = None,
    layout_lab_root: Path | None = None,
) -> Path | None:
    block_root = layout_lab_root or discover_layout_lab_root(repo_root)
    return first_existing_dir(
        [
            Path(override).expanduser() if override else None,
            _env_path("MARKITDOWN_LAYOUT_MODEL"),
            (_env_path("MARKITDOWN_LAYOUT_LAB") / "models") if _env_path("MARKITDOWN_LAYOUT_LAB") else None,
            (block_root / "models") if block_root else None,
            repo_root / ".external" / "layout_model" / "models",
        ]
    )


def default_manifest_path(repo_root: Path = REPO_ROOT, layout_lab_root: Path | None = None) -> Path:
    block_root = layout_lab_root or MODEL_ROOT
    candidate = block_root / "manifests" / "manifest.tsv"
    if candidate.exists():
        return candidate
    candidate = block_root / "archive" / "old_manifests" / "manifest.block_draft.legacy.tsv"
    if candidate.exists():
        return candidate
    candidate = block_root / "archive" / "old_manifests" / "manifest.example.legacy.tsv"
    if candidate.exists():
        return candidate
    candidate = block_root / "archive" / "old_manifests" / "manifest.legacy.mixed.tsv"
    if candidate.exists():
        return candidate
    return repo_root / "samples" / "pdf_layout_classifier" / "manifest.tsv"


def default_feature_dir(layout_lab_root: Path | None, repo_root: Path = REPO_ROOT) -> Path:
    block_root = layout_lab_root or MODEL_ROOT
    if block_root is not None:
        return block_root / "evaluation" / "local_eval" / "features" / "raw"
    return repo_root / ".tmp" / "pdf_model_training" / "features"


def default_eval_output_dir(layout_lab_root: Path | None, repo_root: Path = REPO_ROOT) -> Path:
    block_root = layout_lab_root or MODEL_ROOT
    if block_root is not None:
        return block_root / "evaluation" / "local_eval" / "eval"
    return repo_root / ".external" / "layout_model" / "eval"


def default_model_output_path(
    layout_lab_root: Path | None,
    model_root: Path | None,
    repo_root: Path = REPO_ROOT,
    name: str = "text_block_classifier_linear.json",
) -> Path:
    block_root = layout_lab_root or MODEL_ROOT
    if block_root is not None:
        return block_root / "models" / name
    if model_root:
        return model_root / name
    return repo_root / ".tmp" / "pdf_model_training" / "models" / name


def default_local_eval_model_path(
    layout_lab_root: Path | None,
    model_root: Path | None,
    repo_root: Path = REPO_ROOT,
) -> Path:
    block_root = layout_lab_root or MODEL_ROOT
    if block_root is not None:
        return block_root / "models" / "text_block_classifier_local_eval.json"
    if model_root:
        return model_root / "text_block_classifier_local_eval.json"
    return repo_root / ".external" / "layout_model" / "models" / "text_block_classifier_local_eval.json"


def resolve_existing_path(raw_path: str | Path, repo_root: Path = REPO_ROOT, extra_roots: Iterable[Path | None] = ()) -> Path | None:
    raw = str(raw_path).strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    candidates: list[Path] = []
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.append(repo_root / path)
        for root in extra_roots:
            if root is None:
                continue
            candidates.append(Path(root) / path)
    for candidate in _dedupe_paths(candidates):
        if candidate.exists():
            return candidate.resolve()
    return None


def _legacy_model_candidates(raw: str, layout_lab_root: Path | None) -> list[Path]:
    if layout_lab_root is None or not raw.startswith(LEGACY_LAYOUT_MODEL_PREFIX):
        return []
    suffix = raw[len(LEGACY_LAYOUT_MODEL_PREFIX) :]
    if not suffix:
        return []
    return [
        layout_lab_root / "archive" / "legacy_dataset_bytes" / "datasets" / suffix,
        layout_lab_root / "archive" / "repo_manual_labels" / suffix,
        layout_lab_root / suffix,
    ]


def resolve_pdf_source_path(
    raw_path: str,
    *,
    repo_root: Path = REPO_ROOT,
    manifest_dir: Path | None = None,
    corpus_root: Path | None = None,
    layout_lab_root: Path | None = None,
) -> Path | None:
    raw = raw_path.strip()
    if not raw:
        return None
    direct = resolve_existing_path(raw, repo_root=repo_root, extra_roots=[manifest_dir])
    if direct is not None:
        return direct

    block_root = layout_lab_root or MODEL_ROOT
    candidates: list[Path] = []
    if corpus_root is not None:
        if raw.startswith(LEGACY_CORPUS_PREFIX):
            candidates.append(corpus_root / raw[len(LEGACY_CORPUS_PREFIX) :])
        else:
            candidates.append(corpus_root / raw)
    if block_root is not None:
        candidates.extend(
            [
                block_root / raw,
                block_root / "archive" / "legacy_dataset_bytes" / "datasets" / raw,
            ]
        )
        if raw.startswith(LEGACY_LAYOUT_LAB_PREFIX):
            suffix = raw[len(LEGACY_LAYOUT_LAB_PREFIX) :]
            candidates.extend(
                [
                    block_root / suffix,
                    block_root / "archive" / "legacy_dataset_bytes" / "datasets" / suffix,
                ]
            )
    candidates.extend(_legacy_model_candidates(raw, block_root))
    for candidate in _dedupe_paths(candidates):
        if candidate.exists():
            return candidate.resolve()
    return None


def resolve_layout_lab_path(
    raw_path: str,
    *,
    repo_root: Path = REPO_ROOT,
    manifest_dir: Path | None = None,
    layout_lab_root: Path | None = None,
) -> Path | None:
    raw = raw_path.strip()
    if not raw:
        return None
    direct = resolve_existing_path(raw, repo_root=repo_root, extra_roots=[manifest_dir])
    if direct is not None:
        return direct

    block_root = layout_lab_root or MODEL_ROOT
    candidates: list[Path] = []
    if block_root is not None:
        candidates.extend(
            [
                block_root / raw,
                block_root / "archive" / "repo_manual_labels" / raw,
                block_root / "archive" / "repo_manual_labels" / "all_labels" / raw,
            ]
        )
        if raw.startswith("pdf_model_training/labels/"):
            suffix = raw[len("pdf_model_training/labels/") :]
            candidates.extend(
                [
                    block_root / "labels" / suffix,
                    block_root / "archive" / "repo_manual_labels" / suffix,
                    block_root / "archive" / "repo_manual_labels" / "all_labels" / suffix,
                ]
            )
        if raw.startswith(LEGACY_LAYOUT_LAB_PREFIX):
            suffix = raw[len(LEGACY_LAYOUT_LAB_PREFIX) :]
            candidates.extend(
                [
                    block_root / suffix,
                    block_root / "archive" / "repo_manual_labels" / suffix,
                ]
            )
    candidates.extend(_legacy_model_candidates(raw, block_root))
    for candidate in _dedupe_paths(candidates):
        if candidate.exists():
            return candidate.resolve()
    return None
