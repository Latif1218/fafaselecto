"""
Test de simulation: Applique le nouveau trimming sur les données existantes.
Pas d'appel API - utilise les JSON déjà générés.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.bullet_trimmer import smart_trim_bullet

print("=" * 80)
print("SIMULATION: Impact du nouveau trimming (155->140 chars)")
print("=" * 80)
print()

# Load the JSON generated previously
json_path = Path(__file__).parent.parent / "output" / "test_direct_content.json"

if not json_path.exists():
    print(f"ERROR: {json_path} n'existe pas")
    print("Vous devez d'abord générer un CV avec l'API pour avoir des données à tester.")
    sys.exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    cv_content = json.load(f)

print("Chargé: test_direct_content.json (généré avec trimming 170->155)")
print()

# Extract bullets
all_bullets = []
for exp in cv_content.get("work_experience", []):
    for bullet in exp.get("bullets", []):
        all_bullets.append(bullet)

print(f"Total bullets: {len(all_bullets)}")
print()

# Show current state (already trimmed with 170->155)
print("ÉTAT ACTUEL (avec trimming 170->155):")
print("-" * 80)
total_chars_current = sum(len(b) for b in all_bullets)
avg_current = total_chars_current / len(all_bullets) if all_bullets else 0

for i, bullet in enumerate(all_bullets, 1):
    print(f"{i}. [{len(bullet):3d} chars] {bullet[:70]}...")

print()
print(f"TOTAL: {len(all_bullets)} bullets, {total_chars_current} chars")
print(f"MOYENNE: {avg_current:.1f} chars")
print()

# Apply NEW trimming (155->140)
print("APRÈS NOUVEAU TRIMMING (155->140):")
print("-" * 80)

trimmed_bullets = []
trimmed_count = 0

for bullet in all_bullets:
    original_len = len(bullet)
    trimmed = smart_trim_bullet(bullet)
    trimmed_bullets.append(trimmed)

    if len(trimmed) < original_len:
        trimmed_count += 1

for i, (original, trimmed) in enumerate(zip(all_bullets, trimmed_bullets), 1):
    marker = " [TRIMMED]" if len(trimmed) < len(original) else ""
    delta = f" ({len(original)}->{len(trimmed)})" if len(trimmed) < len(original) else ""
    print(f"{i}. [{len(trimmed):3d} chars]{marker}{delta} {trimmed[:70]}...")

print()
total_chars_new = sum(len(b) for b in trimmed_bullets)
avg_new = total_chars_new / len(trimmed_bullets) if trimmed_bullets else 0

print(f"TOTAL: {len(trimmed_bullets)} bullets, {total_chars_new} chars")
print(f"MOYENNE: {avg_new:.1f} chars")
print(f"TRIMMED: {trimmed_count}/{len(all_bullets)} bullets")
print(f"RÉDUCTION TOTALE: {total_chars_current - total_chars_new} chars")
print()

# Compare with reference
print("=" * 80)
print("COMPARAISON AVEC RÉFÉRENCE ÉLITE")
print("=" * 80)

reference_avg = 139.1  # From cv_modele_content.json analysis

print(f"Référence CV élite:       {reference_avg:.1f} chars/bullet (PFR 90.7%)")
print(f"Avant nouveau trimming:   {avg_current:.1f} chars/bullet (PFR 78.1%)")
print(f"Après nouveau trimming:   {avg_new:.1f} chars/bullet (PFR estimé: ???)")
print()

gap_before = avg_current - reference_avg
gap_after = avg_new - reference_avg

print(f"ÉCART vs référence:")
print(f"  Avant: +{gap_before:.1f} chars ({gap_before/reference_avg*100:+.1f}%)")
print(f"  Après: {gap_after:+.1f} chars ({gap_after/reference_avg*100:+.1f}%)")
print()

# Estimate PFR impact
if abs(gap_after) < abs(gap_before):
    print("[OK] AMÉLIORATION: Le trimming rapproche de la référence élite")

    # Rough PFR estimate (based on chars reduction)
    char_reduction_pct = (total_chars_current - total_chars_new) / total_chars_current * 100
    pfr_before = 78.1
    pfr_loss = char_reduction_pct * 0.3  # Rough estimate: 1% char loss ≈ 0.3% PFR loss
    pfr_estimated = pfr_before - pfr_loss

    print(f"  PFR estimé: {pfr_estimated:.1f}% (perte ~{pfr_loss:.1f}% due au trimming)")
else:
    print("[X] PAS D'AMÉLIORATION: Le trimming s'éloigne encore plus de la référence")

print()
print("=" * 80)
print("NOTE: Pour un test réel avec génération LLM, attendez le reset du quota API")
print("=" * 80)
