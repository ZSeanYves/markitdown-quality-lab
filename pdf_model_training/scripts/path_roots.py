#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
LAYOUT_LAB_ROOT = SCRIPT_DIR.parent
QUALITY_LAB_ROOT = LAYOUT_LAB_ROOT.parent
MAIN_REPO_ROOT = QUALITY_LAB_ROOT.parent
REPO_ROOT = MAIN_REPO_ROOT
LEGACY_CORPUS_PREFIX = ".external/quality_corpus/"
LEGACY_LAYOUT_LAB_PREFIX = "samples/pdf_layout_classifier/"
LEGACY_LAYOUT_MODEL_PREFIX = ".external/layout_model/"
EXTERNAL_QUALITY_REL = "external_quality"
PDF_MODEL_TRAINING_REL = "pdf_model_training"


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


def legacy_layout_model_candidates(raw: str, layout_lab_root: Path | None) -> list[Path]:
    if layout_lab_root is None or not raw.startswith(LEGACY_LAYOUT_MODEL_PREFIX):
        return []
    suffix = raw[len(LEGACY_LAYOUT_MODEL_PREFIX) :]
    if not suffix:
        return []
    if suffix.startswith("datasets/"):
        return [layout_lab_root / suffix]
    if suffix.startswith("labels/"):
        return [layout_lab_root / suffix]
    if suffix.startswith("models/"):
        return [layout_lab_root / suffix]
    if suffix.startswith("features/"):
        return [layout_lab_root / "local_eval" / suffix]
    if suffix.startswith("eval/"):
        return [layout_lab_root / "local_eval" / suffix]
    if suffix.startswith("eval_"):
        return [layout_lab_root / "reports" / suffix]
    return [layout_lab_root / "reports" / suffix]


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


def discover_corpus_root(
    repo_root: Path = REPO_ROOT,
    override: str | None = None,
) -> Path | None:
    quality_lab_root = discover_quality_lab_root(repo_root)
    return first_existing_dir(
        [
            Path(override).expanduser() if override else None,
            _env_path("MARKITDOWN_QUALITY_CORPUS"),
            quality_lab_root / EXTERNAL_QUALITY_REL if quality_lab_root else None,
            repo_root / "markitdown-quality-lab" / EXTERNAL_QUALITY_REL,
            repo_root.parent / "markitdown-quality-lab" / EXTERNAL_QUALITY_REL,
            repo_root.parent / "markitdown-quality-corpus",
            repo_root / ".external" / "quality_corpus",
        ]
    )


def discover_layout_lab_root(
    repo_root: Path = REPO_ROOT,
    override: str | None = None,
) -> Path | None:
    if override:
        return first_existing_dir([Path(override).expanduser()])
    env_root = _env_path("MARKITDOWN_LAYOUT_LAB")
    if env_root is not None:
        return first_existing_dir([env_root])
    if LAYOUT_LAB_ROOT.is_dir():
        return LAYOUT_LAB_ROOT.resolve()
    quality_lab_root = discover_quality_lab_root(repo_root)
    if quality_lab_root is not None:
        return first_existing_dir([quality_lab_root / PDF_MODEL_TRAINING_REL])
    return first_existing_dir(
        [
            repo_root / "markitdown-quality-lab" / PDF_MODEL_TRAINING_REL,
            repo_root.parent / "markitdown-quality-lab" / PDF_MODEL_TRAINING_REL,
        ]
    )


def discover_model_root(
    repo_root: Path = REPO_ROOT,
    override: str | None = None,
    layout_lab_root: Path | None = None,
) -> Path | None:
    quality_lab_root = discover_quality_lab_root(repo_root)
    return first_existing_dir(
        [
            Path(override).expanduser() if override else None,
            _env_path("MARKITDOWN_LAYOUT_MODEL"),
            (_env_path("MARKITDOWN_LAYOUT_LAB") / "models") if _env_path("MARKITDOWN_LAYOUT_LAB") else None,
            LAYOUT_LAB_ROOT / "models",
            (quality_lab_root / PDF_MODEL_TRAINING_REL / "models") if quality_lab_root else None,
            (layout_lab_root / "models") if layout_lab_root else None,
            repo_root / "markitdown-quality-lab" / PDF_MODEL_TRAINING_REL / "models",
            repo_root.parent / "markitdown-quality-lab" / PDF_MODEL_TRAINING_REL / "models",
            repo_root / ".external" / "layout_model" / "models",
        ]
    )


