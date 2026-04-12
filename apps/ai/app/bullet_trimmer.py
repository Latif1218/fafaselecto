
from .logger import get_logger
logger = get_logger(__name__)

"""
Intelligent bullet trimming to reach optimal length (135-155 chars).
Trims bullets > 170 chars to ~155 chars at natural break points.
"""


def smart_trim_bullet(bullet: str, target_max: int = 139) -> str:
    """
    Trim bullet intelligently if too long.

    Rules:
    - If bullet <= 155 chars: keep as-is (acceptable range)
    - If bullet > 155 chars: trim to ~139 chars at natural break (match elite reference)

    Break points priority:
    1. Last "..." before target
    2. Last comma before target
    3. Last space before target

    Args:
        bullet: Original bullet text
        target_max: Maximum target length (default 139)

    Returns:
        Trimmed bullet text
    """
    if len(bullet) <= 155:
        return bullet

    # Try to cut at last "..."
    if "..." in bullet[:target_max]:
        last_ellipsis = bullet[:target_max].rfind("...")
        if last_ellipsis > 110:  # Don't cut too early
            return bullet[:last_ellipsis + 3]

    # Try to cut at last comma
    if "," in bullet[:target_max]:
        last_comma = bullet[:target_max].rfind(",")
        if last_comma > 110:
            return bullet[:last_comma] + ", ..."

    # Last resort: cut at last space
    last_space = bullet[:target_max].rfind(" ")
    if last_space > 110:
        return bullet[:last_space] + "..."

    # Very last resort: hard cut
    return bullet[:target_max - 3] + "..."


def trim_cv_bullets(cv_content: dict) -> dict:
    """
    Apply smart trimming to all work experience bullets.

    Args:
        cv_content: CV content dictionary

    Returns:
        CV content with trimmed bullets
    """
    if "work_experience" not in cv_content:
        return cv_content

    trimmed_count = 0
    total_bullets = 0
    total_chars_before = 0
    total_chars_after = 0

    for exp in cv_content["work_experience"]:
        if "bullets" in exp:
            new_bullets = []
            for b in exp["bullets"]:
                original_len = len(b)
                trimmed_b = smart_trim_bullet(b)
                new_bullets.append(trimmed_b)

                total_bullets += 1
                total_chars_before += original_len
                total_chars_after += len(trimmed_b)

                if len(trimmed_b) < original_len:
                    trimmed_count += 1
                    logger.info("{original_len} -> {len(trimmed_b)} chars (-{original_len - len(trimmed_b)})", extra={"tag": "TRIMMING"})
                    logger.info(f"   Before: {b[:80]}...")
                    logger.info(f"   After:  {trimmed_b[:80]}...")

            exp["bullets"] = new_bullets

    if trimmed_count > 0:
        avg_before = total_chars_before / total_bullets if total_bullets > 0 else 0
        avg_after = total_chars_after / total_bullets if total_bullets > 0 else 0
        logger.info(f"\n[TRIMMING SUMMARY]")
        logger.info(f"   Trimmed: {trimmed_count}/{total_bullets} bullets")
        logger.info(f"   Avg length: {avg_before:.1f} -> {avg_after:.1f} chars")
        logger.info(f"   Total reduction: {total_chars_before - total_chars_after} chars")

    return cv_content


def validate_bullet_lengths(cv_content: dict) -> dict:
    """
    Validate bullet lengths and return stats.

    Args:
        cv_content: CV content dictionary

    Returns:
        Dictionary with validation stats
    """
    stats = {
        "total_bullets": 0,
        "avg_length": 0,
        "min_length": float('inf'),
        "max_length": 0,
        "too_short": 0,  # < 110 chars
        "optimal": 0,    # 110-155 chars
        "too_long": 0,   # > 155 chars
    }

    if "work_experience" not in cv_content:
        return stats

    all_lengths = []

    for exp in cv_content["work_experience"]:
        if "bullets" in exp:
            for bullet in exp["bullets"]:
                length = len(bullet)
                all_lengths.append(length)
                stats["total_bullets"] += 1
                stats["min_length"] = min(stats["min_length"], length)
                stats["max_length"] = max(stats["max_length"], length)

                if length < 110:
                    stats["too_short"] += 1
                elif length > 155:
                    stats["too_long"] += 1
                else:
                    stats["optimal"] += 1

    if all_lengths:
        stats["avg_length"] = sum(all_lengths) / len(all_lengths)

    if stats["min_length"] == float('inf'):
        stats["min_length"] = 0

    return stats
