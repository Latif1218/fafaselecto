"""
Postulae CV Generator - Production Core Module

Clean, stateless CV generation engine for elite one-page CVs.
Optimized for finance, consulting, and selective roles.

By default generates BOTH FR and EN.
Supports PHASE 1 (FR only, fast) and PHASE 2 (EN, deferred) for SaaS optimization.

Public API:
    - generate_cv_from_pdf(): Generate CV from PDF (default: FR + EN, optional: selective)
    - generate_cv_from_data(): Generate CV from structured data (default: FR + EN, optional: selective)
    - generate_cv_phase1_from_pdf(): PHASE 1 - FR only (fast, ~1-2 min)
    - generate_cv_phase2_from_pdf(): PHASE 2 - EN only (deferred, background)
    - CVContent: Data model for structured input
    - CVGenerationResult: Generation output with PDF/DOCX bytes

PFR Logic (Performance Optimized - Single Pass):
    - < 70%: BLOCK generation
    - 70-90%: SINGLE enrichment pass (no retries)
    - 90-97%: ACCEPT (target range)
    - > 97%: SINGLE trimming pass (no retries)
    - Accept results even if slightly outside [90-97] to maintain 1-2 min generation

Two-Phase Generation Example (SaaS optimization):
    >>> from app import generate_cv_phase1_from_pdf, generate_cv_phase2_from_pdf
    >>> with open("resume.pdf", "rb") as f:
    ...     pdf_bytes = f.read()
    >>>
    >>> # PHASE 1: FR only (fast, show to user immediately)
    >>> phase1 = generate_cv_phase1_from_pdf(pdf_bytes, domain="finance")
    >>> pdf_fr = phase1["fr"].pdf_bytes
    >>>
    >>> # PHASE 2: EN + DOCX (background, trigger asynchronously)
    >>> phase2 = generate_cv_phase2_from_pdf(pdf_bytes, domain="finance")
    >>> pdf_en = phase2["en"].pdf_bytes

Standard Example (both languages at once):
    >>> from app import generate_cv_from_pdf
    >>> with open("resume.pdf", "rb") as f:
    ...     results = generate_cv_from_pdf(f.read(), domain="finance")
    >>> pdf_fr = results["fr"].pdf_bytes
    >>> pdf_en = results["en"].pdf_bytes
"""

from apps.ai.app.generator import (
    generate_cv_from_pdf,
    generate_cv_from_data,
    generate_cv_phase1_from_pdf,
    generate_cv_phase2_from_pdf,
    CVGenerator,
)
from .models import CVContent, CVGenerationResult, PageFillMetrics
from .density import DensityCalculator

__version__ = "2.3.0"
__author__ = "Postulae"

__all__ = [
    # Main functions (default: both FR and EN, optional: selective)
    "generate_cv_from_pdf",
    "generate_cv_from_data",

    # Phase 1 & 2 functions (SaaS optimization)
    "generate_cv_phase1_from_pdf",  # FR only (fast)
    "generate_cv_phase2_from_pdf",  # EN only (deferred)

    # Classes
    "CVGenerator",
    "DensityCalculator",

    # Models
    "CVContent",
    "CVGenerationResult",
    "PageFillMetrics",
]
