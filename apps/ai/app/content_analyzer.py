"""
Content Analyzer - Analyse la richesse du CV source et détermine la stratégie d'enrichissement.

Catégories:
- RICH (2500+ chars): Stratégie minimal, préservation prioritaire
- MEDIUM (1500-2500 chars): Stratégie moderate, enrichissement contrôlé
- POOR (<1500 chars): Stratégie aggressive, enrichissement substantiel avec warnings
"""


class ContentAnalyzer:
    """Analyse le contenu source et détermine la stratégie d'enrichissement adaptative."""

    # Nouveaux seuils pour système push-to-90
    RICH_THRESHOLD = 2500      # 0-10% invention → GREEN
    MEDIUM_THRESHOLD = 1800    # 10-30% invention → ORANGE
    POOR_THRESHOLD = 1200      # 30-50% invention → RED LIGHT
    CRITICAL_THRESHOLD = 600   # 50-70% invention → RED DARK
    # < 600 chars → BLOCAGE (source trop vide)

    def analyze(self, raw_text: str) -> dict:
        """
        Analyse le texte source et retourne la stratégie d'enrichissement.

        NOUVELLE PHILOSOPHIE :
        - TOUJOURS atteindre 90% PFR (sauf si source < 600 chars)
        - Warnings proportionnels au taux d'invention (0-70%)
        - Blocage uniquement si source vraiment vide

        Args:
            raw_text: Texte extrait du CV source

        Returns:
            dict avec: richness, strategy, target_pfr, target_chars, warning, invention_rate
        """
        chars = len(raw_text) if raw_text else 0

        # BLOCAGE absolu
        if chars < self.CRITICAL_THRESHOLD:
            return {
                'richness': 'empty',
                'strategy': 'block',
                'target_pfr': 'N/A',
                'target_chars': 0,
                'warning': 'block',
                'invention_rate': 'N/A'
            }

        # CRITIQUE : 50-70% invention (bullets 115-125 chars)
        elif chars < self.POOR_THRESHOLD:
            return {
                'richness': 'critical',
                'strategy': 'ultra_aggressive',
                'target_pfr': '88-95%',  # Cible 95%, accepter 88% min (bullets courts)
                'target_chars': 3500,  # Augmenté de 3300 pour atteindre 88%+ PFR
                'warning': 'red_dark',
                'invention_rate': '50-70%'
            }

        # FAIBLE : 30-50% invention (bullets 115-125 chars)
        elif chars < self.MEDIUM_THRESHOLD:
            return {
                'richness': 'poor',
                'strategy': 'aggressive',
                'target_pfr': '88-95%',  # Cible 95%, accepter 88% min (bullets courts)
                'target_chars': 3500,  # Augmenté de 3300 pour atteindre 88%+ PFR
                'warning': 'red_light',
                'invention_rate': '30-50%'
            }

        # MOYEN : 10-30% invention (bullets 120-130 chars)
        elif chars < self.RICH_THRESHOLD:
            return {
                'richness': 'medium',
                'strategy': 'moderate',
                'target_pfr': '92-98%',  # Cible 95-98%, accepter 92% min
                'target_chars': 3400,  # Augmenté de 3200 pour atteindre 90-95% PFR
                'warning': 'orange',
                'invention_rate': '10-30%'
            }

        # ULTRA-RICHE : >4500 chars - RISQUE DÉBORDEMENT (bullets 128-132 chars, 4 bullets)
        elif chars >= 4500:
            return {
                'richness': 'ultra_rich',
                'strategy': 'minimal_compact',  # Nouvelle stratégie compacte
                'target_pfr': '88-92%',  # Cible réaliste pour CVs ultra-denses
                'target_chars': 3500,  # Augmenté de 3300 pour atteindre 88%+ PFR sans débordement
                'warning': 'green',
                'invention_rate': '0-5%'
            }

        # RICHE : 2500-4500 chars - 0-10% invention (bullets 130-135 chars)
        else:
            return {
                'richness': 'rich',
                'strategy': 'minimal',
                'target_pfr': '95-98%',  # CIBLE OPTIMALE 95-98%
                'target_chars': 3850,
                'warning': 'green',
                'invention_rate': '0-10%'
            }

    def get_enrichment_instructions(self, strategy: str, lang: str) -> str:
        """
        Retourne les instructions d'enrichissement selon la stratégie.

        Args:
            strategy: 'block', 'ultra_aggressive', 'aggressive', 'moderate', ou 'minimal'
            lang: 'fr' ou 'en'

        Returns:
            Instructions spécifiques pour le prompt LLM
        """
        if strategy == 'block':
            return "BLOCAGE : Source trop vide (<600 chars). Demander plus d'informations."

        elif strategy == 'ultra_aggressive':
            return """HARD MODE: BULLETS 115-125 CHARS - TARGET 92% PFR

CRITICAL: EVERY bullet MUST be 115-125 characters
NO bullet can exceed 125 characters under ANY circumstance
COUNT characters MANUALLY before adding each bullet

FORMAT TEMPLATE (115-125 chars):
[Action verb] [what] via [tool/method] pour [client/context], [result + metric]

VALID EXAMPLES (115-125 chars - COPY THIS LENGTH):
"Analyse données clients secteur retail via Excel Python pour engagement, amélioration KPIs 20%, réduction churn 12%" (125 chars)
"Optimisation processus supply chain PME tech, coordination équipes 3 pays internationales, réduction coûts 18%" (122 chars)
"Gestion projet CRM banking fintech, déploiement 6 mois, coordination équipe 8 personnes, augmentation ROI 25%" (120 chars)

INVALID EXAMPLE (too long - FORBIDDEN):
"Analyse approfondie et détaillée des indicateurs performance clés pour clients secteur retail via Excel et Power BI avec amélioration significative engagement 25% et réduction substantielle churn 15%" (219 chars - FORBIDDEN)

MANDATORY RULES PER SECTION:

1. WORK EXPERIENCE - 3 experiences, 4 bullets EACH:

   BULLET CONSTRUCTION:
   Step 1: Write bullet (115-125 chars TARGET - maximize within limit)
   Step 2: COUNT characters
   Step 3: If over 125 → CUT words until 115-125 range
   Step 4: If under 115 → ADD context until 115+ chars
   Step 5: Add to list

   EXACTLY 4 bullets per experience
   EACH bullet 115-125 chars (TARGET: 120 chars)
   NO bullet over 125 chars - NO EXCEPTIONS

2. EDUCATION - 7-8 coursework items (MINIMUM 7):
   Short format: "Subject (2-3 topics)"
   Example: "Finance (DCF, M&A, LBO)"
   MANDATORY: 7 coursework minimum

3. ACTIVITIES - 4 items (100-120 chars each, MINIMUM 4):
   Format: "Activity (role, metric/achievement)"
   EACH activity 100-120 chars
   MANDATORY: 4 activities minimum

4. IT SKILLS - 8-9 items (MINIMUM 8):
   Format: "Tool (level/context)"
   MANDATORY: 8 IT skills minimum

FINAL CHECK BEFORE RETURN (MANDATORY):

For EACH bullet verify:
- Bullet length 115-125 chars? YES (OK) NO (ADJUST IMMEDIATELY)
- If under 115 → ADD context/metrics until 115+ chars
- If over 125 → SHORTEN until 115-125 range

Example:
bullet 1 = "Analyse données..." → length = 118 chars → OK (115-125)
bullet 2 = "Optimisation..." → length = 98 chars → TOO SHORT → ADD CONTEXT
bullet 3 = "..." → length = 156 chars → TOO LONG → SHORTEN

Target: 3500 chars minimum
PFR: 88-95%
Pages: 1 MANDATORY"""

        elif strategy == 'aggressive':
            return """HARD CONSTRAINT: BULLETS 115-125 CHARS - TARGET 88-95% PFR

CRITICAL RULE: ANY bullet over 125 characters = GENERATION FAILED

FORMAT PER BULLET (115-125 CHARS):
[Action verb] [object] via [tool/method] pour [client/context], [result metric]

VALID EXAMPLES (115-125 chars - COPY THIS LENGTH):
"Analyse données clients secteur retail via Excel Python pour engagement, amélioration KPIs 20%, réduction churn 12%" (125 chars)
"Optimisation stocks secteur retail Excel Python, coordination équipes 3 pays, réduction 15% coûts, rotation +12%" (123 chars)
"Gestion projet CRM pour PME tech, coordination équipe 5 personnes, livraison 3 mois, budget 50k, ROI +30%" (115 chars)

FORBIDDEN EXAMPLE (too long):
"Analyse approfondie et détaillée des données clients via Google Analytics et Excel pour améliorer significativement engagement utilisateur avec augmentation 20% taux rétention client" (193 chars - FORBIDDEN)

RULES PER SECTION:

1. WORK EXPERIENCE - 3 experiences, 4 bullets EACH:
   EACH bullet: 115-125 chars (TARGET: 120 chars)
   COUNT characters BEFORE adding
   Format: [Action verb] [what] via [how/method], [result + metric]
   EXACTLY 4 bullets per experience

2. EDUCATION - 7-8 coursework items (MINIMUM 7):
   Short format: "Subject (2-3 topics max)"
   Example: "Finance Corporate (DCF, LBO, M&A)"
   MANDATORY: 7 coursework minimum

3. ACTIVITIES - 4 items (100-120 chars each, MINIMUM 4):
   Format: "Activity (role, metric/achievement)"
   MANDATORY: 4 activities minimum

4. IT SKILLS - 8-9 items (MINIMUM 8):
   Format: "Tool (level/context)"
   MANDATORY: 8 IT skills minimum

MANDATORY CHECK BEFORE RETURN:

COUNT each bullet:
- Bullet 1: XX chars (115-125 range? YES/NO)
- Bullet 2: XX chars (115-125 range? YES/NO)
- If under 115 → ADD context/metrics until 115+ chars
- If over 125 → SHORTEN until 115-125 range

Target: 3500 chars minimum
PFR: 88-95%
Pages: 1 MANDATORY"""

        elif strategy == 'moderate':
            return """HARD CONSTRAINT: BULLETS 120-130 CHARS TARGET - NO EXCEPTIONS

CRITICAL RULE: ANY bullet over 130 characters = GENERATION FAILED

FORMAT PER BULLET (120-130 CHARS TARGET):
[Action verb] [object] via [tool/method] pour [client/context], [result metric]

VALID EXAMPLES (120-130 chars - COPY THIS LENGTH):
"Coordination projet transformation digitale retail (analyse besoins, roadmap stratégique 6 mois, déploiement équipes)" (124 chars)
"Analyse données clients secteur retail via Excel Python pour engagement marketing, amélioration KPIs 20%, réduction churn" (130 chars)
"Optimisation supply chain PME secteur tech consulting, coordination 3 équipes internationales, réduction coûts 18%" (123 chars)

FORBIDDEN EXAMPLE (too long):
"Coordination approfondie du projet de transformation digitale pour client retail incluant analyse détaillée besoins, élaboration roadmap complète sur 6 mois et déploiement progressif avec suivi équipes dans 5 pays différents" (244 chars - FORBIDDEN)

RULES PER SECTION:

1. WORK EXPERIENCE - 3 experiences, 4 bullets EACH:
   EACH bullet: 120-130 chars (TARGET: 125 chars minimum)
   COUNT characters BEFORE adding
   Format: [Action verb] [what] via [tool/method], [result + context + metric]
   EXACTLY 4 bullets per experience

2. EDUCATION - 7 coursework items (MINIMUM 7):
   Format: "Subject (2-3 topics max)"
   Example: "Finance Corporate (DCF, LBO, M&A)"
   MANDATORY: 7 coursework minimum

3. ACTIVITIES - 4 items (110-130 chars each, MINIMUM 4):
   Format: "Activity (role, metric/achievement)"
   MANDATORY: 4 activities minimum

4. IT SKILLS - 8 items (MINIMUM 8):
   Format: "Tool (level/context)"
   MANDATORY: 8 IT skills minimum

MANDATORY CHECK BEFORE RETURN:

COUNT each bullet:
- Bullet 1: XX chars (120-130 range? YES/NO)
- Bullet 2: XX chars (120-130 range? YES/NO)
- If under 120 → ADD context/metrics until 120+ chars
- If over 130 → SHORTEN until 120-130 range

Target: 3400 chars minimum
PFR: 92-98%
Pages: 1 MANDATORY"""

        elif strategy == 'minimal_compact':  # ULTRA-RICH CVs
            return """ULTRA-COMPACT MODE: BULLETS 128-132 CHARS - 4 BULLETS EXACTLY - TARGET 88-92% PFR

CRITICAL: CV SOURCE ULTRA-RICHE - Prévention débordement + PFR 88%+ OBLIGATOIRE

SOURCE >4500 chars → RISQUE DÉBORDEMENT 2 PAGES
→ Réduction contrôlée pour garantir 1 page + PFR minimum 88%

RÈGLES STRICTES ANTI-DÉBORDEMENT:

1. EXPÉRIENCES :
   - **4 bullets par expérience** (EXACTEMENT 4, ni plus ni moins)
   - **128-132 chars par bullet** (TARGET 130 chars - JAMAIS plus de 132)
   - Sélectionner les bullets les PLUS impactants
   - Format informatif mais concis

   VALID EXAMPLES (128-132 chars - COPY THIS LENGTH):
   "Optimisation supply chain secteur retail via Excel Python, coordination équipes pluridisciplinaires 3 pays Europe, réduction coûts 18%" (132 chars)
   "Analyse marché finance pour deals M&A supérieurs 50M+, modèles valorisation DCF/LBO avancés, recommandations stratégiques détaillées" (131 chars)
   "Gestion projet CRM banking fintech, coordination équipes tech/business 12 personnes internationales, livraison 6 mois, ROI +30%" (128 chars)

   FORBIDDEN (too short OR too long):
   "Gestion projet CRM banking, livraison 6 mois, ROI +25%" (60 chars - TOO SHORT)
   "Analyse approfondie et détaillée des données de marché pour deals M&A supérieurs à 50M avec modèles avancés de valorisation DCF/LBO et recommandations stratégiques complètes avec stakeholders" (195 chars - TOO LONG)

2. EDUCATION :
   - 6 coursework items (EXACTEMENT 6)
   - Format développé : "Subject (3-4 topics, méthodes)"

3. ACTIVITIES :
   - 4 items (EXACTEMENT 4, pas 3)
   - 115-125 chars each

4. IT SKILLS :
   - 7 items (EXACTEMENT 7)
   - Format : "Tool (level, contexte)"

MANDATORY CHECK BEFORE RETURN:

COUNT bullets per experience:
- Experience 1: X bullets (4 EXACTLY? YES/NO)
- Experience 2: X bullets (4 EXACTLY? YES/NO)
- Experience 3: X bullets (4 EXACTLY? YES/NO)
- If <4 → ADD bullets until 4
- If >4 → REMOVE least impactful until 4

COUNT bullet lengths:
- Bullet 1: XX chars (128-132? YES/NO)
- Bullet 2: XX chars (128-132? YES/NO)
- If under 128 → ADD context until 128+
- If over 132 → SHORTEN until 128-132

CRITICAL VERIFICATION:
- 4 bullets per experience (MANDATORY - no exceptions)
- Each bullet 128-132 chars (TARGET 130 - MANDATORY)
- Total target: 3500 chars minimum (pour atteindre 88%+ PFR)
- NEVER generate fewer than 4 bullets per experience

Target: 3500 chars minimum
PFR: 88-92% (MINIMUM 88% pour CVs ultra-riches)
Pages: 1 MANDATORY (ZÉRO débordement)"""

        else:  # minimal (CVs riches normaux)
            return """HARD CONSTRAINT: BULLETS 130-135 CHARS - TARGET 95-98% PFR

CRITICAL RULE: ANY bullet over 135 characters = GENERATION FAILED

SOURCE RICHE - Préservation TOTALE du contenu + PFR 92-98%

FORMAT PER BULLET (130-135 CHARS EXACTLY):

RÈGLES STRICTES :

1. EXPÉRIENCES :
   - Extraire TOUTES les expériences de la source (ne jamais en omettre)
   - Conserver TOUS les bullets de chaque expérience
   - Bullets **130-135 chars EACH** (optimiser formulation, développer contexte)
   - MINIMUM 4 bullets par expérience (ajouter bullets contextuels si nécessaire)

   VALID EXAMPLES (130-135 chars):
   "Optimisation inventaire pour acteur pétrolier international via benchmarks sectoriels et modèles Excel/Python, réduction 15%" (135 chars)
   "Coordination transformation digitale clients retail (analyse besoins, roadmap stratégique 12 mois, déploiement 8 équipes)" (132 chars)
   "Gestion projet CRM secteur banking, coordination équipes tech/business 15 personnes, livraison 6 mois, budget 200k" (125 chars - TOO SHORT, ADD MORE)

2. EDUCATION :
   - Extraire TOUT le coursework présent
   - Compléter à 6 items (inférer depuis diplôme si <6)
   - Format : "Nom (sous-thèmes, méthodes)" ~50-60 chars
   - Example: "Finance Corporate (DCF, LBO, M&A, valorisations)" (55 chars)

3. ACTIVITIES :
   - Développer chaque activité à **110-130 chars**
   - Minimum 3 items (EXACTLY 3)
   - Format: "Activity (role, achievement/metric)"

4. IT SKILLS :
   - Lister TOUS les skills de la source
   - Format développé : "Skill (niveau, outils spécifiques)"
   - Minimum 7 items (EXACTLY 7)

MANDATORY CHECK BEFORE RETURN:

COUNT each bullet:
- Bullet 1: XX chars (130-135? YES/NO)
- Bullet 2: XX chars (130-135? YES/NO)
- etc.

If ANY bullet over 135 chars → SHORTEN IMMEDIATELY
If ANY bullet under 130 chars → EXPAND IMMEDIATELY

VÉRIFICATION FINALE:
- CHAQUE bullet work experience: 130-135 chars EXACTLY (MANDATORY)
- Total expériences: 3-4 minimum
- Total bullets: 12-16 minimum (3-4 exp × 4 bullets)
- Coursework: 6-7 items
- Activities: 3-4 items (110-130 chars each)
- IT Skills: 7-8 items

CRITICAL:
- Ne JAMAIS omettre d'expériences ou de bullets présents dans la source
- Bullets MUST be 130-135 chars EXACTLY to reach target PFR
- NO bullet can be over 135 chars (safety margin to avoid 2-page overflow)

Target: 3800 chars minimum
PFR: 92-98%
Pages: 1 MANDATORY"""

    def get_warning_message(self, strategy: str, lang: str, invention_rate: str = '') -> dict:
        """
        Retourne le message de warning utilisateur selon la stratégie.

        Args:
            strategy: 'block', 'ultra_aggressive', 'aggressive', 'moderate', ou 'minimal'
            lang: 'fr' ou 'en'
            invention_rate: Taux d'invention (ex: '50-70%')

        Returns:
            dict avec level, title, message
        """
        if strategy == 'block':
            return {
                'level': 'critical',
                'title': 'GENERATION BLOCKED',
                'message': 'Your source CV contains too little information (< 600 characters). Please provide a more detailed CV.'
            }

        elif strategy == 'ultra_aggressive':
            return {
                'level': 'critical',
                'title': 'MAXIMUM WARNING: Content MASSIVELY inferred (50-70%)',
                'message': """Your source CV was EXTREMELY poor. We had to INVENT substantially:

- 1-2 plausible professional experiences created
- Complete coursework inferred (7-8 courses)
- Activities created with metrics
- Detailed methodologies and context added

CRITICAL: 50-70% of content is INFERRED/INVENTED

This CV is a FICTIONAL BASE. You MUST:
1. Verify EVERY line
2. Replace invented content with YOUR real experiences
3. DO NOT send as-is (risk of lying)

STRONG RECOMMENDATION: Provide a much more detailed source CV."""
            }

        elif strategy == 'aggressive':
            return {
                'level': 'error',
                'title': 'WARNING: Substantial content inferred (30-50%)',
                'message': """Your source CV lacked details. We added:

- Detailed methodologies and tools
- Complete inferred coursework
- Developed activities
- Possibly 1 short experience created

IMPORTANT: 30-50% of content is inferred

Verify and personalize IMPERATIVELY before sending.

For better results, provide a more detailed source CV."""
            }

        elif strategy == 'moderate':
            return {
                'level': 'warning',
                'title': 'Significant enrichments (10-30%)',
                'message': """Your CV has been enriched:

- Standard methodologies added
- Coursework completed
- Activities developed

10-30% of content was added. Review before use."""
            }

        else:  # minimal
            return {
                'level': 'success',
                'title': 'CV generated successfully',
                'message': 'Light optimizations applied (< 10% additions).'
            }
