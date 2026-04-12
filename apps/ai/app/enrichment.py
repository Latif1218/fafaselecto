
from .logger import get_logger
logger = get_logger(__name__)

"""
Content Enrichment for Postulae CV Generator.

INCREMENTAL ENRICHMENT STRATEGY (Stability + Performance):
Instead of global rewriting, enrichment is now INCREMENTAL and CONTROLLED.

Core Rule: 1 enrichment unit = 1 bullet point added to an existing experience.

PFR Gap Estimation:
- Missing PFR = target (92) - current PFR
- Assume 1 bullet ≈ +2.5% PFR (empirical average)
- Derive number of bullets needed (rounded DOWN for safety)

Incremental Process (SINGLE PASS):
1. Calculate PFR gap
2. Estimate bullets needed (max 10 per pass for safety)
3. Add bullets to experiences with fewest bullets
4. Maximum: +1 bullet per experience (ceiling: 5 total per experience)
5. NO new experiences created
6. NO global rewriting

Hard Execution Limits:
- ONE enrichment pass only (no retry loops)
- Accept result even if PFR target not reached
- Maximum 10 bullets added per pass (safety cap)
- No retry if enrichment is insufficient

This ensures predictable, stable, and fast enrichment without unbounded loops.
"""
from copy import deepcopy
from typing import Dict, Optional, List
import json
import os

import openai
from dotenv import load_dotenv
from apps.config import OPENAI_API_KEY
from .models import PageFillMetrics

# Load OpenAI API key
load_dotenv()
openai.api_key = OPENAI_API_KEY


