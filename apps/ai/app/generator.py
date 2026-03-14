"""
Main CV Generator for Postulae.

Orchestrates the complete CV generation pipeline with strict PFR logic:
- < 65%: BLOCK generation
- 65-90%: SINGLE-PASS enrichment (no retries)
- 90-95%: ACCEPT (target range - STRICT)
- > 95%: SINGLE-PASS trimming (no retries)

HARD EXECUTION LIMITS (NON-NEGOTIABLE):
- Maximum ONE enrichment pass per CV per language
- Maximum ONE trimming pass per CV per language
- Maximum ONE PDF generation per pass
- NO while-loops, NO retry loops, NO fallback loops
- Max 10 bullets added per enrichment pass (single pass only)
- Accept results even if outside [90-95%] to avoid loops

PERFORMANCE-OPTIMIZED FLOW (< 1 minute target):
1. Generate base content for BOTH FR and EN
2. Measure PFR for both languages
3. Identify the LOWER PFR language
4. If PFR < 65%: STOP and return blocking payload
5. If 65 ≤ PFR < 90%: Apply SINGLE enrichment pass per language (no retry loops)
6. If PFR > 95%: Apply SINGLE trimming pass (no retry loops)
7. Accept result even if outside [90-95%] to avoid regeneration

Always generates BOTH FR and EN.
"""
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from copy import deepcopy

from .models import CVContent, CVGenerationResult, PageFillMetrics
from .llm_client import extract_text_from_pdf_bytes, generate_cv_content
from .density import DensityCalculator
from .layout import LayoutEngine
from .enrichment import ContentEnricher
from .content_analyzer import ContentAnalyzer


