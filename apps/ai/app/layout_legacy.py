"""
LEGACY Layout Engine for Postulae CV Generator (xhtml2pdf).

⚠️ WARNING: This module is LEGACY and should NOT be used in production.
Use layout_playwright.py instead for production PDF generation.

This file is kept ONLY for backward compatibility if USE_HYBRID_STACK=False.

CRITICAL: This module contains the exact layout logic that produces
the "Fayed Hanafi" reference CV format. ALL layout rules must be preserved.

DO NOT:
- Simplify spacing logic
- Generalize font sizes
- Replace precise values with approximations
- Alter typography hierarchy

This is a PRODUCT CONSTRAINT, not a cosmetic choice.

DEPRECATION WARNING:
- Use app.layout_playwright for production (Playwright/Chromium)
- This xhtml2pdf engine has ±5-8% PFR variance vs 0% with Playwright
"""
import io
import os
import re
import unicodedata
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa


class LayoutEngine:
    """
    Handles CV layout rendering with exact Postulae formatting.
    Preserves all typography, spacing, and density rules.
    """

    # Template directory
    TEMPLATES_DIR = Path(__file__).parent / "templates"

    @staticmethod
    def normalize_cv_data(data: Dict, trim: bool = False, language: str = "fr") -> Dict:
        """
        Normalize CV data to exact template structure.

        IMPORTANT: This normalization maintains compatibility with the precise
        layout template. Changes here can break the one-page layout.

        Args:
            data: Raw CV content dictionary
            trim: If True, apply moderate trimming for overflow
            language: Language for date formatting ("fr" or "en")

        Returns:
            Normalized data dictionary ready for template
        """
        template_data = data.copy() if isinstance(data, dict) else {}
        template_data["language"] = language

        # Flatten contact information
        if template_data.get("contact_information"):
            contact = template_data["contact_information"][0]
            template_data["name"] = contact.get("name", "")
            template_data["address"] = contact.get("address", "")
            template_data["phone"] = contact.get("phone", "")
            template_data["email"] = contact.get("email", "")

        # Education: normalize dates
        for edu in template_data.get("education", []) or []:
            if "year" in edu and "date" in edu:
                year_val = str(edu.get("year", "")).strip()
                date_val = str(edu.get("date", "")).strip()
                if any(ch.isalpha() for ch in date_val):
                    pass  # Keep date with month names
                else:
                    edu["date"] = year_val
                edu.pop("year", None)
            elif "year" in edu:
                edu["date"] = edu.pop("year")

            if edu.get("date"):
                edu["date"] = LayoutEngine._shorten_date_range(str(edu["date"]))
                if language == "fr":
                    edu["date"] = LayoutEngine._convert_date_to_french(edu["date"])

            # Ensure 4-digit years become "Jan YYYY" or "Janv. YYYY" for French
            d = str(edu.get("date", "")).strip()
            if d.isdigit() and len(d) == 4:
                edu["date"] = f"Janv. {d}" if language == "fr" else f"Jan {d}"

            # Normalize location
            if edu.get("location"):
                edu["location"] = LayoutEngine._shorten_location(str(edu["location"]))

        # Map keys: work_experience → experience
        template_data["experience"] = template_data.pop(
            "work_experience", template_data.get("experience", [])
        )

        # Normalize experience dates and locations
        for exp in template_data.get("experience", []) or []:
            if exp.get("date"):
                exp["date"] = LayoutEngine._shorten_date_range(str(exp["date"]))
                if language == "fr":
                    exp["date"] = LayoutEngine._convert_date_to_french(exp["date"])
            if exp.get("location"):
                exp["location"] = LayoutEngine._shorten_location(str(exp["location"]))

        # Map keys: language_skills → languages, etc.
        template_data["languages"] = template_data.pop(
            "language_skills", template_data.get("languages", [])
        )
        template_data["it_skills"] = template_data.pop(
            "it_skills", template_data.get("it_skills", [])
        )
        template_data["databases"] = template_data.pop(
            "financial_databases", template_data.get("databases", [])
        )
        template_data["interests"] = template_data.pop(
            "activities_interests", template_data.get("interests", [])
        )

        # Detect French government CV
        if any(
            "ÉDUCATION" in str(edu.get("institution", ""))
            for edu in template_data.get("education", []) or []
        ):
            template_data["is_french_government"] = True

        # Trimming logic (only when overflow occurs)
        if trim:
            template_data = LayoutEngine._apply_trim(template_data)

        # Clean N/A values
        template_data = LayoutEngine._replace_na_values(template_data)

        return template_data

    @staticmethod
    def _apply_trim(data: Dict) -> Dict:
        """
        Apply moderate trimming to reduce content (overflow scenario).

        Trimming rules:
        - Max 3 education entries
        - Max 3 work experiences with max 4 bullets each
        - Shorten bullets to max 120 chars
        - Limit skills/languages/interests
        """
        # Limit education
        if isinstance(data.get("education"), list):
            data["education"] = data["education"][:3]

        # Limit work experience
        if isinstance(data.get("experience"), list):
            limited_exp = []
            for exp in data["experience"][:3]:
                bullets = exp.get("bullets", [])
                if isinstance(bullets, list):
                    trimmed = []
                    for b in bullets[:4]:
                        text = str(b)
                        max_len = 120
                        if len(text) > max_len:
                            truncated = text[:max_len].rstrip()
                            if "." in truncated:
                                truncated = truncated[: truncated.rfind(".") + 1]
                            elif "," in truncated:
                                truncated = truncated[: truncated.rfind(",")]
                            else:
                                truncated = truncated.rstrip() + "…"
                            text = truncated
                        trimmed.append(text)
                    exp["bullets"] = trimmed
                limited_exp.append(exp)
            data["experience"] = limited_exp

        # Limit other sections
        data["languages"] = (data.get("languages") or [])[:5]
        data["it_skills"] = (data.get("it_skills") or [])[:6]
        data["databases"] = (data.get("databases") or [])[:4]
        data["activities_interests"] = (data.get("activities_interests") or [])[:6]

        return data

    @staticmethod
    def _convert_date_to_french(text: str) -> str:
        """
        Convert English month abbreviations to French in dates.
        Examples: "Jan 2022" → "Janv. 2022"
                  "Aug 2023 - Dec 2024" → "Août 2023 - Déc. 2024"
                  "Jul 2021 -" → "Juil. 2021 -"
        """
        en_to_fr = {
            "Jan": "Janv.",
            "Feb": "Févr.",
            "Mar": "Mars",
            "Apr": "Avr.",
            "May": "Mai",
            "Jun": "Juin",
            "Jul": "Juil.",
            "Aug": "Août",
            "Sep": "Sept.",
            "Oct": "Oct.",
            "Nov": "Nov.",
            "Dec": "Déc.",
        }

        result = text
        for en, fr in en_to_fr.items():
            result = re.sub(rf"\b{en}\b", fr, result)

        return result

    @staticmethod
    def _shorten_date_range(text: str) -> str:
        """
        Convert verbose dates to short forms.
        Examples: "Since July 2025" → "Jul 2025"
                  "July 2025 - December 2025" → "Jul 2025 - Dec 2025"
        """
        months = {
            "january": "Jan",
            "february": "Feb",
            "march": "Mar",
            "april": "Apr",
            "may": "May",
            "june": "Jun",
            "july": "Jul",
            "august": "Aug",
            "september": "Sep",
            "october": "Oct",
            "november": "Nov",
            "december": "Dec",
        }

        t = text.strip()
        t_lower = t.lower()

        # French months → English (+ fix common LLM errors like "Auguste")
        fr_to_en = {
            "janvier": "jan",
            "février": "feb",
            "fevrier": "feb",
            "mars": "mar",
            "avril": "apr",
            "mai": "may",
            "juin": "june",
            "juillet": "july",
            "août": "aug",
            "aout": "aug",
            "auguste": "aug",  # Fix LLM error "Auguste" → "Aug"
            "septembre": "sept",
            "octobre": "oct",
            "novembre": "nov",
            "décembre": "dec",
            "decembre": "dec",
        }
        for fr, en in fr_to_en.items():
            t_lower = re.sub(rf"\b{fr}\b", en, t_lower)

        # Normalize "present" → "now"
        t_lower = re.sub(
            r"\b(present|présent|jusqu'?a\s+present|jusqu'?à\s+présent|aujourd'?hui|current|to\s+date)\b",
            "now",
            t_lower,
        )

        # Replace full month names
        for full, short in months.items():
            t_lower = re.sub(rf"\b{full}\b", short.lower(), t_lower)

        # Capitalize months
        def cap_months(s: str) -> str:
            for short in set(months.values()):
                s = re.sub(rf"\b{short.lower()}\b", short, s)
            return s

        # Handle "since" prefix → convert to "YYYY -"
        m_since = re.match(r"^(since|depuis)\s+(.*)$", t_lower)
        if m_since:
            start = cap_months(m_since.group(2))
            start = re.sub(r"\s*[–—-]\s*", " ", start).strip()
            return f"{start} -"

        # Handle range ending with "now" → convert to "YYYY -"
        m_now = re.match(r"^(.*?)\s*[–—-]\s*now$", t_lower)
        if m_now:
            start = cap_months(m_now.group(1))
            start = re.sub(r"\s*[–—-]\s*", " ", start).strip()
            return f"{start} -"

        t_short = cap_months(t_lower)
        t_short = re.sub(r"\s*[–—]\s*", "-", t_short)
        t_short = re.sub(r"\s*-\s*", "-", t_short)
        t_short = re.sub(r"\s+", " ", t_short).strip()
        return t_short

    @staticmethod
    def _shorten_location(text: str) -> str:
        """
        Convert locations to short English forms.
        - Remove accents
        - Abbreviate: Saint → St, Sainte → Ste
        - Map countries: États-Unis → USA, etc.
        - Keep "City, Country" format
        """

        def strip_accents(s: str) -> str:
            return (
                unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
            )

        s = text.strip()
        parts = [p.strip() for p in s.split(",")]

        country_map = {
            "etats-unis": "USA",
            "etats unis": "USA",
            "united states of america": "USA",
            "united states": "USA",
            "usa": "USA",
            "royaume-uni": "UK",
            "united kingdom": "UK",
            "uk": "UK",
            "emirats arabes unis": "UAE",
            "united arab emirates": "UAE",
            "uae": "UAE",
            "allemagne": "Germany",
            "espagne": "Spain",
            "italie": "Italy",
            "suisse": "Switzerland",
            "belgique": "Belgium",
            "pays-bas": "Netherlands",
            "pays bas": "Netherlands",
            "luxembourg": "Luxembourg",
            "france": "France",
            "canada": "Canada",
            "chine": "China",
            "japon": "Japan",
            "inde": "India",
        }

        def abbreviate_city(city: str) -> str:
            c = strip_accents(city)
            c = re.sub(r"^\s*Saint[-\s]", "St-", c, flags=re.IGNORECASE)
            c = re.sub(r"^\s*Sainte[-\s]", "Ste-", c, flags=re.IGNORECASE)
            c = re.sub(r"\s*-\s*", "-", c)
            c = re.sub(r"\s+", " ", c)
            c = "-".join(part.strip().title() for part in c.split("-"))
            return c.strip()

        if len(parts) == 0:
            return strip_accents(s)
        if len(parts) == 1:
            token = strip_accents(parts[0])
            lowered = token.lower()
            if lowered in country_map:
                return country_map[lowered]
            return abbreviate_city(token)

        # City, Country structure
        city = abbreviate_city(parts[0])
        country_token = strip_accents(parts[-1])
        lower_country = country_token.lower()
        country = country_map.get(lower_country, country_token.title())
        return f"{city}, {country}"

    @staticmethod
    def _replace_na_values(value):
        """Remove N/A, None, null placeholders recursively."""
        if isinstance(value, str):
            if (
                value.strip().upper()
                in {"N/A", "NA", "NOT AVAILABLE", "NONE", "NULL"}
                or value.strip() == ""
            ):
                return ""
            return value
        if isinstance(value, list):
            return [
                LayoutEngine._replace_na_values(v)
                for v in value
                if LayoutEngine._replace_na_values(v) != ""
            ]
        if isinstance(value, dict):
            cleaned_dict = {}
            for k, v in value.items():
                cleaned_value = LayoutEngine._replace_na_values(v)
                if cleaned_value != "":
                    cleaned_dict[k] = cleaned_value
            return cleaned_dict
        return value

    @staticmethod
    def render_cv_html(data: Dict, trim: bool = False, language: str = "fr") -> str:
        """
        Render CV data to HTML using exact Postulae template.

        Args:
            data: CV content dictionary
            trim: Apply trimming if True
            language: Language for rendering ("fr" or "en")

        Returns:
            HTML string with exact layout

        Raises:
            ValueError: If template rendering fails
        """
        try:
            normalized_data = LayoutEngine.normalize_cv_data(data, trim=trim, language=language)

            env = Environment(loader=FileSystemLoader(str(LayoutEngine.TEMPLATES_DIR)))
            template = env.get_template("grid_template.html")

            return template.render(**normalized_data)

        except Exception as e:
            raise ValueError(f"Failed to render HTML template: {str(e)}")

    @staticmethod
    def html_to_pdf(html: str) -> bytes:
        """
        Convert HTML to PDF using xhtml2pdf with exact layout preservation.

        Args:
            html: HTML string

        Returns:
            PDF bytes

        Raises:
            ValueError: If PDF generation fails
        """
        pdf_stream = io.BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf_stream, encoding="UTF-8")

        if pisa_status.err:
            raise ValueError(f"PDF generation failed with {pisa_status.err} errors")

        pdf_bytes = pdf_stream.getvalue()

        if not pdf_bytes:
            raise ValueError("PDF generation produced empty file")

        return pdf_bytes

    @staticmethod
    def generate_pdf_from_data(data: Dict, trim: bool = False, language: str = "fr") -> bytes:
        """
        Generate PDF directly from CV data (convenience method).

        Args:
            data: CV content dictionary
            trim: Apply trimming if True
            language: Language for rendering ("fr" or "en")

        Returns:
            PDF bytes
        """
        html = LayoutEngine.render_cv_html(data, trim=trim, language=language)
        return LayoutEngine.html_to_pdf(html)
