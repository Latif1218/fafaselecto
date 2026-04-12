"""Quick test to see what closing is extracted."""

import sys
sys.path.insert(0, '.')

from app.cover_letter_layout import parse_cover_letter_text

cover_letter_text = """Madame, Monsieur,

Diplômé de HEC Paris avec une formation en mathématiques appliquées à l'école Polytechnique, je souhaite rejoindre Goldman Sachs en tant qu'Investment Banking Analyst au sein de votre division M&A. Ayant contribué à l'exécution d'une transaction pharmaceutique de 450M€ chez Rothschild & Co, je suis convaincu que mon expertise en modélisation financière et ma rigueur analytique me permettront de contribuer immédiatement à vos équipes deal.

Lors de mon stage chez Rothschild & Co, j'ai participé à l'exécution d'une opération M&A pharmaceutique de 450M€, réalisant des modélisations financières (DCF, LBO) et des due diligences sur 8 marchés européens. J'ai optimisé le processus d'analyse de comparables, réduisant le temps de préparation de 30%, ce qui a permis aux banquiers seniors d'accélérer les présentations clients. J'ai également préparé des pitch books pour des dirigeants C-suite, contribuant à 3 mandats totalisant 1,2Md€.

En parallèle, mon expérience au sein du HEC Investment Club a renforcé mes capacités d'analyse et de leadership. En tant que Portfolio Manager, j'ai dirigé une équipe de 5 analystes gérant un fonds de 2M€, générant un rendement annualisé de 22% contre 15% pour le CAC 40. Cette expérience m'a permis d'affiner ma maîtrise des méthodologies DCF et d'évaluation relative, compétences essentielles pour le poste.

L'excellence analytique et la culture méritocratique de Goldman Sachs correspondent parfaitement à mes aspirations professionnelles. Les échanges que j'ai eus avec vos analystes lors des panels organisés par la HEC Finance Society ont confirmé mon intérêt pour votre environnement exigeant et vos opportunités de développement rapide. Votre leadership sur les transactions M&A cross-border complexes, notamment dans les secteurs pharmaceutique et TMT, représente exactement le type de mandats stratégiques sur lesquels je souhaite contribuer.

Je suis disponible pour un entretien à votre convenance et serais ravi de discuter de la manière dont mon expérience en M&A peut contribuer au succès de Goldman Sachs. Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Fayed HANAFI"""

parsed = parse_cover_letter_text(cover_letter_text, "fr")

print("="*80)
print("PARSED RESULTS")
print("="*80)
print(f"\nOPENING ({len(parsed['opening'])} chars):")
print(f"  {parsed['opening']}")

print(f"\nBODY PARAGRAPHS: {len(parsed['body_paragraphs'])}")
for i, p in enumerate(parsed['body_paragraphs']):
    print(f"  {i+1}. {p[:60]}... ({len(p)} chars)")

print(f"\nCLOSING ({len(parsed['closing'])} chars):")
print(f"  {parsed['closing']}")
print("\n")

# Count "Je suis disponible" in closing
count = parsed['closing'].count("Je suis disponible")
print(f"'Je suis disponible' appears {count}x in closing")

# Check if it's also in body paragraphs
for i, p in enumerate(parsed['body_paragraphs']):
    if "Je suis disponible" in p:
        print(f"\n[ALERT] 'Je suis disponible' ALSO found in body paragraph {i+1}!")
        print(f"  {p[:100]}...")
