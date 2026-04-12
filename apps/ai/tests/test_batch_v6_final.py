"""
Test Batch V6 - FINAL PRODUCTION TEST (01/04/2026)

Test complet après cleanup:
- Tous les CVs de SAMPLES/v2
- FR + EN (2 langues)
- PDFs uniquement (pas de DOCX)
- Output: output/2026-04-01/batch_v6/

Validation:
- PFR 86-98%
- 1 page exactement
- Temps < 60s par CV
"""
import sys
from pathlib import Path
from datetime import datetime
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import generate_cv_from_pdf


def test_batch_v6_final():
    """Test batch V6 - Production final avec tous les CVs v2."""

    print("=" * 80)
    print("TEST BATCH V6 - FINAL PRODUCTION (FR + EN)")
    print("=" * 80)
    print()

    samples_dir = Path(r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\v2")
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"output/{today}/batch_v6")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input: {samples_dir}")
    print(f"Output: {output_dir}")
    print(f"Languages: FR + EN")
    print(f"Format: PDF only")
    print()

    # Get all PDF files in v2
    cv_files = sorted(samples_dir.glob("*.pdf"))

    if not cv_files:
        print(f"ERROR: No PDF files found in {samples_dir}")
        return

    print(f"Found {len(cv_files)} CVs to process")
    print()

    results = []
    total_start = time.time()

    for i, cv_path in enumerate(cv_files, 1):
        print("\n" + "=" * 80)
        print(f"[{i}/{len(cv_files)}] {cv_path.name}")
        print("=" * 80)

        cv_start = time.time()

        try:
            # Read PDF
            with open(cv_path, 'rb') as f:
                pdf_bytes = f.read()

            # Generate FR + EN
            result = generate_cv_from_pdf(
                pdf_bytes=pdf_bytes,
                domain="finance",
                languages=["fr", "en"]
            )

            cv_time = time.time() - cv_start

            # Extract results
            result_fr = result["fr"]
            result_en = result["en"]

            # Save PDFs
            cv_name = cv_path.stem.replace(" ", "_")

            output_fr = output_dir / f"{cv_name}_fr.pdf"
            output_en = output_dir / f"{cv_name}_en.pdf"

            with open(output_fr, 'wb') as f:
                f.write(result_fr.pdf_bytes)

            with open(output_en, 'wb') as f:
                f.write(result_en.pdf_bytes)

            # Validation
            success_fr = (
                result_fr.page_count == 1
                and 86 <= result_fr.fill_percentage <= 98
            )
            success_en = (
                result_en.page_count == 1
                and 86 <= result_en.fill_percentage <= 98
            )
            success = success_fr and success_en

            result_data = {
                'cv': cv_path.stem.split(" - ")[0],
                'pfr_fr': result_fr.fill_percentage,
                'pfr_en': result_en.fill_percentage,
                'pages_fr': result_fr.page_count,
                'pages_en': result_en.page_count,
                'time': cv_time,
                'success': success
            }
            results.append(result_data)

            # Display results
            status = "[SUCCESS]" if success else "[FAIL]"
            print(f"\n{status}")
            print(f"  FR: {result_fr.fill_percentage:.1f}% PFR, {result_fr.page_count} page(s)")
            print(f"  EN: {result_en.fill_percentage:.1f}% PFR, {result_en.page_count} page(s)")
            print(f"  Time: {cv_time:.1f}s")
            print(f"  Output: {output_fr.name}, {output_en.name}")

            # Warnings
            if result_fr.page_count != 1:
                print(f"  [WARNING] FR overflow: {result_fr.page_count} pages")
            if result_en.page_count != 1:
                print(f"  [WARNING] EN overflow: {result_en.page_count} pages")
            if result_fr.fill_percentage < 86:
                print(f"  [WARNING] FR PFR too low: {result_fr.fill_percentage:.1f}%")
            if result_en.fill_percentage < 86:
                print(f"  [WARNING] EN PFR too low: {result_en.fill_percentage:.1f}%")

        except Exception as e:
            cv_time = time.time() - cv_start
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()

            results.append({
                'cv': cv_path.stem.split(" - ")[0],
                'pfr_fr': 0,
                'pfr_en': 0,
                'pages_fr': 0,
                'pages_en': 0,
                'time': cv_time,
                'success': False,
                'error': str(e)
            })

    total_time = time.time() - total_start

    # Summary
    print("\n" + "=" * 80)
    print(f"BATCH V6 FINAL - {len(results)} CVs processed")
    print("=" * 80)
    print()

    success_count = sum(1 for r in results if r['success'])
    avg_pfr_fr = sum(r['pfr_fr'] for r in results if r['pfr_fr'] > 0) / max(len(results), 1)
    avg_pfr_en = sum(r['pfr_en'] for r in results if r['pfr_en'] > 0) / max(len(results), 1)
    avg_time = sum(r['time'] for r in results) / max(len(results), 1)

    print(f"Success rate: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")
    print(f"PFR FR average: {avg_pfr_fr:.1f}%")
    print(f"PFR EN average: {avg_pfr_en:.1f}%")
    print(f"Time average: {avg_time:.1f}s per CV")
    print(f"Total time: {total_time/60:.1f} min")
    print()

    # Detail table
    print("DETAIL PAR CV:")
    print("-" * 100)
    print(f"{'CV':<25} {'PFR FR':<10} {'PFR EN':<10} {'Pages FR':<10} {'Pages EN':<10} {'Time':<8} {'Status':<10}")
    print("-" * 100)

    for r in results:
        status = "[OK]" if r['success'] else "[FAIL]"
        print(f"{r['cv']:<25} {r['pfr_fr']:<10.1f} {r['pfr_en']:<10.1f} "
              f"{r['pages_fr']:<10} {r['pages_en']:<10} {r['time']:<8.1f} {status:<10}")

    print("-" * 100)
    print()

    # Verdict
    if success_count == len(results):
        print("[SUCCESS] COMPLET - Tous les CVs valides (FR + EN)")
    elif success_count == 0:
        print("[FAIL] ECHEC COMPLET")
    else:
        print(f"[PARTIAL] - {success_count} success, {len(results) - success_count} failed")

    print()
    print(f"Output directory: {output_dir.absolute()}")
    print()

    return success_count == len(results)


if __name__ == "__main__":
    success = test_batch_v6_final()
    sys.exit(0 if success else 1)
