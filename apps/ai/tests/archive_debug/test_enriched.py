"""
Test avec CV enrichi - ajout de 2 expériences supplémentaires
"""
import os
from app import CVGenerator

# Texte original extrait du PDF
original_text = """marlet MENDES GONCALVES

profil
Je suis à la recherche d'un emploi. Je bénéficie des expériences pratique acquise au cours de divers expérience professionnel. Doté d'une grande capacité d'adaptation, je sais me montrer proactif et digne de confiance dans la réalisation de mes missions.

CONTACT
07 55 43 30 53
marleymendes94@gmail.com
Saint-Maur-des-Fossés (94100)
22 ans
Permis B

COMPÉTENCES
Relation client, accueil physique et téléphonique
Gestion de dossiers (assurance, réclamation, expertise)
Utilisation du Pack Office (Word, Excel)
Travail en équipe et sens du service
Gestion du stress, autonomie et adaptabilité

Langues
Français - Maternelle
Portugais - Notions
Anglais - Notions

centres d'interet
Musculation, boxe
Voyages
Projet dans l'automobile

EXPERIENCES PROFESSIONNELLES

Professeur particulier de Mathématiques - Paris, France
Octobre 2019 - Mars 2021 (18 mois)
Suivi régulier de 3 élèves (4 heures par semaine en moyenne).
- Préparation des concours BCE avec un élève en Classe Préparatoire.
- Réalisation de fiches méthodes compilant les exercices clé et les notions incontournables.

Bredhill Consulting (Conseil en Stratégie en Banques et Assurances) - Paris, France
Juillet 2021 - Décembre 2021 (6 mois)
Consultant Junior
- Restructuration de l'offre de paiement et d'encaissement à proximité et à distance d'un grand groupe bancaire français.
- Réalisation de benchmarks (étude de l'offre de paiement et d'encaissement de 10 banques traditionnelles et 5 néobanques, étude du marché des terminaux de paiement proposés par les fintechs).

Saretec Expertise - Gestionnaire sinistres
Janvier 2024 - Juillet 2024 (7 mois)
Gestion et suivi des dossiers d'expertise pour les compagnies d'assurance
Coordination entre experts, assurés et assureurs
Traitement administratif complet : ouverture, mise à jour, vérification et clôture
Analyse des pièces justificatives et respect des délais et procédures internes
Utilisation de logiciels professionnels de gestion de sinistres

BCA Expertise / AXA - Chargé de réclamation (télétravail partiel)
Janvier 2025 - Février 2025
Analyse et traitement de dossiers de réclamation non automobile
Suivi des informations clients par mail
Application rigoureuse des procédures internes

Mutuelle Fraternelle d'Assurance (MFA), Maisons-Alfort - Chargé de clientèle (alternance)
Septembre 2022 - Juillet 2024
Vente et négociation de contrats d'assurance
Traitement de prospects et appels entrants/sortants
Accueil physique et téléphonique des clients

VVF Amboise - Animateur club vacances
Octobre 2024 - Décembre 2024
Animation d'activités pour enfants et adultes
Organisation d'événements : jeux apéro, soirées, veillées
Accueil des vacanciers

ERELEA électricien, Bondy - Électricien BTP
2021 (2 mois)
Raccordements, encastrements et branchements électriques
Découverte du milieu industriel et travail en équipe

Monoprix, Saint-Maur-des-Fossés - Conseiller clientèle
Juillet 2019
Mise en rayon, encaissement
Conseil et relation client

FORMATIONS PROFESSIONNELLES
BTS Assurance (en alternance)
École BeSAF, Paris - 2022 - Juillet 2024

Baccalauréat professionnel MELEC
Lycée Gourdou Leseurre, Saint-Maur-des-Fossés - 2020 - 2022

Formation LASER - Animateur touristique
Octobre - Décembre 2024
"""

