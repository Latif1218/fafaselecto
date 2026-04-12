"""
Test V3 - Generate Antoine and Marjorie with all V3 corrections.

V3 Changes:
- Margins: 11mm (restored from 9mm)
- Separator spacing: 3.5mm (from 1mm)
- Bullets: Tirets (-) everywhere, max 140 chars (2 lignes)
- Target PFR: 90-98% (realistic)
- Formation: paragraphe cohérence langue
- Dates en cours: "YYYY -"
"""
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import CVGenerator

# Input/output paths
SAMPLES_DIR = Path("C:/Users/Home/Documents/Postulae/CVs/SAMPLES")
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "2026-03-12"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CVs to test v3
CV_FILES = [
    "ANTOINE.pdf",
    "MARJORIE.pdf"
]

def process_cv(cv_path: Path, output_dir: Path):
    """Process a single CV and save v3 outputs."""
    cv_name = cv_path.stem
    print(f"\n{'=' * 80}")
    print(f"PROCESSING V3: {cv_name}")
    print(f"{'=' * 80}\n")

    # Read PDF
    with open(cv_path, 'rb') as f:
        pdf_bytes = f.read()

    # Create generator
    generator = CVGenerator()

    # Time generation
    start_time = time.time()

    try:
        results = generator.generate_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr", "en"]
        )

        elapsed_time = time.time() - start_time

        # Print results
        print(f"OK SUCCESS - Generated in {elapsed_time:.2f}s\n")
        print(f"FR Metrics:")
        print(f"  - PFR: {results['fr'].fill_percentage}%")
        print(f"  - Chars: {results['fr'].char_count}")
        print(f"  - Pages: {results['fr'].page_count}")
        print(f"  - Warning: {results['fr'].warning_info.get('level', 'green').upper()}")

        print(f"\nEN Metrics:")
        print(f"  - PFR: {results['en'].fill_percentage}%")
        print(f"  - Chars: {results['en'].char_count}")
        print(f"  - Pages: {results['en'].page_count}")

        # Save PDFs with v3 suffix
        fr_pdf_path = output_dir / f"{cv_name}_fr_v3.pdf"
        en_pdf_path = output_dir / f"{cv_name}_en_v3.pdf"

        with open(fr_pdf_path, 'wb') as f:
            f.write(results["fr"].pdf_bytes)
        with open(en_pdf_path, 'wb') as f:
            f.write(results["en"].pdf_bytes)

        print(f"\nV3 PDFs saved:")
        print(f"  - FR: {fr_pdf_path}")
        print(f"  - EN: {en_pdf_path}")

        return {
            "name": cv_name,
            "success": True,
            "time_seconds": round(elapsed_time, 2),
            "fr_pfr": results["fr"].fill_percentage,
            "en_pfr": results["en"].fill_percentage,
            "fr_chars": results["fr"].char_count,
            "en_chars": results["en"].char_count,
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"ERROR FAILED after {elapsed_time:.2f}s")
        print(f"Error: {str(e)}")

        return {
            "name": cv_name,
            "success": False,
            "time_seconds": round(elapsed_time, 2),
            "error": str(e)[:200]
        }


def main():
    """Process CVs for v3."""
    print(f"\n{'=' * 80}")
    print(f"V3 TEST: {len(CV_FILES)} CVs")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 80}\n")

    all_metrics = []

    for cv_file in CV_FILES:
        cv_path = SAMPLES_DIR / cv_file

        if not cv_path.exists():
            print(f"ERROR SKIP: {cv_file} not found")
            continue

        metrics = process_cv(cv_path, OUTPUT_DIR)
        all_metrics.append(metrics)

        # Brief pause between CVs
        time.sleep(1)

    # Summary
    print(f"\n{'=' * 80}")
    print(f"V3 SUMMARY")
    print(f"{'=' * 80}\n")

    successes = [m for m in all_metrics if m["success"]]

    if successes:
        print(f"Results:")
        for m in successes:
            print(f"\n{m['name']}:")
            print(f"  - FR PFR: {m['fr_pfr']}% ({m['fr_chars']} chars)")
            print(f"  - EN PFR: {m['en_pfr']}% ({m['en_chars']} chars)")
            print(f"  - Time: {m['time_seconds']}s")

        avg_fr_pfr = sum(m["fr_pfr"] for m in successes) / len(successes)
        avg_en_pfr = sum(m["en_pfr"] for m in successes) / len(successes)

        print(f"\nAverage PFR:")
        print(f"  - FR: {avg_fr_pfr:.1f}%")
        print(f"  - EN: {avg_en_pfr:.1f}%")

        print(f"\nV3 Changes Applied:")
        print(f"  - Margins: 11mm (restored)")
        print(f"  - Separator -> entry: 3.5mm (from 1mm)")
        print(f"  - Bullets: Tirets (-) everywhere, max 140 chars")
        print(f"  - Target PFR: 90-98%")
        print(f"  - Padding: cap 140 chars (2 lignes max)")

    print(f"\nCompare v1/v2/v3 in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
