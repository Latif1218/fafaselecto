# Cover Letter Generator API Documentation

## Overview

The Cover Letter Generator creates premium, ATS-optimized cover letters for elite finance and consulting roles (Goldman Sachs, McKinsey, BCG, JP Morgan, Bain, etc.).

**Stack:**
- **LLM:** Claude Sonnet 4.5 (generation) + Haiku 3 (extraction + translation)
- **Layout:** Jinja2 + Playwright (PDF) + pdf2docx (DOCX)
- **Pricing:** ~$0.015 per cover letter (FR+EN)
- **Time:** ~20-25 seconds

---

## Quick Start

```python
from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files

# 1. Prepare CV data (from Postulae CV generator)
cv_data = {
    "contact_information": [...],
    "education": [...],
    "work_experience": [...],
    "it_skills": [...],
    "language_skills": [...]
}

# 2. Provide job offer text (copy-pasted by user)
job_offer = """
Goldman Sachs - Investment Banking Analyst (M&A)
Paris, France

Requirements:
- 0-2 years experience
- Strong financial modeling (DCF, LBO)
- English + French fluency
...
"""

# 3. Optional user notes
additional_notes = "Passionné par M&A cross-border, admire culture méritocratique"

# 4. Generate cover letter
result = generate_cover_letter(
    cv_data=cv_data,
    job_offer=job_offer,
    additional_notes=additional_notes,
    language="fr",  # Primary language
    generate_both_languages=True  # Generate FR + EN
)

# 5. Generate PDF/DOCX
for lang, letter in [("fr", result['cover_letter_fr']), ("en", result['cover_letter_en'])]:
    pdf_result = generate_cover_letter_files(
        cover_letter=letter,
        cv_data=cv_data,
        job_requirements=result['job_requirements'],
        output_dir="output/cover_letters",
        filename_base=f"cover_letter_{user_id}",
        language=lang,
        generate_docx=True
    )
    print(f"Generated: {pdf_result['pdf_path']}")
```

---

## API Reference

### `generate_cover_letter()`

Main orchestrator function. Generates cover letter content from CV and job offer.

**Function:**
```python
def generate_cover_letter(
    cv_data: Dict,
    job_offer: str,
    additional_notes: Optional[str] = None,
    language: str = "fr",
    generate_both_languages: bool = False
) -> Dict
```

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `cv_data` | `Dict` | Yes | Structured CV data from Postulae CV generator |
| `job_offer` | `str` | Yes | Raw job offer text (copy-pasted by user) |
| `additional_notes` | `str` | No | User notes (motivations, networking, specific interests) |
| `language` | `str` | No | Primary language (`"fr"` or `"en"`). Default: `"fr"` |
| `generate_both_languages` | `bool` | No | Generate both FR and EN. Default: `False` |

**Returns:** `Dict`

```python
{
    "job_requirements": {
        "company_name": "Goldman Sachs",
        "position": "Investment Banking Analyst",
        "division": "M&A",
        "required_skills": ["Financial modeling", "DCF", ...],
        "experience_years": "0-2",
        "sector": "Finance - Investment Banking",
        "key_values": ["Meritocracy", "Intellectual rigor", ...],
        "key_responsibilities": [...]
    },
    "matched_data": {
        "matched_achievements": [...],  # Top 2-3 achievements from CV
        "matched_skills": [...],
        "cultural_fit_signals": [...]
    },
    "cover_letter_fr": "Madame, Monsieur, ...",  # French cover letter text
    "cover_letter_en": "Dear Hiring Manager, ...",  # English cover letter text (if generate_both_languages=True)
    "word_count_fr": 350,
    "word_count_en": 320,
    "generation_time": 23.5,  # seconds
    "cost_estimate": 0.0150  # USD
}
```

**Errors:**
- `ValueError`: If job extraction fails, generation fails, or constraints not met

---

### `generate_cover_letter_files()`

Generates PDF and DOCX files from cover letter text.