def main():
    output_dir = "Output"
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "="*60)
    print("Test avec CV ENRICHI (+ 2 experiences)")
    print("="*60)

    try:
        from app.llm_client import generate_cv_content
        from app.density import DensityCalculator
        from app.layout import LayoutEngine
        from app.enrichment import ContentEnricher
        import time

        density_calc = DensityCalculator()
        layout_engine = LayoutEngine()
        enricher = ContentEnricher()

        # ETAPE 1: Generation du contenu de base FR
        print("\n[ETAPE 1] Generation du contenu de base FR...")
        start = time.time()
        base_content_fr = generate_cv_content(
            input_data={"raw_text": original_text},
            domain="finance",
            language="fr",
            enrichment_mode=False,
        )
        print(f"Complete en {time.time() - start:.1f}s")

        # ETAPE 2: Calcul PFR initial
        print("\n[ETAPE 2] Calcul du PFR initial...")
        pdf_bytes = layout_engine.generate_pdf_from_data(base_content_fr, trim=False)
        metrics = density_calc.calculate_pfr(pdf_bytes)

        print(f"PFR INITIAL: {metrics.fill_percentage}%")
        print(f"Pages: {metrics.page_count}")
        print(f"Caracteres: {metrics.char_count}")

        # ETAPE 3: Check seuil
        print(f"\n[ETAPE 3] Verification des seuils...")
        print(f"PFR {metrics.fill_percentage}% vs seuils:")
        print(f"  - BLOCK < 70%: {'OUI - BLOQUE' if metrics.fill_percentage < 70 else 'NON'}")
        print(f"  - ENRICHMENT 70-90%: {'OUI - ENRICHIR' if 70 <= metrics.fill_percentage < 90 else 'NON'}")
        print(f"  - TARGET 90-97%: {'OUI - ACCEPTE' if 90 <= metrics.fill_percentage <= 97 else 'NON'}")
        print(f"  - TRIM > 97%: {'OUI - TRIMMER' if metrics.fill_percentage > 97 else 'NON'}")

        if metrics.fill_percentage < 70:
            print("\n>>> GENERATION BLOQUEE - PFR trop faible <<<")
            print("Tentative d'enrichissement manuel pour analyse...")

            # Essayer enrichissement quand meme
            print("\n[TEST] Enrichissement force...")
            enriched_content = enricher.aggressive_enrich_content(
                content=base_content_fr,
                current_metrics=metrics,
                domain="finance",
                language="fr",
                original_text=original_text,
            )

            pdf_enriched = layout_engine.generate_pdf_from_data(enriched_content, trim=False)
            metrics_enriched = density_calc.calculate_pfr(pdf_enriched)

            print(f"PFR APRES ENRICHISSEMENT: {metrics_enriched.fill_percentage}%")
            print(f"Pages: {metrics_enriched.page_count}")
            print(f"Gain: +{metrics_enriched.fill_percentage - metrics.fill_percentage:.1f}%")

            # Sauvegarder quand meme pour analyse
            with open(os.path.join(output_dir, "test_MARLET_base_fr.pdf"), "wb") as f:
                f.write(pdf_bytes)
            with open(os.path.join(output_dir, "test_MARLET_enriched_fr.pdf"), "wb") as f:
                f.write(pdf_enriched)

            print(f"\nFichiers sauvegardes pour analyse:")
            print(f"  - Output/test_MARLET_base_fr.pdf (PFR: {metrics.fill_percentage}%)")
            print(f"  - Output/test_MARLET_enriched_fr.pdf (PFR: {metrics_enriched.fill_percentage}%)")

            return

        generator = CVGenerator()

        # PHASE 1: FR only (fast)
        print("\n[PHASE 1] Generation FR complete...")
        import time
        phase1_start = time.time()

        phase1_results = generator._generate_languages(
            input_data={"raw_text": original_text},
            domain="finance",
            is_enhance=True,
            original_text=original_text,
            languages=["fr"]
        )

        phase1_time = time.time() - phase1_start

        result_fr = phase1_results["fr"]
        output_pdf_fr = os.path.join(output_dir, "output_MARLET_enriched_fr.pdf")
        output_docx_fr = os.path.join(output_dir, "output_MARLET_enriched_fr.docx")

        print(f"\n[FR] Complété en {phase1_time:.1f}s")
        print(f"PFR: {result_fr.fill_percentage}%")
        print(f"Pages: {result_fr.page_count}")
        print(f"Caractères: {result_fr.char_count}")

        if result_fr.warnings:
            print("\nAvertissements:")
            for warning in result_fr.warnings:
                print(f"  - {warning}")

        with open(output_pdf_fr, "wb") as f:
            f.write(result_fr.pdf_bytes)

        with open(output_docx_fr, "wb") as f:
            f.write(result_fr.docx_bytes)

        print(f"\nFichiers sauvegardés:")
        print(f"  - {output_pdf_fr}")
        print(f"  - {output_docx_fr}")

        # PHASE 2: EN (deferred)
        print("\n[PHASE 2] Génération EN...")
        phase2_start = time.time()

        phase2_results = generator._generate_languages(
            input_data={"raw_text": original_text},
            domain="finance",
            is_enhance=True,
            original_text=original_text,
            languages=["en"]
        )

        phase2_time = time.time() - phase2_start

        result_en = phase2_results["en"]
        output_pdf_en = os.path.join(output_dir, "output_MARLET_enriched_en.pdf")
        output_docx_en = os.path.join(output_dir, "output_MARLET_enriched_en.docx")

        print(f"\n[EN] Complété en {phase2_time:.1f}s")
        print(f"PFR: {result_en.fill_percentage}%")
        print(f"Pages: {result_en.page_count}")
        print(f"Caractères: {result_en.char_count}")

        if result_en.warnings:
            print("\nAvertissements:")
            for warning in result_en.warnings:
                print(f"  - {warning}")

        with open(output_pdf_en, "wb") as f:
            f.write(result_en.pdf_bytes)

        with open(output_docx_en, "wb") as f:
            f.write(result_en.docx_bytes)

        print(f"\nFichiers sauvegardés:")
        print(f"  - {output_pdf_en}")
        print(f"  - {output_docx_en}")

        print(f"\n{'='*60}")
        print(f"RÉSUMÉ - Temps total: {phase1_time + phase2_time:.1f}s")
        print(f"Phase 1 (FR): {phase1_time:.1f}s - PFR: {result_fr.fill_percentage}%")
        print(f"Phase 2 (EN): {phase2_time:.1f}s - PFR: {result_en.fill_percentage}%")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\nERREUR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
