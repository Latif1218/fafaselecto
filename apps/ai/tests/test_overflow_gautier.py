"""
Test ultra simple: Gautier ROUAS (débordait EN).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import generate_cv_from_pdf


def test_gautier():
    """Test Gautier ROUAS - débordait EN dans batch V6."""

    pdf_path = Path(r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\v2\Gautier ROUAS - Community Manager Chine 103368148.pdf")

    if not pdf_path.exists():
        print("[SKIP] File not found")
        return

    print("TEST: Gautier ROUAS (debordait EN)")
    print("=" * 60)

    pdf_bytes = pdf_path.read_bytes()

    try:
        # Generate FR only (faster)
        result = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr"]
        )

        result_fr = result["fr"]

        pages = result_fr.page_count
        pfr = result_fr.fill_percentage

        print(f"[OK] SUCCESS")
        print(f"  FR: {pfr:.1f}% PFR, {pages} page(s)")

        if pages == 1:
            print("\n[OK] NO OVERFLOW - 1 page guaranteed")
        else:
            print(f"\n[FAIL] OVERFLOW - {pages} pages")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    test_gautier()