**Function:**
```python
def generate_cover_letter_files(
    cover_letter: str,
    cv_data: Dict,
    job_requirements: Dict,
    output_dir: str,
    filename_base: str,
    language: str = "fr",
    generate_docx: bool = True
) -> Dict
```

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `cover_letter` | `str` | Yes | Cover letter text (from `generate_cover_letter()`) |
| `cv_data` | `Dict` | Yes | CV data (for header/contact) |
| `job_requirements` | `Dict` | Yes | Job requirements (from `generate_cover_letter()`) |
| `output_dir` | `str` | Yes | Output directory path |
| `filename_base` | `str` | Yes | Base filename (e.g., `"cover_letter_user123"`) |
| `language` | `str` | No | Language (`"fr"` or `"en"`). Default: `"fr"` |
| `generate_docx` | `bool` | No | Also generate DOCX. Default: `True` |

**Returns:** `Dict`

```python
{
    "pdf_path": "output/cover_letters/cover_letter_user123_fr.pdf",
    "docx_path": "output/cover_letters/cover_letter_user123_fr.docx",
    "page_count": 1,
    "word_count": 350,
    "warnings": ["Cover letter long (413 words), may overflow 1 page"]
}
```

**Errors:**
- `FileNotFoundError`: If template not found
- `ValueError`: If PDF generation fails or page count != 1

---

## Pipeline Steps

### 1. Extract Job Requirements (Haiku 3)

Analyzes job offer text and extracts structured data.

**Input:**
```
Goldman Sachs - Investment Banking Analyst (M&A)
Paris, France

Requirements:
- 0-2 years experience in finance
- Strong financial modeling (DCF, LBO)
...
```

**Output:**
```json
{
  "company_name": "Goldman Sachs",
  "position": "Investment Banking Analyst",
  "division": "M&A",
  "required_skills": ["Financial modeling", "DCF", "LBO"],
  "experience_years": "0-2",
  "sector": "Finance - Investment Banking",
  "key_values": ["Meritocracy", "Client-first"],
  "key_responsibilities": [...]
}
```

**Cost:** ~$0.0002 per extraction

---

### 2. Match CV to Job (Internal Logic)

Matches CV achievements to job requirements without LLM call.

**Logic:**
- Scan `work_experience` for skill keyword matches
- Prioritize experiences with quantified metrics (%, €, $)
- Detect cultural fit signals (collaboration, leadership, analytical)
- Return top 2-3 most relevant achievements

**Output:**
```json
{
  "matched_achievements": [
    {
      "company": "Rothschild & Co",
      "role": "Investment Banking Intern",
      "responsibilities": [...],
      "skill_match_count": 3
    }
  ],
  "matched_skills": ["Financial Modeling", "Python"],
  "cultural_fit_signals": ["Client-first", "Collaboration"]
}
```

**Cost:** $0 (no LLM)

---

### 3. Generate Cover Letter (Sonnet 4.5)

Generates 250-400 word cover letter following strict structure.

**Prompt constraints:**
- **Length:** 250-400 words (target: 300-350)
- **Structure:** 5 paragraphs (opening + 2 achievements + why company + closing)
- **Tone:** Formal FR (vouvoiement) or professional EN
- **Metrics:** Minimum 2-3 quantified achievements
- **Company mentions:** 2-3×
- **Zero invention:** Uses only facts from CV

**Output:**
```
Madame, Monsieur,

Diplômé de HEC Paris avec une expérience concrète en M&A, je souhaite rejoindre
Goldman Sachs en tant qu'Analyste Investment Banking...

[350 words total]

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Fayed HANAFI
```

**Cost:** ~$0.0145 per generation

---

### 4. Translate (Haiku 3, optional)

Translates cover letter from FR→EN or EN→FR.

**Constraints:**
- Preserve all metrics exactly (22% stays 22%, €450M stays €450M)
- Adapt formulas (Madame, Monsieur → Dear Hiring Manager)
- Adapt closing (Salutations distinguées → Sincerely)
- Maintain word count ±10%

**Cost:** ~$0.0003 per translation

---

### 5. Layout PDF/DOCX (Playwright + pdf2docx)

Generates PDF using Chromium headless rendering.

**Template:** `cover_letter_template.html`
- **Marges:** 20mm top/bottom, 25mm left/right
- **Font:** Times New Roman, 11pt
- **Line-height:** 1.5 (aéré, pas compressé)
- **Sections:** Header, Date, Recipient, Opening, Body (3-5 §), Closing, Signature

**DOCX conversion:** pdf2docx library

