"""
CV Domain Detection Utilities for Postulae.
Uses LLM to classify the primary professional domain from CV text.
"""

import logging
import openai
from apps.config import OPENAI_API_KEY  

logger = logging.getLogger(__name__)

openai.api_key = OPENAI_API_KEY  

def detect_domain_from_cv_text(raw_text: str) -> str:
    """
    Using LLM primary domain detect CV text form cv
    
    Returns:
        str: "finance", "tech", "consulting", "marketing", "engineering", "general" etc
    """
    try:
        truncated_text = raw_text[:3500]  

        prompt = f"""
You are a professional CV domain classifier.
Analyze the CV text below and determine the SINGLE MOST LIKELY professional domain or industry.

Common domains to choose from:
- finance
- consulting
- tech (or software/it)
- marketing
- engineering
- healthcare
- education
- law
- general (if mixed or unclear)

Rules:
- Return ONLY the domain name in lowercase (one word or "tech")
- Pick the most dominant one based on job titles, skills, companies, responsibilities
- If multiple domains are equally present → choose "general"
- Do NOT explain, do NOT add extra text — just the domain name.

CV text:
{truncated_text}
"""

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,          
            max_tokens=30,
            top_p=1.0,
        )

        domain = response.choices[0].message.content.strip().lower()

        domain_mapping = {
            "tech": ["tech", "software", "it", "developer", "programmer", "engineer software", "data science"],
            "engineering": ["engineering", "mechanical", "civil", "electrical"],
            "finance": ["finance", "banking", "investment", "accounting", "financial"],
            "consulting": ["consulting", "strategy", "management consulting"],
            "marketing": ["marketing", "digital marketing", "brand", "advertising"],
        }

        for canonical, keywords in domain_mapping.items():
            if any(kw in domain for kw in keywords):
                return canonical

        valid_domains = [
            "finance", "consulting", "tech", "marketing", "engineering",
            "healthcare", "education", "law", "general"
        ]

        return domain if domain in valid_domains else "general"

    except Exception as e:
        logger.warning(f"Domain detection failed: {str(e)}", exc_info=True)
        return "finance" 