# Cover Letter Generator - Guide d'Intégration Production

## 🎯 Pipeline Complet: PDF CV → Cover Letter PDF

### Workflow Utilisateur

```
1. User upload CV (PDF)
2. User paste job offer (text)
3. User add optional notes (motivations)
4. Backend génère cover letter (FR ou EN ou les deux)
5. User télécharge PDF + DOCX
```

---

## 📋 Étape 1: Extraction CV PDF → JSON

**IMPORTANT**: Le cover letter generator suppose que le CV est déjà structuré en JSON (output du CV generator Postulae). Si l'utilisateur upload un PDF brut, il faut d'abord l'extraire.

### Option A: Utiliser le CV Generator Postulae (RECOMMANDÉ)

```python
from app.generator import generate_cv
from app.llm_client import extract_text_from_pdf_bytes

# Step 1: Extract PDF
with open("cv.pdf", "rb") as f:
    pdf_bytes = f.read()

raw_text = extract_text_from_pdf_bytes(pdf_bytes)

# Step 2: Structure CV avec Postulae pipeline
cv_result = generate_cv(
    raw_text=raw_text,
    domain="finance",  # ou "consulting", "tech", etc.
    language="fr"
)

cv_data = cv_result["cv_content"]  # JSON structuré
```

**Avantage**: CV déjà optimisé, structuré, validé (garantit qualité cover letter)

---

### Option B: Extraction Directe PDF → JSON (Si pas de CV Postulae)

```python
from app.llm_client_anthropic import generate_cv_content_claude
from app.llm_client import extract_text_from_pdf_bytes

# Step 1: Extract text
with open("cv_externe.pdf", "rb") as f:
    pdf_bytes = f.read()

raw_text = extract_text_from_pdf_bytes(pdf_bytes)

# Step 2: Structure avec Claude (minimal)
cv_data = generate_cv_content_claude(
    input_data={"raw_text": raw_text},
    system_prompt=load_prompt("base_system.txt"),
    language="fr"
)
```

**Inconvénient**: Pas optimisé comme CV Postulae, peut manquer de qualité

---

## 📋 Étape 2: Génération Cover Letter

```python
from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files

# Generate content (FR + EN)
result = generate_cover_letter(
    cv_data=cv_data,  # JSON from Step 1
    job_offer=job_offer_text,  # Pasted by user
    additional_notes=user_notes,  # Optional
    language="fr",  # Primary language
    generate_both_languages=True  # FR + EN
)

# Generate PDFs
output_dir = f"output/user_{user_id}"

for lang in ["fr", "en"]:
    pdf_result = generate_cover_letter_files(
        cover_letter=result[f'cover_letter_{lang}'],
        cv_data=cv_data,
        job_requirements=result['job_requirements'],
        output_dir=output_dir,
        filename_base=f"cover_letter_{job_id}",
        language=lang,
        generate_docx=True
    )

    print(f"{lang.upper()}: {pdf_result['pdf_path']}")

    # CRITICAL: Validate page count
    if pdf_result['page_count'] != 1:
        raise ValueError(f"Cover letter overflows to {pdf_result['page_count']} pages")
```

---

## ⚠️ Validations Critiques

### 1. Page Count = 1 (NON NÉGOCIABLE)

```python
# After PDF generation
from PyPDF2 import PdfReader

reader = PdfReader(pdf_path)
page_count = len(reader.pages)

if page_count != 1:
    # BLOCK generation, trim content, regenerate
    raise ValueError(f"Cover letter {page_count} pages (MUST be 1)")
```

### 2. Word Count 240-280

```python
word_count = len(cover_letter.split())

if word_count > 280:
    # BLOCK - prompt LLM failed constraints
    raise ValueError(f"Cover letter too long ({word_count} words, max 280)")

if word_count < 240:
    # WARNING - may look sparse
    warnings.append(f"Cover letter short ({word_count} words)")
```

### 3. No Duplicates (Signature, Closing)

```python
# Check for duplicate signatures
if cover_letter.count(candidate_name) > 2:
    # ISSUE: Name appears >2 times (1 in opening context, 1 in signature = max 2)
    warnings.append("Duplicate signature detected")
```

### 4. No LinkedIn/Contact Info

```python
# Check for forbidden content
forbidden = ["linkedin", "http://", "https://", "@", "tel:", "+33", "+1"]

for forbidden_term in forbidden:
    if forbidden_term.lower() in cover_letter.lower():
        warnings.append(f"Forbidden content detected: {forbidden_term}")
```

---

## 🔧 Pipeline Flask Complet

