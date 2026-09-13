"""PasswordHasher — service de hachage sécurisé (SRP).

Conçu par l'agent TDD-Guide du workflow ECC.
Utilise bcrypt avec salt intégré, work factor configurable.
Comparaison en temps constant intégrée (bcrypt gère ça).
"""

import bcrypt


class PasswordHasher:
    """Hash et vérifie les mots de passe avec bcrypt.

    Attributes:
        rounds: Work factor bcrypt (10-16). Plus = plus lent mais plus sûr.
    """

    MIN_ROUNDS = 10
    MAX_ROUNDS = 16
    MIN_PASSWORD_LENGTH = 4

    def __init__(self, rounds: int = 12):
        if not self.MIN_ROUNDS <= rounds <= self.MAX_ROUNDS:
            raise ValueError(
                f"bcrypt rounds must be between {self.MIN_ROUNDS} and {self.MAX_ROUNDS}"
            )
        self.rounds = rounds

    def hash(self, password: str) -> str:
        """Retourne un hash bcrypt avec salt intégré."""
        self._validate_password(password)
        salt = bcrypt.gensalt(self.rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, password: str, stored_hash: str) -> bool:
        """Vérifie en temps constant."""
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))

    def _validate_password(self, password: str) -> None:
        if not password or len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
            )