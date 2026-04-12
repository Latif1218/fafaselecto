"""
Test batch CV Grader FAST - Sans génération complète
Utilise heuristiques pour grading rapide sans appels Claude
"""

import sys
import os
import io

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.cv_grader import grade_cv, format_client_output, analyze_cv_metadata
from app.llm_client import extract_text_from_pdf_bytes
import re


def simulate_cv_structure_from_text(raw_text: str) -> dict:
    """
    Simule une structure CV basique depuis le texte brut
    Pour grading rapide sans appel LLM
    """
    # Détection expériences (patterns simples)
    exp_patterns = [
        r'(?:consultant|analyst|manager|director|stagiaire|intern|developer)',
        r'(?:•|-)\s*([A-Z][^\n]{60,200})',  # Bullets probables
    ]

    bullets = []
    for pattern in exp_patterns:
        bullets.extend(re.findall(pattern, raw_text, re.IGNORECASE))

    # Structure minimale pour grading
    return {
        "work_experience": [
            {
                "company": "Entreprise Simulée",
                "position": "Poste",
                "bullets": bullets[:20]  # Max 20 bullets détectés
            }
        ],
        "education": [
            {
                "institution": "Formation",
                "degree": "Diplôme",
                "coursework": ["Cours 1", "Cours 2", "Cours 3"]
            }
        ],
        "contact_information": [{"email": "email@example.com"}],
        "language_skills": ["Français", "Anglais"],
        "it_skills": ["Excel", "Python"]
    }


def grade_cv_fast(pdf_path: str):
    """
    Grade un CV rapidement sans appel LLM
    """
    print(f"\n{'='*60}")
    print(f"GRADING FAST: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")

    # 1. Extraire texte
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    try:
        raw_text = extract_text_from_pdf_bytes(pdf_bytes, filename=os.path.basename(pdf_path))
        print(f"✓ Texte extrait: {len(raw_text)} chars")
    except Exception as e:
        print(f"✗ Erreur extraction: {e}")
        return None

    # 2. Simuler structure CV (pas d'appel LLM)
    cv_data = simulate_cv_structure_from_text(raw_text)
    bullets_detected = len(cv_data['work_experience'][0]['bullets'])
    print(f"✓ Structure simulée: {bullets_detected} bullets détectés")

    # 3. Analyser métadonnées
    analysis = analyze_cv_metadata(raw_text, page_count=1)
    print(f"✓ PFR estimé: {analysis['pfr']}%")

    # 4. Grading
    result = grade_cv(cv_data, analysis)
    output = format_client_output(result)

    # 5. Affichage
    print(f"\n📊 RÉSULTAT GRADING")
    print(f"Score: {output['score']}/100 {output['color_display']}")
    print(f"Couleur: {output['color']}")
    print(f"\n💡 TIPS UPSELL:")
    for i, tip in enumerate(output['tips'], 1):
        print(f"  {i}. {tip}")
    print(f"\n🎯 CTA: {output['cta']}")

    return {
        "filename": os.path.basename(pdf_path),
        "score": output['score'],
        "color": output['color'],
        "pfr": analysis['pfr'],
        "tips": output['tips'],
        "cta": output['cta'],
        "char_count": len(raw_text),
        "bullets_detected": bullets_detected
    }


def main():
    samples_dir = r"C:\Users\Home\Documents\Postulae\CVs\SAMPLES"

    pdf_files = [
        os.path.join(samples_dir, f)
        for f in os.listdir(samples_dir)
        if f.endswith('.pdf')
    ]

    print(f"\n{'='*60}")
    print(f"TEST BATCH GRADER FAST - {len(pdf_files)} CVs SAMPLES")
    print(f"{'='*60}")

    results = []
    for pdf_path in sorted(pdf_files):
        try:
            result = grade_cv_fast(pdf_path)
            if result:
                results.append(result)
        except Exception as e:
            print(f"\n✗ ERREUR sur {os.path.basename(pdf_path)}: {e}")

    # Analyse globale
    print(f"\n\n{'='*60}")
    print(f"📈 ANALYSE BATCH - {len(results)} CVs gradés")
    print(f"{'='*60}\n")

    if not results:
        print("❌ Aucun CV gradé avec succès")
        return results

    # Stats
    scores = [r['score'] for r in results]
    avg_score = sum(scores) / len(scores)

    print(f"📊 SCORES:")
    print(f"  Moyenne: {avg_score:.1f}/100")
    print(f"  Min: {min(scores)}/100 ({[r['filename'] for r in results if r['score'] == min(scores)][0]})")
    print(f"  Max: {max(scores)}/100 ({[r['filename'] for r in results if r['score'] == max(scores)][0]})")

    # Distribution couleurs
    from collections import Counter
    colors = Counter(r['color'] for r in results)
    print(f"\n🎨 DISTRIBUTION COULEURS:")
    emoji_map = {"red": "🔴", "orange": "🟠", "yellow": "🟡", "light_green": "🟢", "dark_green": "💚"}
    for color, count in colors.most_common():
        pct = count/len(results)*100
        print(f"  {emoji_map.get(color, '⚪')} {color:12} : {count} CVs ({pct:.0f}%)")

    # PFR
    pfr_avg = sum(r['pfr'] for r in results) / len(results)
    print(f"\n📏 PFR MOYEN: {pfr_avg:.1f}%")

    # Tips les plus fréquents (POUR ANALYSE UPSELL)
    all_tips = []
    for r in results:
        all_tips.extend(r['tips'])

    tips_counter = Counter(all_tips)
    print(f"\n💡 TOP 5 TIPS UPSELL (les plus donnés):")
    for tip, count in tips_counter.most_common(5):
        print(f"  • {tip[:70]}... ({count}×)")

    # Détail par CV
    print(f"\n\n{'='*60}")
    print(f"📋 DÉTAIL PAR CV (trié par score)")
    print(f"{'='*60}\n")

    results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)

    for r in results_sorted:
        emoji = emoji_map.get(r['color'], '⚪')
        print(f"{r['filename']:20} | {r['score']:3}/100 {emoji} | PFR: {r['pfr']:5.1f}% | {r['char_count']:4} chars | {r['bullets_detected']} bullets")
        # Premier tip (le plus important pour upsell)
        if r['tips']:
            print(f"  → {r['tips'][0][:75]}")

    # Analyse upsell par couleur
    print(f"\n\n{'='*60}")
    print(f"🎯 ANALYSE UPSELL PAR COULEUR")
    print(f"{'='*60}\n")

    for color in ["red", "orange", "yellow", "light_green", "dark_green"]:
        cvs_color = [r for r in results if r['color'] == color]
        if cvs_color:
            emoji = emoji_map.get(color, '⚪')
            print(f"\n{emoji} {color.upper()} ({len(cvs_color)} CVs):")
            for r in cvs_color:
                print(f"  • {r['filename']}: \"{r['cta']}\"")

    print(f"\n{'='*60}")
    print(f"✅ TEST BATCH TERMINÉ - {len(results)}/{len(pdf_files)} CVs gradés")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    results = main()