```python
from flask import Flask, request, jsonify, send_file
from app.generator import generate_cv
from app.llm_client import extract_text_from_pdf_bytes
from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files

app = Flask(__name__)

@app.route('/api/cover-letter/generate', methods=['POST'])
def generate_cover_letter_endpoint():
    """
    Generate cover letter from CV PDF + job offer.

    Expects:
    - cv_pdf: File upload (PDF bytes)
    - job_offer: Text (copy-pasted)
    - additional_notes: Text (optional)
    - language: "fr" or "en"
    - generate_both: Boolean
    """
    try:
        # Step 1: Extract CV PDF
        cv_pdf = request.files['cv_pdf']
        pdf_bytes = cv_pdf.read()

        raw_text = extract_text_from_pdf_bytes(pdf_bytes)

        # Step 2: Structure CV (use Postulae pipeline)
        cv_result = generate_cv(
            raw_text=raw_text,
            domain=request.form.get('domain', 'finance'),
            language=request.form.get('language', 'fr')
        )

        cv_data = cv_result["cv_content"]

        # Step 3: Generate cover letter
        job_offer = request.form.get('job_offer')
        additional_notes = request.form.get('additional_notes', '')
        language = request.form.get('language', 'fr')
        generate_both = request.form.get('generate_both', 'true').lower() == 'true'

        result = generate_cover_letter(
            cv_data=cv_data,
            job_offer=job_offer,
            additional_notes=additional_notes,
            language=language,
            generate_both_languages=generate_both
        )

        # Step 4: Generate PDFs
        user_id = request.form.get('user_id', 'anonymous')
        job_id = request.form.get('job_id', 'job')
        output_dir = f"output/user_{user_id}"

        pdf_paths = {}

        for lang in (['fr', 'en'] if generate_both else [language]):
            if result.get(f'cover_letter_{lang}'):
                pdf_result = generate_cover_letter_files(
                    cover_letter=result[f'cover_letter_{lang}'],
                    cv_data=cv_data,
                    job_requirements=result['job_requirements'],
                    output_dir=output_dir,
                    filename_base=f"cover_letter_{job_id}",
                    language=lang,
                    generate_docx=True
                )

                # VALIDATE: Page count MUST be 1
                if pdf_result['page_count'] != 1:
                    return jsonify({
                        'success': False,
                        'error': f"Cover letter {lang.upper()} overflows to {pdf_result['page_count']} pages (must be 1)"
                    }), 400

                pdf_paths[lang] = {
                    'pdf': pdf_result['pdf_path'],
                    'docx': pdf_result['docx_path'],
                    'word_count': pdf_result['word_count'],
                    'warnings': pdf_result['warnings']
                }

        return jsonify({
            'success': True,
            'cover_letters': {
                'fr': result.get('cover_letter_fr'),
                'en': result.get('cover_letter_en')
            },
            'files': pdf_paths,
            'metadata': {
                'cost': result['cost_estimate'],
                'time': result['generation_time'],
                'word_count_fr': result.get('word_count_fr'),
                'word_count_en': result.get('word_count_en')
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cover-letter/download/<lang>/<filename>')
def download_cover_letter(lang, filename):
    """Download generated cover letter PDF or DOCX."""
    file_path = f"output/{filename}"
    return send_file(file_path, as_attachment=True)
```

---

## 🚨 Checklist Production

### Avant Mise en Production

- [ ] **Test extraction PDF → JSON** sur 10+ CVs variés
- [ ] **Test génération cover letter** sur 10+ job offers variés
- [ ] **Validate page count = 1** sur TOUS les tests (0% tolérance)
- [ ] **Check no duplicates** (signature, closing)
- [ ] **Check no LinkedIn/URLs** dans le texte
- [ ] **Check word count 240-280** (100% des cas)
- [ ] **Test FR + EN** (traduction preserve metrics)
- [ ] **Monitor costs** ($0.015 target)
- [ ] **Monitor time** (<30s target)

### Monitoring Production

```python
# Track metrics
metrics = {
    'total_generated': 0,
    'page_overflow_rate': 0.0,  # Must be 0%
    'word_count_avg': 0.0,      # Target 260-275
    'cost_avg': 0.0,             # Target $0.015
    'time_avg': 0.0,             # Target <30s
    'warnings_rate': 0.0         # Track warnings
}
```

---

## 📊 Exemple Complet

```python
# Complete pipeline example
from app.llm_client import extract_text_from_pdf_bytes
from app.generator import generate_cv
from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files

# Step 1: Extract CV
with open("fayed_cv.pdf", "rb") as f:
    pdf_bytes = f.read()

raw_text = extract_text_from_pdf_bytes(pdf_bytes)

# Step 2: Generate CV JSON
cv_result = generate_cv(
    raw_text=raw_text,
    domain="finance",
    language="fr"
)

cv_data = cv_result["cv_content"]

# Step 3: Generate cover letter
job_offer = """
Goldman Sachs - Investment Banking Analyst (M&A)
Paris, France
...
"""

result = generate_cover_letter(
    cv_data=cv_data,
    job_offer=job_offer,
    additional_notes="Passionate about M&A",
    language="fr",
    generate_both_languages=True
)

# Step 4: Generate PDFs
for lang in ["fr", "en"]:
    pdf_result = generate_cover_letter_files(
        cover_letter=result[f'cover_letter_{lang}'],
        cv_data=cv_data,
        job_requirements=result['job_requirements'],
        output_dir="output/fayed",
        filename_base="cover_letter_goldman",
        language=lang,
        generate_docx=True
    )

    print(f"{lang.upper()}:")
    print(f"  PDF: {pdf_result['pdf_path']}")
    print(f"  Pages: {pdf_result['page_count']} (MUST be 1)")
    print(f"  Words: {pdf_result['word_count']}")

    if pdf_result['warnings']:
        for warning in pdf_result['warnings']:
            print(f"  WARNING: {warning}")
```

---

**Dernière mise à jour**: 1er avril 2026
**Status**: Production-ready avec validations strictes
