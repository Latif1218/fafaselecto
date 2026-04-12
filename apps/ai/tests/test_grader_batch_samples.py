"""
Test batch CV Grader sur tous les CVs SAMPLES
Objectif: Valider scores et tips pour upsell freemium
"""

import sys
import os
import io

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.generator import CVGenerator
from app.cv_grader import grade_cv, format_client_output
from app.models import CVGenerationResult
from app.llm_client import extract_text_from_pdf_bytes
from app.llm_client_anthropic import generate_cv_content_claude


def grade_cv_from_pdf(pdf_path: str, generator: CVGenerator):
    """
    Grade un CV depuis son PDF en réutilisant le JSON généré par Postulae

    Returns:
        dict avec score, tips, CTA + métadonnées
    """
    print(f"\n{'='*60}")
    print(f"GRADING: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")

    # 1. Lire PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # 2. Extraire et structurer CV (comme Postulae le ferait)
    try:
        raw_text = extract_text_from_pdf_bytes(pdf_bytes, filename=os.path.basename(pdf_path))
        print(f"✓ Texte extrait: {len(raw_text)} chars")

        # Générer structure JSON FR (comme pour génération CV)
        cv_data = generate_cv_content_claude(
            raw_text=raw_text,
            language="fr",
            enrichment_instructions=None  # Pas d'enrichissement pour grading
        )
        print(f"✓ CV structuré: {len(cv_data.get('work_experience', []))} expériences")

    except Exception as e:
        print(f"✗ Erreur extraction/structuration: {e}")
        return None

    # 3. Analyser métadonnées (sans générer PDF complet)
    analysis = {
        "page_count": 1,  # Assume 1 page pour samples
        "pfr": 0,  # Sera estimé par formule
        "has_colors": False,  # Conservative (pas Vision API pour ce test)
        "has_charts": False,
        "has_photo": False,
        "has_column_format": False,  # Sera détecté via heuristiques
        "has_dates": True,  # Assume présent
        "mixed_languages": False
    }

    # Estimation PFR depuis contenu structuré
    total_chars = sum(
        len(' '.join(exp.get('bullets', [])))
        for exp in cv_data.get('work_experience', [])
    )
    total_chars += sum(
        len(' '.join(edu.get('coursework', [])))
        for edu in cv_data.get('education', [])
    )

    # Formule calibrée (cf cv_grader.py)
    estimated_bullets = max(1, total_chars // 150)
    pfr_estimate = min(98, max(40, (total_chars * 0.027) + (estimated_bullets * 1.5) + 35))
    analysis["pfr"] = round(pfr_estimate, 1)

    print(f"✓ PFR estimé: {analysis['pfr']}%")

    # 4. Grading
    result = grade_cv(cv_data, analysis)
    output = format_client_output(result)

    # 5. Affichage résultats
    print(f"\n📊 RÉSULTAT GRADING")
    print(f"Score: {output['score']}/100 {output['color_display']}")
    print(f"Couleur: {output['color']}")
    print(f"\n💡 TIPS UPSELL:")
    for i, tip in enumerate(output['tips'], 1):
        print(f"  {i}. {tip}")
    print(f"\n🎯 CTA: {output['cta']}")

    # Métadonnées pour analyse batch
    return {
        "filename": os.path.basename(pdf_path),
        "score": output['score'],
        "color": output['color'],
        "pfr": analysis['pfr'],
        "tips_count": len(output['tips']),
        "tips": output['tips'],
        "cta": output['cta'],
        "experiences_count": len(cv_data.get('work_experience', [])),
        "bullets_total": sum(len(exp.get('bullets', [])) for exp in cv_data.get('work_experience', []))
    }


def main():
    """Test batch sur tous les CVs SAMPLES"""

    samples_dir = r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES"

    # Liste PDFs uniquement (pas .jpg ni dossiers)
    pdf_files = [
        os.path.join(samples_dir, f)
        for f in os.listdir(samples_dir)
        if f.endswith('.pdf')
    ]

    print(f"\n{'='*60}")
    print(f"TEST BATCH GRADER - {len(pdf_files)} CVs SAMPLES")
    print(f"{'='*60}")

    # Init generator
    generator = CVGenerator()

    # Grade tous les CVs
    results = []
    for pdf_path in sorted(pdf_files):
        try:
            result = grade_cv_from_pdf(pdf_path, generator)
            if result:
                results.append(result)
        except Exception as e:
            print(f"\n✗ ERREUR sur {os.path.basename(pdf_path)}: {e}")

    # Analyse globale
    print(f"\n\n{'='*60}")
    print(f"📈 ANALYSE BATCH - {len(results)} CVs gradés")
    print(f"{'='*60}\n")

    # Stats scores
    if not results:
        print("❌ Aucun CV gradé avec succès")
        return results

    scores = [r['score'] for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0

    print(f"Score moyen: {avg_score:.1f}/100")
    print(f"Score min: {min(scores)}/100 ({[r['filename'] for r in results if r['score'] == min(scores)][0]})")
    print(f"Score max: {max(scores)}/100 ({[r['filename'] for r in results if r['score'] == max(scores)][0]})")

    # Distribution couleurs
    from collections import Counter
    colors = Counter(r['color'] for r in results)
    print(f"\n🎨 Distribution couleurs:")
    for color, count in colors.most_common():
        emoji = {"red": "🔴", "orange": "🟠", "yellow": "🟡", "light_green": "🟢", "dark_green": "💚"}
        print(f"  {emoji.get(color, '⚪')} {color}: {count} CVs ({count/len(results)*100:.0f}%)")

    # PFR moyen
    pfr_avg = sum(r['pfr'] for r in results) / len(results) if results else 0
    print(f"\n📏 PFR moyen: {pfr_avg:.1f}%")

    # Tips les plus fréquents
    all_tips = []
    for r in results:
        all_tips.extend(r['tips'])

    tips_counter = Counter(all_tips)
    print(f"\n💡 Top 5 tips upsell (les plus donnés):")
    for tip, count in tips_counter.most_common(5):
        print(f"  • {tip} ({count}×)")

    # Détail par CV
    print(f"\n\n{'='*60}")
    print(f"📋 DÉTAIL PAR CV")
    print(f"{'='*60}\n")

    # Trier par score décroissant
    results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)

    for r in results_sorted:
        emoji = {"red": "🔴", "orange": "🟠", "yellow": "🟡", "light_green": "🟢", "dark_green": "💚"}
        print(f"{r['filename']:20} | {r['score']:3}/100 {emoji.get(r['color'], '⚪')} | PFR: {r['pfr']:5.1f}% | {r['experiences_count']} exp, {r['bullets_total']} bullets")
        if r['tips']:
            print(f"  Tips: {r['tips'][0][:60]}...")

    print(f"\n{'='*60}")
    print(f"✅ TEST BATCH TERMINÉ - {len(results)}/{len(pdf_files)} CVs gradés")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    results = main()