**Cost:** $0 (self-hosted)

---

## Quality Metrics

### Validation Criteria

| Metric | Target | Hard Limit | Action if Failed |
|---|---|---|---|
| Word count | 300-350 | 250-450 | Regenerate or warn user |
| Paragraph count | 4-5 | ≥4 | Regenerate |
| Company mentions | 2-3× | ≥2 | Regenerate |
| Quantified metrics | 2-3 | ≥2 | Warn user (low impact) |
| Page count | 1 | 1 exactly | **BLOCK** generation |
| Cost | <$0.015 | <$0.020 | Optimize prompts |
| Time | 15-25s | <30s | Acceptable |

### Warning System

**🟢 GREEN (Success):**
- Word count: 280-380
- Metrics: 2-3 quantified
- Company mentions: 2-3×
- Page count: 1
- No issues

**🟠 ORANGE (Warning):**
- Word count: 250-280 or 380-420
- Metrics: 1 quantified
- Company mentioned 1×
- → Action: Show warning, allow user to proceed

**🔴 RED (Block):**
- Word count: <250 or >450
- Page count: ≠ 1
- Company not mentioned
- → Action: BLOCK generation, show error

---

## Cost Breakdown

### Per Cover Letter (FR only)

| Step | Model | Cost |
|---|---|---|
| Extract job requirements | Claude Haiku 3 | $0.0002 |
| Generate cover letter | Claude Sonnet 4.5 | $0.0145 |
| PDF generation | Playwright (self-hosted) | $0.0000 |
| **TOTAL FR** | | **$0.0147** |

### Per Cover Letter (FR + EN)

| Step | Model | Cost |
|---|---|---|
| Extract job requirements | Claude Haiku 3 | $0.0002 |
| Generate FR | Claude Sonnet 4.5 | $0.0145 |
| Translate EN | Claude Haiku 3 | $0.0003 |
| PDF generation (2×) | Playwright | $0.0000 |
| **TOTAL FR+EN** | | **$0.0150** |

### Subscription Limits (based on Anthropic API limits)

**Assumptions:**
- Abonnement 20€/mois → ~$22 credits
- Abonnement 150€/mois → ~$165 credits
- Cost per cover letter: $0.015 (FR+EN)

| Subscription | Monthly Cost | Cover Letters/Month |
|---|---|---|
| 20€/mois | $22 | **1,467 cover letters** |
| 150€/mois | $165 | **11,000 cover letters** |

---

## Example Usage

### Basic Usage (FR only)

```python
from app.cover_letter_generator import generate_cover_letter

result = generate_cover_letter(
    cv_data=my_cv,
    job_offer=job_text,
    language="fr",
    generate_both_languages=False
)

print(f"Generated in {result['generation_time']:.2f}s")
print(f"Cost: ${result['cost_estimate']:.4f}")
print(f"Word count: {result['word_count_fr']}")
print(result['cover_letter_fr'])
```

### Advanced Usage (FR + EN with PDF)

```python
from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files

# Generate content
result = generate_cover_letter(
    cv_data=cv_data,
    job_offer=job_offer,
    additional_notes="Passionate about M&A, networking with analysts",
    language="fr",
    generate_both_languages=True
)

# Generate PDFs
for lang in ["fr", "en"]:
    letter = result[f'cover_letter_{lang}']

    pdf_result = generate_cover_letter_files(
        cover_letter=letter,
        cv_data=cv_data,
        job_requirements=result['job_requirements'],
        output_dir=f"output/user_{user_id}",
        filename_base=f"cover_letter_{job_id}",
        language=lang,
        generate_docx=True
    )

    print(f"{lang.upper()}: {pdf_result['pdf_path']}")
    print(f"  Pages: {pdf_result['page_count']}")
    print(f"  Words: {pdf_result['word_count']}")

    if pdf_result['warnings']:
        for warning in pdf_result['warnings']:
            print(f"  [WARN] {warning}")
```

### Error Handling

