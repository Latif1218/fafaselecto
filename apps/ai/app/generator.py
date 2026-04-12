
from .logger import get_logger
logger = get_logger(__name__)

"""
Main CV Generator for Postulae.

Orchestrates the complete CV generation pipeline with strict PFR logic:
- < 40%: BLOCK generation
- 40-90%: SINGLE-PASS enrichment (no retries)
- 86-98%: ACCEPT (target range - EXTENDED for dense CVs)
- > 98%: SINGLE-PASS trimming (no retries)

HARD EXECUTION LIMITS (NON-NEGOTIABLE):
- Maximum ONE enrichment pass per CV per language
- Maximum ONE trimming pass per CV per language
- Maximum ONE PDF generation per pass
- NO while-loops, NO retry loops, NO fallback loops
- Max 10 bullets added per enrichment pass (single pass only)
- Accept results even if outside [86-98%] to avoid loops

PERFORMANCE-OPTIMIZED FLOW (< 1 minute target):
1. Generate base content for BOTH FR and EN
2. Measure PFR for both languages
3. Identify the LOWER PFR language
4. If PFR < 40%: STOP and return blocking payload
5. If 40 ≤ PFR < 90%: Apply SINGLE enrichment pass per language (no retry loops)
6. If PFR > 98%: Apply SINGLE trimming pass (no retry loops)
7. Accept result even if outside [86-98%] to avoid regeneration

Always generates BOTH FR and EN.
"""
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from copy import deepcopy

from .models import CVContent, CVGenerationResult, PageFillMetrics
from .llm_client import extract_text_from_pdf_bytes  # OpenAI Vision (extraction only)
from .llm_client_anthropic import generate_cv_content_claude, translate_cv_content_claude, MODEL_SONNET, MODEL_HAIKU  # Claude (structuration + traduction)
from .density import DensityCalculator
from .layout_legacy import LayoutEngine  # LEGACY: Use layout_playwright in production
from .layout_playwright import generate_pdf_from_data as generate_pdf_playwright  # Playwright (PDF production)
from .enrichment import ContentEnricher
from .content_analyzer import ContentAnalyzer
from pathlib import Path

