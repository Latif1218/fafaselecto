"""
Test elite bullet length generation with new prompt system.
Verifies that bullets match elite CV standard (120-190 chars).
"""
import json
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm_client import extract_text_from_pdf_bytes, generate_cv_content

print("="*80)
print("ELITE BULLET LENGTH TEST - New Prompt System")
print("="*80)
print("\nTarget: Elite CV standard (90%+ PFR)")
print("  - Premium experiences (MBB, IB): 150-190 chars per bullet")
print("  - Standard experiences: 120-160 chars per bullet")
print("  - Minimum acceptable: 100 chars")
print()

# Test with Fayed Hanafi's CV (reference elite CV - 90.7% PFR)
input_path = "input/CV_Fayed_HANAFI_fr_PDF.pdf"

if not os.path.exists(input_path):
    print(f"[X] Test file not found: {input_path}")
    print("   Using alternative test file...")
    # Try alternative
    input_path = "input/CHLOE.pdf"
    if not os.path.exists(input_path):
        print("[X] No test files available. Exiting.")
        exit(1)

print(f"[FILE] Test input: {input_path}")

with open(input_path, "rb") as f:
    pdf_bytes = f.read()

# Extract text
print("\n[1/3] Extracting text from PDF...")
raw_text = extract_text_from_pdf_bytes(pdf_bytes, filename=os.path.basename(input_path))
print(f"   ✓ Extracted {len(raw_text)} characters")

# Generate content (FRENCH to test NOM pattern)
print("\n[2/3] Generating CV content with NEW ELITE PROMPT...")
print("   (watch for validation warnings below)")
print()
content = generate_cv_content(
    input_data={"raw_text": raw_text},
    domain="finance",
    language="fr",
    enrichment_mode=False,
)
print()

# Analyze bullet lengths
print("="*80)
print("[3/3] BULLET LENGTH ANALYSIS")
print("="*80)

if "work_experience" not in content or len(content.get("work_experience", [])) == 0:
    print("[X] CRITICAL: No work_experience generated!")
    print("   Cannot analyze bullet lengths.")
    exit(1)

all_bullets = []
bullet_details = []

for idx, exp in enumerate(content["work_experience"]):
    company = exp.get("company", "Unknown")
    position = exp.get("position", "Unknown")
    bullets = exp.get("bullets", [])

    print(f"\n--- Experience #{idx+1}: {position} @ {company}")
    print(f"   Bullets: {len(bullets)}")

    for bullet_idx, bullet in enumerate(bullets):
        bullet_len = len(bullet)
        all_bullets.append(bullet_len)
        bullet_details.append({
            "exp_num": idx+1,
            "company": company,
            "bullet_num": bullet_idx+1,
            "length": bullet_len,
            "text": bullet
        })

        # Color-coded output based on elite standards
        if bullet_len >= 150:
            status = "[OK] EXCELLENT"
        elif bullet_len >= 120:
            status = "[OK] GOOD"
        elif bullet_len >= 100:
            status = "[!]  ACCEPTABLE"
        else:
            status = "[X] TOO SHORT"

        print(f"   Bullet {bullet_idx+1}: {bullet_len} chars {status}")
        print(f"      \"{bullet[:70]}...\"")

# Statistics
print("\n" + "="*80)
print("[STATS] STATISTICS")
print("="*80)

