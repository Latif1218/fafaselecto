
from .logger import get_logger
logger = get_logger(__name__)

"""
Anthropic Claude Client for Postulae CV Generator.

Handles all interactions with Claude models (Sonnet 4.5 + Haiku 3).
Optimized for:
- Structuration CV (Sonnet 4.5): Most intelligent model, best constraint adherence
- Traduction (Haiku 3): Ultra fast, -89% cost vs Sonnet

PRICING (Mars 2026):
- Sonnet 4.5: $3/1M input, $15/1M output
- Haiku 3: $0.25/1M input, $1.25/1M output

COST PER CV:
- Structuration (Sonnet 4.5): ~$0.058
- Traduction (Haiku 3): ~$0.005
"""
import json
import os
from typing import Dict, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from apps.config import ANTHROPIC_API_KEY

load_dotenv()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Model identifiers (latest available with current API key)
# NOTE: API key has access to Claude 4.5 (better than 3.5!)
MODEL_SONNET = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5 (most intelligent)
# MODEL_HAIKU = "claude-3-haiku-20240307"      # Claude 3 Haiku (fast, cheap)
MODEL_HAIKU = "claude-haiku-4-5"      # Claude 3 Haiku (fast, cheap)

def generate_cv_content_claude(
    input_data: Dict,
    system_prompt: str,
    domain: str = "finance",
    language: str = "en",
    model: str = MODEL_SONNET,
    enrichment_instructions: Optional[str] = None,
) -> Dict:
    """
    Generate CV content using Claude (Sonnet or Haiku).

    Args:
        input_data: Input data (raw_text from PDF or structured data)
        system_prompt: System prompt (from prompts/base_system.txt)
        domain: Target domain (finance, consulting, startup, government)
        language: Output language (en, fr)
        model: Claude model to use (MODEL_SONNET or MODEL_HAIKU)
        enrichment_instructions: Optional adaptive enrichment instructions

    Returns:
        Structured CV content as dictionary

    Raises:
        ValueError: If generation fails
    """
    try:
        # Build complete system prompt
        full_system_prompt = system_prompt

        # Add language specification
        if language == "fr":
            full_system_prompt += "\n\nOutput must be in French."
        else:
            full_system_prompt += "\n\nOutput must be in English."

        # Add adaptive enrichment instructions if provided
        if enrichment_instructions:
            full_system_prompt += "\n\n" + enrichment_instructions

        # Prepare user content
        if "raw_text" in input_data:
            user_content = f"Resume data: {input_data['raw_text']}"
        else:
            user_content = f"Resume data: {json.dumps(input_data, ensure_ascii=False)}"

        # Call Claude API with retry on JSON error (max 1 retry)
        max_retries = 1
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = anthropic_client.messages.create(
                    model=model,
                    max_tokens=4096,
                    temperature=0.3,
                    system=full_system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ]
                )

                # Extract JSON from response
                content_text = response.content[0].text

                # Parse JSON (Claude returns raw JSON when prompted correctly)
                try:
                    content = json.loads(content_text)
                    # Success - break retry loop
                    break
                except json.JSONDecodeError as e:
                    # Fallback: extract JSON from markdown code blocks if present
                    if "```json" in content_text:
                        json_start = content_text.find("```json") + 7
                        json_end = content_text.find("```", json_start)
                        content_text = content_text[json_start:json_end].strip()
                        content = json.loads(content_text)
                        break
                    elif "```" in content_text:
                        json_start = content_text.find("```") + 3
                        json_end = content_text.find("```", json_start)
                        content_text = content_text[json_start:json_end].strip()
                        content = json.loads(content_text)
                        break
                    else:
                        # JSON parse error - retry if attempts remaining
                        last_error = e
                        if attempt < max_retries:
                            logger.info("JSON parse error, retrying ({attempt + 1}/{max_retries})...", extra={"tag": "RETRY"})
                            continue
                        else:
                            raise ValueError(f"Failed to parse JSON from Claude response after {max_retries + 1} attempts: {str(e)}")
            except Exception as e:
                last_error = e
                if attempt < max_retries and "JSONDecodeError" in str(type(e).__name__):
                    logger.info("Error occurred, retrying ({attempt + 1}/{max_retries})...", extra={"tag": "RETRY"})
                    continue
                else:
                    raise

        # Log bullet stats
        _log_bullet_stats(content, model)

        return content

    except Exception as e:
        raise ValueError(f"Failed to generate CV content with Claude: {str(e)}")


