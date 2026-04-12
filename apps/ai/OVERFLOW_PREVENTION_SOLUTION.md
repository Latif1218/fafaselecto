# 🛡️ SOLUTION ANTI-DÉBORDEMENT 2 PAGES (01/04/2026)

## Problème identifié

Dans le batch V6, **2/7 CVs** ont débordé sur 2 pages:
- Gautier ROUAS (débordement EN - bullets 148-160 chars moyenne)
- Manon BOUTIN (débordement FR - bullets 167-193 chars moyenne)

**Cause racine:**
- Le LLM (Claude Sonnet 4.5) génère parfois des bullets très longs (150-193 chars)
- Le template CSS accepte max 140 chars/bullet (2 lignes)
- L'ancien code `_enforce_bullet_limit()` tronquait à 135 chars APRÈS génération (trop tard)
- Résultat: Truncation brutale qui casse les phrases → débordement si trop de bullets

## Solution implémentée (01/04/2026)

### Architecture en 3 niveaux

**NIVEAU 1: Prévention initiale** (`app/generator.py` ligne 441-476)
- Détection overflow IMMÉDIATEMENT après génération PDF initiale
- Si `page_count > 1`:
  1. Apply `_enforce_one_page_hard_limit()` (bullets 130 chars, 3 max)
  2. Re-render PDF
  3. Si ENCORE overflow → Apply `_ultra_aggressive_trim()` (bullets 110 chars, 2 max)
  4. Re-render PDF

**NIVEAU 2: Protection finale** (`app/generator.py` ligne 683-705)
- Détection overflow AVANT validation finale
- Même logique que Niveau 1
- Catch les overflows causés par enrichissement/trimming

**NIVEAU 3: Validation stricte** (`app/generator.py` ligne 712-715)
- Si ENCORE `page_count > 1` après Niveau 1 + 2
- → Raise ValueError (échec critique)
- Normalement IMPOSSIBLE si Niveau 1/2 fonctionnent

### Fonctions de protection

#### `_enforce_one_page_hard_limit()` (ligne 863-906)

**Objectif:** Réduire contenu pour garantir 1 page SANS trop sacrifier

**Actions:**
1. Bullets max **130 chars** (2 lignes garanties avec marge)
2. Max **3 bullets** par expérience (au lieu de 4-5)
3. Coursework max **5 items** (réduit si > 5)
4. Activities max **3 items** (réduit si > 3)
5. IT skills max **6 items** (réduit si > 6)

**PFR attendu après:** 80-92% (acceptable)

#### `_ultra_aggressive_trim()` (ligne 908-953)

**Objectif:** DERNIER RECOURS - Garantir 1 page à TOUT PRIX

**Actions:**
1. Bullets max **110 chars** (ultra compact, ~1.5 lignes)
2. Max **2 bullets** par expérience (brutal cut)
3. **Supprime coursework complètement** (mesure désespérée)
4. **Supprime activities complètement** (mesure désespérée)
5. IT skills max **4 items** (minimal)

**PFR attendu après:** 70-85% (sous-optimal mais acceptable)

**Warning:** Cette fonction sacrifie beaucoup de contenu. Elle ne devrait **jamais** être appelée si Niveau 1 fonctionne.

### Ordre d'exécution

```
1. Generate base content with LLM
   ↓
2. Apply `_enforce_bullet_limit()` (135 chars max) - PRÉVENTIF
   ↓
3. Generate PDF
   ↓
4. [NIVEAU 1] If overflow → `_enforce_one_page_hard_limit()` → re-render
   ↓
5. [NIVEAU 1] If STILL overflow → `_ultra_aggressive_trim()` → re-render
   ↓
6. Continue with enrichment/trimming logic (existing code)
   ↓
7. [NIVEAU 2] If overflow → `_enforce_one_page_hard_limit()` → re-render
   ↓
8. [NIVEAU 2] If STILL overflow → `_ultra_aggressive_trim()` → re-render
   ↓
9. [NIVEAU 3] If STILL overflow → Raise ValueError (normalement impossible)
```

## Différences avec ancien code

### AVANT (01/04/2026 00h00):
```python
# Ligne 436 - PRÉVENTIF mais trop tardif
content = self._enforce_bullet_limit(content)  # 135 chars max

# Ligne 441 - Génération PDF
pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
metrics = self.density_calc.calculate_pfr(pdf_bytes)

# Ligne 690 - VALIDATION (TROP TARD, déjà 2 pages)
if metrics.page_count != 1:
    raise ValueError("CV must be exactly one page.")
```

**Problème:** Si le PDF généré fait 2 pages, on raise immédiatement sans essayer de corriger.

