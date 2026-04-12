"""
Analyse directe des bullets générés par le nouveau prompt.
Extrait le JSON structuré et mesure longueurs de bullets.
"""
import os
import sys
import json
from pathlib import Path
from PIL import Image
import io

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm_client import extract_text_from_pdf_bytes, generate_cv_content

print("="*80)
print("ANALYSE DÉTAILLÉE DES BULLETS - Nouveau Prompt")
print("="*80)
print()

# ============================================================================
# TEST 1 : BAD_CV
# ============================================================================

print("[TEST 1] BAD_CV.png")
print("-"*80)

try:
    # Load and convert PNG
    with open("input/BAD_CV.png", "rb") as f:
        png_bytes = f.read()

    img = Image.open(io.BytesIO(png_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')

    pdf_buffer = io.BytesIO()
    img.save(pdf_buffer, format='PDF')
    pdf_bytes = pdf_buffer.getvalue()

    # Extract text
    print("\n[1/2] Extracting text...")
    raw_text = extract_text_from_pdf_bytes(pdf_bytes, filename="BAD_CV.pdf")
    print(f"   Extracted {len(raw_text)} chars")

    # Generate content
    print("\n[2/2] Generating structured content (FR)...")
    print()
    content = generate_cv_content(
        input_data={"raw_text": raw_text},
        domain="finance",
        language="fr",
        enrichment_mode=False
    )
    print()

    # Save JSON
    os.makedirs("output", exist_ok=True)
    with open("output/bad_cv_content.json", "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved JSON: output/bad_cv_content.json")

    # Analyze bullets
    print("\n" + "="*80)
    print("BULLETS ANALYSIS - BAD_CV")
    print("="*80)

    if "work_experience" in content:
        total_bullets = 0
        all_bullet_lengths = []

        for idx, exp in enumerate(content["work_experience"]):
            company = exp.get("company", "Unknown")
            position = exp.get("position", "Unknown")
            bullets = exp.get("bullets", [])

            print(f"\n--- Experience #{idx+1}: {position} @ {company}")
            print(f"    Bullets: {len(bullets)}")

            for bullet_idx, bullet in enumerate(bullets):
                bullet_len = len(bullet)
                all_bullet_lengths.append(bullet_len)
                total_bullets += 1

                if bullet_len >= 150:
                    status = "[OK] EXCELLENT"
                elif bullet_len >= 120:
                    status = "[OK] GOOD"
                elif bullet_len >= 100:
                    status = "[!] ACCEPTABLE"
                else:
                    status = "[X] TOO SHORT"

                print(f"    Bullet {bullet_idx+1}: {bullet_len} chars {status}")
                print(f"       \"{bullet[:70]}...\"")

        if all_bullet_lengths:
            avg_len = sum(all_bullet_lengths) / len(all_bullet_lengths)
            print(f"\n[STATS] Total bullets: {total_bullets}")
            print(f"[STATS] Average length: {avg_len:.1f} chars")
            print(f"[STATS] Min: {min(all_bullet_lengths)} | Max: {max(all_bullet_lengths)}")

            excellent = sum(1 for x in all_bullet_lengths if x >= 150)
            good = sum(1 for x in all_bullet_lengths if 120 <= x < 150)
            acceptable = sum(1 for x in all_bullet_lengths if 100 <= x < 120)
            too_short = sum(1 for x in all_bullet_lengths if x < 100)

            print(f"\n[STATS] Distribution:")
            print(f"   [OK] EXCELLENT (150-190): {excellent} ({excellent/total_bullets*100:.1f}%)")
            print(f"   [OK] GOOD (120-149): {good} ({good/total_bullets*100:.1f}%)")
            print(f"   [!] ACCEPTABLE (100-119): {acceptable} ({acceptable/total_bullets*100:.1f}%)")
            print(f"   [X] TOO SHORT (<100): {too_short} ({too_short/total_bullets*100:.1f}%)")
    else:
        print("\n[X] NO work_experience found!")

    # Check coursework
    if "education" in content:
        print(f"\n[STATS] Education entries: {len(content['education'])}")
        for idx, edu in enumerate(content["education"]):
            coursework = edu.get("coursework", [])
            print(f"   #{idx+1} {edu.get('institution', 'Unknown')}: {len(coursework)} coursework items")

    # Check IT skills
    it_skills = content.get("it_skills", [])
    print(f"\n[STATS] IT Skills: {len(it_skills)} items")

except Exception as e:
    print(f"\n[X] Test 1 FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 2 : CV MODÈLE
# ============================================================================

print("\n\n" + "="*80)
print("[TEST 2] CV_Fayed_HANAFI_fr_PDF.pdf (CV Modèle)")
print("-"*80)

try:
    # Load PDF
    with open("input/CV_Fayed_HANAFI_fr_PDF.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Extract text
    print("\n[1/2] Extracting text...")
    raw_text = extract_text_from_pdf_bytes(pdf_bytes, filename="CV_Fayed_HANAFI_fr.pdf")
    print(f"   Extracted {len(raw_text)} chars")

    # Generate content
    print("\n[2/2] Generating structured content (FR)...")
    print()
    content = generate_cv_content(
        input_data={"raw_text": raw_text},
        domain="finance",
        language="fr",
        enrichment_mode=False
    )
    print()

    # Save JSON
    with open("output/cv_modele_content.json", "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved JSON: output/cv_modele_content.json")

    # Analyze bullets
    print("\n" + "="*80)
    print("BULLETS ANALYSIS - CV MODÈLE")
    print("="*80)

    if "work_experience" in content:
        total_bullets = 0
        all_bullet_lengths = []

        for idx, exp in enumerate(content["work_experience"]):
            company = exp.get("company", "Unknown")
            position = exp.get("position", "Unknown")
            bullets = exp.get("bullets", [])

            print(f"\n--- Experience #{idx+1}: {position} @ {company}")
            print(f"    Bullets: {len(bullets)}")

            for bullet_idx, bullet in enumerate(bullets):
                bullet_len = len(bullet)
                all_bullet_lengths.append(bullet_len)
                total_bullets += 1

                if bullet_len >= 150:
                    status = "[OK] EXCELLENT"
                elif bullet_len >= 120:
                    status = "[OK] GOOD"
                elif bullet_len >= 100:
                    status = "[!] ACCEPTABLE"
                else:
                    status = "[X] TOO SHORT"

                print(f"    Bullet {bullet_idx+1}: {bullet_len} chars {status}")
                print(f"       \"{bullet[:70]}...\"")

        if all_bullet_lengths:
            avg_len = sum(all_bullet_lengths) / len(all_bullet_lengths)
            print(f"\n[STATS] Total bullets: {total_bullets}")
            print(f"[STATS] Average length: {avg_len:.1f} chars")
            print(f"[STATS] Min: {min(all_bullet_lengths)} | Max: {max(all_bullet_lengths)}")

            excellent = sum(1 for x in all_bullet_lengths if x >= 150)
            good = sum(1 for x in all_bullet_lengths if 120 <= x < 150)
            acceptable = sum(1 for x in all_bullet_lengths if 100 <= x < 120)
            too_short = sum(1 for x in all_bullet_lengths if x < 100)

            print(f"\n[STATS] Distribution:")
            print(f"   [OK] EXCELLENT (150-190): {excellent} ({excellent/total_bullets*100:.1f}%)")
            print(f"   [OK] GOOD (120-149): {good} ({good/total_bullets*100:.1f}%)")
            print(f"   [!] ACCEPTABLE (100-119): {acceptable} ({acceptable/total_bullets*100:.1f}%)")
            print(f"   [X] TOO SHORT (<100): {too_short} ({too_short/total_bullets*100:.1f}%)")

            # Compare to reference
            print(f"\n[COMPARE] Reference CV (original) average: 127 chars")
            print(f"[COMPARE] Generated CV (new prompt) average: {avg_len:.1f} chars")
            print(f"[COMPARE] Difference: {avg_len - 127:+.1f} chars")
    else:
        print("\n[X] NO work_experience found!")

    # Check coursework
    if "education" in content:
        print(f"\n[STATS] Education entries: {len(content['education'])}")
        for idx, edu in enumerate(content["education"]):
            coursework = edu.get("coursework", [])
            status = "[OK]" if len(coursework) >= 6 else "[!]" if len(coursework) >= 5 else "[X]"
            print(f"   {status} #{idx+1} {edu.get('institution', 'Unknown')}: {len(coursework)} coursework items")

    # Check IT skills
    it_skills = content.get("it_skills", [])
    status = "[OK]" if len(it_skills) >= 6 else "[X]"
    print(f"\n[STATS] {status} IT Skills: {len(it_skills)} items")

except Exception as e:
    print(f"\n[X] Test 2 FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Analysis complete!")
print("="*80)
