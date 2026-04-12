"""
Batch test - Generate CVs from SAMPLES folder.

Generates 5 CVs using hybrid stack and saves to output/2026-03-12/
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

# CVs to process
CV_FILES = [
    "ANTOINE.pdf",
    "CHLOE.pdf",
    "LOGAN.pdf",
    "LORENZO.pdf",
    "MARJORIE.pdf"
]

def process_cv(cv_path: Path, output_dir: Path):
    """Process a single CV and save outputs."""
    cv_name = cv_path.stem
    print(f"\n{'=' * 80}")
    print(f"PROCESSING: {cv_name}")
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

        # Extract metrics
        metrics = {
            "name": cv_name,
            "success": True,
            "time_seconds": round(elapsed_time, 2),
            "fr_pfr": results["fr"].fill_percentage,
            "en_pfr": results["en"].fill_percentage,
            "fr_chars": results["fr"].char_count,
            "en_chars": results["en"].char_count,
            "fr_pages": results["fr"].page_count,
            "en_pages": results["en"].page_count,
            "warning": results["fr"].warning_info.get("level", "green")
        }

        # Print results
        print(f"OK SUCCESS - Generated in {elapsed_time:.2f}s\n")
        print(f"FR Metrics:")
        print(f"  - PFR: {metrics['fr_pfr']}%")
        print(f"  - Chars: {metrics['fr_chars']}")
        print(f"  - Pages: {metrics['fr_pages']}")
        print(f"  - Warning: {metrics['warning'].upper()}")

        print(f"\nEN Metrics:")
        print(f"  - PFR: {metrics['en_pfr']}%")
        print(f"  - Chars: {metrics['en_chars']}")
        print(f"  - Pages: {metrics['en_pages']}")

        # Save PDFs
        fr_pdf_path = output_dir / f"{cv_name}_fr.pdf"
        en_pdf_path = output_dir / f"{cv_name}_en.pdf"

        with open(fr_pdf_path, 'wb') as f:
            f.write(results["fr"].pdf_bytes)
        with open(en_pdf_path, 'wb') as f:
            f.write(results["en"].pdf_bytes)

        print(f"\nPDF PDFs saved:")
        print(f"  - FR: {fr_pdf_path.name}")
        print(f"  - EN: {en_pdf_path.name}")

        return metrics

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
    """Process all CVs in batch."""
    print(f"\n{'=' * 80}")
    print(f"BATCH PROCESSING: {len(CV_FILES)} CVs")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 80}\n")

    all_metrics = []
    total_start = time.time()

    for cv_file in CV_FILES:
        cv_path = SAMPLES_DIR / cv_file

        if not cv_path.exists():
            print(f"ERROR SKIP: {cv_file} not found")
            continue

        metrics = process_cv(cv_path, OUTPUT_DIR)
        all_metrics.append(metrics)

        # Brief pause between CVs
        time.sleep(1)

    total_time = time.time() - total_start

    # Summary
    print(f"\n{'=' * 80}")
    print(f"BATCH SUMMARY")
    print(f"{'=' * 80}\n")

    successes = [m for m in all_metrics if m["success"]]
    failures = [m for m in all_metrics if not m["success"]]

    print(f"Total CVs: {len(all_metrics)}")
    print(f"Successes: {len(successes)}")
    print(f"Failures: {len(failures)}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time: {total_time/len(all_metrics):.1f}s per CV\n")

    if successes:
        avg_fr_pfr = sum(m["fr_pfr"] for m in successes) / len(successes)
        avg_en_pfr = sum(m["en_pfr"] for m in successes) / len(successes)

        print(f"Average PFR:")
        print(f"  - FR: {avg_fr_pfr:.1f}%")
        print(f"  - EN: {avg_en_pfr:.1f}%")

        print(f"\nWarning levels:")
        for level in ["green", "orange", "red_light", "red_dark"]:
            count = sum(1 for m in successes if m["warning"] == level)
            if count > 0:
                print(f"  - {level.upper()}: {count}")

    if failures:
        print(f"\nFAILED CVs:")
        for m in failures:
            print(f"  - {m['name']}: {m.get('error', 'Unknown error')[:100]}")

    print(f"\nTotal cost estimate: ${len(successes) * 0.066:.2f} (FR + EN)")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