### APRÈS (01/04/2026 02h00):
```python
# Ligne 436 - PRÉVENTIF (même qu'avant)
content = self._enforce_bullet_limit(content)  # 135 chars max

# Ligne 441 - Génération PDF
pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
metrics = self.density_calc.calculate_pfr(pdf_bytes)

# Ligne 451 - DÉTECTION OVERFLOW IMMÉDIATE
if metrics.page_count > 1:
    # CORRECTION 1: Hard limit
    content = self._enforce_one_page_hard_limit(content, lang)
    pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
    metrics = self.density_calc.calculate_pfr(pdf_bytes)

    # CORRECTION 2: Ultra aggressive (si toujours overflow)
    if metrics.page_count > 1:
        content = self._ultra_aggressive_trim(content)
        pdf_bytes = generate_pdf_playwright(content, trim=False, language=lang)
        metrics = self.density_calc.calculate_pfr(pdf_bytes)

# ... (enrichissement/trimming)

# Ligne 683 - DÉTECTION OVERFLOW FINALE (avant validation)
if metrics.page_count > 1:
    # Même logique: hard limit → ultra trim

# Ligne 712 - VALIDATION (dernier recours)
if metrics.page_count != 1:
    raise ValueError("CV must be exactly one page.")
```

**Avantage:** Détection + correction AVANT la validation finale.

## Métriques attendues

### CVs normaux (bullets 120-140 chars):
- **Niveau 1** jamais appelé
- PFR: 86-98% (optimal)

### CVs avec bullets longs (140-170 chars):
- **Niveau 1** appelé
- `_enforce_one_page_hard_limit()` suffit
- PFR: 80-92% (acceptable)

### CVs avec bullets très longs (170-200 chars):
- **Niveau 1** + `_ultra_aggressive_trim()` appelé
- PFR: 70-85% (sous-optimal)
- **Coursework et activities supprimés** (sacrifice nécessaire)

### Taux de succès attendu:
- **100% garantie 1 page** (ZÉRO débordement)
- **~10-15% nécessitent ultra trim** (sacrifice contenu)
- **Trade-off accepté:** Mieux vaut 1 page à 75% PFR que 2 pages rejetées

## Tests de validation

**Test simple:** `tests/test_overflow_simple.py`
- Test avec Gautier ROUAS (débordait EN)
- Génère FR + EN
- Vérifie: `page_count == 1` pour les deux

**Test complet:** `tests/test_overflow_prevention.py`
- Test avec Gautier ROUAS + Manon BOUTIN
- Génère FR + EN pour chaque
- Vérifie: `page_count == 1` + `PFR >= 70%`

## Code modifié

**Fichiers:**
- `app/generator.py` (3 modifications)
  - Ligne 441-476: Niveau 1 protection
  - Ligne 683-705: Niveau 2 protection
  - Ligne 908-953: `_ultra_aggressive_trim()` (NEW)

**Lignes ajoutées:** ~90 lignes
**Complexité:** O(1) (max 2 re-renders par langue)

## Impact sur performance

**Cas normal (pas d'overflow):**
- Temps: **+0s** (pas de re-render)
- Coût: **+$0** (pas d'appel LLM)

**Cas overflow niveau 1:**
- Temps: **+2-3s** (1 re-render)
- Coût: **+$0** (pas d'appel LLM)

**Cas overflow niveau 2 (ultra trim):**
- Temps: **+4-6s** (2 re-renders)
- Coût: **+$0** (pas d'appel LLM)

**Impact global:** Négligeable (<5% sur temps total)

## Logging

**Nouveau tags:**
- `[EMERGENCY]` - Overflow détecté, correction en cours
- `[ULTRA TRIM]` - Ultra aggressive trim appliqué (sacrifice contenu)

**Exemples:**
```
2026-04-01 02:00:00 - app.generator - WARNING - OVERFLOW DETECTED: 2 pages - applying emergency reduction [EMERGENCY]
2026-04-01 02:00:02 - app.generator - INFO - After emergency reduction: 1 page(s), 84.2% PFR [EMERGENCY]
2026-04-01 02:00:04 - app.generator - WARNING - ULTRA AGGRESSIVE TRIM applied - content severely reduced [EMERGENCY]
```

## Prochaines étapes

- [ ] Valider avec batch complet (7 CVs SAMPLES)
- [ ] Mesurer taux d'utilisation ultra trim (<15% attendu)
- [ ] Ajuster seuils si nécessaire (actuellement 130/110 chars)
- [ ] Documenter dans CLAUDE.md

---

**Session:** 01/04/2026 02h00-03h00
**Version:** 6.1 (Overflow prevention system)
**Statut:** ✅ Implémenté, en test
