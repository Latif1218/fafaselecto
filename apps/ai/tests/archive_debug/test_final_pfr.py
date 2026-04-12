"""
TEST FINAL: Generation de 3 CVs avec marges ajustees
Objectif: Verifier gain de +2 points PFR (86.5% -> 88%)
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generator import CVGenerator
from app.density import DensityCalculator

print('='*80)
print('TEST FINAL - GENERATION 3 CVS AVEC MARGES AJUSTEES')
print('='*80)
print()

print('MODIFICATIONS APPLIQUEES:')
print('  - .hr { margin: 15px 0 5px 0; } -> margin: 16px 0 6px 0; }')
print('  - .details-gap { margin-bottom: 35px; } -> margin-bottom: 37px; }')
print()
print('IMPACT ATTENDU: +1.5-2 points PFR')
print()
print('='*80)
print()

# Test CVs
test_cvs = [
    {
        'name': 'CV_Fayed_HANAFI_fr_PDF.pdf',
        'path': Path(__file__).parent.parent / 'input' / 'CV_Fayed_HANAFI_fr_PDF.pdf',
        'languages': ['fr'],
        'pfr_avant': 86.5,
    },
    {
        'name': 'CV_Fayed_HANAFI_en_PDF.pdf',
        'path': Path(__file__).parent.parent / 'input' / 'CV_Fayed_HANAFI_en_PDF.pdf',
        'languages': ['en'],
        'pfr_avant': None,  # Non teste avant
    },
    {
        'name': 'BAD_CV.png',
        'path': Path(__file__).parent.parent / 'input' / 'BAD_CV.png',
        'languages': ['fr'],
        'pfr_avant': 65.8,  # Derniere generation
    },
]

results = []

for idx, cv in enumerate(test_cvs, 1):
    print(f'[TEST {idx}/3] {cv["name"]}')
    print('-'*80)

    if not cv['path'].exists():
        print(f'  [SKIP] Fichier introuvable: {cv["path"]}')
        print()
        continue

    try:
        # Load PDF/PNG
        pdf_bytes = cv['path'].read_bytes()

        # Generate CV
        print(f'  Generation en cours...')
        generator = CVGenerator()
        result = generator.generate_from_pdf(pdf_bytes, domain='finance', languages=cv['languages'])

        # Get metrics for each language
        for lang in cv['languages']:
            lang_result = result[lang]
            pfr = lang_result.fill_percentage
            chars = lang_result.char_count

            # Recalculate with DensityCalculator for text height
            metrics = DensityCalculator.calculate_pfr(lang_result.pdf_bytes)

            # Save PDF
            output_name = cv['name'].replace('.pdf', '').replace('.png', '') + f'_FINAL_{lang.upper()}.pdf'
            output_path = Path(__file__).parent.parent / 'output' / output_name
            output_path.write_bytes(lang_result.pdf_bytes)

            # Store result
            result_data = {
                'cv_name': cv['name'],
                'language': lang,
                'pfr': pfr,
                'chars': chars,
                'text_height': metrics.text_height,
                'pfr_avant': cv['pfr_avant'],
                'output': output_name,
            }
            results.append(result_data)

            # Display
            print(f'  [{lang.upper()}] PFR: {pfr:.1f}% | Chars: {chars} | Output: {output_name}')
            if metrics.text_height:
                print(f'        Text height: {metrics.text_height:.1f} pts')

            if cv['pfr_avant']:
                gain = pfr - cv['pfr_avant']
                print(f'        Gain vs avant: {gain:+.1f} points')

        print()

    except Exception as e:
        print(f'  [ERROR] {str(e)}')
        print()
        continue

# Summary table
print('='*80)
print('TABLEAU RECAPITULATIF')
print('='*80)
print()

print(f'{"CV":<35} | {"Lang":<4} | {"PFR Avant":<12} | {"PFR Apres":<12} | {"Gain":<8} | {"Chars"}')
print('-'*80)

for r in results:
    cv_short = r['cv_name'][:33]
    pfr_avant = f"{r['pfr_avant']:.1f}%" if r['pfr_avant'] else "N/A"
    pfr_apres = f"{r['pfr']:.1f}%"

    if r['pfr_avant']:
        gain = r['pfr'] - r['pfr_avant']
        gain_str = f"{gain:+.1f}%"
    else:
        gain_str = "N/A"

    print(f'{cv_short:<35} | {r["language"]:<4} | {pfr_avant:<12} | {pfr_apres:<12} | {gain_str:<8} | {r["chars"]}')

print()
print('='*80)
print('ANALYSE')
print('='*80)
print()

# Check if target reached
pfr_values = [r['pfr'] for r in results if r['language'] == 'fr']
if pfr_values:
    avg_pfr = sum(pfr_values) / len(pfr_values)
    print(f'PFR moyen (FR): {avg_pfr:.1f}%')

    if avg_pfr >= 88:
        print('[SUCCESS] Objectif 88% atteint!')
    elif avg_pfr >= 87:
        print('[GOOD] Proche de l\'objectif (87-88%)')
    elif avg_pfr >= 85:
        print('[OK] Dans la zone acceptable (85-87%)')
    else:
        print('[WARNING] PFR encore sous 85%')

    print()

# Check gains
gains = [r['pfr'] - r['pfr_avant'] for r in results if r['pfr_avant']]
if gains:
    avg_gain = sum(gains) / len(gains)
    print(f'Gain moyen: {avg_gain:+.1f} points')

    if avg_gain >= 1.5:
        print('[SUCCESS] Gain attendu atteint (+1.5-2 pts)')
    elif avg_gain >= 1.0:
        print('[PARTIAL] Gain partiel (+1-1.5 pts)')
    else:
        print('[LIMITED] Gain limite (<1 pt)')

print()
print('='*80)
print('FICHIERS GENERES')
print('='*80)
print()

for r in results:
    print(f'  {r["output"]} (PFR: {r["pfr"]:.1f}%)')

print()
print('='*80)
