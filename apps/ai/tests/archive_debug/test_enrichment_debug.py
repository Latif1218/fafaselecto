"""
Debug test for enrichment logic
"""
import os
from app.llm_client import generate_cv_content
from app.density import DensityCalculator
from app.layout import LayoutEngine
from app.enrichment import ContentEnricher

def main():
    # Load test PDF
    input_path = "input/CHLOE.pdf"
    with open(input_path, "rb") as f:
        pdf_bytes = f.read()

    print("\n" + "="*70)
    print("ENRICHMENT DEBUG TEST")
    print("="*70)

    # Extract from PDF
    print("\n[1] Extracting text from PDF...")
    from app.llm_client import extract_text_from_pdf_bytes
    original_text = extract_text_from_pdf_bytes(pdf_bytes, filename="test.pdf")
    print(f"Extracted {len(original_text)} characters")

    # Generate base content
    print("\n[2] Generating base content (FR)...")
    base_content = generate_cv_content(
        input_data={"raw_text": original_text},
        domain="finance",
        language="fr",
        enrichment_mode=False,
    )

    # Check experiences
    experiences = base_content.get("experience", [])
    print(f"\n[3] Analyzing {len(experiences)} experiences:")
    for i, exp in enumerate(experiences):
        title = exp.get("title", "N/A")
        company = exp.get("company", "N/A")
        bullets = exp.get("bullets", [])
        print(f"  [{i}] {title} @ {company}")
        print(f"      Bullets: {len(bullets)}")
        for b in bullets:
            print(f"        - {b[:60]}...")

    # Measure PFR
    print("\n[4] Measuring PFR...")
    layout_engine = LayoutEngine()
    density_calc = DensityCalculator()

    pdf_bytes_base = layout_engine.generate_pdf_from_data(base_content, trim=False)
    metrics = density_calc.calculate_pfr(pdf_bytes_base)

    print(f"  PFR: {metrics.fill_percentage}%")
    print(f"  Pages: {metrics.page_count}")
    print(f"  Characters: {metrics.char_count}")

    # Calculate enrichment needs
    enricher = ContentEnricher()
    pfr_gap = enricher.TARGET_PFR - metrics.fill_percentage
    bullets_needed = int(pfr_gap / enricher.BULLET_PFR_IMPACT)

    print(f"\n[5] Enrichment calculation:")
    print(f"  PFR gap: {pfr_gap:.1f}%")
    print(f"  Bullets needed (estimated): {bullets_needed}")

    # Try enrichment
    print(f"\n[6] Attempting enrichment...")
    enriched_content = enricher.incremental_enrich_content(
        content=base_content,
        current_metrics=metrics,
        domain="finance",
        language="fr",
        original_text=original_text,
    )

    # Check if bullets were added
    enriched_experiences = enriched_content.get("experience", [])
    print(f"\n[7] After enrichment - {len(enriched_experiences)} experiences:")
    bullets_added = 0
    for i, exp in enumerate(enriched_experiences):
        title = exp.get("title", "N/A")
        company = exp.get("company", "N/A")
        bullets = exp.get("bullets", [])
        original_bullets = experiences[i].get("bullets", []) if i < len(experiences) else []
        delta = len(bullets) - len(original_bullets)
        bullets_added += delta

        print(f"  [{i}] {title} @ {company}")
        print(f"      Bullets: {len(original_bullets)} -> {len(bullets)} (delta: +{delta})")
        if delta > 0:
            print(f"      NEW BULLETS:")
            for b in bullets[len(original_bullets):]:
                print(f"        + {b}")

    print(f"\n[8] Summary:")
    print(f"  Total bullets added: {bullets_added}")
    print(f"  Expected: {bullets_needed}")
    print(f"  Success rate: {bullets_added}/{bullets_needed}")

    # Measure new PFR
    pdf_bytes_enriched = layout_engine.generate_pdf_from_data(enriched_content, trim=False)
    metrics_enriched = density_calc.calculate_pfr(pdf_bytes_enriched)

    print(f"\n[9] PFR after enrichment:")
    print(f"  Before: {metrics.fill_percentage}%")
    print(f"  After: {metrics_enriched.fill_percentage}%")
    print(f"  Delta: +{metrics_enriched.fill_percentage - metrics.fill_percentage:.1f}%")

if __name__ == "__main__":
    main()