def translate_cv_content_claude(
    cv_content: Dict,
    source_language: str,
    target_language: str,
    model: str = MODEL_HAIKU,
) -> Dict:
    """
    Translate CV content using Claude (Haiku by default for speed/cost).

    Args:
        cv_content: Structured CV content in source language
        source_language: Source language code (fr, en)
        target_language: Target language code (fr, en)
        model: Claude model to use (MODEL_HAIKU recommended for translation)

    Returns:
        Translated CV content as dictionary

    Raises:
        ValueError: If translation fails
    """
    try:
        source_lang_name = "French" if source_language == "fr" else "English"
        target_lang_name = "French" if target_language == "fr" else "English"

        system_prompt = f"""You are a professional translator specializing in CVs for finance and consulting roles.

Translate the following CV from {source_lang_name} to {target_lang_name}.

CRITICAL REQUIREMENTS:
1. Maintain EXACT JSON structure (same keys, same nesting)
2. Preserve bullet point lengths (±10 chars max deviation)
3. Keep professional terminology appropriate for finance/consulting
4. Maintain dates, numbers, and proper nouns unchanged
5. Return ONLY valid JSON, no markdown, no explanations

Example:
Input (FR): "Réalisation de 2 due diligences avec études de marché approfondies"
Output (EN): "Conducted 2 due diligences with in-depth market research studies"

Length preservation is CRITICAL - aim for same character count (±10%)."""

        user_content = f"CV to translate:\n\n{json.dumps(cv_content, ensure_ascii=False, indent=2)}"

        # Call Claude API
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=0.2,  # Lower temp for translation (more deterministic)
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_content
                }
            ]
        )

        # Extract JSON from response
        content_text = response.content[0].text

        # Parse JSON
        try:
            translated_content = json.loads(content_text)
        except json.JSONDecodeError:
            # Fallback: extract JSON from markdown code blocks
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                content_text = content_text[json_start:json_end].strip()
                translated_content = json.loads(content_text)
            elif "```" in content_text:
                json_start = content_text.find("```") + 3
                json_end = content_text.find("```", json_start)
                content_text = content_text[json_start:json_end].strip()
                translated_content = json.loads(content_text)
            else:
                raise ValueError(f"Failed to parse JSON from translation: {content_text[:200]}")

        # Validate translation quality (check bullet length preservation)
        _validate_translation_quality(cv_content, translated_content, source_language, target_language)

        return translated_content

    except Exception as e:
        raise ValueError(f"Failed to translate CV with Claude: {str(e)}")


def _log_bullet_stats(content: Dict, model: str):
    """Log bullet length statistics for quality monitoring."""
    total_bullets = 0
    total_chars = 0
    min_len = float('inf')
    max_len = 0

    for exp in content.get('work_experience', []):
        for bullet in exp.get('bullets', []):
            bullet_len = len(bullet)
            total_bullets += 1
            total_chars += bullet_len
            min_len = min(min_len, bullet_len)
            max_len = max(max_len, bullet_len)

    if total_bullets > 0:
        avg_len = total_chars / total_bullets
        logger.info(f"\n[CLAUDE {model.upper()}] Bullet stats:")
        logger.info(f"   Total bullets: {total_bullets}")
        logger.info(f"   Average length: {avg_len:.1f} chars")
        logger.info(f"   Range: {min_len}-{max_len} chars")

        # Target: 140-210 chars
        optimal_count = sum(1 for exp in content.get('work_experience', [])
                           for bullet in exp.get('bullets', [])
                           if 140 <= len(bullet) <= 210)
        logger.info(f"   Optimal (140-210): {optimal_count}/{total_bullets} ({optimal_count/total_bullets*100:.1f}%)")


def _validate_translation_quality(
    source: Dict,
    translated: Dict,
    source_lang: str,
    target_lang: str
):
    """
    Validate translation quality (bullet length preservation).

    Logs warnings if bullets are shortened >10%.
    """
    warnings = []

    source_exp = source.get('work_experience', [])
    translated_exp = translated.get('work_experience', [])

    if len(source_exp) != len(translated_exp):
        warnings.append(f"Experience count mismatch: {len(source_exp)} -> {len(translated_exp)}")

    for i, (src_exp, trl_exp) in enumerate(zip(source_exp, translated_exp)):
        src_bullets = src_exp.get('bullets', [])
        trl_bullets = trl_exp.get('bullets', [])

        if len(src_bullets) != len(trl_bullets):
            warnings.append(f"Exp #{i+1} bullet count mismatch: {len(src_bullets)} -> {len(trl_bullets)}")
            continue

        for j, (src_bullet, trl_bullet) in enumerate(zip(src_bullets, trl_bullets)):
            src_len = len(src_bullet)
            trl_len = len(trl_bullet)
            shrinkage = (src_len - trl_len) / src_len * 100 if src_len > 0 else 0

            if shrinkage > 10:
                warnings.append(
                    f"Exp #{i+1} bullet #{j+1} shortened {shrinkage:.1f}%: {src_len} -> {trl_len} chars"
                )

    if warnings:
        logger.warning(f"\n[TRANSLATION QUALITY] {source_lang.upper()}->{target_lang.upper()} warnings:")
        for warning in warnings[:5]:  # Limit to 5 warnings
            logger.warning(f"   WARNING:  {warning}")
        if len(warnings) > 5:
            logger.warning(f"   ... and {len(warnings) - 5} more warnings")

        # If severe shrinkage, recommend fallback to Sonnet
        severe_warnings = [w for w in warnings if "shortened" in w and "%" in w]
        if len(severe_warnings) >= 3:
            logger.info(f"\n   TIP: RECOMMENDATION: Consider using Sonnet for translation (+$0.051/CV)")
