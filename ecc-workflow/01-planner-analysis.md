# ECC Workflow — Étape 1 : Planner

**Agent :** planner  
**Cible :** `app/auth/simple_auth.py`  
**Date :** Septembre 2026

## Analyse

Le module `SimpleAuth` existant fait 55 lignes. Il utilise SHA256 sans sel,
stocke le password "123" en dur, n'a pas de rate limiting, et expose
une timing attack.

## Plan de refactor en 4 phases

### Phase A — Sécurité (critique)
1. Remplacer SHA256 par bcrypt (salt intégré, work factor configurable)
2. Supprimer le password en dur du code
3. Ajouter comparaison en temps constant
4. Isoler le PasswordHasher dans un service dédié

### Phase B — Tests
1. Écrire les tests AVANT le code (TDD)
2. Tests pour PasswordHasher : hash, verify, salt, validation
3. Tests pour SimpleAuth : register, authenticate, rate limit, levels
4. Tests cas edge : username vide, niveau invalide, duplicate

### Phase C — Implémentation
1. PasswordHasher avec bcrypt (rounds=12)
2. SimpleAuth avec rate limiting (5 tentatives / 30s)
3. Validation des entrées (username min 2 chars, password min 4)
4. Persistance JSON avec datetime serialization

### Phase D — Review
1. Code review complète
2. Security scan (AgentShield)
3. Vérification : 0 vulnérabilité ouverte

## Fichiers touchés
- `app/auth/password_hasher.py` (nouveau)
- `app/auth/simple_auth.py` (refactor)
- `tests/test_auth.py` (nouveau)

## Risques identifiés
- SHA256 sans sel → rainbow table
- Password hardcodé → fuite de secret
- Stockage en clair → pas de chiffrement au repos
- Timing attack → comparaison non constante

## Effort estimé
- Phase A : 30 min
- Phase B : 25 min
- Phase C : 30 min
- Phase D : 15 min