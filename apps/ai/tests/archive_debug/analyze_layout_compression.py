"""
ANALYSE CRITIQUE DU LAYOUT - Identification de la compression verticale

OBJECTIF: Trouver pourquoi on perd 55.5 points de hauteur (763.6 → 708.1 pts)
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

print('='*80)
print('ETAPE 1: IDENTIFICATION DES PARAMETRES CSS COMPRESSIFS')
print('='*80)
print()

# Paramètres identifiés dans le template
params_actuels = {
    'body line-height': 1.1,
    '.inst/.company line-height': 0.7,
    '.degree line-height': 0.7,
    '.role line-height': 0.7,
    'bullets li margin-bottom': '0.5px',
    '.details-gap margin-bottom': '35px',
    '.hr margin': '15px 0 5px 0',
}

params_recommandes = {
    'body line-height': 1.15,  # Standard CV: 1.15-1.2
    '.inst/.company line-height': 1.0,  # Normal: 1.0
    '.degree line-height': 1.0,
    '.role line-height': 1.0,
    'bullets li margin-bottom': '1.5px',  # Plus d'espace entre bullets
    '.details-gap margin-bottom': '38px',  # Légèrement plus
    '.hr margin': '16px 0 6px 0',  # Légèrement plus
}

print('PARAMETRES ACTUELS (compressifs):')
print('-'*80)
for param, valeur in params_actuels.items():
    print(f'  {param:<35} = {valeur}')

print()
print('PARAMETRES RECOMMANDES (expansifs):')
print('-'*80)
for param, valeur in params_recommandes.items():
    print(f'  {param:<35} = {valeur}')

print()
print('='*80)
print('ETAPE 2: CALCUL DE L\'IMPACT THEORIQUE')
print('='*80)
print()

# Estimations basées sur le contenu du CV
estimations = {
    'Lignes de texte (body)': 35,  # ~35 lignes de texte normal
    'Titres (inst/company/degree/role)': 10,  # ~10 titres
    'Bullets': 7,  # 7 bullets
    'Sections (hr)': 4,  # 4 sections
    'Entries (details-gap)': 6,  # ~6 entries (edu + exp)
}

print('ESTIMATIONS DE CONTENU:')
print('-'*80)
for element, count in estimations.items():
    print(f'  {element:<35} : {count}')

print()

# Calcul de l'impact
font_size_body = 9  # 9pt
font_size_titre = 9  # 9pt

impact_body_lh = estimations['Lignes de texte (body)'] * font_size_body * (params_recommandes['body line-height'] - params_actuels['body line-height'])

impact_titres_lh = estimations['Titres (inst/company/degree/role)'] * font_size_titre * (params_recommandes['.inst/.company line-height'] - params_actuels['.inst/.company line-height'])

impact_bullets = estimations['Bullets'] * (1.5 - 0.5)  # margin-bottom

impact_hr = estimations['Sections (hr)'] * (16 + 6 - 15 - 5)  # margin top+bottom

impact_gaps = estimations['Entries (details-gap)'] * (38 - 35)  # margin-bottom

impact_total = impact_body_lh + impact_titres_lh + impact_bullets + impact_hr + impact_gaps

print('CALCUL D\'IMPACT (en points):')
print('-'*80)
print(f'  Body line-height (1.1->1.15):        +{impact_body_lh:.1f} pts')
print(f'  Titres line-height (0.7->1.0):       +{impact_titres_lh:.1f} pts')
print(f'  Bullets margin (0.5px->1.5px):       +{impact_bullets:.1f} pts')
print(f'  HR margins (15/5->16/6):             +{impact_hr:.1f} pts')
print(f'  Details gaps (35px->38px):           +{impact_gaps:.1f} pts')
print('-'*80)
print(f'  TOTAL THEORIQUE:                     +{impact_total:.1f} pts')
print()
print(f'  OBJECTIF (perte actuelle):           +55.5 pts')
print(f'  ECART:                                {impact_total - 55.5:+.1f} pts')

print()
print('='*80)
print('ETAPE 3: DIAGNOSTIC')
print('='*80)
print()

if abs(impact_total - 55.5) < 10:
    print('[OK] Les parametres identifies expliquent la compression!')
    print(f'=> Impact theorique: {impact_total:.1f} pts vs objectif 55.5 pts')
    print(f'=> Ecart: {abs(impact_total - 55.5):.1f} pts (acceptable)')
else:
    print('[WARNING] Impact theorique different de l\'objectif')
    print(f'=> Impact calcule: {impact_total:.1f} pts')
    print(f'=> Objectif: 55.5 pts')
    print(f'=> Ecart: {abs(impact_total - 55.5):.1f} pts')
    print()
    print('Causes possibles:')
    print('  - Estimations de contenu incorrectes')
    print('  - Autres parametres non identifies')
    print('  - Effets de cascade CSS')

print()
print('='*80)
print('ETAPE 4: PARAMETRES CRITIQUES A CORRIGER')
print('='*80)
print()

critiques = [
    ('line-height body', '1.1', '1.15', f'+{impact_body_lh:.1f} pts', 'CRITIQUE'),
    ('line-height titres', '0.7', '1.0', f'+{impact_titres_lh:.1f} pts', 'CRITIQUE'),
    ('bullets margin', '0.5px', '1.5px', f'+{impact_bullets:.1f} pts', 'MOYEN'),
    ('hr margins', '15/5', '16/6', f'+{impact_hr:.1f} pts', 'FAIBLE'),
    ('details gaps', '35px', '38px', f'+{impact_gaps:.1f} pts', 'FAIBLE'),
]

print(f'{"Parametre":<25} | {"Actuel":<10} | {"Nouveau":<10} | {"Impact":<12} | {"Priorite"}')
print('-'*80)
for param, actuel, nouveau, impact, priorite in critiques:
    print(f'{param:<25} | {actuel:<10} | {nouveau:<10} | {impact:<12} | {priorite}')

print()
print('='*80)
print('RECOMMANDATION FINALE')
print('='*80)
print()

print('CORRECTIONS A APPLIQUER dans grid_template.html:')
print()
print('1. Ligne 13 (body):')
print('   AVANT: line-height: 1.1;')
print('   APRES: line-height: 1.15;')
print()
print('2. Ligne 178 (.inst, .company):')
print('   AVANT: line-height: 0.7;')
print('   APRES: line-height: 1.0;')
print()
print('3. Ligne 193 (.degree):')
print('   AVANT: line-height: 0.7;')
print('   APRES: line-height: 1.0;')
print()
print('4. Ligne 202 (.role):')
print('   AVANT: line-height: 0.7;')
print('   APRES: line-height: 1.0;')
print()
print('5. Ligne 275 (.bullets li):')
print('   AVANT: margin-bottom: 0.5px;')
print('   APRES: margin-bottom: 1.5px;')
print()
print('IMPACT TOTAL ATTENDU: +{:.1f} pts (objectif: +55.5 pts)'.format(impact_total))
print()
print('='*80)
