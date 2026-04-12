"""
Test script to validate new template calibration with Fayed CV reference

Validates:
1. New CSS values (fonts, margins, columns)
2. Duration display under dates
3. Visual match with input/CV_Fayed_HANAFI_fr_PDF.pdf
"""
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.generator import generate_cv_from_pdf

def main():
    print("\n" + "="*70)
    print("TEMPLATE CALIBRATION TEST - CV Fayed HANAFI")
    print("="*70)

    # Load Fayed CV
    input_path = "input/CV_Fayed_HANAFI_fr_PDF.pdf"
    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found")
        return

    with open(input_path, "rb") as f:
        pdf_bytes = f.read()

    print(f"\n[OK] Loaded: {input_path} ({len(pdf_bytes)} bytes)")

    # Generate French only for quick test
    print("\n[TEST] Generating CV with NEW template calibration...")
    print("Expected changes:")
    print("  - Body font: 10pt (was 9.25pt)")
    print("  - Margins: 0.6in (was 0.45in)")
    print("  - Name: 17pt (was 14pt)")
    print("  - Dates: 10pt bold (was 7.8pt italic)")
    print("  - Lieux: 10pt regular (was 7.6pt italic)")
    print("  - Colonnes: 18% / 57% / 25% (was 25% / 47% / 28%)")
    print("  - Institutions: 10.5pt, line-height 1.0 (was 9pt, 0.7)")
    print("  - Duration: visible sous dates")

    start_time = time.time()

    try:
        results = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr"]  # French only for quick test
        )

        total_time = time.time() - start_time

        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)

        if "fr" in results:
            fr = results["fr"]
            print(f"\n[FR] French CV:")
            print(f"  PFR: {fr.fill_percentage}%")
            print(f"  Pages: {fr.page_count}")
            print(f"  Characters: {fr.char_count}")

            # Save with calibration suffix
            os.makedirs("Output", exist_ok=True)
            with open("Output/fayed_calibrated_fr.pdf", "wb") as f:
                f.write(fr.pdf_bytes)
            with open("Output/fayed_calibrated_fr.docx", "wb") as f:
                f.write(fr.docx_bytes)

            print(f"\n  [OK] Saved: Output/fayed_calibrated_fr.pdf")
            print(f"  [OK] Saved: Output/fayed_calibrated_fr.docx")

            if fr.warnings:
                print(f"\n  Warnings:")
                for w in fr.warnings:
                    print(f"    - {w}")

        print("\n" + "="*70)
        print("VALIDATION CHECKLIST")
        print("="*70)

        print("\n[ ] Compare Output/fayed_calibrated_fr.pdf with input/CV_Fayed_HANAFI_fr_PDF.pdf")
        print("[ ] Nom décalé du haut (~10-15mm)")
        print("[ ] Contenu moins à droite (colonnes ajustées)")
        print("[ ] Durée '6 mois' visible sous date")
        print("[ ] Police 10-11pt (lisible)")
        print("[ ] Espacements identiques")
        print("[ ] Bold/italic corrects")
        print("[ ] PFR dans zone acceptable")

        print(f"\n[OK] Total generation time: {total_time:.1f}s")

        print("\n" + "="*70)
        print("TEST COMPLETE - MANUAL VISUAL VALIDATION REQUIRED")
        print("="*70)

    except Exception as e:
        print(f"\n[FAIL] ERROR:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
