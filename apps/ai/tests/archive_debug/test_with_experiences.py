"""
Test with experiences properly extracted
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
print("TEST: BAD_CV.png with experiences")
print("="*70)

# Extract text
print("\n[1] Extracting text...")
text = extract_text_from_pdf_bytes(pdf_bytes, filename="bad_cv.pdf")
print(f"Extracted: {len(text)} characters")

# Generate FR content
print("\n[2] Generating FR content...")
content = generate_cv_content(
    input_data={"raw_text": text},
    domain="finance",
    language="fr",
    enrichment_mode=False,
)

print(f"\nGenerated content:")
print(f"  Name: {content.get('contact_information', [{}])[0].get('name', 'N/A')}")
print(f"  Work experiences: {len(content.get('work_experience', []))}")
print(f"  Education: {len(content.get('education', []))}")

# Show experiences
if content.get('work_experience'):
    print(f"\nWork Experiences:")
    for i, exp in enumerate(content['work_experience']):
        print(f"\n  [{i+1}] {exp.get('position', 'N/A')}")
        print(f"      Company: {exp.get('company', 'N/A')}")
        print(f"      Date: {exp.get('date', 'N/A')}")
        print(f"      Location: {exp.get('location', 'N/A')}")
        print(f"      Duration: {exp.get('duration', 'N/A')}")
        print(f"      Bullets: {len(exp.get('bullets', []))}")
        for j, b in enumerate(exp.get('bullets', [])):
            print(f"        {j+1}. {b}")

# Measure PFR
print("\n[3] Generating PDF and measuring PFR...")
layout = LayoutEngine()
density = DensityCalculator()

# IMPORTANT: Use the correct key for layout_engine
# The layout engine expects 'experience' not 'work_experience'
# Let's check if we need to normalize the data

# Normalize: copy work_experience to experience if missing
if 'work_experience' in content and 'experience' not in content:
    content['experience'] = content['work_experience']

pdf_out = layout.generate_pdf_from_data(content, trim=False)
metrics = density.calculate_pfr(pdf_out)

print(f"\n  PFR: {metrics.fill_percentage}%")
print(f"  Pages: {metrics.page_count}")
print(f"  Characters: {metrics.char_count}")

print("\n[4] VALIDATION:")
if metrics.fill_percentage >= 90:
    print(f"  [OK] OPTIMAL - PFR >= 90%")
elif metrics.fill_percentage >= 65:
    print(f"  [OK] ACCEPTABLE - PFR >= 65% (will attempt enrichment)")
else:
    print(f"  [BLOCKED] TOO LOW - PFR < 65%")
    print(f"\n  With 2 experiences and 6 total bullets, PFR is still {metrics.fill_percentage}%")
    print(f"  This suggests the bullets are too short or there's not enough content.")
    print(f"  Enrichment will add more bullets to reach 90-95% target.")

# Try enrichment if needed
if 65 <= metrics.fill_percentage < 90:
    print("\n[5] Applying enrichment (PFR < 90%)...")
    from app.enrichment import ContentEnricher

    enricher = ContentEnricher()
    enriched_content = enricher.incremental_enrich_content(
        content=content,
        current_metrics=metrics,
        domain="finance",
        language="fr",
        original_text=text,
    )

    # Check how many bullets were added
    original_bullets = sum(len(exp.get('bullets', [])) for exp in content.get('experience', []))
    enriched_bullets = sum(len(exp.get('bullets', [])) for exp in enriched_content.get('experience', []))
    print(f"  Bullets: {original_bullets} -> {enriched_bullets} (+{enriched_bullets - original_bullets})")

    # Measure new PFR
    pdf_enriched = layout.generate_pdf_from_data(enriched_content, trim=False)
    metrics_enriched = density.calculate_pfr(pdf_enriched)

    print(f"  PFR after enrichment: {metrics_enriched.fill_percentage}%")
    print(f"  Delta: +{metrics_enriched.fill_percentage - metrics.fill_percentage:.1f}%")

    if metrics_enriched.fill_percentage >= 90:
        print(f"\n  [OK] SUCCESS - Reached target PFR!")
        # Save
        os.makedirs("Output", exist_ok=True)
        with open("Output/bad_cv_enriched_success.pdf", "wb") as f:
            f.write(pdf_enriched)
        print(f"  Saved: Output/bad_cv_enriched_success.pdf")
    else:
        print(f"\n  [SUBOPTIMAL] PFR {metrics_enriched.fill_percentage}% - accepted (single-pass limit)")
