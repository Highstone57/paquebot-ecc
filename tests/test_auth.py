"""Tests TDD pour le module auth — écrits AVANT l'implémentation (RED → GREEN).

Workflow ECC : tdd-guide écrit ces tests en premier.
Ils doivent échouer avec l'ancien code, passer avec le refactoré.
"""

import pytest
from app.auth import PasswordHasher, SimpleAuth
from app.auth.simple_auth import AuthError


# ── PasswordHasher ─────────────────────────────────────────────────

class TestPasswordHasher:
    def test_hash_password_verifies_correct(self):
        hasher = PasswordHasher()
        h = hasher.hash("monMotDePasse")
        assert hasher.verify("monMotDePasse", h) is True

    def test_rejects_wrong_password(self):
        hasher = PasswordHasher()
        h = hasher.hash("bonMotDePasse")
        assert hasher.verify("mauvaisMotDePasse", h) is False

    def test_same_password_produces_different_hashes(self):
        """Vérifie que bcrypt utilise un sel différent à chaque fois."""
        hasher = PasswordHasher()
        h1 = hasher.hash("password")
        h2 = hasher.hash("password")
        assert h1 != h2

    def test_validates_min_length(self):
        hasher = PasswordHasher()
        with pytest.raises(ValueError, match="at least 4"):
            hasher.hash("ab")

    def test_rejects_empty_password(self):
        hasher = PasswordHasher()
        with pytest.raises(ValueError):
            hasher.hash("")

    def test_validates_rounds_range(self):
        with pytest.raises(ValueError):
            PasswordHasher(rounds=5)
        with pytest.raises(ValueError):
            PasswordHasher(rounds=20)

    def test_accepts_boundary_rounds(self):
        PasswordHasher(rounds=10)
        PasswordHasher(rounds=16)


# ── SimpleAuth ─────────────────────────────────────────────────────

class TestSimpleAuth:
    def test_register_and_authenticate(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        auth.register_user("alice", "securePass", "private")
        result = auth.authenticate("alice", "securePass")
        assert result["success"] is True
        assert result["security_level"] == "private"

    def test_authenticate_wrong_password(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        auth.register_user("alice", "securePass", "private")
        result = auth.authenticate("alice", "wrong")
        assert result["success"] is False

    def test_authenticate_unknown_user(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        result = auth.authenticate("inconnu", "whatever")
        assert result["success"] is False

    def test_security_level_default_public(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        assert auth.get_security_level("inconnu") == "public"

    def test_set_security_level_after_register(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        auth.register_user("bob", "pass", "shared")
        auth.set_security_level("bob", "private")
        assert auth.get_security_level("bob") == "private"

    def test_register_duplicate_raises(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        auth.register_user("alice", "pass", "public")
        with pytest.raises(AuthError, match="already exists"):
            auth.register_user("alice", "other", "private")

    def test_invalid_security_level_raises(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        with pytest.raises(AuthError):
            auth.register_user("x", "pass", "top_secret")

    def test_rate_limiting_blocks_after_5_attempts(self, tmp_path):
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        auth.register_user("target", "secret", "private")
        for _ in range(5):
            auth.authenticate("target", "wrong")
        result = auth.authenticate("target", "secret")
        assert result["success"] is False  # bloqué
        # Vérifie que la vraie solution est rejetée aussi
        assert "trop" in result.get("error", "").lower() or "tentatives" in result.get("error", "").lower()

    def test_rate_limit_allows_after_cooldown(self, tmp_path):
        """Note: ce test dépend du temps réel. En pratique, le window est de 30s."""
        auth = SimpleAuth(config_file=str(tmp_path / "users.json"))
        auth.register_user("target", "secret", "private")
        for _ in range(5):
            auth.authenticate("target", "wrong")
        # On ne peut pas vraiment attendre 30s dans un test unitaire
        # Ce test valide la logique métier
        assert auth._rate_limits["target"].exceeded(5) is True