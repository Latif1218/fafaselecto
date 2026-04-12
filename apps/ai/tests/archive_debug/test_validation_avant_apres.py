"""
Test de validation AVANT/APRÈS nouveau prompt système.
Compare les PFR sur BAD_CV (54% avant) et CV élite (90.7% avant).
"""
import os
import sys
import time
from pathlib import Path
from PIL import Image
import io

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import generate_cv_from_pdf

print("="*80)
print("TEST DE VALIDATION - AVANT/APRÈS NOUVEAU PROMPT SYSTÈME")
print("="*80)
print("\nObjectif : Reproduire qualité des CV élites (90%+ PFR)")
print("Cible bullets : 120-160 caractères (référence élite : 127 chars)")
print()

# ============================================================================
# TEST 1 : BAD_CV (54% PFR AVANT)
# ============================================================================

print("\n" + "="*80)
print("TEST 1 : BAD_CV.png (PFR AVANT : ~54%)")
print("="*80)
print("Objectif : Atteindre 85-92% PFR (gain de +31 à +38 points)")
print()

test1_success = False
test1_pfr = 0
test1_time = 0
test1_avg_bullet_len = 0

try:
    input_path = "input/BAD_CV.png"

    if not os.path.exists(input_path):
        print(f"[X] File not found: {input_path}")
    else:
        print(f"[1/4] Loading {input_path}...")
        with open(input_path, "rb") as f:
            png_bytes = f.read()
        print(f"   Loaded {len(png_bytes)} bytes")

        print("\n[2/4] Converting PNG to PDF...")
        img = Image.open(io.BytesIO(png_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')

        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, format='PDF')
        pdf_bytes = pdf_buffer.getvalue()
        print(f"   Converted to PDF: {len(pdf_bytes)} bytes")

        print("\n[3/4] Generating CV with NEW ELITE PROMPT...")
        print("   (watch for bullet length warnings below)")
        print()

        start_time = time.time()

        results = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr"]
        )

        test1_time = time.time() - start_time

        print()
        print("[4/4] Results:")

        fr = results["fr"]
        test1_pfr = fr.fill_percentage

        print(f"   PFR: {test1_pfr:.1f}%")
        print(f"   Pages: {fr.page_count}")
        print(f"   Characters: {fr.char_count}")
        print(f"   Time: {test1_time:.1f}s")

        # Analyze bullets
        if hasattr(fr, 'structured_content') and fr.structured_content:
            content = fr.structured_content
            if "work_experience" in content:
                bullets = []
                for exp in content["work_experience"]:
                    bullets.extend(exp.get("bullets", []))

                if bullets:
                    avg_len = sum(len(b) for b in bullets) / len(bullets)
                    test1_avg_bullet_len = avg_len
                    print(f"   Avg bullet length: {avg_len:.1f} chars (target: 120-160)")

        # Save
        os.makedirs("output", exist_ok=True)
        with open("output/bad_cv_NEW_PROMPT_fr.pdf", "wb") as f:
            f.write(fr.pdf_bytes)
        print(f"\n   [OK] Saved: output/bad_cv_NEW_PROMPT_fr.pdf")

        test1_success = True