# Feature flag: Enable hybrid stack (Claude + Playwright)
USE_HYBRID_STACK = True  # Set to False to use legacy OpenAI + xhtml2pdf


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

        # Load system prompt for Claude (reused across calls)
        if USE_HYBRID_STACK:
            prompts_dir = Path(__file__).parent / "prompts"
            self.base_system_prompt = (prompts_dir / "base_system.txt").read_text(encoding='utf-8')

    def _generate_pdf(self, content: Dict, trim: bool = False, language: str = "fr") -> bytes:
        """
        Generate PDF using configured engine (Playwright or xhtml2pdf).

        Args:
            content: CV content dictionary
            trim: Apply trimming if True
            language: Language for rendering ("fr" or "en")

        Returns:
            PDF bytes
        """
        if USE_HYBRID_STACK:
            return generate_pdf_playwright(content, trim=trim, language=language)
        else:
            return LayoutEngine.generate_pdf_from_data(content, trim=trim, language=language)

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
        SÉCURITÉ: Désactive padding si >3200 chars (risque débordement).

        Args:
            content: Contenu CV structuré
            target_chars: Cible de caractères

        Returns:
            Contenu padded si nécessaire
        """
        current_chars = self._count_chars(content)

        # SÉCURITÉ: Ne pas padder si déjà >3200 chars (risque débordement 2 pages)
        if current_chars >= 3200:
            logger.info("SKIPPED - Content {current_chars} chars (>3200, overflow risk)", extra={"tag": "PADDING"})
            return content

        if current_chars < target_chars:
            deficit = target_chars - current_chars
            logger.info("Content too short: {current_chars}/{target_chars} chars", extra={"tag": "PADDING"})
            logger.info("Auto-padding: +{deficit} chars needed", extra={"tag": "PADDING"})

            # Expand chaque bullet proportionnellement (max 2 lignes = 140 chars)
            for exp in content.get('work_experience', []):
                for i, bullet in enumerate(exp.get('bullets', [])):
                    # Target minimum 100 chars per bullet (max 140 chars = 2 lignes)
                    if len(bullet) < 100:
                        # Ajouter du contexte générique mais pertinent
                        additions = [
                            ", avec coordination d'équipes pluridisciplinaires",
                            ", incluant analyses de données approfondies",
                            ", en collaboration avec stakeholders",
                            ", avec production de livrables détaillés",
                            ", optimisation continue des processus"
                        ]

                        # Ajouter jusqu'à atteindre 100 chars
                        while len(bullet) < 100 and additions:
                            bullet += additions.pop(0)

                        exp['bullets'][i] = bullet[:140]  # Cap à 140 chars MAX (2 lignes)

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
            logger.info("After padding: {new_chars} chars (+{new_chars - current_chars})", extra={"tag": "PADDING"})

        return content

    def _enforce_bullet_limit(self, content: Dict) -> Dict:
        """
        Force tous les bullets à max 135 chars (sécurité 1 page + PFR 88%+).

        Args:
            content: Contenu CV structuré

        Returns:
            Contenu avec bullets limités
        """
        # Trim work experience bullets à 135 chars (compromis PFR/overflow)
        for exp in content.get('work_experience', []):
            bullets = exp.get('bullets', [])
            exp['bullets'] = [b[:135] if len(b) > 135 else b for b in bullets]

        # Trim education bullets (if any)
        for edu in content.get('education', []):
            if 'bullets' in edu:
                bullets = edu.get('bullets', [])
                edu['bullets'] = [b[:135] if len(b) > 135 else b for b in bullets]

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
            Dictionary with requested language keys -> CVGenerationResult

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
        logger.info(f"\n[ANALYSIS] Source: {analysis['richness']} ({len(original_text)} chars)")
        logger.info("Strategy: {analysis['strategy']} -> Target {analysis['target_pfr']}", extra={"tag": "ANALYSIS"})

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
            Dictionary with requested language keys -> CVGenerationResult

        Raises:
            ValueError: If generation fails
        """
        if languages is None:
            languages = ["fr", "en"]

        domain = cv_content.domain
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
        4. If PFR < 40: STOP and raise blocking error
        5. If 40 ≤ PFR < 90: Apply SINGLE enrichment pass per language (no retries/fallbacks)
        6. If PFR > 98: Apply SINGLE trimming pass (no retry loops)
        7. Accept result even if slightly outside [86, 98] (no regeneration)

        Args:
            input_data: Input data dictionary
            domain: Target domain
            is_enhance: True if from PDF
            original_text: Original text if from PDF
            languages: List of languages to generate (e.g., ["fr"] or ["en"] or ["fr", "en"])

        Returns:
            Dictionary with requested language keys -> CVGenerationResult

        Raises:
            ValueError: If PFR < 70%
        """
        # Step 1 & 2: Generate base content for requested languages and measure PFR
        base_results = {}
        base_content = {}
        base_metrics = {}

        if USE_HYBRID_STACK and len(languages) == 2 and "fr" in languages and "en" in languages:
            # OPTIMIZED HYBRID STACK: Generate FR with Sonnet, then translate to EN with Haiku
            logger.info("\n[HYBRID STACK OPTIMIZED] FR (Sonnet) -> EN (Haiku translation)")

            # Generate FR first with Sonnet
            enrichment_instructions_fr = self.analyzer.get_enrichment_instructions(
                analysis['strategy'], "fr"
            )

            content_fr = generate_cv_content_claude(
                input_data=input_data,
                system_prompt=self.base_system_prompt,
                domain=domain,
                language="fr",
                model=MODEL_SONNET,
                enrichment_instructions=enrichment_instructions_fr,
            )

            # Apply intelligent padding if content too short (SKIP for aggressive/ultra_aggressive)
            if analysis['strategy'] not in ['aggressive', 'ultra_aggressive']:
                content_fr = self._pad_content_if_needed(content_fr, analysis['target_chars'])
            base_content["fr"] = content_fr

            # Translate FR -> EN with Haiku (ultra fast, -89% cost)
            logger.info("\n[HYBRID STACK] Translating FR -> EN with Claude Haiku 3.5")
            content_en = translate_cv_content_claude(
                cv_content=content_fr,
                source_language="fr",
                target_language="en",
                model=MODEL_HAIKU,
            )

            base_content["en"] = content_en

            # Measure PFR for both languages
            for lang in ["fr", "en"]:
                pdf_bytes = self._generate_pdf(base_content[lang], trim=False, language=lang)
                metrics = self.density_calc.calculate_pfr(pdf_bytes)
                base_metrics[lang] = metrics

        else:
            # STANDARD GENERATION: Generate each language independently
            for lang in languages:
                # Get adaptive enrichment instructions
                enrichment_instructions = self.analyzer.get_enrichment_instructions(
                    analysis['strategy'], lang
                )

                # Generate base content with adaptive enrichment
                if USE_HYBRID_STACK:
                    # HYBRID STACK: Claude Sonnet for structuration
                    logger.info(f"\n[HYBRID STACK] Using Claude Sonnet 3.5 for {lang.upper()} structuration")
                    content = generate_cv_content_claude(
                        input_data=input_data,
                        system_prompt=self.base_system_prompt,
                        domain=domain,
                        language=lang,
                        model=MODEL_SONNET,
                        enrichment_instructions=enrichment_instructions,
                    )
                else:
                    # LEGACY STACK: OpenAI GPT-4o
                    from app.llm_client import generate_cv_content
                    content = generate_cv_content(
                        input_data=input_data,
                        domain=domain,
                        language=lang,
                        enrichment_mode=False,
                        enrichment_instructions=enrichment_instructions,
                    )

                # Apply intelligent padding if content too short (SKIP for aggressive/ultra_aggressive)
                if analysis['strategy'] not in ['aggressive', 'ultra_aggressive']:
                    content = self._pad_content_if_needed(content, analysis['target_chars'])

                # PREVENTIVE: Detect overflow risk BEFORE layout
                # Seuil ajusté pour garantir 1 page + PFR 88%+
                content_chars = self._count_chars(content)
                avg_bullet_len = self._get_avg_bullet_length(content)

                # Risque CRITIQUE : >3300 chars (débordement probable)
                if content_chars > 3300:
                    logger.info("Content {content_chars} chars > 3300 - applying smart reduction", extra={"tag": "OVERFLOW PREVENTION"})
                    content = self._prevent_overflow_smart(content)
                # Risque modéré : >3100 chars ET bullets très longs (>140 chars avg)
                elif content_chars > 3100 and avg_bullet_len > 140:
                    logger.info("Content {content_chars} chars + bullets {avg_bullet_len:.0f} chars avg - applying smart reduction", extra={"tag": "OVERFLOW PREVENTION"})
                    content = self._prevent_overflow_smart(content)

                # CRITICAL: Enforce 130 char limit on ALL bullets (2 lignes max)
                content = self._enforce_bullet_limit(content)

                base_content[lang] = content

                # Render and measure
                if USE_HYBRID_STACK:
                    # HYBRID STACK: Playwright for PDF generation
                    pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
                else:
                    # LEGACY STACK: xhtml2pdf
                    pdf_bytes = self._generate_pdf(content, trim=False, language=lang)

                metrics = self.density_calc.calculate_pfr(pdf_bytes)

                # CRITICAL: Progressive trim if overflow detected
                if metrics.page_count > 1:
                    logger.warning(f"OVERFLOW DETECTED: {metrics.page_count} pages - applying progressive trim", extra={"tag": "EMERGENCY"})

                    # Try level 1 (minimal)
                    content = self._trim_level_1(content)
                    if USE_HYBRID_STACK:
                        pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
                    else:
                        pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                    metrics = self.density_calc.calculate_pfr(pdf_bytes)
                    logger.info(f"After trim level 1: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

                    # If still overflow, try level 2 (moderate)
                    if metrics.page_count > 1:
                        logger.info("Still overflow - trying level 2", extra={"tag": "EMERGENCY"})
                        content = self._trim_level_2(content)
                        if USE_HYBRID_STACK:
                            pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
                        else:
                            pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                        metrics = self.density_calc.calculate_pfr(pdf_bytes)
                        logger.info(f"After trim level 2: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

                        # If still overflow, try level 3 (aggressive)
                        if metrics.page_count > 1:
                            logger.warning("Still overflow - trying level 3", extra={"tag": "EMERGENCY"})
                            content = self._trim_level_3(content)
                            if USE_HYBRID_STACK:
                                pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
                            else:
                                pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                            metrics = self.density_calc.calculate_pfr(pdf_bytes)
                            logger.info(f"After trim level 3: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

                            # Last resort: level 4 (ultra)
                            if metrics.page_count > 1:
                                logger.error("Still overflow - applying level 4 (ULTRA)", extra={"tag": "EMERGENCY"})
                                content = self._trim_level_4(content)
                                if USE_HYBRID_STACK:
                                    pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
                                else:
                                    pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                                metrics = self.density_calc.calculate_pfr(pdf_bytes)
                                logger.info(f"After trim level 4: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

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
            # TARGET: 90-98% PFR (optimal), accepter 75-98% (acceptable si trim level 3-4)
            # ZÉRO débordement 2 pages (hard limit enforcement)
            OPTIMAL_MIN = 88.0  # MINIMUM acceptable 88% PFR
            OPTIMAL_MAX = 98.0  # MAX 98% pour éviter débordement
            HARD_MINIMUM = 75.0  # MINIMUM absolu 75% PFR (accepté si trim level 3-4 appliqué)

            # CAS 1: Multi-pages - APPLIQUER HARD LIMIT IMMÉDIATEMENT
            if metrics.page_count > 1:
                warnings.append(
                    f"Multi-pages detected ({metrics.page_count} pages) - applying HARD LIMIT enforcement"
                )

                # HARD LIMIT: Garantie ZÉRO débordement
                content = self._enforce_one_page_hard_limit(content, language=lang)
                pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                metrics = self.density_calc.calculate_pfr(pdf_bytes)

                new_pfr = metrics.fill_percentage
                warnings.append(
                    f"After HARD LIMIT: {new_pfr}%, {metrics.page_count} page(s) (delta: {new_pfr - initial_pfr:+.1f}%)"
                )

                # Si ENCORE 2 pages après hard limit, trim agressivement
                if metrics.page_count > 1:
                    warnings.append(
                        f"Still multi-pages after HARD LIMIT - applying aggressive trimming"
                    )
                    content = self.enricher.trim_content(content, step=3)
                    pdf_bytes = self._generate_pdf(content, trim=True, language=lang)
                    metrics = self.density_calc.calculate_pfr(pdf_bytes)
                    warnings.append(f"After aggressive trimming: {metrics.fill_percentage}%, {metrics.page_count} page(s)")

                # Si TOUJOURS 2 pages, erreur (ne devrait jamais arriver avec hard limit)
                if metrics.page_count > 1:
                    raise ValueError(
                        f"CRITICAL: Unable to fit CV on one page even after HARD LIMIT + trimming. "
                        f"Current: {metrics.page_count} pages. This should never happen."
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

                    pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
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
                        pdf_bytes = self._generate_pdf(content, trim=True, language=lang)
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
                pdf_bytes = self._generate_pdf(content, trim=True, language=lang)
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

                pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
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
                    pdf_bytes = self._generate_pdf(content, trim=True, language=lang)
                    metrics = self.density_calc.calculate_pfr(pdf_bytes)
                    warnings.append(f"After corrective trimming: {metrics.fill_percentage}%")

            # CAS 4: PFR already in [90%, 95%] - ACCEPT as-is
            else:
                warnings.append(
                    f"PFR {metrics.fill_percentage}% already in optimal zone [90-95%] - no adjustment needed"
                )
                pdf_bytes = self._generate_pdf(content, trim=False, language=lang)

            # CRITICAL: Progressive trim if overflow detected
            if metrics.page_count > 1:
                logger.warning(f"OVERFLOW DETECTED: {metrics.page_count} pages - applying progressive trim", extra={"tag": "EMERGENCY"})

                # Try level 1 (minimal)
                content = self._trim_level_1(content)
                pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                metrics = self.density_calc.calculate_pfr(pdf_bytes)
                logger.info(f"After trim level 1: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

                # If still overflow, try level 2 (moderate)
                if metrics.page_count > 1:
                    logger.info("Still overflow - trying level 2", extra={"tag": "EMERGENCY"})
                    content = self._trim_level_2(content)
                    pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                    metrics = self.density_calc.calculate_pfr(pdf_bytes)
                    logger.info(f"After trim level 2: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

                    # If still overflow, try level 3 (aggressive)
                    if metrics.page_count > 1:
                        logger.warning("Still overflow - trying level 3", extra={"tag": "EMERGENCY"})
                        content = self._trim_level_3(content)
                        pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                        metrics = self.density_calc.calculate_pfr(pdf_bytes)
                        logger.info(f"After trim level 3: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

                        # Last resort: level 4 (ultra)
                        if metrics.page_count > 1:
                            logger.error("Still overflow - applying level 4 (ULTRA)", extra={"tag": "EMERGENCY"})
                            content = self._trim_level_4(content)
                            pdf_bytes = self._generate_pdf(content, trim=False, language=lang)
                            metrics = self.density_calc.calculate_pfr(pdf_bytes)
                            logger.info(f"After trim level 4: {metrics.page_count} page(s), {metrics.fill_percentage:.1f}% PFR", extra={"tag": "EMERGENCY"})

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

    def _get_avg_bullet_length(self, content: Dict) -> float:
        """Calcule la longueur moyenne des bullets."""
        total_chars = 0
        total_bullets = 0

        for exp in content.get('work_experience', []) or []:
            bullets = exp.get('bullets', [])
            for bullet in bullets:
                total_chars += len(bullet)
                total_bullets += 1

        return total_chars / max(total_bullets, 1)

    def _prevent_overflow_smart(self, content: Dict) -> Dict:
        """
        SMART PREVENTION: Réduit intelligemment le contenu pour éviter débordement.

        Stratégie adaptative ajustée pour maintenir 88%+ PFR:
        1. Bullets déjà limités à 135 chars par _enforce_bullet_limit()
        2. Si >3400 chars → réduire bullets à 132 chars
        3. Si encore >3300 chars → limiter à 4 bullets par expérience
        4. Si encore >3200 chars → limiter coursework/activities/skills

        Args:
            content: CV content avec risque débordement (bullets déjà à 135 chars max)

        Returns:
            Content optimisé pour 1 page avec PFR maximal
        """
        from copy import deepcopy
        content_safe = deepcopy(content)

        # Check chars count
        current_chars = self._count_chars(content_safe)

        # Step 1: Si >3400 chars, réduire bullets à 132 chars (garde plus de contenu qu'avant)
        if current_chars > 3400:
            for exp in content_safe.get('work_experience', []) or []:
                if exp.get('bullets'):
                    exp['bullets'] = [b[:132] for b in exp['bullets']]
            current_chars = self._count_chars(content_safe)

        # Step 2: Si encore >3300 chars, limiter à 4 bullets par expérience
        if current_chars > 3300:
            for exp in content_safe.get('work_experience', []) or []:
                if exp.get('bullets') and len(exp['bullets']) > 4:
                    exp['bullets'] = exp['bullets'][:4]
            current_chars = self._count_chars(content_safe)

        # Step 3: Si encore >3200 chars, limiter sections
        if current_chars > 3200:
            # Limiter coursework à 5 items
            for edu in content_safe.get('education', []) or []:
                if edu.get('coursework') and len(edu['coursework']) > 5:
                    edu['coursework'] = edu['coursework'][:5]

            # Limiter activities à 3 items
            if content_safe.get('activities_interests'):
                if isinstance(content_safe['activities_interests'], dict):
                    items = content_safe['activities_interests'].get('items', [])
                    if len(items) > 3:
                        content_safe['activities_interests']['items'] = items[:3]
                elif isinstance(content_safe['activities_interests'], list):
                    if len(content_safe['activities_interests']) > 3:
                        content_safe['activities_interests'] = content_safe['activities_interests'][:3]

            # Limiter IT skills à 6 items
            if content_safe.get('it_skills') and len(content_safe['it_skills']) > 6:
                content_safe['it_skills'] = content_safe['it_skills'][:6]

        new_chars = self._count_chars(content_safe)
        logger.info("After smart reduction: {new_chars} chars", extra={"tag": "OVERFLOW PREVENTION"})

        return content_safe

    def _prevent_overflow(self, content: Dict) -> Dict:
        """
        PREVENTIVE: Réduit agressivement le contenu AVANT layout si risque débordement.

        Stratégie progressive :
        1. Limiter bullets à 120 chars (au lieu de 130)
        2. Limiter à 3 bullets par expérience
        3. Limiter coursework à 5 items
        4. Limiter activities à 3 items
        5. Limiter IT skills à 6 items

        Args:
            content: CV content avec risque débordement

        Returns:
            Content réduit pour garantir 1 page
        """
        from copy import deepcopy
        content_safe = deepcopy(content)

        # Step 1: Tronquer TOUS les bullets à 120 chars (sécurité maximale)
        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets'):
                exp['bullets'] = [b[:120] for b in exp['bullets']]

        # Step 2: Limiter à 3 bullets par expérience
        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets') and len(exp['bullets']) > 3:
                exp['bullets'] = exp['bullets'][:3]

        # Step 3: Limiter coursework à 5 items
        for edu in content_safe.get('education', []) or []:
            if edu.get('coursework') and len(edu['coursework']) > 5:
                edu['coursework'] = edu['coursework'][:5]

        # Step 4: Limiter activities à 3 items
        if content_safe.get('activities_interests'):
            if isinstance(content_safe['activities_interests'], dict):
                items = content_safe['activities_interests'].get('items', [])
                if len(items) > 3:
                    content_safe['activities_interests']['items'] = items[:3]
            elif isinstance(content_safe['activities_interests'], list):
                if len(content_safe['activities_interests']) > 3:
                    content_safe['activities_interests'] = content_safe['activities_interests'][:3]

        # Step 5: Limiter IT skills à 6 items
        if content_safe.get('it_skills') and len(content_safe['it_skills']) > 6:
            content_safe['it_skills'] = content_safe['it_skills'][:6]

        new_chars = self._count_chars(content_safe)
        logger.info("After reduction: {new_chars} chars", extra={"tag": "OVERFLOW PREVENTION"})

        return content_safe

    def _enforce_one_page_hard_limit(self, content: Dict, language: str = "fr") -> Dict:
        """
        HARD ENFORCEMENT: Garantit ZÉRO débordement 2 pages en tronquant agressivement.

        Stratégie progressive jusqu'à 1 page garantie :
        1. Tronquer bullets > 140 chars à 140 chars max
        2. Limiter à 3 bullets par expérience (au lieu de 4-5)
        3. Limiter coursework à 5 items max
        4. Limiter activities à 3 items max
        5. Limiter IT skills à 6 items max

        Args:
            content: CV content
            language: Language code

        Returns:
            Content garanti 1 page
        """
        content_safe = deepcopy(content)

        # Step 1: Enforce bullet length HARD LIMIT (130 chars max pour sécurité)
        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets'):
                exp['bullets'] = [b[:130] if len(b) > 130 else b for b in exp['bullets']]

        # Step 2: Limit bullets per experience (3 max for safety)
        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets') and len(exp['bullets']) > 3:
                exp['bullets'] = exp['bullets'][:3]

        # Step 3: Limit coursework (5 max)
        for edu in content_safe.get('education', []) or []:
            if edu.get('coursework') and len(edu['coursework']) > 5:
                edu['coursework'] = edu['coursework'][:5]

        # Step 4: Limit activities (3 max)
        if content_safe.get('activities_interests'):
            content_safe['activities_interests'] = content_safe['activities_interests'][:3]

        # Step 5: Limit IT skills (6 max)
        if content_safe.get('it_skills'):
            content_safe['it_skills'] = content_safe['it_skills'][:6]

        return content_safe

    def _trim_level_1(self, content: Dict) -> Dict:
        """
        TRIM LEVEL 1 (MINIMAL): Réduction légère pour éviter overflow.

        Actions:
        1. Bullets max 130 chars (2 lignes garanties)
        2. Max 4 bullets par expérience
        3. Coursework max 6 items
        4. Activities max 4 items
        5. IT skills max 7 items

        PFR attendu: 85-90%
        """
        content_safe = deepcopy(content)

        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets'):
                exp['bullets'] = [b[:130] if len(b) > 130 else b for b in exp['bullets']]
                if len(exp['bullets']) > 4:
                    exp['bullets'] = exp['bullets'][:4]

        for edu in content_safe.get('education', []) or []:
            if edu.get('coursework') and len(edu['coursework']) > 6:
                edu['coursework'] = edu['coursework'][:6]

        if content_safe.get('activities_interests'):
            if isinstance(content_safe['activities_interests'], list) and len(content_safe['activities_interests']) > 4:
                content_safe['activities_interests'] = content_safe['activities_interests'][:4]

        if content_safe.get('it_skills') and len(content_safe['it_skills']) > 7:
            content_safe['it_skills'] = content_safe['it_skills'][:7]

        return content_safe

    def _trim_level_2(self, content: Dict) -> Dict:
        """
        TRIM LEVEL 2 (MODERATE): Réduction modérée si level 1 insuffisant.

        Actions:
        1. Bullets max 120 chars
        2. Max 3 bullets par expérience
        3. Coursework max 5 items
        4. Activities max 3 items
        5. IT skills max 6 items

        PFR attendu: 80-87%
        """
        content_safe = deepcopy(content)

        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets'):
                exp['bullets'] = [b[:120] if len(b) > 120 else b for b in exp['bullets']]
                if len(exp['bullets']) > 3:
                    exp['bullets'] = exp['bullets'][:3]

        for edu in content_safe.get('education', []) or []:
            if edu.get('coursework') and len(edu['coursework']) > 5:
                edu['coursework'] = edu['coursework'][:5]

        if content_safe.get('activities_interests'):
            if isinstance(content_safe['activities_interests'], list) and len(content_safe['activities_interests']) > 3:
                content_safe['activities_interests'] = content_safe['activities_interests'][:3]

        if content_safe.get('it_skills') and len(content_safe['it_skills']) > 6:
            content_safe['it_skills'] = content_safe['it_skills'][:6]

        return content_safe

    def _trim_level_3(self, content: Dict) -> Dict:
        """
        TRIM LEVEL 3 (AGGRESSIVE): Réduction agressive si level 2 insuffisant.

        Actions:
        1. Bullets max 112 chars (plus serré)
        2. Max 2.5 bullets par expérience (moyenne: garde 2 ou 3 selon nombre d'expériences)
        3. Coursework max 2 items (réduction 66%)
        4. Activities max 1 item
        5. IT skills max 4 items

        PFR attendu: 78-85%
        """
        content_safe = deepcopy(content)

        # Bullets max 112 chars
        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets'):
                exp['bullets'] = [b[:112] if len(b) > 112 else b for b in exp['bullets']]

        # Max 2-3 bullets depending on experience count
        experiences = content_safe.get('work_experience', []) or []
        if len(experiences) > 3:
            # Many experiences → limit to 2 bullets each
            for exp in experiences:
                if exp.get('bullets') and len(exp['bullets']) > 2:
                    exp['bullets'] = exp['bullets'][:2]
        else:
            # Few experiences → allow 3 bullets
            for exp in experiences:
                if exp.get('bullets') and len(exp['bullets']) > 3:
                    exp['bullets'] = exp['bullets'][:3]

        # Coursework max 2 items
        for edu in content_safe.get('education', []) or []:
            if edu.get('coursework') and len(edu['coursework']) > 2:
                edu['coursework'] = edu['coursework'][:2]

        # Activities max 1 item
        if content_safe.get('activities_interests'):
            if isinstance(content_safe['activities_interests'], list) and len(content_safe['activities_interests']) > 1:
                content_safe['activities_interests'] = content_safe['activities_interests'][:1]

        # IT skills max 4 items
        if content_safe.get('it_skills') and len(content_safe['it_skills']) > 4:
            content_safe['it_skills'] = content_safe['it_skills'][:4]

        return content_safe

    def _trim_level_4(self, content: Dict) -> Dict:
        """
        TRIM LEVEL 4 (ULTRA): DERNIER RECOURS - Garantit 1 page à TOUT PRIX.

        Actions:
        1. Bullets max 110 chars (ultra compact)
        2. Max 2 bullets par expérience (brutal cut)
        3. Supprime coursework complètement
        4. Supprime activities complètement
        5. IT skills max 4 items

        PFR attendu: 70-78%
        """
        content_safe = deepcopy(content)

        for exp in content_safe.get('work_experience', []) or []:
            if exp.get('bullets'):
                exp['bullets'] = [b[:110] if len(b) > 110 else b for b in exp['bullets']]
                if len(exp['bullets']) > 2:
                    exp['bullets'] = exp['bullets'][:2]

        for edu in content_safe.get('education', []) or []:
            if edu.get('coursework'):
                edu['coursework'] = []

        if content_safe.get('activities_interests'):
            content_safe['activities_interests'] = []

        if content_safe.get('it_skills') and len(content_safe['it_skills']) > 4:
            content_safe['it_skills'] = content_safe['it_skills'][:4]

        logger.warning("TRIM LEVEL 4 (ULTRA) applied - content severely reduced", extra={"tag": "EMERGENCY"})
        return content_safe

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
                f"Content overflow: {metrics.page_count} pages. Applying HARD LIMIT enforcement."
            )
            # Use HARD LIMIT enforcement for multi-page overflow
            return self._enforce_one_page_hard_limit(content)
        else:
            warnings.append(
                f"PFR {metrics.fill_percentage}% (> 97%). Applying single-pass trimming."
            )
            # Use light trimming (step 1) for slight overflow
            step = 1
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
        Dictionary with requested language keys -> CVGenerationResult
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
        Dictionary with requested language keys -> CVGenerationResult
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
        Dictionary with key "fr" -> CVGenerationResult (PDF only, no DOCX yet)
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
        Dictionary with key "en" -> CVGenerationResult (PDF + DOCX)
    """
    generator = CVGenerator()
    return generator.generate_from_pdf(pdf_bytes, domain, languages=["en"])
