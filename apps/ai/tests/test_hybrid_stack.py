"""
Benchmark Hybrid Stack vs Legacy Stack.

Teste la nouvelle stack (Claude + Playwright) vs ancienne (OpenAI + xhtml2pdf)
sur le CV de référence Fayed HANAFI.

Usage:
    python tests/test_hybrid_stack.py
"""
import time
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import CVGenerator, USE_HYBRID_STACK


def benchmark_cv_generation(pdf_path: str, stack_name: str):
    """
    Benchmark CV generation with current stack.

    Args:
        pdf_path: Path to input PDF
        stack_name: Name of stack being tested

    Returns:
        dict with metrics
    """
    print(f"\n{'=' * 80}")
    print(f"BENCHMARK: {stack_name}")
    print(f"{'=' * 80}\n")

    # Read PDF
    with open(pdf_path, 'rb') as f:
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
            "stack": stack_name,
            "success": True,
            "time_seconds": round(elapsed_time, 2),
            "fr_pfr": results["fr"].fill_percentage,
            "en_pfr": results["en"].fill_percentage,
            "fr_chars": results["fr"].char_count,
            "en_chars": results["en"].char_count,
            "fr_pages": results["fr"].page_count,
            "en_pages": results["en"].page_count,
        }

        # Print results
        print(f"OK SUCCESS - Generated in {elapsed_time:.2f}s\n")
        print(f"FR Metrics:")
        print(f"  - PFR: {metrics['fr_pfr']}%")
        print(f"  - Chars: {metrics['fr_chars']}")
        print(f"  - Pages: {metrics['fr_pages']}")

        print(f"\nEN Metrics:")
        print(f"  - PFR: {metrics['en_pfr']}%")
        print(f"  - Chars: {metrics['en_chars']}")
        print(f"  - Pages: {metrics['en_pages']}")

        # Save PDFs for visual comparison
        output_dir = Path(__file__).parent.parent / "output" / "benchmark"
        output_dir.mkdir(parents=True, exist_ok=True)

        fr_pdf_path = output_dir / f"fayed_fr_{stack_name.lower().replace(' ', '_')}.pdf"
        en_pdf_path = output_dir / f"fayed_en_{stack_name.lower().replace(' ', '_')}.pdf"

        with open(fr_pdf_path, 'wb') as f:
            f.write(results["fr"].pdf_bytes)
        with open(en_pdf_path, 'wb') as f:
            f.write(results["en"].pdf_bytes)

        print(f"\nPDF PDFs saved:")
        print(f"  - FR: {fr_pdf_path}")
        print(f"  - EN: {en_pdf_path}")

        return metrics

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"ERROR FAILED after {elapsed_time:.2f}s")
        print(f"Error: {str(e)}")

        return {
            "stack": stack_name,
            "success": False,
            "time_seconds": round(elapsed_time, 2),
            "error": str(e)
        }


def main():
    """Run benchmark comparison."""
    # Path to reference CV
    cv_path = Path(__file__).parent.parent / "input" / "CV_Fayed_HANAFI_fr_PDF.pdf"

    if not cv_path.exists():
        print(f"ERROR ERROR: CV not found at {cv_path}")
        print("Please ensure CV_Fayed_HANAFI_fr_PDF.pdf is in input/ folder")
        return

    # Determine current stack
    stack_name = "Hybrid Stack (Claude + Playwright)" if USE_HYBRID_STACK else "Legacy Stack (OpenAI + xhtml2pdf)"

    # Run benchmark
    metrics = benchmark_cv_generation(str(cv_path), stack_name)

    # Summary
    print(f"\n{'=' * 80}")
    print("BENCHMARK SUMMARY")
    print(f"{'=' * 80}\n")

    if metrics["success"]:
        print(f"Stack: {metrics['stack']}")
        print(f"Time: {metrics['time_seconds']}s")
        print(f"FR PFR: {metrics['fr_pfr']}% | EN PFR: {metrics['en_pfr']}%")
        print(f"Cost estimate: $0.066/CV (FR + EN)" if USE_HYBRID_STACK else "Cost estimate: $0.083/CV (FR + EN)")
    else:
        print(f"ERROR Benchmark failed: {metrics.get('error')}")

    print("\nTIP: To switch stacks, modify USE_HYBRID_STACK in app/generator.py")


if __name__ == "__main__":
    main()