except Exception as e:
    print(f"\n[X] Test 1 FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 2 : CV MODÈLE (90.7% PFR AVANT)
# ============================================================================

print("\n" + "="*80)
print("TEST 2 : CV_Fayed_HANAFI_fr_PDF.pdf (PFR AVANT : 90.7%)")
print("="*80)
print("Objectif : Maintenir 88-94% PFR (pas de dégradation)")
print()

test2_success = False
test2_pfr = 0
test2_time = 0
test2_avg_bullet_len = 0

try:
    input_path = "input/CV_Fayed_HANAFI_fr_PDF.pdf"

    if not os.path.exists(input_path):
        print(f"[X] File not found: {input_path}")
    else:
        print(f"[1/3] Loading {input_path}...")
        with open(input_path, "rb") as f:
            pdf_bytes = f.read()
        print(f"   Loaded {len(pdf_bytes)} bytes")

        print("\n[2/3] Generating CV with NEW ELITE PROMPT...")
        print("   (watch for bullet length warnings below)")
        print()

        start_time = time.time()

        results = generate_cv_from_pdf(
            pdf_bytes=pdf_bytes,
            domain="finance",
            languages=["fr"]
        )

        test2_time = time.time() - start_time

        print()
        print("[3/3] Results:")

        fr = results["fr"]
        test2_pfr = fr.fill_percentage

        print(f"   PFR: {test2_pfr:.1f}%")
        print(f"   Pages: {fr.page_count}")
        print(f"   Characters: {fr.char_count}")
        print(f"   Time: {test2_time:.1f}s")

        # Analyze bullets
        if hasattr(fr, 'structured_content') and fr.structured_content:
            content = fr.structured_content
            if "work_experience" in content:
                bullets = []
                for exp in content["work_experience"]:
                    bullets.extend(exp.get("bullets", []))

                if bullets:
                    avg_len = sum(len(b) for b in bullets) / len(bullets)
                    test2_avg_bullet_len = avg_len
                    print(f"   Avg bullet length: {avg_len:.1f} chars (target: 120-160)")

        # Save
        os.makedirs("output", exist_ok=True)
        with open("output/cv_modele_NEW_PROMPT_fr.pdf", "wb") as f:
            f.write(fr.pdf_bytes)
        print(f"\n   [OK] Saved: output/cv_modele_NEW_PROMPT_fr.pdf")

        test2_success = True

except Exception as e:
    print(f"\n[X] Test 2 FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TABLEAU COMPARATIF
# ============================================================================

print("\n" + "="*80)
print("TABLEAU COMPARATIF - AVANT/APRÈS")
print("="*80)
print()

# Display table
header = f"{'CV Name':<20} | {'PFR AVANT':<11} | {'PFR APRÈS':<11} | {'Delta':<8}"
separator = "-"*len(header)

print(separator)
print(header)
print(separator)

# Test 1
if test1_success:
    delta1 = test1_pfr - 54.0
    delta1_str = f"+{delta1:.1f}%" if delta1 >= 0 else f"{delta1:.1f}%"
    print(f"{'BAD_CV (faible)':<20} | {'54.0%':<11} | {f'{test1_pfr:.1f}%':<11} | {delta1_str:<8}")
else:
    print(f"{'BAD_CV (faible)':<20} | {'54.0%':<11} | {'FAILED':<11} | {'N/A':<8}")

# Test 2
if test2_success:
    delta2 = test2_pfr - 90.7
    delta2_str = f"+{delta2:.1f}%" if delta2 >= 0 else f"{delta2:.1f}%"
    print(f"{'CV Modèle (bon)':<20} | {'90.7%':<11} | {f'{test2_pfr:.1f}%':<11} | {delta2_str:<8}")
else:
    print(f"{'CV Modèle (bon)':<20} | {'90.7%':<11} | {'FAILED':<11} | {'N/A':<8}")

print(separator)

# ============================================================================
# BULLET LENGTH ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("ANALYSE LONGUEUR BULLETS")
print("="*80)
print()

print(f"{'CV Name':<20} | {'Avg Bullet (chars)':<20} | {'Statut':<30}")
print("-"*75)

# Test 1
if test1_success and test1_avg_bullet_len > 0:
    if 120 <= test1_avg_bullet_len <= 160:
        status1 = "[OK] OPTIMAL (120-160)"
    elif test1_avg_bullet_len > 160:
        status1 = "[!] TOO LONG (>160, risk verbosity)"
    else:
        status1 = "[X] TOO SHORT (<120, low PFR)"
    print(f"{'BAD_CV':<20} | {f'{test1_avg_bullet_len:.1f}':<20} | {status1:<30}")
elif test1_success:
    print(f"{'BAD_CV':<20} | {'N/A':<20} | {'No bullets analyzed':<30}")

# Test 2
if test2_success and test2_avg_bullet_len > 0:
    if 120 <= test2_avg_bullet_len <= 160:
        status2 = "[OK] OPTIMAL (120-160)"
    elif test2_avg_bullet_len > 160:
        status2 = "[!] TOO LONG (>160, risk verbosity)"
    else:
        status2 = "[X] TOO SHORT (<120, low PFR)"
    print(f"{'CV Modèle':<20} | {f'{test2_avg_bullet_len:.1f}':<20} | {status2:<30}")
elif test2_success:
    print(f"{'CV Modèle':<20} | {'N/A':<20} | {'No bullets analyzed':<30}")

print("-"*75)
print("Référence élite (Fayed CV original) : 127 chars")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print()

success_criteria = []

# Criterion 1: BAD_CV PFR
if test1_success:
    if 85 <= test1_pfr <= 92:
        print("[OK] BAD_CV atteint 85-92% PFR : Transformation réussie")
        success_criteria.append(True)
    else:
        print(f"[!] BAD_CV PFR = {test1_pfr:.1f}% (cible : 85-92%)")
        success_criteria.append(False)
else:
    print("[X] BAD_CV test failed")
    success_criteria.append(False)

# Criterion 2: CV Modèle PFR
if test2_success:
    if 88 <= test2_pfr <= 94:
        print("[OK] CV Modèle reste 88-94% : Pas de dégradation")
        success_criteria.append(True)
    else:
        print(f"[!] CV Modèle PFR = {test2_pfr:.1f}% (cible : 88-94%)")
        success_criteria.append(False)
else:
    print("[X] CV Modèle test failed")
    success_criteria.append(False)

# Criterion 3: Bullet length
if test1_success and test1_avg_bullet_len > 0 and test2_success and test2_avg_bullet_len > 0:
    avg_overall = (test1_avg_bullet_len + test2_avg_bullet_len) / 2
    if 120 <= avg_overall <= 160:
        print(f"[OK] Bullets moyens = {avg_overall:.1f} chars : Cible atteinte (120-160)")
        success_criteria.append(True)
    elif avg_overall > 160:
        print(f"[!] Bullets moyens = {avg_overall:.1f} chars : Trop longs (>160)")
        print("    Ajustement nécessaire : Réduire cible à 120-150 chars dans prompt")
        success_criteria.append(False)
    else:
        print(f"[X] Bullets moyens = {avg_overall:.1f} chars : Trop courts (<120)")
        success_criteria.append(False)
else:
    print("[!] Bullet length analysis incomplete")
    success_criteria.append(False)

# Overall verdict
print()
score = sum(success_criteria)
total = len(success_criteria)

print(f"Score global : {score}/{total}")
print()

if score == total:
    print("[EXCELLENT] Nouveau prompt validé - Prêt pour production")
elif score >= 2:
    print("[GOOD] Nouveau prompt efficace - Ajustements mineurs recommandés")
else:
    print("[NEEDS WORK] Nouveau prompt nécessite ajustements")

print("\n" + "="*80)
print("RECOMMANDATIONS")
print("="*80)
print()

if test1_success and test1_pfr < 85:
    print("1. BAD_CV PFR encore trop bas :")
    print("   - Vérifier extraction work_experience")
    print("   - Augmenter longueur minimale bullets à 130 chars")

if test2_success and test2_pfr > 94:
    print("2. CV Modèle PFR trop haut (>95% = trimming) :")
    print("   - Réduire longueur maximale bullets à 150 chars")

if (test1_avg_bullet_len > 160 or test2_avg_bullet_len > 160):
    print("3. Bullets trop longs (risque verbosité) :")
    print("   - Ajuster prompt : cible 120-150 chars (au lieu de 150-190)")
    print("   - Référence élite : 127 chars suffit pour 90.7% PFR")

if score == total:
    print("Aucun ajustement nécessaire - Système prêt !")

print("\n" + "="*80)
print("Test de validation terminé")
print("="*80)
