"""
Test script for Push-to-90 system.
Compares BEFORE (old system, PFR ~69%) vs AFTER (new system, target 90%+).
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import CVGenerator
import time


def format_warning_level(warning_info):
    """Format warning level with severity indicator."""
    level_map = {
        'success': 'GREEN',
        'warning': 'ORANGE',
        'error': 'RED LIGHT',
        'critical': 'RED DARK'
    }
    return level_map.get(warning_info['level'], 'UNKNOWN')


def test_bad_cv_push_to_90():
    """Test BAD_CV with new push-to-90 system."""
    print("=" * 80)
    print("PUSH-TO-90 SYSTEM TEST - BAD_CV")
    print("=" * 80)

    input_dir = Path(__file__).parent.parent / "input"
    cv_path = input_dir / "BAD_CV_converted.pdf"

    print(f"\nFile: {cv_path}")

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

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)

        print(f"\n[SUCCESS] Generation completed in {duration:.1f}s")
        print(f"\nPFR METRICS:")
        print(f"  Before (old system): 69.0%")
        print(f"  After (new system):  {result_fr.fill_percentage:.1f}%")
        print(f"  Gain:                +{result_fr.fill_percentage - 69.0:.1f} points")

        print(f"\nOUTPUT:")
        print(f"  Pages:               {result_fr.page_count}")
        print(f"  Characters:          {result_fr.char_count}")

        print(f"\nWARNING SYSTEM:")
        print(f"  Level:               {format_warning_level(result_fr.warning_info)}")
        print(f"  Title:               {result_fr.warning_info['title']}")
        print(f"\n  Message:")
        for line in result_fr.warning_info['message'].split('\n'):
            print(f"    {line}")

        print(f"\nDIAGNOSTICS:")
        print(f"  Total warnings:      {len(result_fr.warnings)}")
        if result_fr.warnings:
            print(f"  Last 3 warnings:")
            for w in result_fr.warnings[-3:]:
                print(f"    - {w}")

        # Success summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        target_met = result_fr.fill_percentage >= 90.0
        status = "[PASS]" if target_met else "[PARTIAL]"

        print(f"\n{status} Push-to-90 Target:")
        print(f"  Expected:  90%+")
        print(f"  Achieved:  {result_fr.fill_percentage:.1f}%")
        print(f"  Status:    {'Target MET' if target_met else 'Below target but accepted'}")

        print(f"\n{status} Warning System:")
        print(f"  Expected:  RED DARK (ultra_aggressive strategy)")
        print(f"  Achieved:  {format_warning_level(result_fr.warning_info)}")

        return {
            'success': True,
            'pfr_before': 69.0,
            'pfr_after': result_fr.fill_percentage,
            'gain': result_fr.fill_percentage - 69.0,
            'target_met': target_met,
            'warning_level': format_warning_level(result_fr.warning_info),
            'duration': duration
        }

    except Exception as e:
        duration = time.time() - start
        print(f"\n[FAILED]")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Error: {str(e)[:300]}")

        return {
            'success': False,
            'error': str(e)[:200],
            'duration': duration
        }


def main():
    """Run push-to-90 test."""
    result = test_bad_cv_push_to_90()

    if result['success']:
        print("\n" + "=" * 80)
        print("CONCLUSION")
        print("=" * 80)

        if result['target_met']:
            print("\n[SUCCESS] Push-to-90 system is OPERATIONAL")
            print(f"  BAD_CV pushed from 69% to {result['pfr_after']:.1f}% (+{result['gain']:.1f} points)")
            print(f"  Warning system active: {result['warning_level']}")
            print(f"  Generation time: {result['duration']:.1f}s")
        else:
            print("\n[PARTIAL SUCCESS] System improved PFR but didn't reach 90%")
            print(f"  Improvement: {result['pfr_before']:.1f}% -> {result['pfr_after']:.1f}% (+{result['gain']:.1f} points)")
            print(f"  Gap to target: {90.0 - result['pfr_after']:.1f} points")
            print(f"  Recommendation: Increase enrichment aggressiveness")
    else:
        print("\n[FAILURE] System did not work as expected")
        print(f"  Error: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()
