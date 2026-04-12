"""
Test V4 - Generate Antoine and Marjorie with final corrections + cost tracking.

V4 Changes:
- Espacement entre expériences: 4mm (from 1mm)
- Alignement durée/poste: margin-top: 0 (même baseline)
- Dates: "YYYY -" pour en cours, majuscules, fix "Auguste" → "Aug"
- Aération: .low-pfr activée par défaut
- Cost tracking détaillé
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

# CVs to test v4
CV_FILES = [
    "ANTOINE.pdf",
    "MARJORIE.pdf"
]

# PRICING (Mars 2026 - Hybrid Stack)
COST_EXTRACTION = 0.0025      # OpenAI GPT-4o Vision per CV
COST_STRUCTURATION = 0.058    # Claude Sonnet 4.5 per CV (FR)
COST_TRANSLATION = 0.005      # Claude Haiku 3 per CV (EN)
COST_TOTAL_PER_CV = COST_EXTRACTION + COST_STRUCTURATION + COST_TRANSLATION  # $0.066

def process_cv(cv_path: Path, output_dir: Path):
    """Process a single CV and save v4 outputs."""
    cv_name = cv_path.stem
    print(f"\n{'=' * 80}")
    print(f"PROCESSING V4: {cv_name}")
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

        # Cost breakdown
        print(f"\nCost Breakdown:")
        print(f"  - Extraction (GPT-4o Vision): ${COST_EXTRACTION:.4f}")
        print(f"  - Structuration FR (Sonnet 4.5): ${COST_STRUCTURATION:.4f}")
        print(f"  - Translation EN (Haiku 3): ${COST_TRANSLATION:.4f}")
        print(f"  - PDF Generation (Playwright): $0.0000 (self-hosted)")
        print(f"  - TOTAL: ${COST_TOTAL_PER_CV:.4f} per CV (FR + EN)")

        # Save PDFs with v4 suffix
        fr_pdf_path = output_dir / f"{cv_name}_fr_v4.pdf"
        en_pdf_path = output_dir / f"{cv_name}_en_v4.pdf"

        with open(fr_pdf_path, 'wb') as f:
            f.write(results["fr"].pdf_bytes)
        with open(en_pdf_path, 'wb') as f:
            f.write(results["en"].pdf_bytes)

        print(f"\nV4 PDFs saved:")
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
            "cost": COST_TOTAL_PER_CV
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"ERROR FAILED after {elapsed_time:.2f}s")
        print(f"Error: {str(e)}")

        return {
            "name": cv_name,
            "success": False,
            "time_seconds": round(elapsed_time, 2),
            "error": str(e)[:200],
            "cost": 0
        }


def main():
    """Process CVs for v4."""
    print(f"\n{'=' * 80}")
    print(f"V4 FINAL TEST: {len(CV_FILES)} CVs")
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
    print(f"V4 FINAL SUMMARY")
    print(f"{'=' * 80}\n")

    successes = [m for m in all_metrics if m["success"]]

    if successes:
        print(f"Results:")
        for m in successes:
            print(f"\n{m['name']}:")
            print(f"  - FR PFR: {m['fr_pfr']}% ({m['fr_chars']} chars)")
            print(f"  - EN PFR: {m['en_pfr']}% ({m['en_chars']} chars)")
            print(f"  - Time: {m['time_seconds']}s")
            print(f"  - Cost: ${m['cost']:.4f}")

        avg_fr_pfr = sum(m["fr_pfr"] for m in successes) / len(successes)
        avg_en_pfr = sum(m["en_pfr"] for m in successes) / len(successes)
        total_cost = sum(m["cost"] for m in successes)

        print(f"\nAverage PFR:")
        print(f"  - FR: {avg_fr_pfr:.1f}%")
        print(f"  - EN: {avg_en_pfr:.1f}%")

        print(f"\nTotal Cost: ${total_cost:.4f} ({len(successes)} CVs)")
        print(f"Cost per PDF: ${COST_TOTAL_PER_CV / 2:.4f} (1 language)")

        print(f"\nV4 Changes Applied:")
        print(f"  - Espacement expériences: 4mm (from 1mm)")
        print(f"  - Alignement durée/poste: margin-top: 0")
        print(f"  - Dates: 'YYYY -' format, majuscules, fix Auguste")
        print(f"  - Aération: .low-pfr enabled (spacing++)")

    print(f"\nCompare v1/v2/v3/v4 in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
