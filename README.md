# 🚢 Paquebot-ECC

**App web personnelle — construite avec le workflow ECC (Everything Claude Code).**

Ce projet montre concrètement comment les 68 agents et 292 skills d'ECC
transforment une idée en code fonctionnel, sécurisé et testé.

## Le workflow ECC appliqué

Chaque module de ce projet suit le même cycle :

```
Planner → TDD (RED) → Implémentation (GREEN) → Code Review → Security Review → Memory
```

| Étape | Agent | Livrable |
|-------|-------|----------|
| 1 | **Planner** | Analyse, découpage, risques, effort estimé |
| 2 | **TDD Guide** | Tests écrits AVANT le code (RED phase) |
| 3 | *(toi + ECC)* | Implémentation minimale qui fait passer les tests (GREEN) |
| 4 | **Code Reviewer** | Relecture qualité, score, suggestions |
| 5 | **Security Reviewer** | Scan vulnérabilités, AgentShield |
| 6 | **Continuous Learning** | Pattern mémorisé pour les prochaines fois |

## Ce que contient le repo

```
paquebot-ecc/
├── app/
│   ├── auth/           ← Module auth (refactoré par ECC)
│   │   ├── password_hasher.py  ← bcrypt + salt + work factor
│   │   └── simple_auth.py      ← Rate limiting + validation
│   └── api/
│       └── main.py     ← API REST FastAPI + page web
├── tests/
│   └── test_auth.py    ← 16 tests TDD
├── ecc-workflow/       ← Traces complètes du workflow ECC
│   ├── 01-planner-analysis.md
│   └── 02-tdd-tests.md
└── docs/               ← Vision et roadmap (à venir)
```

## Démarrer

```bash
cd ~/dev/paquebot-ecc
pip install -r requirements.txt
python -m app.api.main
```

Puis ouvrir **http://localhost:8080** — accessible depuis le téléphone
et les ordis sur le réseau local si le serveur écoute sur `0.0.0.0`.

## Le contrat ECC

Toi : *"Je veux un module d'authentification simple"*

ECC :
- Planifie le travail en phases
- Écrit les tests d'abord
- Implémente avec bcrypt + rate limiting + validation
- Review le code (qualité + sécurité)
- Mémorise le pattern pour la prochaine fois

Tu restes le capitaine. ECC est la salle des machines.

## Roadmap

1. ✅ **Module auth** — fonctionnel, testé, sécurisé
2. 🔜 **Interface web** — dashboard, profil, logs
3. 🔜 **Multi-utilisateurs** — gestion des comptes, niveaux
4. 🔜 **Agents ECC** — intégration des 68 agents dans l'app
5. 🔜 **Réseau IA local** — sync entre machines

---

*Construit avec l'ECC (Everything Claude Code) — affaan-m/ECC — 257k ★*