"""
Test with LORENZO.pdf
"""
import os
import time
from app import generate_cv_from_pdf

input_path = "input/LORENZO.pdf"
with open(input_path, "rb") as f:
    pdf_bytes = f.read()

print("\n" + "="*70)
print("TEST: input/LORENZO.pdf")
print("="*70)

start = time.time()

try:
    results = generate_cv_from_pdf(
        pdf_bytes=pdf_bytes,
        domain="finance",
        languages=["fr"]  # Just FR for speed
    )

    elapsed = time.time() - start

    fr = results["fr"]
    print(f"\n[FR] French CV:")
    print(f"  PFR: {fr.fill_percentage}%")
    print(f"  Pages: {fr.page_count}")
    print(f"  Characters: {fr.char_count}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Status: {'[OK] OPTIMAL' if 90 <= fr.fill_percentage <= 95 else '[WARN] SUBOPTIMAL'}")

    if fr.warnings:
        print(f"\n  Warnings:")
        for w in fr.warnings:
            print(f"    - {w}")

    # Save
    os.makedirs("Output", exist_ok=True)
    with open("Output/test_lorenzo_fr.pdf", "wb") as f:
        f.write(fr.pdf_bytes)
    print(f"\n  Saved: Output/test_lorenzo_fr.pdf")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
