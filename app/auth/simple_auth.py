"""SimpleAuth — authentification avec hash sécurisé, rate limiting, validation.

Workflow ECC appliqué :
  1. Planner → découpage en phases (sécurité → tests → implémentation → review)
  2. TDD Guide → tests écrits avant le code (RED phase)
  3. Implémentation → GREEN (ce fichier)
  4. Code Reviewer → revu et approuvé
  5. Security Reviewer → 0 vulnérabilité ouverte
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .password_hasher import PasswordHasher


@dataclass
class _AttemptWindow:
    """Suivi des tentatives récentes pour le rate limiting."""
    attempts: list[float] = field(default_factory=list)

    def record(self) -> None:
        self.attempts.append(time.time())

    def prune(self, window_seconds: int = 30) -> None:
        cutoff = time.time() - window_seconds
        self.attempts = [t for t in self.attempts if t > cutoff]

    def exceeded(self, max_attempts: int = 5) -> bool:
        self.prune()
        return len(self.attempts) >= max_attempts


class AuthError(Exception):
    """Erreur d'authentification métier."""
    pass


class SimpleAuth:
    """Système d'authentification avec multi-niveaux de sécurité.

    Usage:
        auth = SimpleAuth("config/users.json")
        auth.register_user("vianey", "motdepasse", "private")
        result = auth.authenticate("vianey", "motdepasse")
    """

    VALID_LEVELS = frozenset({"private", "shared", "public"})
    RATE_LIMIT_ATTEMPTS = 5
    RATE_LIMIT_WINDOW = 30  # secondes

    def __init__(
        self,
        config_file: str = "config/auth.json",
        hasher: Optional[PasswordHasher] = None,
    ):
        self.config_file = config_file
        self.hasher = hasher or PasswordHasher()
        self._users: dict = self._load()
        self._rate_limits: dict[str, _AttemptWindow] = {}

    # ── Registration ──────────────────────────────────────────────

    def register_user(self, username: str, password: str, security_level: str = "public") -> None:
        """Crée un nouvel utilisateur."""
        self._validate_username(username)
        self._validate_level(security_level)
        if username in self._users:
            raise AuthError(f"User '{username}' already exists")

        self._users[username] = {
            "password_hash": self.hasher.hash(password),
            "security_level": security_level,
            "created_at": datetime.now().isoformat(),
        }
        self._save()

    # ── Authentication ────────────────────────────────────────────

    def authenticate(self, username: str, password: str) -> dict:
        """Authentifie un utilisateur. Retourne un dict {success, username, security_level}."""
        # Rate limit check
        window = self._rate_limits.setdefault(username, _AttemptWindow())
        window.record()
        if window.exceeded(self.RATE_LIMIT_ATTEMPTS):
            return {
                "success": False,
                "error": "Trop de tentatives. Réessayez dans 30 secondes.",
            }

        # User lookup
        user = self._users.get(username)
        if user is None:
            # Dummy verify en temps constant pour ne pas fuiter l'existence
            self.hasher.verify("dummy", self._dummy_hash())
            return {"success": False, "error": "Identifiants invalides"}

        if not self.hasher.verify(password, user["password_hash"]):
            return {"success": False, "error": "Identifiants invalides"}

        return {
            "success": True,
            "username": username,
            "security_level": user["security_level"],
        }

    # ── Security Level ────────────────────────────────────────────

    def get_security_level(self, username: str) -> str:
        """Retourne le niveau de sécurité d'un utilisateur."""
        return self._users.get(username, {}).get("security_level", "public")

    def set_security_level(self, username: str, level: str) -> None:
        """Change le niveau de sécurité d'un utilisateur existant."""
        if username not in self._users:
            raise AuthError(f"User '{username}' not found")
        self._validate_level(level)
        self._users[username]["security_level"] = level
        self._save()

    # ── Persistence ───────────────────────────────────────────────

    def _load(self) -> dict:
        if not os.path.exists(self.config_file):
            return {}
        with open(self.config_file, "r") as f:
            return json.load(f)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self._users, f, indent=2, default=str)

    # ── Validation ────────────────────────────────────────────────

    def _validate_username(self, username: str) -> None:
        if not username or len(username) < 2:
            raise AuthError("Username must be at least 2 characters")

    def _validate_level(self, level: str) -> None:
        if level not in self.VALID_LEVELS:
            raise AuthError(f"Level must be one of: {', '.join(self.VALID_LEVELS)}")

    # Hash bcrypt valide pour comparaison factice (généré une fois)
    _DUMMY_HASH = "$2b$12$Lf4rxMHQ1Z4EsN9X8XdtjeheVXiHURlaT3vQwugs7V.BkQ6A05Etu"

    @staticmethod
    def _dummy_hash() -> str:
        """Hash factice valide pour comparaison en temps constant."""
        return SimpleAuth._DUMMY_HASH