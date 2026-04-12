"""
Test with BAD_CV.png
Note: PNG format, will convert to PDF first or use image processing
"""
import os
import time

def main():
    input_path = "input/BAD_CV.png"

    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found")
        return

    print("\n" + "="*70)
    print("TEST: BAD_CV.png")
    print("="*70)

    # Try to convert PNG to PDF or process as image
    try:
        from PIL import Image
        import io

        # Load PNG
        with open(input_path, "rb") as f:
            png_bytes = f.read()

        print(f"Input: {input_path} ({len(png_bytes)} bytes)")

        # Convert PNG to PDF
        print("\n[1] Converting PNG to PDF...")
        img = Image.open(io.BytesIO(png_bytes))

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Save as PDF
        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, format='PDF')
        pdf_bytes = pdf_buffer.getvalue()

        print(f"Converted to PDF: {len(pdf_bytes)} bytes")

        # Now use the standard pipeline
        print("\n[2] Generating CV (FR only for speed)...")
        from app import generate_cv_from_pdf

        start_time = time.time()

        results = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr"]
        )

        total_time = time.time() - start_time

        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)

        fr = results["fr"]
        print(f"\n[FR] French CV:")
        print(f"  PFR: {fr.fill_percentage}%")
        print(f"  Pages: {fr.page_count}")
        print(f"  Characters: {fr.char_count}")
        print(f"  Time: {total_time:.1f}s")

        if 90 <= fr.fill_percentage <= 95:
            status = "[OK] OPTIMAL (90-95%)"
        elif fr.fill_percentage < 90:
            status = "[WARN] BELOW TARGET - accepted (single-pass limit)"
        else:
            status = "[WARN] ABOVE TARGET - accepted (single-pass limit)"
        print(f"  Status: {status}")

        if fr.warnings:
            print(f"\n  Warnings:")
            for w in fr.warnings:
                print(f"    - {w}")

        # Save
        os.makedirs("Output", exist_ok=True)
        with open("Output/bad_cv_fr.pdf", "wb") as f:
            f.write(fr.pdf_bytes)
        with open("Output/bad_cv_fr.docx", "wb") as f:
            f.write(fr.docx_bytes)

        print(f"\n  [OK] Saved: Output/bad_cv_fr.pdf")
        print(f"  [OK] Saved: Output/bad_cv_fr.docx")

    except ImportError:
        print("\nERROR: PIL (Pillow) not installed")
        print("Install with: pip install Pillow")
    except ValueError as e:
        error_msg = str(e)
        print(f"\n[BLOCKED] Generation blocked:")
        if len(error_msg) > 500:
            print(f"\n{error_msg[:500]}...")
        else:
            print(f"\n{error_msg}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
