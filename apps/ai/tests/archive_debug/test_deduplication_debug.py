"""Debug deduplication logic."""

text = """Madame, Monsieur,

Diplômé d'HEC Paris avec une formation en mathématiques appliquées de l'école Polytechnique, je souhaite rejoindre Goldman Sachs en tant qu'Analyste Investment Banking au sein de votre division M&A. Ayant contribué à l'exécution d'une transaction pharmaceutique de 450M€ chez Rothschild & Co, je suis convaincu que mon expertise en modélisation financière et ma rigueur analytique me permettront de contribuer immédiatement à vos équipes deal.

Lors de mon stage chez Rothschild & Co, j'ai participé à l'exécution d'une opération M&A pharmaceutique de 450M€, en réalisant des modélisations financières (DCF, LBO) et des due diligences sur 8 marchés européens. J'ai optimisé le processus d'analyse de comparables, réduisant le temps de préparation de 30%, ce qui a permis aux banquiers seniors d'accélérer les présentations clients. J'ai également préparé des pitch books pour des dirigeants C-suite, contribuant à 3 mandats totalisant 1,2Md€.

En tant que Portfolio Manager du HEC Investment Club, j'ai démontré mes capacités de leadership et d'analyse rigoureuse en gérant un portefeuille de 2M€ avec une équipe de 5 analystes. En appliquant des méthodologies DCF et d'évaluation relative strictes sur des mid-caps françaises, nous avons généré un rendement annualisé de 22% contre 15% pour le CAC 40. Cette expérience a renforcé ma capacité à structurer des analyses complexes et à présenter des recommandations devant 100+ investisseurs.

La culture méritocratique de Goldman Sachs et son excellence dans les opérations M&A cross-border correspondent parfaitement à mes aspirations. Les échanges avec vos analystes lors des panels HEC Finance Society que j'ai organisés ont confirmé l'alignement entre vos valeurs de rigueur intellectuelle et mon parcours. Votre rôle de conseil sur des acquisitions pharmaceutiques majeures en Europe illustre exactement le type de mandats stratégiques auxquels je souhaite contribuer.

Je suis disponible pour un entretien à votre convenance et serais ravi de discuter de la manière dont mon expérience en M&A peut contribuer au succès de Goldman Sachs. Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Je suis disponible pour un entretien à votre convenance et serais ravi de discuter de la manière dont mon expérience en M&A peut contribuer au succès de Goldman Sachs. Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Fayed HANAFI"""

print("ORIGINAL TEXT:")
print(f"Paragraphs: {len(text.split(chr(10)+chr(10)))}")
print("")

# Apply deduplication logic
paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

print(f"After split: {len(paragraphs)} paragraphs")
for i, p in enumerate(paragraphs):
    print(f"{i+1}. {p[:60]}... ({len(p)} chars)")

# Check for duplicate paragraphs (especially closing)
deduplicated = []
seen = set()
duplicates_found = 0

for i, para in enumerate(paragraphs):
    # Normalize for comparison (remove extra spaces, punctuation differences)
    normalized = " ".join(para.split()).lower()

    print(f"\nPara {i+1}: len={len(normalized)}, in_seen={normalized in seen}")

    if normalized not in seen or len(normalized) < 20:  # Allow short paragraphs
        deduplicated.append(para)
        seen.add(normalized)
        print(f"  -> ADDED")
    else:
        duplicates_found += 1
        print(f"  -> SKIPPED (duplicate)")

print(f"\n\nDUPLICATES FOUND: {duplicates_found}")
print(f"FINAL PARAGRAPHS: {len(deduplicated)}")

if duplicates_found > 0:
    result = "\n\n".join(deduplicated)
    print(f"\nDEDUPLICATED TEXT:\n{result}")
