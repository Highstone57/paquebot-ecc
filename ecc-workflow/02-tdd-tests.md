# ECC Workflow — Étape 2 : TDD Guide

**Agent :** tdd-guide  
**Phase :** RED (tests écrits avant le code)

## Tests écrits

Fichier : `tests/test_auth.py` — 16 tests au total.

### PasswordHasher (7 tests)
- `test_hash_password_verifies_correct` — un hash bcrypt vérifie son propre password
- `test_rejects_wrong_password` — un hash rejette un mauvais password
- `test_same_password_produces_different_hashes` — bcrypt utilise un sel unique
- `test_validates_min_length` — password trop court → erreur
- `test_rejects_empty_password` — password vide → erreur
- `test_validates_rounds_range` — rounds hors limites → erreur
- `test_accepts_boundary_rounds` — rounds aux limites acceptés

### SimpleAuth (9 tests)
- `test_register_and_authenticate` — inscription puis connexion OK
- `test_authenticate_wrong_password` — mauvais mot de passe → échec
- `test_authenticate_unknown_user` — utilisateur inconnu → échec
- `test_security_level_default_public` — inconnu → niveau "public"
- `test_set_security_level_after_register` — changement de niveau
- `test_register_duplicate_raises` — double inscription → erreur
- `test_invalid_security_level_raises` — niveau invalide → erreur
- `test_rate_limiting_blocks_after_5_attempts` — rate limit après 5 tentatives
- `test_rate_limit_allows_after_cooldown` — rate limit reset après fenêtre

## Résultat
- 16 tests écrits
- 0 passent (RED) — le code refactoré n'existe pas encore
- C'est normal : RED phase du TDD