from typing import Dict, List, Optional
import re
import requests
from bs4 import BeautifulSoup


def extract_job_offer_from_url(url: str, timeout: int = 12) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:300])


def simple_offer_parser(job_text: str) -> Dict:
    """
    Lightweight fallback parser.
    This is not perfect, but gives the LLM structured hints.
    """
    company_name: Optional[str] = None
    position_title: Optional[str] = None
    requirements: List[str] = []

    lines = [line.strip() for line in job_text.splitlines() if line.strip()]
    joined_text = "\n".join(lines)

    title_patterns = [
        r"(?i)(?:position|role|job title)\s*:\s*(.+)",
        r"(?i)we are hiring\s+(.+)",
        r"(?i)opening for\s+(.+)",
    ]

    company_patterns = [
        r"(?i)(?:company|employer|organization)\s*:\s*(.+)",
        r"(?i)at\s+([A-Z][A-Za-z0-9&,\.\-\s]+)",
    ]

    for pattern in title_patterns:
        match = re.search(pattern, joined_text)
        if match:
            position_title = match.group(1).strip()[:255]
            break

    for pattern in company_patterns:
        match = re.search(pattern, joined_text)
        if match:
            company_name = match.group(1).strip()[:255]
            break

    bullet_like = []
    for line in lines:
        if line.startswith(("-", "•", "*")):
            cleaned = line.lstrip("-•* ").strip()
            if cleaned:
                bullet_like.append(cleaned)

    if bullet_like:
        requirements = bullet_like[:8]

    return {
        "company_name": company_name,
        "position_title": position_title,
        "requirements": requirements
    }