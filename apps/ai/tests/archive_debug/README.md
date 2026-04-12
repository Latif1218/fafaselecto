# Tests Archivés - Debug et Expérimentaux

Ce dossier contient les tests de debug, expérimentaux et obsolètes qui ont été utilisés pendant le développement.

**Ces tests ne sont PAS exécutés en production.**

## Catégories

### Tests de debug ponctuel
Fichiers créés pour debugger un problème spécifique lors d'une session:
- `debug_*.py` - Scripts de debug divers
- `test_*_debug.py` - Tests de debug spécifiques
- `test_*_solo.py` - Tests isolés sur un seul CV

### Tests expérimentaux
Fichiers créés pour tester des approches alternatives:
- `test_elite_*.py` - Tests d'approches "elite" non retenues
- `analyze_*.py` - Scripts d'analyse exploratoire
- `test_compare_*.py` - Comparaisons de versions

### Tests de session spécifique
Fichiers créés pour une session de développement particulière:
- `test_2026_03_21_*.py` - Tests session 21/03/2026
- `test_antoine_solo.py` - Test spécifique Antoine
- `test_*_marjorie.py` - Tests spécifiques Marjorie

## Tests Production (à garder dans tests/)

Les tests suivants DOIVENT rester dans `tests/`:
- `test_v5_calibrated.py` - Tests validation PFR 86-98%
- `test_batch_samples.py` - Tests batch sur samples
- `test_cover_letter.py` - Tests lettres de motivation
- `test_cover_letter_fayed.py` - Tests cover letter sur Fayed

## Restauration

Pour restaurer un test archivé:
```bash
cp archive_debug/test_xxx.py ../test_xxx.py
```
