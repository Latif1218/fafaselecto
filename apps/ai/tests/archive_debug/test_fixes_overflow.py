"""
Test des fixes overflow + retry JSON
31/03/2026
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import generate_cv_from_pdf
from datetime import datetime

def test_fixes():
    """Test les 3 CVs qui ont échoué."""

    samples_dir = Path(r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES\v2")
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"output/{today}/fixes_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Les 3 CVs qui ont échoué
    cv_files = [
        "JINFENG HU - Community Manager Chine 103474313.pdf",  # Débordement
        "Manon BOUTIN - Community Manager Chine 103434003.pdf",  # Débordement
        "Paul ZHOU - Community Manager Chine 103470096.pdf"  # JSON error
    ]

    print("=" * 80)
    print("TEST FIXES - Overflow Prevention + JSON Retry")
    print("=" * 80)
    print()

    for cv_file in cv_files:
        print(f"\nTEST: {cv_file}")
        print("-" * 80)

        input_path = samples_dir / cv_file

        try:
            with open(input_path, 'rb') as f:
                pdf_bytes = f.read()

            result = generate_cv_from_pdf(
                pdf_bytes=pdf_bytes,
                domain="finance",
                languages=["fr"]
            )

            result_fr = result["fr"]

            # Save
            cv_name = cv_file.replace(".pdf", "").replace(" ", "_")
            output_path = output_dir / f"{cv_name}_fr.pdf"
            with open(output_path, 'wb') as f:
                f.write(result_fr.pdf_bytes)

            success = (
                result_fr.page_count == 1
                and 85 <= result_fr.fill_percentage <= 98
            )

            status = "SUCCESS" if success else "FAIL"
            print(f"RESULT: {status}")
            print(f"  PFR: {result_fr.fill_percentage:.1f}%")
            print(f"  Pages: {result_fr.page_count}")
            print(f"  Output: {output_path.name}")

        except Exception as e:
            print(f"ERROR: {str(e)}")

    print("\n" + "=" * 80)
    print("Test terminé")
    print("=" * 80)

if __name__ == "__main__":
    test_fixes()