```python
try:
    result = generate_cover_letter(
        cv_data=cv_data,
        job_offer=job_offer,
        language="fr"
    )

    # Validate word count
    if result['word_count_fr'] < 280:
        print("[WARN] Cover letter short, consider adding achievements")
    elif result['word_count_fr'] > 400:
        print("[WARN] Cover letter long, may overflow 1 page")

    # Generate PDF
    pdf_result = generate_cover_letter_files(
        cover_letter=result['cover_letter_fr'],
        cv_data=cv_data,
        job_requirements=result['job_requirements'],
        output_dir="output",
        filename_base="cover_letter",
        language="fr"
    )

    # Validate page count
    if pdf_result['page_count'] != 1:
        raise ValueError(f"Page count is {pdf_result['page_count']}, must be 1 page exactly")

except ValueError as e:
    print(f"[ERROR] Generation failed: {str(e)}")
    # Fallback: Retry with shorter prompts or manual intervention
```

---

## Testing

### Unit Tests

```bash
# Run all cover letter tests
python tests/test_cover_letter.py

# Run Fayed reference test
python tests/test_cover_letter_fayed.py
```

### Test Outputs

**Expected results (Fayed + Goldman Sachs):**
- ✅ Cost: $0.0150
- ✅ Time: 20-25s
- ✅ Word count FR: 380-420
- ✅ Word count EN: 350-380
- ✅ Company mentions: 5× (FR + EN)
- ✅ Metrics: 4+ quantified
- ✅ Page count: 1 (both FR and EN)

---

## Limitations & Known Issues

### Current Limitations

1. **Word count variance:** LLM may generate 250-450 words (target: 300-350)
   - **Solution:** Accept range 250-420, warn if >380

2. **Company name extraction:** Sometimes fails if job offer poorly formatted
   - **Solution:** Fallback to user input or manual override

3. **CV-to-job matching:** Basic keyword matching, may miss nuanced fits
   - **Solution:** Future: Use LLM-based semantic matching

4. **PDF page overflow:** If >420 words, may overflow to 2 pages
   - **Solution:** Hard block if page_count != 1, ask user to simplify

### Future Improvements

- [ ] **A/B test prompts** for optimal word count (300-350 consistently)
- [ ] **Semantic CV-job matching** (use LLM embedding similarity)
- [ ] **Cover letter scoring** (like CV Grader, 0-100 pts)
- [ ] **Templates per industry** (finance vs consulting vs tech)
- [ ] **Multi-language support** (ES, DE, IT beyond FR/EN)

---

## Production Integration

### SaaS Workflow

```
User flow:
1. User uploads CV → Postulae generates structured CV JSON
2. User copy-pastes job offer
3. User adds optional notes (motivations, networking)
4. System generates cover letter (FR or EN or both)
5. User previews, edits if needed
6. User downloads PDF + DOCX

Backend:
- Store cover letter in DB (user_id, job_id, version)
- Track usage metrics (cost, time, word count)
- Monitor quality (warnings, page overflows)
```

### API Endpoint (Flask example)

```python
@app.route('/api/cover-letter/generate', methods=['POST'])
def generate_cover_letter_endpoint():
    data = request.json

    try:
        result = generate_cover_letter(
            cv_data=data['cv_data'],
            job_offer=data['job_offer'],
            additional_notes=data.get('additional_notes'),
            language=data.get('language', 'fr'),
            generate_both_languages=data.get('both_languages', False)
        )

        # Generate PDFs
        pdf_paths = {}
        for lang in ['fr', 'en']:
            if result.get(f'cover_letter_{lang}'):
                pdf_result = generate_cover_letter_files(
                    cover_letter=result[f'cover_letter_{lang}'],
                    cv_data=data['cv_data'],
                    job_requirements=result['job_requirements'],
                    output_dir=f"output/user_{current_user.id}",
                    filename_base=f"cover_letter_{job_id}",
                    language=lang,
                    generate_docx=True
                )
                pdf_paths[lang] = {
                    'pdf': pdf_result['pdf_path'],
                    'docx': pdf_result['docx_path']
                }

        return jsonify({
            'success': True,
            'cover_letters': {
                'fr': result.get('cover_letter_fr'),
                'en': result.get('cover_letter_en')
            },
            'pdf_paths': pdf_paths,
            'metadata': {
                'cost': result['cost_estimate'],
                'time': result['generation_time'],
                'word_count_fr': result.get('word_count_fr'),
                'word_count_en': result.get('word_count_en')
            }
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

---

**Last updated:** March 31, 2026
**Version:** 1.0