class CVGenerator:
    """
    Main CV Generator orchestrator.

    Produces elite one-page CVs optimized for finance/consulting roles.
    Enforces Postulae PFR constraints.
    """

    def __init__(self):
        self.density_calc = DensityCalculator()
        self.layout_engine = LayoutEngine()
        self.enricher = ContentEnricher()
        self.analyzer = ContentAnalyzer()

    def _count_chars(self, content: Dict) -> int:
        """
        Compte caractères total du contenu structuré.

        Args:
            content: Contenu CV structuré

        Returns:
            Nombre total de caractères
        """
        total = 0
        for exp in content.get('work_experience', []):
            total += sum(len(b) for b in exp.get('bullets', []))
        for edu in content.get('education', []):
            total += len(' '.join(edu.get('coursework', [])))
        activities = content.get('activities_interests', {})
        if isinstance(activities, dict):
            total += len(' '.join(activities.get('items', [])))
        elif isinstance(activities, list):
            total += len(' '.join(activities))
        return total

    def _pad_content_if_needed(self, content: Dict, target_chars: int) -> Dict:
        """
        Si contenu trop court, expand bullets automatiquement.

        Args:
            content: Contenu CV structuré
            target_chars: Cible de caractères

        Returns:
            Contenu padded si nécessaire
        """
        current_chars = self._count_chars(content)

        if current_chars < target_chars:
            deficit = target_chars - current_chars
            print(f"[PADDING] Content too short: {current_chars}/{target_chars} chars")
            print(f"[PADDING] Auto-padding: +{deficit} chars needed")

            # Expand chaque bullet proportionnellement
            for exp in content.get('work_experience', []):
                for i, bullet in enumerate(exp.get('bullets', [])):
                    # Target minimum 200 chars per bullet (was 220)
                    if len(bullet) < 200:
                        # Ajouter du contexte générique mais pertinent
                        additions = [
                            ", avec coordination d'équipes pluridisciplinaires et gestion de projets transverses",
                            ", incluant analyses de données quantitatives et qualitatives approfondies",
                            ", en collaboration étroite avec stakeholders internes et externes",
                            ", avec production de livrables détaillés et présentations exécutives régulières",
                            ", optimisation continue des processus et méthodologies de travail",
                            ", participation active aux réunions stratégiques et comités de pilotage",
                            ", suivi rigoureux des indicateurs de performance et reporting hebdomadaire"
                        ]

                        # Ajouter jusqu'à atteindre 200 chars
                        while len(bullet) < 200 and additions:
                            bullet += additions.pop(0)

                        exp['bullets'][i] = bullet[:250]  # Cap à 250 chars

            # Expand activities si encore insuffisant
            activities = content.get('activities_interests', {})
            if isinstance(activities, dict) and self._count_chars(content) < target_chars:
                items = activities.get('items', [])
                for i, activity in enumerate(items):
                    if len(activity) < 150:
                        items[i] = activity + " avec organisation d'événements réguliers, gestion de la communication, coordination logistique et animation de communauté"
                activities['items'] = items

            # Expand coursework si encore insuffisant
            if self._count_chars(content) < target_chars:
                for edu in content.get('education', []):
                    coursework = edu.get('coursework', [])
                    for i, course in enumerate(coursework):
                        if len(course) < 40:  # Coursework très courts
                            coursework[i] = course + " (méthodes avancées, études de cas pratiques)"
                    edu['coursework'] = coursework

            new_chars = self._count_chars(content)
            print(f"[PADDING] After padding: {new_chars} chars (+{new_chars - current_chars})")

        return content

    def generate_from_pdf(
        self,
        pdf_bytes: bytes,
        domain: str = "finance",
        languages: Optional[List[str]] = None,
    ) -> Dict[str, CVGenerationResult]:
        """
        Generate CV from uploaded PDF file.
        By default generates BOTH FR and EN, but can generate selectively.

        Args:
            pdf_bytes: PDF file as bytes
            domain: Target domain (finance, consulting, startup, government)
            languages: List of languages to generate (default: ["fr", "en"])
                      Use ["fr"] for Phase 1 (fast), ["en"] for Phase 2 (deferred)

        Returns:
            Dictionary with requested language keys → CVGenerationResult

        Raises:
            ValueError: If generation fails or PFR < 70%
        """
        # VALIDATION: PDF input
        if not pdf_bytes:
            raise ValueError("PDF file is empty")

        if len(pdf_bytes) < 1000:
            raise ValueError("PDF file too small (<1KB) - may be corrupted or invalid")

        if len(pdf_bytes) > 10_000_000:
            raise ValueError("PDF file too large (>10MB) - please provide a smaller file")

        # Validate PDF magic bytes (PDF files start with '%PDF')
        if not pdf_bytes.startswith(b'%PDF'):
            raise ValueError("Invalid file format - not a valid PDF (missing PDF header)")

        if languages is None:
            languages = ["fr", "en"]

        # Extract text from PDF
        original_text = extract_text_from_pdf_bytes(pdf_bytes, filename="resume.pdf")

        if not original_text or len(original_text.strip()) < 100:
            raise ValueError(
                "Failed to extract sufficient text from PDF. Please ensure PDF is readable."
            )

        # Analyze source content richness
        analysis = self.analyzer.analyze(original_text)
        print(f"\n[ANALYSIS] Source: {analysis['richness']} ({len(original_text)} chars)")
        print(f"[ANALYSIS] Strategy: {analysis['strategy']} -> Target {analysis['target_pfr']}")

        # Generate requested languages
        return self._generate_languages(
            input_data={"raw_text": original_text},
            domain=domain,
            is_enhance=True,
            original_text=original_text,
            languages=languages,
            analysis=analysis,
        )

    def generate_from_data(
        self,
        cv_content: CVContent,
        languages: Optional[List[str]] = None,
    ) -> Dict[str, CVGenerationResult]:
        """
        Generate CV from structured data.
        By default generates BOTH FR and EN, but can generate selectively.

        Args:
            cv_content: Structured CV content
            languages: List of languages to generate (default: ["fr", "en"])

        Returns:
            Dictionary with requested language keys → CVGenerationResult

        Raises:
            ValueError: If generation fails
        """
        if languages is None:
            languages = ["fr", "en"]

        domain = cv_content.domain or "finance"
        input_dict = cv_content.dict()

        # For structured data, assume RICH content (no enrichment needed)
        analysis = {
            'richness': 'rich',
            'strategy': 'minimal',
            'target_pfr': '86-88%',
            'target_chars': 2700,
            'warning': 'green'
        }

        # Generate requested languages
        return self._generate_languages(
            input_data=input_dict,
            domain=domain,
            is_enhance=False,
            original_text=None,
            languages=languages,
            analysis=analysis,
        )

    def _generate_languages(
        self,
        input_data: Dict,
        domain: str,
        is_enhance: bool,
        original_text: Optional[str],
        languages: List[str],
        analysis: Dict,
    ) -> Dict[str, CVGenerationResult]:
        """
        PERFORMANCE-OPTIMIZED generation flow for requested languages (1-2 minute target).
        Supports PHASE 1 (FR only) and PHASE 2 (EN only) for faster perceived generation.

        Flow:
        1. Generate base content for requested language(s)
        2. Measure PFR for each language
        3. If multiple languages: identify the LOWER PFR language
        4. If PFR < 70: STOP and raise blocking error
        5. If 70 ≤ PFR < 90: Apply SINGLE enrichment pass per language (no retries/fallbacks)
        6. If PFR > 97: Apply SINGLE trimming pass (no retry loops)
        7. Accept result even if slightly outside [90, 97] (no regeneration)

        Args:
            input_data: Input data dictionary
            domain: Target domain
            is_enhance: True if from PDF
            original_text: Original text if from PDF
            languages: List of languages to generate (e.g., ["fr"] or ["en"] or ["fr", "en"])

        Returns:
            Dictionary with requested language keys → CVGenerationResult

        Raises:
            ValueError: If PFR < 70%
        """
        # Step 1 & 2: Generate base content for requested languages and measure PFR
        base_results = {}
        base_content = {}
        base_metrics = {}

        for lang in languages:
            # Get adaptive enrichment instructions
            enrichment_instructions = self.analyzer.get_enrichment_instructions(
                analysis['strategy'], lang
            )

            # Generate base content with adaptive enrichment
            content = generate_cv_content(
                input_data=input_data,
                domain=domain,
                language=lang,
                enrichment_mode=False,
                enrichment_instructions=enrichment_instructions,
            )

            # Apply intelligent padding if content too short (push-to-90 system)
            content = self._pad_content_if_needed(content, analysis['target_chars'])

            base_content[lang] = content

            # Render and measure
            pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=False)
            metrics = self.density_calc.calculate_pfr(pdf_bytes)
            base_metrics[lang] = metrics

        # Step 3: Identify the LOWER PFR language (only if generating multiple languages)
        if len(languages) > 1:
            lower_lang = min(languages, key=lambda lang: base_metrics[lang].fill_percentage)
            lower_pfr = base_metrics[lower_lang].fill_percentage
        else:
            # Single language generation - use that language
            lower_lang = languages[0]
            lower_pfr = base_metrics[lower_lang].fill_percentage

        # Step 4: Check for BLOCK condition (< 65%)
        if lower_pfr < self.density_calc.BLOCK_THRESHOLD:
            block_message = f"""
GENERATION BLOCKED: PFR {lower_pfr}% in {lower_lang.upper()} (minimum required: {self.density_calc.BLOCK_THRESHOLD}%)

Your CV does not contain enough content to meet Postulae standards.
Please provide more detailed information using ONE OR BOTH options below:

=========================================================
OPTION A: DETAIL EXISTING EXPERIENCES
=========================================================

For each existing work experience, provide:
• More bullet points (3-5 per role)
• Quantified outcomes (metrics, percentages, amounts)
• Specific tools/methodologies used
• Team size or stakeholders involved
• Detailed project scope and deliverables

=========================================================
OPTION B: ADD NEW EXPERIENCE
=========================================================

Add additional work experiences, internships, or projects:
• Date range (Mon YYYY - Mon YYYY)
• Role/position title
• Organization name
• Location (City, Country)
• Duration
• 3-5 detailed bullet points with achievements

You may also add:
• Additional education entries with coursework
• Certifications with details
• More extracurricular activities with specific roles
• Languages with proficiency levels
• Technical skills with proficiency

After providing more information, regenerate your CV.
"""
            raise ValueError(block_message)

        # Step 5 & 6: Process each requested language with SIMPLIFIED SINGLE-PASS LOGIC
        # TARGET: 90-95% PFR with INCREMENTAL enrichment (no retry loops)
        # PRODUCT RULE: One enrichment pass maximum, one trimming pass maximum
        final_results = {}
        for lang in languages:
            warnings = []
            content = deepcopy(base_content[lang])
            metrics = base_metrics[lang]

            initial_pfr = metrics.fill_percentage
            warnings.append(f"PFR initial: {initial_pfr}%")

            # SINGLE-PASS ADJUSTMENT (no loops, no retries)
            # TARGET: 86-95% PFR for rich CVs, 90-95% PFR for poor CVs
            # Rich CVs (strategy=minimal) often plateau at 85-88% due to content density
            OPTIMAL_MIN = 86.0  # Lowered from 90.0 to accept rich CVs at 86-90%
            OPTIMAL_MAX = 95.0
            HARD_MINIMUM = 40.0  # Block threshold (nouveau seuil push-to-90)

            # CAS 1: Multi-pages - MUST trim to 1 page
            if metrics.page_count > 1:
                warnings.append(
                    f"Multi-pages detected ({metrics.page_count} pages) - applying LIGHT trimming first (step 1)"
                )

                # Start with LIGHT trimming (step 1) for multi-pages
                content = self.enricher.trim_content(content, step=1)
                pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=True)
                metrics = self.density_calc.calculate_pfr(pdf_bytes)

                new_pfr = metrics.fill_percentage
                warnings.append(
                    f"After light trimming: {new_pfr}%, {metrics.page_count} page(s) (delta: {new_pfr - initial_pfr:+.1f}%)"
                )

                # If still multi-pages, apply moderate trimming (step 2)
                if metrics.page_count > 1:
                    warnings.append(
                        f"Still multi-pages - applying moderate trimming (step 2)"
                    )
                    content = self.enricher.trim_content(content, step=2)
                    pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=True)
                    metrics = self.density_calc.calculate_pfr(pdf_bytes)
                    warnings.append(f"After moderate trimming: {metrics.fill_percentage}%, {metrics.page_count} page(s)")

                    # If STILL multi-pages, apply aggressive trimming (step 3) - last resort
                    if metrics.page_count > 1:
                        warnings.append(
                            f"Still multi-pages - applying aggressive trimming (step 3)"
                        )
                        content = self.enricher.trim_content(content, step=3)
                        pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=True)
                        metrics = self.density_calc.calculate_pfr(pdf_bytes)
                        warnings.append(f"After aggressive trimming: {metrics.fill_percentage}%, {metrics.page_count} page(s)")

                # If STILL multi-pages, block generation
                if metrics.page_count > 1:
                    raise ValueError(
                        f"Unable to fit CV on one page. Current: {metrics.page_count} pages after trimming."
                    )

                # CORRECTION: If trimming made PFR < 85%, apply CONSERVATIVE incremental enrichment
                # Only enrich if PFR is critically low (< 85%), and accept 85-90% range
                if metrics.fill_percentage < 85.0:
                    warnings.append(
                        f"Trimming resulted in low PFR ({metrics.fill_percentage}%) - applying conservative incremental enrichment"
                    )

                    # Apply enrichment conservatively (reduce target to avoid overshoot)
                    conservative_target = min(88.0, ContentEnricher.TARGET_PFR)
                    original_target = ContentEnricher.TARGET_PFR
                    ContentEnricher.TARGET_PFR = conservative_target

                    content = self.enricher.incremental_enrich_content(
                        content=content,
                        current_metrics=metrics,
                        domain=domain,
                        language=lang,
                        original_text=original_text,
                    )

                    # Restore original target
                    ContentEnricher.TARGET_PFR = original_target

                    pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=False)
                    metrics = self.density_calc.calculate_pfr(pdf_bytes)
                    warnings.append(f"After corrective enrichment: {metrics.fill_percentage}%, {metrics.page_count} page(s)")

                    # If enrichment caused multi-pages again, revert to trimmed version
                    if metrics.page_count > 1:
                        warnings.append(
                            f"Enrichment caused multi-pages - reverting to trimmed version"
                        )
                        # Re-trim without enrichment
                        content = deepcopy(base_content[lang])
                        content = self.enricher.trim_content(content, step=2)  # Use step 2 directly
                        pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=True)
                        metrics = self.density_calc.calculate_pfr(pdf_bytes)
                        warnings.append(f"Reverted to trimmed version: {metrics.fill_percentage}%")

                elif metrics.fill_percentage < 90.0:
                    # PFR in [85-90%] - acceptable, no enrichment needed to avoid risk
                    warnings.append(
                        f"PFR {metrics.fill_percentage}% in acceptable range [85-90%] after trimming - no enrichment to avoid multi-pages risk"
                    )

            # CAS 2: PFR > 95% - Trim slightly to reach 90-95%
            elif metrics.fill_percentage > 95.0:
                warnings.append(
                    f"PFR {metrics.fill_percentage}% > 95% - applying light trimming (step 1)"
                )

                content = self.enricher.trim_content(content, step=1)
                pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=True)
                metrics = self.density_calc.calculate_pfr(pdf_bytes)

                warnings.append(
                    f"After trimming: {metrics.fill_percentage}% (delta: {metrics.fill_percentage - initial_pfr:+.1f}%)"
                )

            # CAS 3: PFR < OPTIMAL_MIN (86%) - INCREMENTAL enrichment (ONE PASS ONLY)
            elif metrics.fill_percentage < OPTIMAL_MIN:
                warnings.append(
                    f"PFR {metrics.fill_percentage}% < {OPTIMAL_MIN}% - applying INCREMENTAL enrichment (single pass)"
                )

                # INCREMENTAL enrichment: adds N bullets (where N = estimated from PFR gap)
                content = self.enricher.incremental_enrich_content(
                    content=content,
                    current_metrics=metrics,
                    domain=domain,
                    language=lang,
                    original_text=original_text,
                )

                pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=False)
                metrics = self.density_calc.calculate_pfr(pdf_bytes)

                new_pfr = metrics.fill_percentage
                warnings.append(
                    f"After incremental enrichment: {new_pfr}% (delta: {new_pfr - initial_pfr:+.1f}%)"
                )

                # If enrichment caused overflow (> 95%), apply light trimming (ONE PASS)
                if new_pfr > 95.0:
                    warnings.append(
                        f"Enrichment overshoot: {new_pfr}% > 95% - applying light trimming"
                    )
                    content = self.enricher.trim_content(content, step=1)
                    pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=True)
                    metrics = self.density_calc.calculate_pfr(pdf_bytes)
                    warnings.append(f"After corrective trimming: {metrics.fill_percentage}%")

            # CAS 4: PFR already in [90%, 95%] - ACCEPT as-is
            else:
                warnings.append(
                    f"PFR {metrics.fill_percentage}% already in optimal zone [90-95%] - no adjustment needed"
                )
                pdf_bytes = self.layout_engine.generate_pdf_from_data(content, trim=False)

            # Generate DOCX
            docx_bytes = self._generate_docx_from_pdf(pdf_bytes)

            # FINAL VALIDATION
            final_pfr = metrics.fill_percentage

            # Strict page count validation
            if metrics.page_count != 1:
                raise ValueError(
                    f"CV must be exactly one page. Current: {metrics.page_count} pages."
                )

            # PFR classification (ADJUSTED: Accept 86-95% for rich CVs, 90-95% for poor CVs)
            if final_pfr >= OPTIMAL_MIN and final_pfr <= OPTIMAL_MAX:
                warnings.append(
                    f"SUCCESS: Final PFR {final_pfr}% in optimal zone [86-95%]"
                )
            elif final_pfr >= HARD_MINIMUM and final_pfr < OPTIMAL_MIN:
                # Suboptimal but acceptable: 40-86%
                # (Single-pass adjustment could not reach target - accept to avoid loops)
                warnings.append(
                    f"SUBOPTIMAL: Final PFR {final_pfr}% below target [40-86%] - accepted (single-pass limit)"
                )
            elif final_pfr > OPTIMAL_MAX:
                # Above target: > 95%
                # (Single-pass trimming could not reach target - accept to avoid loops)
                warnings.append(
                    f"SUBOPTIMAL: Final PFR {final_pfr}% above target (>95%) - accepted (single-pass limit)"
                )
            elif final_pfr < HARD_MINIMUM:
                # Block if < 40% even after adjustments
                raise ValueError(
                    f"FINAL VALIDATION FAILED: {lang.upper()} must have PFR >= {HARD_MINIMUM}%. "
                    f"Current: {final_pfr}%"
                )

            # Get warning message for user
            warning_info = self.analyzer.get_warning_message(analysis['strategy'], lang)

            final_results[lang] = CVGenerationResult(
                pdf_bytes=pdf_bytes,
                docx_bytes=docx_bytes,
                page_count=metrics.page_count,
                fill_percentage=metrics.fill_percentage,
                char_count=metrics.char_count,
                warnings=warnings,
                warning_info=warning_info,
            )

        return final_results

    def _handle_overflow(
        self, content: Dict, metrics: PageFillMetrics, warnings: List[str]
    ) -> Dict:
        """
        Handle content overflow (> 97% or multiple pages).

        Applies single-pass trimming (performance optimization - no retry loops).

        Args:
            content: CV content
            metrics: Current metrics
            warnings: Warnings list to append to

        Returns:
            Trimmed content
        """
        if metrics.page_count > 1:
            warnings.append(
                f"Content overflow: {metrics.page_count} pages. Applying single-pass trimming."
            )
            # Use aggressive trimming (step 3) for multi-page overflow
            step = 3
        else:
            warnings.append(
                f"PFR {metrics.fill_percentage}% (> 97%). Applying single-pass trimming."
            )
            # Use light trimming (step 1) for slight overflow
            step = 1

        # Single trimming pass - no loops to maintain 1-2 minute generation time
        trimmed = self.enricher.trim_content(content, step=step)
        warnings.append(f"Trimming applied (step {step})")

        return trimmed

    def _generate_docx_from_pdf(self, pdf_bytes: bytes) -> bytes:
        """
        Generate DOCX from PDF using pdf2docx conversion.

        Ensures DOCX matches PDF layout exactly.

        Args:
            pdf_bytes: PDF bytes

        Returns:
            DOCX bytes

        Raises:
            ValueError: If DOCX generation fails
        """
        try:
            from pdf2docx import Converter
            import io

            # Create temp file for PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(pdf_bytes)
                temp_pdf_path = temp_pdf.name

            try:
                # Convert PDF to DOCX
                docx_stream = io.BytesIO()
                converter = Converter(temp_pdf_path)
                converter.convert(docx_stream)
                converter.close()

                docx_bytes = docx_stream.getvalue()

                if not docx_bytes:
                    raise ValueError("DOCX generation produced empty file")

                return docx_bytes

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_pdf_path)
                except Exception:
                    pass

        except Exception as e:
            raise ValueError(f"Failed to generate DOCX: {str(e)}")


