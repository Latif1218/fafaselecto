"""
Page Fill Rate (PFR) calculation for Postulae CV Generator.

Measures content density to ensure CVs meet Postulae standards.
Critical for Postulae's product constraint: exactly one page, optimal density.
"""
import io
from typing import Tuple

import pdfplumber

from .models import PageFillMetrics


class DensityCalculator:
    """Calculate page fill rate from PDF bytes."""

    # PFR thresholds (Postulae product constraints - UPDATED 12/03/2026 V3)
    BLOCK_THRESHOLD = 40.0                  # Below this: BLOCK generation
    ENRICHMENT_THRESHOLD = 90.0             # 90-98%: Target range (realistic with 2-line bullets)
    ACCEPTANCE_RANGE = [90.0, 98.0]        # Acceptable PFR range (PRODUCTION: 90-98%)
    TRIM_THRESHOLD = 98.0                  # Above this: Trim (risk of overflow to 2 pages)
    ENRICHMENT_TARGET = 94.0                # Target when enrichment needed (centre zone optimale 90-98%)

    MINIMUM_CHARS = 2200  # Minimum character count

    @staticmethod
    def calculate_pfr(pdf_bytes: bytes) -> PageFillMetrics:
        """
        Calculate Page Fill Rate from PDF bytes.

        Args:
            pdf_bytes: PDF file as bytes

        Returns:
            PageFillMetrics with page count, fill %, character count, etc.

        Raises:
            ValueError: If PDF cannot be analyzed
        """
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                page_count = len(pdf.pages)

                if page_count == 0:
                    raise ValueError("PDF has no pages")

                if page_count == 1:
                    page = pdf.pages[0]
                    text_content = page.extract_text() or ""
                    words = page.extract_words()

                    if words:
                        # Calculate vertical text coverage
                        text_top = min(word["top"] for word in words)
                        text_bottom = max(word["bottom"] for word in words)
                        text_height = text_bottom - text_top
                        page_height = page.height
                        fill_percentage = (text_height / page_height) * 100
                    else:
                        text_height = 0
                        page_height = page.height if page else 0
                        fill_percentage = 0.0

                    char_count = len(text_content.strip())

                    return PageFillMetrics(
                        page_count=1,
                        fill_percentage=round(fill_percentage, 1),
                        char_count=char_count,
                        text_height=text_height,
                        page_height=page_height,
                    )
                else:
                    # Multiple pages - assume full fill, count total chars
                    total_text = ""
                    for page in pdf.pages:
                        total_text += page.extract_text() or ""

                    return PageFillMetrics(
                        page_count=page_count,
                        fill_percentage=100.0,  # Assume full if multiple pages
                        char_count=len(total_text.strip()),
                        text_height=None,
                        page_height=None,
                    )

        except Exception as e:
            # Fallback to conservative estimates
            return PageFillMetrics(
                page_count=1,
                fill_percentage=0.0,
                char_count=0,
                text_height=None,
                page_height=None,
            )

    @classmethod
    def is_acceptable(cls, metrics: PageFillMetrics) -> bool:
        """
        Check if page fill metrics meet Postulae standards.

        Args:
            metrics: Page fill metrics

        Returns:
            True if acceptable (1 page, 90-98% fill)
        """
        return (
            metrics.page_count == 1
            and cls.ACCEPTANCE_RANGE[0] <= metrics.fill_percentage <= cls.ACCEPTANCE_RANGE[1]
            and metrics.char_count >= cls.MINIMUM_CHARS
        )

    @classmethod
    def needs_aggressive_enrichment(cls, metrics: PageFillMetrics) -> bool:
        """
        Check if content needs aggressive enrichment (40-90% range).

        Args:
            metrics: Page fill metrics

        Returns:
            True if aggressive enrichment is needed (40% ≤ PFR < 90%)
        """
        return (
            metrics.page_count == 1
            and metrics.fill_percentage >= cls.BLOCK_THRESHOLD
            and metrics.fill_percentage < cls.ENRICHMENT_THRESHOLD
        )

    @classmethod
    def needs_enrichment(cls, metrics: PageFillMetrics) -> bool:
        """
        Check if content needs enrichment (below 90%).

        Args:
            metrics: Page fill metrics

        Returns:
            True if enrichment is needed (PFR < 90%)
        """
        return (
            metrics.page_count == 1
            and metrics.fill_percentage < cls.ENRICHMENT_THRESHOLD
            and metrics.fill_percentage >= cls.BLOCK_THRESHOLD
        )

    @classmethod
    def needs_trimming(cls, metrics: PageFillMetrics) -> bool:
        """
        Check if content needs trimming (overflow or > 98%).

        Args:
            metrics: Page fill metrics

        Returns:
            True if trimming is needed
        """
        return metrics.page_count > 1 or metrics.fill_percentage > cls.TRIM_THRESHOLD

    @classmethod
    def is_blocked(cls, metrics: PageFillMetrics) -> bool:
        """
        Check if generation should be blocked (< 40% PFR).

        Args:
            metrics: Page fill metrics

        Returns:
            True if PFR < 40% (blocked)
        """
        return (
            metrics.page_count == 1
            and metrics.fill_percentage < cls.BLOCK_THRESHOLD
        )

    @classmethod
    def get_status_message(cls, metrics: PageFillMetrics) -> str:
        """
        Get human-readable status message for metrics.

        Args:
            metrics: Page fill metrics

        Returns:
            Status message
        """
        if metrics.page_count > 1:
            return f"OVERFLOW: {metrics.page_count} pages. Content must be trimmed."

        if cls.is_blocked(metrics):
            return f"BLOCKED: {metrics.fill_percentage}% fill (< 40%). More content required from user."

        if cls.needs_aggressive_enrichment(metrics):
            return f"ENRICHMENT REQUIRED: {metrics.fill_percentage}% fill (40-90%). Will enrich to ~94%."

        if cls.is_acceptable(metrics):
            return f"ACCEPTED: {metrics.fill_percentage}% fill, {metrics.char_count} chars."

        if metrics.fill_percentage > cls.TRIM_THRESHOLD:
            return f"TRIM: {metrics.fill_percentage}% fill (> 98%). Will trim to avoid overflow."

        return f"Status: {metrics.fill_percentage}% fill, {metrics.char_count} chars."
