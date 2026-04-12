"""
Test du système anti-débordement 2 pages (ZÉRO OVERFLOW GARANTI).

Test avec les CVs qui débordaient dans le batch V6:
- Gautier ROUAS (débordement EN)
- Manon BOUTIN (débordement FR)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import generate_cv_from_pdf
from datetime import datetime


def test_overflow_prevention():
    """Test anti-overflow sur CVs qui débordaient."""

    # CVs qui débordaient dans batch V6
    test_cases = [
        {
            "name": "Gautier ROUAS",
            "file": r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\v2\Gautier ROUAS - Community Manager Chine 103368148.pdf",
            "expected_overflow": "EN version (débordement 2 pages batch V6)",
        },
        {
            "name": "Manon BOUTIN",
            "file": r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\v2\Manon BOUTIN - Community Manager Chine 103434003.pdf",
            "expected_overflow": "FR version (débordement 2 pages batch V6)",
        },
    ]

    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"output/{today}/overflow_prevention")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("TEST OVERFLOW PREVENTION - ZÉRO DÉBORDEMENT GARANTI")
    print("=" * 80)
    print()

    results = []

    for test_case in test_cases:
        name = test_case["name"]
        file_path = Path(test_case["file"])

        print(f"Testing: {name}")
        print(f"  Previous issue: {test_case['expected_overflow']}")
        print()

        if not file_path.exists():
            print(f"  [SKIP] File not found: {file_path}")
            print()
            continue

        # Read PDF
        pdf_bytes = file_path.read_bytes()

        # Generate CV (FR + EN)
        try:
            result = generate_cv_from_pdf(
                pdf_bytes=pdf_bytes,
                domain="finance",
                languages=["fr", "en"]
            )

            result_fr = result["fr"]
            result_en = result["en"]

            # Save PDFs
            safe_name = name.replace(" ", "_").replace("-", "_")
            output_fr = output_dir / f"{safe_name}_fr_overflow_fixed.pdf"
            output_en = output_dir / f"{safe_name}_en_overflow_fixed.pdf"

            output_fr.write_bytes(result_fr.pdf_bytes)
            output_en.write_bytes(result_en.pdf_bytes)

            # Check pages
            pages_fr = result_fr.page_count
            pages_en = result_en.page_count
            pfr_fr = result_fr.fill_percentage
            pfr_en = result_en.fill_percentage

            success = (pages_fr == 1 and pages_en == 1)

            result_status = {
                "name": name,
                "pages_fr": pages_fr,
                "pages_en": pages_en,
                "pfr_fr": pfr_fr,
                "pfr_en": pfr_en,
                "success": success,
            }

            results.append(result_status)

            # Print result
            if success:
                print(f"  [OK] SUCCESS")
                print(f"    FR: {pfr_fr:.1f}% PFR, {pages_fr} page")
                print(f"    EN: {pfr_en:.1f}% PFR, {pages_en} page")
            else:
                print(f"  [FAIL] FAILED")
                print(f"    FR: {pfr_fr:.1f}% PFR, {pages_fr} page(s)")
                print(f"    EN: {pfr_en:.1f}% PFR, {pages_en} page(s)")

            print(f"  Saved: {output_fr.name}, {output_en.name}")
            print()

        except Exception as e:
            print(f"  [ERROR] {e}")
            print()
            results.append({
                "name": name,
                "success": False,
                "error": str(e),
            })

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    success_count = sum(1 for r in results if r.get("success", False))

    print(f"Total CVs tested: {total}")
    print(f"Success (1 page FR + EN): {success_count}/{total}")
    print(f"Success rate: {success_count/total*100:.0f}%")
    print()

    for r in results:
        if r.get("success"):
            print(f"[OK] {r['name']}: {r['pages_fr']} page FR, {r['pages_en']} page EN ({r['pfr_fr']:.1f}% FR, {r['pfr_en']:.1f}% EN)")
        else:
            error = r.get("error", "Unknown")
            print(f"[FAIL] {r['name']}: {error}")

    print()
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    test_overflow_prevention()
