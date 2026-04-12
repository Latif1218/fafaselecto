"""
Test BAD_CV with enrichment_mode=True from start
"""
import os
from PIL import Image
import io
from app.llm_client import extract_text_from_pdf_bytes, generate_cv_content
from app.density import DensityCalculator
from app.layout import LayoutEngine

input_path = "input/BAD_CV.png"

# Convert PNG to PDF
with open(input_path, "rb") as f:
    png_bytes = f.read()

img = Image.open(io.BytesIO(png_bytes))
if img.mode != 'RGB':
    img = img.convert('RGB')

pdf_buffer = io.BytesIO()
img.save(pdf_buffer, format='PDF')
pdf_bytes = pdf_buffer.getvalue()

print("="*70)
print("TEST: BAD_CV with enrichment_mode=True")
print("="*70)

# Extract
print("\n[1] Extracting text...")
text = extract_text_from_pdf_bytes(pdf_bytes, filename="bad_cv.pdf")
print(f"Extracted: {len(text)} characters")

# Generate with enrichment_mode=True
print("\n[2] Generating with enrichment_mode=True...")
content = generate_cv_content(
    input_data={"raw_text": text},
    domain="finance",
    language="fr",
    enrichment_mode=True,  # ← TRY WITH ENRICHMENT
)

print(f"\nGenerated content:")
print(f"  Name: {content.get('name', 'N/A')}")
print(f"  Experiences: {len(content.get('experience', []))}")
print(f"  Education: {len(content.get('education', []))}")
print(f"  Skills: {len(content.get('it_skills', []))}")

if content.get('experience'):
    print(f"\nExperiences:")
    for i, exp in enumerate(content['experience']):
        title = exp.get('title', 'N/A')
        company = exp.get('company', 'N/A')
        bullets = exp.get('bullets', [])
        print(f"  [{i+1}] {title} @ {company}")
        print(f"      Bullets: {len(bullets)}")
        for b in bullets:
            print(f"        - {b}")
else:
    print("\n  [!] STILL 0 EXPERIENCES - enrichment_mode didn't help")

# Measure PFR
print("\n[3] Measuring PFR...")
layout = LayoutEngine()
density = DensityCalculator()

pdf_out = layout.generate_pdf_from_data(content, trim=False)
metrics = density.calculate_pfr(pdf_out)

print(f"  PFR: {metrics.fill_percentage}%")
print(f"  Pages: {metrics.page_count}")
print(f"  Characters: {metrics.char_count}")
print(f"  Status: {'BLOCKED (<65%)' if metrics.fill_percentage < 65 else 'OK'}")

if metrics.fill_percentage >= 65:
    # Save if successful
    os.makedirs("Output", exist_ok=True)
    with open("Output/bad_cv_enriched_fr.pdf", "wb") as f:
        f.write(pdf_out)
    print(f"\n  [OK] Saved: Output/bad_cv_enriched_fr.pdf")
else:
    print(f"\n  [BLOCKED] Still below 65% threshold")
    print(f"\n  This confirms the issue is with LLM content generation quality,")
    print(f"  not with the hardening logic (which correctly blocks insufficient content).")
