"""
Test simple: ZÉRO débordement 2 pages, PFR flexible.

Teste avec Gautier ROUAS (débordement EN dans batch V6).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import CVGenerator
from app.llm_client import extract_text_from_pdf_bytes
from app.llm_client_anthropic import generate_cv_content_claude, translate_cv_content_claude, MODEL_SONNET, MODEL_HAIKU
from app.content_analyzer import ContentAnalyzer
from app.enrichment import ContentEnricher
from app.density import DensityCalculator
from app.layout_playwright import generate_pdf_from_data
from datetime import datetime


def test_overflow_simple():
    """Test anti-overflow avec 1 CV."""

    pdf_path = Path(r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\v2\Gautier ROUAS - Community Manager Chine 103368148.pdf")

    if not pdf_path.exists():
        print(f"[SKIP] File not found: {pdf_path}")
        return

    print("=" * 80)
    print("TEST OVERFLOW SIMPLE - Gautier ROUAS")
    print("=" * 80)
    print()

    # Read PDF
    pdf_bytes = pdf_path.read_bytes()

    # Extract text
    print("[1/6] Extracting text from PDF...")
    input_data = extract_text_from_pdf_bytes(pdf_bytes)
    print(f"  Extracted: {len(input_data['raw_text'])} chars")
    print()

    # Analyze content
    print("[2/6] Analyzing content richness...")
    analyzer = ContentAnalyzer()
    analysis = analyzer.analyze_content(input_data['raw_text'])
    print(f"  Richness: {analysis['richness']}")
    print(f"  Strategy: {analysis['strategy']}")
    print(f"  Target PFR: {analysis['target_pfr']}")
    print()

    # Generate FR content
    print("[3/6] Generating FR content...")
    enrichment_instructions = analyzer.get_enrichment_instructions(analysis['strategy'], 'fr')

    with open("app/prompts/base_system.txt", "r", encoding="utf-8") as f:
        base_system_prompt = f.read()

    content_fr = generate_cv_content_claude(
        input_data=input_data,
        system_prompt=base_system_prompt,
        domain="finance",
        language="fr",
        model=MODEL_SONNET,
        enrichment_instructions=enrichment_instructions,
    )
    print(f"  Generated FR content")
    print()

    # Translate to EN
    print("[4/6] Translating to EN...")
    content_en = translate_cv_content_claude(
        cv_content=content_fr,
        target_language="en",
        model=MODEL_HAIKU
    )
    print(f"  Translated to EN")
    print()

    # Generate PDFs
    print("[5/6] Generating PDFs...")
    pdf_fr = generate_pdf_from_data(content_fr, trim=False, language="fr")
    pdf_en = generate_pdf_from_data(content_en, trim=False, language="en")
    print(f"  Generated FR PDF: {len(pdf_fr)} bytes")
    print(f"  Generated EN PDF: {len(pdf_en)} bytes")
    print()

    # Measure PFR
    print("[6/6] Measuring PFR...")
    density_calc = DensityCalculator()
    metrics_fr = density_calc.calculate_pfr(pdf_fr)
    metrics_en = density_calc.calculate_pfr(pdf_en)
    print(f"  FR: {metrics_fr.fill_percentage:.1f}% PFR, {metrics_fr.page_count} page(s)")
    print(f"  EN: {metrics_en.fill_percentage:.1f}% PFR, {metrics_en.page_count} page(s)")
    print()

    # Check overflow
    overflow_fr = (metrics_fr.page_count > 1)
    overflow_en = (metrics_en.page_count > 1)

    # Results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)

    if not overflow_fr and not overflow_en:
        print("[OK] NO OVERFLOW - Both FR and EN are 1 page")
        print(f"  FR: {metrics_fr.fill_percentage:.1f}% PFR")
        print(f"  EN: {metrics_en.fill_percentage:.1f}% PFR")

        # Save PDFs
        today = datetime.now().strftime("%Y-%m-%d")
        output_dir = Path(f"output/{today}/overflow_test")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_fr = output_dir / "Gautier_ROUAS_fr_no_overflow.pdf"
        output_en = output_dir / "Gautier_ROUAS_en_no_overflow.pdf"

        output_fr.write_bytes(pdf_fr)
        output_en.write_bytes(pdf_en)

        print(f"\nSaved: {output_fr}, {output_en}")
    else:
        print("[FAIL] OVERFLOW DETECTED")
        if overflow_fr:
            print(f"  FR: {metrics_fr.page_count} pages ({metrics_fr.fill_percentage:.1f}% PFR)")
        if overflow_en:
            print(f"  EN: {metrics_en.page_count} pages ({metrics_en.fill_percentage:.1f}% PFR)")


if __name__ == "__main__":
    test_overflow_simple()
