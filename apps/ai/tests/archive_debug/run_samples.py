"""
Quick test: generate PDFs for LOGAN and MARLET from SAMPLES folder.
Output saved to output/ directory.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.generator import generate_cv_from_pdf

SAMPLES_DIR = r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

CVS_TO_TEST = ["LOGAN.pdf", "MARLET.pdf"]


def run(cv_filename):
    name = cv_filename.replace(".pdf", "")
    pdf_path = os.path.join(SAMPLES_DIR, cv_filename)

    print(f"\n{'='*50}")
    print(f"Processing: {cv_filename}")
    print(f"{'='*50}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    print(f"  File size: {len(pdf_bytes)/1024:.0f} KB")

    start = time.time()
    results = generate_cv_from_pdf(pdf_bytes=pdf_bytes, domain="finance", languages=["fr"])
    elapsed = time.time() - start

    result = results.get("fr")
    if result is None:
        print(f"  ERROR: No result returned")
        return

    print(f"  Time: {elapsed:.1f}s")
    print(f"  PFR: {result.fill_percentage:.1f}%")
    print(f"  Pages: {result.page_count}")
    print(f"  Warning: {result.warning_info}")
    if result.warnings:
        for w in result.warnings:
            print(f"    - {w}")

    if result.pdf_bytes:
        out_path = os.path.join(OUTPUT_DIR, f"{name}_generated.pdf")
        with open(out_path, "wb") as f:
            f.write(result.pdf_bytes)
        print(f"  Saved: {out_path}")
    else:
        print(f"  ERROR: No PDF bytes in result")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for cv in CVS_TO_TEST:
        run(cv)
    print("\nDone.")