if all_bullets:
    avg_len = sum(all_bullets) / len(all_bullets)
    min_len = min(all_bullets)
    max_len = max(all_bullets)

    # Count by category
    excellent = sum(1 for x in all_bullets if x >= 150)
    good = sum(1 for x in all_bullets if 120 <= x < 150)
    acceptable = sum(1 for x in all_bullets if 100 <= x < 120)
    too_short = sum(1 for x in all_bullets if x < 100)

    print(f"\nTotal bullets analyzed: {len(all_bullets)}")
    print(f"Average length: {avg_len:.1f} chars")
    print(f"Min length: {min_len} chars")
    print(f"Max length: {max_len} chars")

    print(f"\nDistribution:")
    print(f"  [OK] EXCELLENT (150-190 chars): {excellent} ({excellent/len(all_bullets)*100:.1f}%)")
    print(f"  [OK] GOOD (120-149 chars): {good} ({good/len(all_bullets)*100:.1f}%)")
    print(f"  [!]  ACCEPTABLE (100-119 chars): {acceptable} ({acceptable/len(all_bullets)*100:.1f}%)")
    print(f"  [X] TOO SHORT (<100 chars): {too_short} ({too_short/len(all_bullets)*100:.1f}%)")

    # Elite standard compliance
    elite_compliant = excellent + good
    print(f"\n[TARGET] Elite Standard Compliance (≥120 chars): {elite_compliant}/{len(all_bullets)} ({elite_compliant/len(all_bullets)*100:.1f}%)")

    if elite_compliant / len(all_bullets) >= 0.80:
        print("   [OK] PASS - Meets elite standard (≥80% bullets at 120+ chars)")
    else:
        print("   [X] FAIL - Below elite standard (need ≥80% bullets at 120+ chars)")

    # Compare to reference CV (Fayed Hanafi: 127 chars average)
    print(f"\n[COMPARE] Comparison to Reference Elite CV (Fayed Hanafi FR):")
    print(f"   Reference average: 127 chars")
    print(f"   Generated average: {avg_len:.1f} chars")
    diff = avg_len - 127
    if diff >= 0:
        print(f"   Difference: +{diff:.1f} chars [OK]")
    else:
        print(f"   Difference: {diff:.1f} chars [!]")

# Check coursework
print("\n" + "="*80)
print("[EDU] COURSEWORK ANALYSIS")
print("="*80)

if "education" in content:
    for idx, edu in enumerate(content["education"]):
        institution = edu.get("institution", "Unknown")
        coursework = edu.get("coursework", [])
        coursework_count = len(coursework)

        print(f"\n--- Education #{idx+1}: {institution}")
        print(f"   Coursework items: {coursework_count}")

        if coursework_count >= 6:
            print(f"   [OK] EXCELLENT (elite standard: 6-8 items)")
        elif coursework_count >= 5:
            print(f"   [OK] GOOD (minimum: 5 items)")
        else:
            print(f"   [X] TOO SHORT (need 6-8 items for elite CVs)")

        print(f"   Items: {', '.join(coursework[:5])}{'...' if len(coursework) > 5 else ''}")

# Check IT skills
print("\n" + "="*80)
print("[TECH] IT SKILLS ANALYSIS")
print("="*80)

it_skills = content.get("it_skills", [])
it_skills_count = len(it_skills)

print(f"\nIT Skills count: {it_skills_count}")
if it_skills_count >= 6:
    print("   [OK] GOOD (elite standard: 6+ items)")
else:
    print(f"   [X] TOO SHORT (need 6+ items, got {it_skills_count})")

print(f"   Items: {', '.join(it_skills)}")

# Final verdict
print("\n" + "="*80)
print("[TARGET] FINAL VERDICT")
print("="*80)

if all_bullets:
    elite_rate = elite_compliant / len(all_bullets)
    avg_passes = avg_len >= 120
    coursework_passes = all(len(edu.get("coursework", [])) >= 5 for edu in content.get("education", []))
    skills_passes = it_skills_count >= 6

    total_score = sum([
        elite_rate >= 0.80,
        avg_passes,
        coursework_passes,
        skills_passes
    ])

    print(f"\nChecklist:")
    print(f"  {'[OK]' if elite_rate >= 0.80 else '[X]'} ≥80% bullets at 120+ chars: {elite_compliant}/{len(all_bullets)} ({elite_rate*100:.1f}%)")
    print(f"  {'[OK]' if avg_passes else '[X]'} Average bullet length ≥120 chars: {avg_len:.1f}")
    print(f"  {'[OK]' if coursework_passes else '[X]'} All coursework ≥5 items: {coursework_passes}")
    print(f"  {'[OK]' if skills_passes else '[X]'} IT skills ≥6 items: {it_skills_count}")

    print(f"\nScore: {total_score}/4")

    if total_score == 4:
        print("[EXCELLENT] EXCELLENT - Ready for 90%+ PFR")
    elif total_score >= 3:
        print("[OK] GOOD - Should achieve 85-90% PFR")
    elif total_score >= 2:
        print("[!]  FAIR - May achieve 80-85% PFR")
    else:
        print("[X] POOR - Likely <80% PFR, needs improvement")

print("\n" + "="*80)
print("Test complete!")
print("="*80)