class ContentEnricher:
    """
    Handles INCREMENTAL content expansion for underfilled CVs.

    Philosophy:
    - Incremental: Add bullets one by one, never global rewriting
    - Controlled: Estimate exact number of bullets needed
    - Predictable: Target 90-95% PFR without overshoot
    - Fast: One enrichment pass maximum, no retry loops
    """

    # PFR estimation constants
    BULLET_PFR_IMPACT = 2.5  # Average PFR increase per bullet added
    TARGET_PFR = 92.0  # Center of optimal zone (90-95%)
    MAX_BULLETS_PER_EXPERIENCE = 5  # Product constraint (ceiling)
    MAX_ENRICHMENT_PASSES = 1  # One pass only for performance

    # HARD EXECUTION LIMIT: Bullet generation budget per single enrichment pass
    # A single enrichment pass can add multiple bullets (up to the calculated need)
    # but there is NO RETRY if the pass doesn't reach the target PFR
    MAX_BULLETS_TO_ADD_PER_PASS = 10  # Safety limit per enrichment pass

    @staticmethod
    def incremental_enrich_content(
        content: Dict,
        current_metrics: PageFillMetrics,
        domain: str = "finance",
        language: str = "en",
        original_text: Optional[str] = None,
    ) -> Dict:
        """
        INCREMENTAL enrichment for low-density CVs (< 90% PFR).

        Strategy:
        1. Calculate PFR gap: target (92%) - current PFR
        2. Estimate bullets needed: gap / 2.5% (rounded DOWN)
        3. Identify experiences with fewest bullets
        4. Add calculated number of bullets (max 10 per pass) via LLM
        5. NO global rewriting, NO new experiences

        HARD EXECUTION LIMITS (NON-NEGOTIABLE):
        - ONE enrichment pass only (no retry loops)
        - Accept result even if PFR target not reached
        - Maximum 10 bullets added per enrichment pass (safety cap)
        - Maximum +1 bullet per experience (ceiling: 5 bullets total per experience)
        - Do NOT retry if enrichment is insufficient

        Rules:
        - Bullets must be contextual (scope, method, impact, tools)
        - NO invented facts or dates
        - Single pass only - accept results as-is

        Args:
            content: Current CV content
            current_metrics: Current page fill metrics
            domain: Target domain
            language: Output language
            original_text: Original CV text for context (unused in incremental mode)

        Returns:
            Incrementally enriched content dictionary
        """
        enriched = deepcopy(content)
        current_pfr = current_metrics.fill_percentage

        # Step 1: Calculate PFR gap
        pfr_gap = max(0, ContentEnricher.TARGET_PFR - current_pfr)

        # Step 2: Estimate bullets needed (rounded DOWN for safety)
        bullets_needed = int(pfr_gap / ContentEnricher.BULLET_PFR_IMPACT)

        if bullets_needed <= 0:
            # Already at target, no enrichment needed
            return enriched

        # Step 3: Identify experiences with fewest bullets (prioritize enrichment)
        experiences = enriched.get("experience", [])
        if not experiences:
            # No experiences to enrich, return as-is
            return enriched

        # Count bullets per experience and sort by count (ascending)
        exp_with_counts = []
        for idx, exp in enumerate(experiences):
            bullet_count = len(exp.get("bullets", []))
            exp_with_counts.append((idx, bullet_count, exp))

        exp_with_counts.sort(key=lambda x: x[1])  # Sort by bullet count (fewest first)

        # Step 4: Distribute bullets across experiences (max +1 per experience)
        bullets_to_add = min(
            bullets_needed,
            len(experiences),
            ContentEnricher.MAX_BULLETS_TO_ADD_PER_PASS
        )  # Max +1 per exp, with safety cap

        # Select experiences to enrich (those with fewest bullets)
        experiences_to_enrich = exp_with_counts[:bullets_to_add]

        # Step 5: Add bullets to selected experiences (SINGLE PASS, no retry)
        bullets_added = 0

        for exp_idx, current_bullet_count, exp in experiences_to_enrich:
            # Skip if experience already has max bullets
            if current_bullet_count >= ContentEnricher.MAX_BULLETS_PER_EXPERIENCE:
                continue

            # Call LLM to generate 1 contextual bullet for this experience
            new_bullet = ContentEnricher._generate_single_bullet(
                experience=exp,
                domain=domain,
                language=language,
            )

            if new_bullet:
                # Add the new bullet to the experience
                if "bullets" not in enriched["experience"][exp_idx]:
                    enriched["experience"][exp_idx]["bullets"] = []
                enriched["experience"][exp_idx]["bullets"].append(new_bullet)
                bullets_added += 1

        # CRITICAL: Accept result even if bullets_added < bullets_needed
        # NO RETRY - single pass only as per hard execution limits
        return enriched

    @staticmethod
    def _generate_single_bullet(
        experience: Dict, domain: str, language: str
    ) -> Optional[str]:
        """
        Generate a SINGLE contextual bullet for a given experience.

        Uses LLM to expand based on existing context (role, company, existing bullets).
        Does NOT invent facts.

        Args:
            experience: Experience dictionary with title, company, bullets
            domain: Target domain (finance, consulting, etc.)
            language: Output language (fr or en)

        Returns:
            Single bullet point string, or None if generation fails
        """
        # Extract experience context
        title = experience.get("title", "")
        company = experience.get("company", "")
        existing_bullets = experience.get("bullets", [])

        # Build prompt for single bullet generation
        if language == "fr":
            prompt = f"""Tu es un expert en rédaction de CV pour le secteur {domain}.

Rôle: {title}
Entreprise: {company}
Bullets existants:
{chr(10).join(f'- {b}' for b in existing_bullets)}

Génère UN SEUL bullet point supplémentaire qui:
1. Est contextuel au rôle et aux bullets existants
2. Ajoute une dimension manquante (scope, méthode, outils, impact, coordination)
3. Est quantifié si possible (métriques, pourcentages, tailles)
4. N'invente PAS de faits
5. Fait 15-25 mots
6. Style: professionnel, finance/conseil

Réponds UNIQUEMENT avec le bullet point, sans tiret, sans numéro."""

        else:  # English
            prompt = f"""You are a CV writing expert for {domain} sector.

Role: {title}
Company: {company}
Existing bullets:
{chr(10).join(f'- {b}' for b in existing_bullets)}

Generate ONE additional bullet point that:
1. Is contextual to the role and existing bullets
2. Adds a missing dimension (scope, method, tools, impact, coordination)
3. Is quantified if possible (metrics, percentages, sizes)
4. Does NOT invent facts
5. Is 15-25 words
6. Style: professional, finance/consulting tone

Respond ONLY with the bullet point, no dash, no number."""

        try:
            # Call LLM (OpenAI GPT-4)
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional CV writer. Generate contextual, factual bullet points.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=100,
            )

            bullet = response.choices[0].message.content.strip()

            # Clean up (remove dash/number if present)
            if bullet.startswith("- "):
                bullet = bullet[2:]
            if bullet.startswith("• "):
                bullet = bullet[2:]
            if bullet and bullet[0].isdigit() and bullet[1:3] in [". ", ") "]:
                bullet = bullet[3:]

            return bullet if bullet else None

        except Exception as e:
            # If LLM call fails, return None (no enrichment for this experience)
            logger.error(f"Warning: Failed to generate bullet: {e}")
            return None

    @staticmethod
    def aggressive_enrich_content(
        content: Dict,
        current_metrics: PageFillMetrics,
        domain: str = "finance",
        language: str = "en",
        original_text: Optional[str] = None,
    ) -> Dict:
        """
        DEPRECATED: Use incremental_enrich_content instead.

        This method is kept for backward compatibility but now delegates
        to incremental_enrich_content for stability.

        Args:
            content: Current CV content
            current_metrics: Current page fill metrics
            domain: Target domain
            language: Output language
            original_text: Original CV text for context

        Returns:
            Incrementally enriched content dictionary
        """
        # Delegate to incremental enrichment (stable, predictable)
        return ContentEnricher.incremental_enrich_content(
            content=content,
            current_metrics=current_metrics,
            domain=domain,
            language=language,
            original_text=original_text,
        )

    @staticmethod
    def enrich_content(
        content: Dict,
        current_metrics: PageFillMetrics,
        domain: str = "finance",
        language: str = "en",
        original_text: Optional[str] = None,
    ) -> Dict:
        """
        DEPRECATED: Use incremental_enrich_content instead.

        Kept for backward compatibility.
        """
        return ContentEnricher.incremental_enrich_content(
            content=content,
            current_metrics=current_metrics,
            domain=domain,
            language=language,
            original_text=original_text,
        )

    @staticmethod
    def trim_content(content: Dict, step: int = 1) -> Dict:
        """
        Trim content to fit on one page (overflow scenario).

        PRODUCT RULE: Trimming should be MINIMAL and SURGICAL.
        - NO removal of bullets or experiences unless absolutely necessary
        - Prefer shortening bullet LENGTH over removing bullets
        - One trimming pass maximum

        Trimming steps (progressive):
        1. Shorten longest bullets slightly (85% of original length)
        2. Limit bullets to 3 per experience, shorten to 80%
        3. Aggressive: Keep only 2 experiences with 2 bullets each (last resort)

        Args:
            content: CV content to trim
            step: Trimming aggressiveness (1=light, 2=moderate, 3=aggressive)

        Returns:
            Trimmed content
        """
        trimmed = deepcopy(content)

        if step == 1:
            # LIGHT TRIM: Shorten bullet length slightly, keep all experiences
            for exp in trimmed.get("experience", []):
                if "bullets" in exp:
                    # Shorten bullets to 85% (remove filler words)
                    shortened_bullets = []
                    for bullet in exp["bullets"]:
                        words = bullet.split()
                        target_words = max(10, int(len(words) * 0.85))
                        shortened = " ".join(words[:target_words])
                        if not shortened.endswith("."):
                            shortened += "..."
                        shortened_bullets.append(shortened)
                    exp["bullets"] = shortened_bullets

        elif step == 2:
            # MODERATE TRIM: Limit to 3 bullets per exp, shorten to 80%
            for exp in trimmed.get("experience", []):
                if "bullets" in exp:
                    # Keep only 3 bullets
                    exp["bullets"] = exp["bullets"][:3]
                    # Shorten to 80%
                    shortened_bullets = []
                    for bullet in exp["bullets"]:
                        words = bullet.split()
                        target_words = max(10, int(len(words) * 0.80))
                        shortened = " ".join(words[:target_words])
                        if not shortened.endswith("."):
                            shortened += "..."
                        shortened_bullets.append(shortened)
                    exp["bullets"] = shortened_bullets

            # Limit education to 2 entries
            if "education" in trimmed and len(trimmed["education"]) > 2:
                trimmed["education"] = trimmed["education"][:2]

        elif step == 3:
            # AGGRESSIVE TRIM: Minimal content (last resort)
            if "experience" in trimmed:
                trimmed["experience"] = trimmed["experience"][:2]
                for exp in trimmed["experience"]:
                    if "bullets" in exp:
                        exp["bullets"] = exp["bullets"][:2]

            if "education" in trimmed:
                trimmed["education"] = trimmed["education"][:2]

            # Limit all other sections
            trimmed["languages"] = trimmed.get("languages", [])[:3]
            trimmed["it_skills"] = trimmed.get("it_skills", [])[:3]
            trimmed["activities_interests"] = trimmed.get(
                "activities_interests", []
            )[:2]

            # Remove certifications
            if "certifications" in trimmed:
                del trimmed["certifications"]

        return trimmed
