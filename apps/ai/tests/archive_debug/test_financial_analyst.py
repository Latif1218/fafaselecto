"""
Test with Financial-Analyst-CV-Sample.pdf
"""
import os
import time
from app import generate_cv_from_pdf

def main():
    input_path = "input/Financial-Analyst-CV-Sample.pdf"

    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found")
        return

    with open(input_path, "rb") as f:
        pdf_bytes = f.read()

    print("\n" + "="*70)
    print("TEST: Financial Analyst CV Sample")
    print("="*70)
    print(f"Input: {input_path} ({len(pdf_bytes)} bytes)")

    print("\n[GENERATING] Both FR + EN languages...")
    print("Expected: Single-pass enrichment, target PFR 90-95%, < 2 min total")

    start_time = time.time()

    try:
        results = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr", "en"]
        )

        total_time = time.time() - start_time

        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)

        # FR Results
        if "fr" in results:
            fr = results["fr"]
            print(f"\n[FR] French CV:")
            print(f"  PFR: {fr.fill_percentage}%")
            print(f"  Pages: {fr.page_count}")
            print(f"  Characters: {fr.char_count}")

            if 90 <= fr.fill_percentage <= 95:
                status = "[OK] OPTIMAL (90-95%)"
            elif 85 <= fr.fill_percentage < 90:
                status = "[WARN] SUBOPTIMAL (85-90%) - accepted"
            elif fr.fill_percentage > 95:
                status = "[WARN] ABOVE TARGET (>95%) - accepted"
            else:
                status = "[WARN] BELOW TARGET (<85%) - accepted"
            print(f"  Status: {status}")

            if fr.warnings:
                print(f"\n  Warnings:")
                for w in fr.warnings[:10]:  # First 10 warnings
                    print(f"    - {w}")
                if len(fr.warnings) > 10:
                    print(f"    ... and {len(fr.warnings) - 10} more")

            # Save FR
            os.makedirs("Output", exist_ok=True)
            with open("Output/financial_analyst_fr.pdf", "wb") as f:
                f.write(fr.pdf_bytes)
            with open("Output/financial_analyst_fr.docx", "wb") as f:
                f.write(fr.docx_bytes)
            print(f"\n  [OK] Saved: Output/financial_analyst_fr.pdf")
            print(f"  [OK] Saved: Output/financial_analyst_fr.docx")

        # EN Results
        if "en" in results:
            en = results["en"]
            print(f"\n[EN] English CV:")
            print(f"  PFR: {en.fill_percentage}%")
            print(f"  Pages: {en.page_count}")
            print(f"  Characters: {en.char_count}")

            if 90 <= en.fill_percentage <= 95:
                status = "[OK] OPTIMAL (90-95%)"
            elif 85 <= en.fill_percentage < 90:
                status = "[WARN] SUBOPTIMAL (85-90%) - accepted"
            elif en.fill_percentage > 95:
                status = "[WARN] ABOVE TARGET (>95%) - accepted"
            else:
                status = "[WARN] BELOW TARGET (<85%) - accepted"
            print(f"  Status: {status}")

            if en.warnings:
                print(f"\n  Warnings:")
                for w in en.warnings[:10]:
                    print(f"    - {w}")
                if len(en.warnings) > 10:
                    print(f"    ... and {len(en.warnings) - 10} more")

            # Save EN
            with open("Output/financial_analyst_en.pdf", "wb") as f:
                f.write(en.pdf_bytes)
            with open("Output/financial_analyst_en.docx", "wb") as f:
                f.write(en.docx_bytes)
            print(f"\n  [OK] Saved: Output/financial_analyst_en.pdf")
            print(f"  [OK] Saved: Output/financial_analyst_en.docx")

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"  Total time: {total_time:.1f}s")
        print(f"  Time per language: {total_time/2:.1f}s avg")
        print(f"  Performance: {'[OK] PASS' if total_time < 120 else '[FAIL] > 2 min'}")
        print(f"\n  FR PFR: {results['fr'].fill_percentage}% - {results['fr'].page_count} page(s)")
        print(f"  EN PFR: {results['en'].fill_percentage}% - {results['en'].page_count} page(s)")
        print("="*70)

    except ValueError as e:
        error_msg = str(e)
        print(f"\n[BLOCKED] Generation blocked:")
        if "GENERATION BLOCKED" in error_msg:
            print(f"\n{error_msg[:500]}")
        else:
            print(f"  {error_msg}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
