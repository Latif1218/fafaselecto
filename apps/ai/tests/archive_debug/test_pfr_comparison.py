"""
TEST CRITIQUE: Comparaison PFR PDF original vs PDF généré
Utilise la MÊME méthode de calcul (DensityCalculator) pour les deux
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.density import DensityCalculator

print('='*80)
print('ANALYSE CRITIQUE: PFR ORIGINAL VS GENERE')
print('='*80)
print()

# 1. PDF ORIGINAL (référence)
print('[1/2] Calcul PFR du PDF ORIGINAL (CV_Fayed_HANAFI_fr_PDF.pdf)')
print('-'*80)

pdf_original_path = Path(__file__).parent.parent / 'input' / 'CV_Fayed_HANAFI_fr_PDF.pdf'
pdf_original_bytes = pdf_original_path.read_bytes()

metrics_original = DensityCalculator.calculate_pfr(pdf_original_bytes)

print(f'PFR: {metrics_original.fill_percentage}%')
print(f'Characters: {metrics_original.char_count}')
print(f'Text height: {metrics_original.text_height:.1f} points' if metrics_original.text_height else 'N/A')
print(f'Page height: {metrics_original.page_height:.1f} points' if metrics_original.page_height else 'N/A')
print(f'Coverage: {metrics_original.text_height / metrics_original.page_height * 100:.1f}%' if metrics_original.text_height and metrics_original.page_height else 'N/A')
print()

# 2. PDF GENERE (dernier test)
print('[2/2] Calcul PFR du PDF GENERE (cv_modele_NEW_PROMPT_fr.pdf)')
print('-'*80)

pdf_genere_path = Path(__file__).parent.parent / 'output' / 'cv_modele_NEW_PROMPT_fr.pdf'

if not pdf_genere_path.exists():
    print('ERREUR: PDF genere introuvable')
    sys.exit(1)

pdf_genere_bytes = pdf_genere_path.read_bytes()

metrics_genere = DensityCalculator.calculate_pfr(pdf_genere_bytes)

print(f'PFR: {metrics_genere.fill_percentage}%')
print(f'Characters: {metrics_genere.char_count}')
print(f'Text height: {metrics_genere.text_height:.1f} points' if metrics_genere.text_height else 'N/A')
print(f'Page height: {metrics_genere.page_height:.1f} points' if metrics_genere.page_height else 'N/A')
print(f'Coverage: {metrics_genere.text_height / metrics_genere.page_height * 100:.1f}%' if metrics_genere.text_height and metrics_genere.page_height else 'N/A')
print()

# 3. COMPARAISON
print('='*80)
print('COMPARAISON DETAILLEE')
print('='*80)
print()

print(f'{"Métrique":<30} | {"Original":<15} | {"Généré":<15} | {"Delta"}')
print('-'*80)
print(f'{"PFR (%)":<30} | {metrics_original.fill_percentage:<15.1f} | {metrics_genere.fill_percentage:<15.1f} | {metrics_genere.fill_percentage - metrics_original.fill_percentage:+.1f}')
print(f'{"Characters":<30} | {metrics_original.char_count:<15} | {metrics_genere.char_count:<15} | {metrics_genere.char_count - metrics_original.char_count:+d}')

if metrics_original.text_height and metrics_genere.text_height:
    print(f'{"Text height (points)":<30} | {metrics_original.text_height:<15.1f} | {metrics_genere.text_height:<15.1f} | {metrics_genere.text_height - metrics_original.text_height:+.1f}')

if metrics_original.page_height and metrics_genere.page_height:
    print(f'{"Page height (points)":<30} | {metrics_original.page_height:<15.1f} | {metrics_genere.page_height:<15.1f} | {metrics_genere.page_height - metrics_original.page_height:+.1f}')

print()

# 4. DIAGNOSTIC
print('='*80)
print('DIAGNOSTIC')
print('='*80)
print()

pfr_diff = abs(metrics_genere.fill_percentage - metrics_original.fill_percentage)
char_diff = metrics_genere.char_count - metrics_original.char_count

print(f'Ecart PFR: {pfr_diff:.1f} points')
print(f'Ecart caracteres: {char_diff:+d} chars')
print()

if pfr_diff < 3:
    print('[OK] PFR quasiment identique (<3 points)')
    print('=> Le contenu genere est EQUIVALENT')
    print('=> Pas besoin d\'enrichissement')
elif pfr_diff < 6:
    print('[WARNING] PFR legerement inferieur (3-6 points)')
    print('=> Petit ecart, possiblement du au layout ou spacing')
    if char_diff < -50:
        print('=> Manque de contenu detecte ({} chars)'.format(abs(char_diff)))
    else:
        print('=> Contenu similaire, ecart probablement layout/espacement')
elif pfr_diff < 10:
    print('[CRITICAL] PFR significativement inferieur (6-10 points)')
    if char_diff < -100:
        print('=> CONTENU INSUFFISANT ({} chars manquants)'.format(abs(char_diff)))
        print('=> Action requise: enrichir bullets, activities, coursework')
    else:
        print('=> PROBLEME DE LAYOUT/RENDU')
        print('=> Contenu similaire ({:+d} chars) mais PFR different'.format(char_diff))
        print('=> Verifier: marges, line-height, spacing, font-size')
else:
    print('[FAIL] PFR tres inferieur (>10 points)')
    print('=> PROBLEME MAJEUR de contenu OU de layout')

print()

# 5. VERIFICATION HYPOTHESE
print('='*80)
print('VERIFICATION HYPOTHESE UTILISATEUR')
print('='*80)
print()

if metrics_original.fill_percentage < 85:
    print('[HYPOTHESE VALIDEE]')
    print(f'Le PDF original a un PFR de {metrics_original.fill_percentage}%, PAS 90.7%!')
    print('=> Le "90.7%" cite etait probablement une erreur ou calcule differemment')
    print('=> Nos CVs generes sont CONFORMES a la reference reelle')
elif metrics_original.fill_percentage >= 88:
    print('[HYPOTHESE INVALIDEE]')
    print(f'Le PDF original a bien un PFR de {metrics_original.fill_percentage}%')
    print('=> Le calcul est coherent')
    print('=> Il y a un vrai ecart de contenu ou layout a combler')
else:
    print('[ZONE GRISE]')
    print(f'Le PDF original a un PFR de {metrics_original.fill_percentage}%')
    print('=> Entre 85-88%, proche de notre generation')

print()
print('='*80)
print('RECOMMANDATION')
print('='*80)
print()

if metrics_original.fill_percentage < 84:
    print('=> NE PAS enrichir davantage')
    print('=> Le systeme genere deja au niveau de la reference')
    print('=> Se concentrer sur le pattern francais (deja OK)')
elif char_diff < -100 and pfr_diff > 6:
    print('=> ENRICHIR le contenu:')
    print('   1. Allonger activities_interests (ajouter details)')
    print('   2. Completer coursework pour toutes educations')
    print('   3. Augmenter legerement longueur bullets (+10-15 chars)')
else:
    print('=> VERIFIER le layout:')
    print('   1. Marges identiques au PDF original?')
    print('   2. Line-height identique?')
    print('   3. Font-size identique?')

print('='*80)