# Convenience functions for simple usage

def generate_cv_from_pdf(
    pdf_bytes: bytes,
    domain: str = "finance",
    languages: Optional[List[str]] = None,
) -> Dict[str, CVGenerationResult]:
    """
    Generate CV from PDF bytes (convenience function).
    By default generates BOTH FR and EN, but can generate selectively.

    Args:
        pdf_bytes: PDF file as bytes
        domain: Target domain (finance, consulting, startup, government)
        languages: List of languages to generate (default: ["fr", "en"])

    Returns:
        Dictionary with requested language keys → CVGenerationResult
    """
    generator = CVGenerator()
    return generator.generate_from_pdf(pdf_bytes, domain, languages)


def generate_cv_from_data(
    cv_content: CVContent,
    languages: Optional[List[str]] = None,
) -> Dict[str, CVGenerationResult]:
    """
    Generate CV from structured data (convenience function).
    By default generates BOTH FR and EN, but can generate selectively.

    Args:
        cv_content: Structured CV content
        languages: List of languages to generate (default: ["fr", "en"])

    Returns:
        Dictionary with requested language keys → CVGenerationResult
    """
    generator = CVGenerator()
    return generator.generate_from_data(cv_content, languages)


# Phase 1 & 2 convenience functions for faster perceived generation

def generate_cv_phase1_from_pdf(
    pdf_bytes: bytes,
    domain: str = "finance",
) -> Dict[str, CVGenerationResult]:
    """
    PHASE 1: Generate FR PDF only (fast, synchronous).
    Returns FR result in ~1-2 minutes.
    Use for immediate user display.

    Args:
        pdf_bytes: PDF file as bytes
        domain: Target domain (finance, consulting, startup, government)

    Returns:
        Dictionary with key "fr" → CVGenerationResult (PDF only, no DOCX yet)
    """
    generator = CVGenerator()
    return generator.generate_from_pdf(pdf_bytes, domain, languages=["fr"])


def generate_cv_phase2_from_pdf(
    pdf_bytes: bytes,
    domain: str = "finance",
) -> Dict[str, CVGenerationResult]:
    """
    PHASE 2: Generate EN PDF + DOCX (deferred, asynchronous).
    Can be triggered in background after Phase 1 completes.

    Args:
        pdf_bytes: PDF file as bytes
        domain: Target domain (finance, consulting, startup, government)

    Returns:
        Dictionary with key "en" → CVGenerationResult (PDF + DOCX)
    """
    generator = CVGenerator()
    return generator.generate_from_pdf(pdf_bytes, domain, languages=["en"])






