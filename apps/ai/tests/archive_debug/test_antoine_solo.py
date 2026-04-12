"""
Test ANTOINE uniquement - 31/03/2026
Retry après erreur JSON parsing
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import generate_cv_from_pdf

def test_antoine():
    """Test ANTOINE uniquement."""

    print("=" * 80)
    print("TEST ANTOINE - RETRY")
    print("=" * 80)
    print()

    # Input/output paths
    input_path = Path(r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\ANTOINE.pdf")
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"output/{today}/antoine_retry")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        return

    # Read PDF
    with open(input_path, 'rb') as f:
        pdf_bytes = f.read()

    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print()

    try:
        # Generate
        result = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr"]
        )

        result_fr = result["fr"]

        # Save PDF
        output_path = output_dir / "ANTOINE_fr.pdf"
        with open(output_path, 'wb') as f:
            f.write(result_fr.pdf_bytes)

        # Results
        success = (
            result_fr.page_count == 1
            and 88 <= result_fr.fill_percentage <= 98
        )

        status = "SUCCESS" if success else "FAIL"
        print()
        print("=" * 80)
        print(f"RESULT: {status}")
        print("=" * 80)
        print(f"  PFR: {result_fr.fill_percentage:.1f}%")
        print(f"  Pages: {result_fr.page_count}")
        print(f"  Chars: {result_fr.char_count}")
        print(f"  PDF: {output_path}")
        print()

        if success:
            print("✓ ANTOINE génération réussie!")
        else:
            if result_fr.page_count > 1:
                print("✗ Débordement 2 pages")
            else:
                print(f"✗ PFR {result_fr.fill_percentage:.1f}% hors cible 88-98%")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_antoine()
