"""
Test script for adaptive enrichment system.
Tests 2 CV profiles:
1. CV riche (Fayed HANAFI) - Expected: strategy minimal, PFR 86-88%, warning GREEN
2. CV faible (BAD_CV) - Expected: strategy aggressive, PFR 90-92%, warning RED
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import CVGenerator
import time


def format_warning_level(warning_info):
    """Format warning level."""
    if warning_info['level'] == 'success':
        return 'GREEN'
    elif warning_info['level'] == 'warning':
        return 'ORANGE'
    else:
        return 'RED'


def test_cv(cv_path, cv_name):
    """Test a single CV and return metrics."""
    print(f"\n{'=' * 80}")
    print(f"Testing: {cv_name}")
    print(f"Path: {cv_path}")
    print(f"{'=' * 80}")

    generator = CVGenerator()

    # Read PDF
    with open(cv_path, "rb") as f:
        pdf_bytes = f.read()

    # Measure time
    start = time.time()

    # Generate (FR only for speed)
    try:
        results = generator.generate_from_pdf(pdf_bytes, domain="finance", languages=["fr"])
        duration = time.time() - start

        result_fr = results["fr"]

        print(f"\n[SUCCESS]")
        print(f"   Duration: {duration:.1f}s")
        print(f"   PFR: {result_fr.fill_percentage:.1f}%")
        print(f"   Pages: {result_fr.page_count}")
        print(f"   Warning: {format_warning_level(result_fr.warning_info)}")
        print(f"   Title: {result_fr.warning_info['title']}")
        print(f"   Message: {result_fr.warning_info['message']}")

        return {
            'cv_name': cv_name,
            'success': True,
            'duration': duration,
            'pfr': result_fr.fill_percentage,
            'pages': result_fr.page_count,
            'warning': format_warning_level(result_fr.warning_info),
            'warning_info': result_fr.warning_info,
        }

    except Exception as e:
        duration = time.time() - start
        print(f"\n[FAILED]")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Error: {str(e)[:200]}")

        return {
            'cv_name': cv_name,
            'success': False,
            'duration': duration,
            'error': str(e)[:100],
        }


def main():
    """Run tests and display report."""
    input_dir = Path(__file__).parent.parent / "input"

    # Test cases
    test_cases = [
        (input_dir / "CV_Fayed_HANAFI_fr_PDF.pdf", "CV Modèle (Fayed)"),
        (input_dir / "BAD_CV_converted.pdf", "BAD_CV"),
    ]

    results = []
    for cv_path, cv_name in test_cases:
        result = test_cv(cv_path, cv_name)
        results.append(result)

    # Display summary report
    print(f"\n{'=' * 100}")
    print("SUMMARY REPORT")
    print(f"{'=' * 100}")

    print(f"\n+---------------------+------------+----------+----------+----------+-------------+")
    print(f"| CV                  | Source     | Strategy | PFR      | Pages    | Warning     |")
    print(f"+---------------------+------------+----------+----------+----------+-------------+")

    for result in results:
        if result['success']:
            cv_name_padded = result['cv_name'][:19].ljust(19)
            source_chars = "XXXX"  # Not tracked in current implementation
            strategy = "?"  # Not tracked in result
            pfr_str = f"{result['pfr']:.1f}%".ljust(8)
            pages_str = str(result['pages']).ljust(8)
            warning_str = result['warning'].ljust(11)

            print(f"| {cv_name_padded} | {source_chars} chars | {strategy.ljust(8)} | {pfr_str} | {pages_str} | {warning_str} |")
        else:
            cv_name_padded = result['cv_name'][:19].ljust(19)
            print(f"| {cv_name_padded} | FAILED     | -        | -        | -        | -           |")

    print(f"+---------------------+------------+----------+----------+----------+-------------+")

    print(f"\nTotal tests: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}/{len(results)}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}/{len(results)}")

    # Detailed results
    print(f"\n{'=' * 100}")
    print("DETAILED RESULTS")
    print(f"{'=' * 100}")

    for result in results:
        if result['success']:
            print(f"\n{result['cv_name']}:")
            print(f"  PFR: {result['pfr']:.1f}%")
            print(f"  Warning Level: {result['warning']}")
            print(f"  Warning Title: {result['warning_info']['title']}")
            print(f"  Warning Message: {result['warning_info']['message']}")
        else:
            print(f"\n{result['cv_name']}: FAILED")
            print(f"  Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
