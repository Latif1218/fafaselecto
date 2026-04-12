"""
Test script to generate CVs for 3 Community Manager profiles
Generates in original language (French)
"""
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.generator import generate_cv_from_pdf

def process_cv(input_path, output_name):
    """Process a single CV"""
    print(f"\n{'='*70}")
    print(f"Processing: {os.path.basename(input_path)}")
    print('='*70)

    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found")
        return None

    with open(input_path, "rb") as f:
        pdf_bytes = f.read()

    print(f"[OK] Loaded: {len(pdf_bytes)} bytes")

    start_time = time.time()

    try:
        results = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr"]  # Original language (French)
        )

        generation_time = time.time() - start_time

        if "fr" in results:
            fr = results["fr"]
            print(f"\n[FR] French CV:")
            print(f"  PFR: {fr.fill_percentage}%")
            print(f"  Pages: {fr.page_count}")
            print(f"  Characters: {fr.char_count}")
            print(f"  Time: {generation_time:.1f}s")

            # Save outputs
            os.makedirs("Output", exist_ok=True)
            pdf_path = f"Output/{output_name}_fr.pdf"
            docx_path = f"Output/{output_name}_fr.docx"

            with open(pdf_path, "wb") as f:
                f.write(fr.pdf_bytes)
            with open(docx_path, "wb") as f:
                f.write(fr.docx_bytes)

            print(f"\n  [OK] Saved: {pdf_path}")
            print(f"  [OK] Saved: {docx_path}")

            if fr.warnings:
                print(f"\n  Warnings:")
                for w in fr.warnings:
                    print(f"    - {w}")

            return {
                "name": os.path.basename(input_path),
                "pfr": fr.fill_percentage,
                "pages": fr.page_count,
                "time": generation_time
            }

    except Exception as e:
        print(f"\n[FAIL] ERROR:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("\n" + "="*70)
    print("COMMUNITY MANAGER CVs - BATCH GENERATION")
    print("="*70)

    cvs = [
        ("input/JINFENG HU - Community Manager Chine 103474313.pdf", "jinfeng_hu"),
        ("input/Guorong ZHAO - Community Manager Chine 103356475.pdf", "guorong_zhao"),
        ("input/Leonie BOITTIN - Community Manager Chine 103121803.pdf", "leonie_boittin")
    ]

    results = []
    start_time = time.time()

    for input_path, output_name in cvs:
        result = process_cv(input_path, output_name)
        if result:
            results.append(result)

    total_time = time.time() - start_time

    # Summary
    print("\n" + "="*70)
    print("BATCH SUMMARY")
    print("="*70)

    for r in results:
        print(f"\n{r['name']}")
        print(f"  PFR: {r['pfr']}%")
        print(f"  Pages: {r['pages']}")
        print(f"  Time: {r['time']:.1f}s")

    print(f"\n{'='*70}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per CV: {total_time/len(results):.1f}s")
    print(f"Success rate: {len(results)}/{len(cvs)}")
    print("="*70)

if __name__ == "__main__":
    main()
