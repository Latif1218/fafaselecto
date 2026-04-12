"""
Test BATCH - 5 CVs SAMPLES avec Option C Hybride
Session 21/03/2026

Objectif: Valider Option C sur échantillon représentatif
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import generate_cv_from_pdf
from app.llm_client import extract_text_from_pdf_bytes
from app.content_analyzer import ContentAnalyzer


def test_batch_5cvs():
    """Test batch sur 5 CVs SAMPLES."""

    print("=" * 80)
    print("TEST BATCH - 5 CVs SAMPLES - OPTION C HYBRIDE")
    print("=" * 80)
    print()

    # CV samples directory
    samples_dir = Path(r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES")

    # Create output directory with today's date
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"output/{today}/batch")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print()

    # Liste des CVs à tester
    cv_files = [
        "MARJORIE.pdf",
        "ANTOINE.pdf",
        "CHLOE.pdf",
        "LOGAN.pdf",
        "LORENZO.pdf"
    ]

    results = []
    total_start = time.time()

    for cv_file in cv_files:
        print("\n" + "=" * 80)
        print(f"TEST: {cv_file}")
        print("=" * 80)

        input_path = samples_dir / cv_file

        if not input_path.exists():
            print(f"SKIP - Fichier non trouve: {input_path}")
            continue

        try:
            # Read PDF
            with open(input_path, 'rb') as f:
                pdf_bytes = f.read()

            # Extract text
            start_extract = time.time()
            raw_text = extract_text_from_pdf_bytes(pdf_bytes)
            extract_time = time.time() - start_extract
            source_chars = len(raw_text)

            # Analyze
            analyzer = ContentAnalyzer()
            analysis = analyzer.analyze(raw_text)

            print(f"Source: {source_chars} chars")
            print(f"Strategy: {analysis['strategy']}")
            print(f"Target PFR: {analysis['target_pfr']}")
            print(f"Target chars: {analysis['target_chars']}")

            # Generate
            start_gen = time.time()
            result = generate_cv_from_pdf(
                pdf_bytes=pdf_bytes,
                domain="finance",
                languages=["fr"]
            )
            gen_time = time.time() - start_gen

            result_fr = result["fr"]

            # Save PDF
            cv_name = cv_file.replace(".pdf", "")
            output_path = output_dir / f"{cv_name}_fr.pdf"
            with open(output_path, 'wb') as f:
                f.write(result_fr.pdf_bytes)

            # Results
            # TARGET: 95-98% PFR (optimal), ACCEPTER: 85-98% (acceptable)
            success = (
                result_fr.page_count == 1
                and 85 <= result_fr.fill_percentage <= 98
            )

            result_data = {
                'cv': cv_name,
                'source_chars': source_chars,
                'strategy': analysis['strategy'],
                'target_chars': analysis['target_chars'],
                'generated_chars': result_fr.char_count,
                'pfr': result_fr.fill_percentage,
                'pages': result_fr.page_count,
                'time': gen_time,
                'success': success
            }
            results.append(result_data)

            status = "SUCCESS" if success else "FAIL"
            print(f"\nRESULT: {status}")
            print(f"  PFR: {result_fr.fill_percentage}%")
            print(f"  Pages: {result_fr.page_count}")
            print(f"  Chars: {result_fr.char_count}")
            print(f"  Time: {gen_time:.1f}s")
            print(f"  PDF: {output_path}")

        except Exception as e:
            print(f"ERROR: {str(e)}")
            results.append({
                'cv': cv_file.replace(".pdf", ""),
                'source_chars': 0,
                'strategy': 'error',
                'target_chars': 0,
                'generated_chars': 0,
                'pfr': 0,
                'pages': 0,
                'time': 0,
                'success': False,
                'error': str(e)
            })

    total_time = time.time() - total_start

    # Summary
    print("\n" + "=" * 80)
    print("RESUME BATCH - 5 CVs")
    print("=" * 80)
    print()

    success_count = sum(1 for r in results if r['success'])
    avg_pfr = sum(r['pfr'] for r in results if r['success']) / max(success_count, 1)
    avg_time = sum(r['time'] for r in results if r['success']) / max(success_count, 1)

    print(f"Taux succes: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")
    print(f"PFR moyen: {avg_pfr:.1f}%")
    print(f"Temps moyen: {avg_time:.1f}s")
    print(f"Temps total: {total_time/60:.1f} min")
    print()

    # Detail par CV
    print("DETAIL PAR CV:")
    print("-" * 80)
    print(f"{'CV':<12} {'Strategy':<15} {'Source':<8} {'Gen':<8} {'PFR':<7} {'Pages':<6} {'Time':<6} {'Status':<8}")
    print("-" * 80)

    for r in results:
        status = "OK" if r['success'] else "FAIL"
        print(f"{r['cv']:<12} {r['strategy']:<15} {r['source_chars']:<8} {r['generated_chars']:<8} "
              f"{r['pfr']:<7.1f} {r['pages']:<6} {r['time']:<6.1f} {status:<8}")

    print("-" * 80)
    print()

    # Verdict
    if success_count == len(results):
        print("SUCCESS COMPLET - Tous les CVs valides!")
    else:
        print(f"PARTIEL - {len(results) - success_count} echecs")

    print()
    return success_count == len(results)


if __name__ == "__main__":
    test_batch_5cvs()
