"""
Test script for a single CV generation.
Generates PDF in original language and saves to output/.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import CVGenerator
import time


def test_single_cv(cv_filename, output_name=None):
    """
    Test a single CV and save results.

    Args:
        cv_filename: Filename in input/ directory
        output_name: Optional output filename (defaults to cv_filename)
    """
    input_dir = Path(__file__).parent.parent / "input"
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    cv_path = input_dir / cv_filename

    if not cv_path.exists():
        print(f"[ERROR] File not found: {cv_path}")
        return

    print("=" * 80)
    print(f"TESTING: {cv_filename}")
    print("=" * 80)

    generator = CVGenerator()

    # Read PDF
    with open(cv_path, "rb") as f:
        pdf_bytes = f.read()

    # Measure time
    start = time.time()

    # Generate (FR only)
    try:
        results = generator.generate_from_pdf(pdf_bytes, domain="finance", languages=["fr"])
        duration = time.time() - start

        result_fr = results["fr"]

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)

        print(f"\n[SUCCESS] Generation completed in {duration:.1f}s")

        print(f"\nMETRICS:")
        print(f"  PFR:                 {result_fr.fill_percentage:.1f}%")
        print(f"  Pages:               {result_fr.page_count}")
        print(f"  Characters:          {result_fr.char_count}")

        print(f"\nWARNING SYSTEM:")
        level_map = {
            'success': 'GREEN',
            'warning': 'ORANGE',
            'error': 'RED LIGHT',
            'critical': 'RED DARK'
        }
        warning_level = level_map.get(result_fr.warning_info['level'], 'UNKNOWN')
        print(f"  Level:               {warning_level}")
        print(f"  Title:               {result_fr.warning_info['title']}")
        print(f"\n  Message:")
        for line in result_fr.warning_info['message'].split('\n'):
            print(f"    {line}")

        # Save to output
        if output_name is None:
            output_name = cv_filename.replace('.pdf', '')

        output_pdf = output_dir / f"{output_name}_generated_FR.pdf"
        output_docx = output_dir / f"{output_name}_generated_FR.docx"

        with open(output_pdf, "wb") as f:
            f.write(result_fr.pdf_bytes)

        with open(output_docx, "wb") as f:
            f.write(result_fr.docx_bytes)

        print(f"\nOUTPUT SAVED:")
        print(f"  PDF:  {output_pdf}")
        print(f"  DOCX: {output_docx}")

        print("\n" + "=" * 80)
        print("SUCCESS")
        print("=" * 80)

    except Exception as e:
        duration = time.time() - start
        print(f"\n[FAILED]")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Error: {str(e)[:500]}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Use command line argument
        cv_file = sys.argv[1]
        output_name = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Default to JINFENG HU
        cv_file = "JINFENG HU - Community Manager Chine 103474313.pdf"
        output_name = "JINFENG_HU"

    test_single_cv(cv_file, output_name)
