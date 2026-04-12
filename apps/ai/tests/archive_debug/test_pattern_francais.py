"""
Test du pattern français (NOM vs VERBE) et calcul PFR
"""
import sys
import json
from pathlib import Path

# Fix encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm_client import extract_text_from_pdf_bytes, generate_cv_content
from app.generator import CVGenerator

print('='*80)
print('TEST PATTERN FRANCAIS + PFR')
print('='*80)
print()

# Load CV Modèle
pdf_path = Path(__file__).parent.parent / 'input' / 'CV_Fayed_HANAFI_fr_PDF.pdf'
pdf_bytes = pdf_path.read_bytes()

print('[1/3] Extraction du texte...')
raw_text = extract_text_from_pdf_bytes(pdf_bytes, 'CV_Fayed_HANAFI_fr_PDF.pdf')
print(f'   Texte extrait: {len(raw_text)} chars')
print()

print('[2/3] Generation du contenu (strategie bullets longs)...')
cv_content = generate_cv_content({'raw_text': raw_text}, domain='finance', language='fr')
print()

print('[3/3] Validation du pattern francais:')
print('='*80)

# Check all bullets for pattern
work_exp = cv_content.get('work_experience', [])
all_bullets = []
errors = []

for idx, exp in enumerate(work_exp, 1):
    company = exp.get('company', 'Unknown')
    bullets = exp.get('bullets', [])

    print(f'\nExperience #{idx}: {company}')
    print('-'*80)

    for bidx, bullet in enumerate(bullets, 1):
        all_bullets.append(bullet)

        # Check if starts with verb (past participle) - FORBIDDEN
        forbidden_starts = [
            'Optimise', 'Realise', 'Gere', 'Analyse', 'Contribue',
            'Developpe', 'Cree', 'Pilote', 'Mis en place', 'Lance',
            'Coordonne', 'Supervise', 'Elabore', 'Restructure'
        ]

        # Also check accented versions
        forbidden_accented = [
            'Optimisé', 'Réalisé', 'Géré', 'Analysé', 'Contribué',
            'Développé', 'Créé', 'Piloté', 'Lancé',
            'Coordonné', 'Supervisé', 'Élaboré', 'Restructuré'
        ]

        is_error = False
        for verb in forbidden_starts + forbidden_accented:
            if bullet.startswith(verb):
                is_error = True
                break

        marker = '[X] ANGLICISME' if is_error else '[OK]'
        print(f'  Bullet #{bidx} [{len(bullet):3d} chars] {marker}')
        print(f'    {bullet[:100]}...')

        if is_error:
            errors.append((idx, bidx, bullet))

print()
print('='*80)
print('RESUME PATTERN')
print('='*80)
print(f'Total bullets: {len(all_bullets)}')
print(f'Pattern correct (NOM): {len(all_bullets) - len(errors)}')
print(f'Anglicismes (VERBE): {len(errors)}')

if len(errors) > 0:
    print()
    print('ERREURS DETECTEES:')
    for exp_idx, bullet_idx, bullet in errors:
        print(f'  Exp #{exp_idx}, Bullet #{bullet_idx}: {bullet[:80]}...')

# Bullet length stats
avg_len = sum(len(b) for b in all_bullets) / len(all_bullets) if all_bullets else 0
print()
print(f'Longueur moyenne bullets: {avg_len:.1f} chars')
print(f'Range: {min(len(b) for b in all_bullets)}-{max(len(b) for b in all_bullets)} chars')

# Generate full CV and get PFR
print()
print('='*80)
print('GENERATION PDF ET CALCUL PFR')
print('='*80)

generator = CVGenerator()
result = generator.generate_from_pdf(pdf_bytes, domain='finance', languages=['fr'])

# Access result properly - it's a dict with 'fr' key containing CVGenerationResult
fr_result = result['fr']
pfr_fr = fr_result.fill_percentage
chars_fr = fr_result.char_count

print(f'\nPFR FR: {pfr_fr:.1f}%')
print(f'Characters: {chars_fr}')
print(f'Target: 88-92%')
print(f'Ecart: {pfr_fr - 90:.1f} points')

print()
print('='*80)
print('RESULTAT FINAL')
print('='*80)

if len(errors) == 0 and pfr_fr >= 88 and pfr_fr <= 92:
    print('[SUCCESS] Pattern FR correct + PFR dans la cible!')
elif len(errors) == 0:
    print(f'[PARTIAL] Pattern FR correct mais PFR {pfr_fr:.1f}% (cible: 88-92%)')
elif pfr_fr >= 88 and pfr_fr <= 92:
    print(f'[PARTIAL] PFR OK mais {len(errors)} anglicismes detectes')
else:
    print(f'[FAIL] {len(errors)} anglicismes + PFR {pfr_fr:.1f}% hors cible')

print('='*80)