def default_manifest_path(repo_root: Path = REPO_ROOT, layout_lab_root: Path | None = None) -> Path:
    if LAYOUT_LAB_ROOT.is_dir():
        candidate = LAYOUT_LAB_ROOT / "manifest.tsv"
        if candidate.exists():
            return candidate
    if layout_lab_root:
        candidate = layout_lab_root / "manifest.tsv"
        if candidate.exists():
            return candidate
    return repo_root / "samples" / "pdf_layout_classifier" / "manifest.tsv"


def default_feature_dir(layout_lab_root: Path | None, repo_root: Path = REPO_ROOT) -> Path:
    if LAYOUT_LAB_ROOT.is_dir():
        return LAYOUT_LAB_ROOT / "evaluation" / "local_eval" / "features" / "raw"
    if layout_lab_root:
        return layout_lab_root / "evaluation" / "local_eval" / "features" / "raw"
    return repo_root / ".tmp" / "pdf_model_training" / "features"


def default_eval_output_dir(layout_lab_root: Path | None, repo_root: Path = REPO_ROOT) -> Path:
    if LAYOUT_LAB_ROOT.is_dir():
        return LAYOUT_LAB_ROOT / "evaluation" / "local_eval" / "eval"
    if layout_lab_root:
        return layout_lab_root / "evaluation" / "local_eval" / "eval"
    return repo_root / ".external" / "layout_model" / "eval"


def default_model_output_path(
    layout_lab_root: Path | None,
    model_root: Path | None,
    repo_root: Path = REPO_ROOT,
    name: str = "pdf_layout_linear.json",
) -> Path:
    if LAYOUT_LAB_ROOT.is_dir():
        return (LAYOUT_LAB_ROOT / "models" / name)
    if model_root:
        return model_root / name
    if layout_lab_root:
        return layout_lab_root / "models" / name
    return repo_root / ".tmp" / "pdf_model_training" / "models" / name


def default_local_eval_model_path(
    layout_lab_root: Path | None,
    model_root: Path | None,
    repo_root: Path = REPO_ROOT,
) -> Path:
    if LAYOUT_LAB_ROOT.is_dir():
        return LAYOUT_LAB_ROOT / "models" / "pdf_layout_linear_local_eval.json"
    if model_root:
        return model_root / "pdf_layout_linear_local_eval.json"
    if layout_lab_root:
        return layout_lab_root / "models" / "pdf_layout_linear_local_eval.json"
    return repo_root / ".external" / "layout_model" / "models" / "pdf_layout_linear_local_eval.json"


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

    candidates: list[Path] = []
    if corpus_root is not None:
        if raw.startswith(LEGACY_CORPUS_PREFIX):
            candidates.append(corpus_root / raw[len(LEGACY_CORPUS_PREFIX) :])
        else:
            candidates.append(corpus_root / raw)
    candidates.extend(legacy_layout_model_candidates(raw, layout_lab_root))
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

    candidates: list[Path] = []
    candidates.extend(legacy_layout_model_candidates(raw, layout_lab_root))
    if layout_lab_root is not None:
        if raw.startswith(LEGACY_LAYOUT_LAB_PREFIX):
            candidates.append(layout_lab_root / raw[len(LEGACY_LAYOUT_LAB_PREFIX) :])
        else:
            candidates.append(layout_lab_root / raw)
    for candidate in _dedupe_paths(candidates):
        if candidate.exists():
            return candidate.resolve()
    return None
