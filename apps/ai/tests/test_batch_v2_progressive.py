"""
Batch test V2 - Avec système de trim progressif (4 niveaux).

Test tous les CVs SAMPLES/v2 avec la nouvelle logique overflow prevention.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import generate_cv_from_pdf


def test_batch_v2_progressive():
    """Test batch V2 avec trim progressif."""

    samples_dir = Path(r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\v2")
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"output/{today}/batch_v2_progressive")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("BATCH V2 - TRIM PROGRESSIF (4 NIVEAUX)")
    print("=" * 80)
    print(f"\nInput: {samples_dir}")
    print(f"Output: {output_dir}")
    print(f"Languages: FR + EN")
    print(f"Format: PDF only\n")

    # Get all PDFs
    pdf_files = sorted(samples_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} CVs to process\n")

    results = []
    total_time = 0

    for idx, pdf_path in enumerate(pdf_files, 1):
        name = pdf_path.stem
        print("=" * 80)
        print(f"[{idx}/{len(pdf_files)}] {name}")
        print("=" * 80)

        pdf_bytes = pdf_path.read_bytes()

        try:
            start = datetime.now()

            # Generate FR + EN
            result = generate_cv_from_pdf(
                pdf_bytes=pdf_bytes,
                domain="finance",
                languages=["fr", "en"]
            )

            elapsed = (datetime.now() - start).total_seconds()
            total_time += elapsed

            result_fr = result["fr"]
            result_en = result["en"]

            # Save PDFs
            safe_name = name.replace(" ", "_").replace("-", "_")
            output_fr = output_dir / f"{safe_name}_fr.pdf"
            output_en = output_dir / f"{safe_name}_en.pdf"

            output_fr.write_bytes(result_fr.pdf_bytes)
            output_en.write_bytes(result_en.pdf_bytes)

            # Check success
            pages_fr = result_fr.page_count
            pages_en = result_en.page_count
            pfr_fr = result_fr.fill_percentage
            pfr_en = result_en.fill_percentage

            success = (pages_fr == 1 and pages_en == 1 and pfr_fr >= 75.0 and pfr_en >= 75.0)

            results.append({
                "name": name,
                "pages_fr": pages_fr,
                "pages_en": pages_en,
                "pfr_fr": pfr_fr,
                "pfr_en": pfr_en,
                "time": elapsed,
                "success": success,
            })

            # Print result
            status = "[OK] SUCCESS" if success else "[FAIL] FAILED"
            print(f"\n{status}")
            print(f"  FR: {pfr_fr:.1f}% PFR, {pages_fr} page(s)")
            print(f"  EN: {pfr_en:.1f}% PFR, {pages_en} page(s)")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Output: {output_fr.name}, {output_en.name}")
            print()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            print()
            results.append({
                "name": name,
                "success": False,
                "error": str(e),
            })

    # Summary
    print("=" * 80)
    print(f"BATCH V2 PROGRESSIVE - {len(pdf_files)} CVs processed")
    print("=" * 80)
    print()

    success_count = sum(1 for r in results if r.get("success", False))
    avg_time = total_time / len(results) if results else 0

    print(f"Success rate: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")

    if success_count > 0:
        success_results = [r for r in results if r.get("success", False)]
        avg_pfr_fr = sum(r["pfr_fr"] for r in success_results) / len(success_results)
        avg_pfr_en = sum(r["pfr_en"] for r in success_results) / len(success_results)
        print(f"PFR FR average: {avg_pfr_fr:.1f}%")
        print(f"PFR EN average: {avg_pfr_en:.1f}%")

    print(f"Time average: {avg_time:.1f}s per CV")
    print(f"Total time: {total_time/60:.1f} min")
    print()

    print("DETAIL PAR CV:")
    print("-" * 100)
    print(f"{'CV':<30} {'PFR FR':<10} {'PFR EN':<10} {'Pages FR':<10} {'Pages EN':<10} {'Time':<8} {'Status':<10}")
    print("-" * 100)

    for r in results:
        if r.get("success"):
            print(f"{r['name'][:30]:<30} {r['pfr_fr']:<10.1f} {r['pfr_en']:<10.1f} {r['pages_fr']:<10} {r['pages_en']:<10} {r['time']:<8.1f} [OK]")
        else:
            error = r.get("error", "Unknown")[:50]
            print(f"{r['name'][:30]:<30} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<8} [FAIL] {error}")

    print("-" * 100)
    print()

    if success_count == len(results):
        print("[SUCCESS] - All CVs generated successfully")
    else:
        print(f"[PARTIAL] - {success_count} success, {len(results) - success_count} failed")

    print()
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    test_batch_v2_progressive()
