"""API REST de Paquebot-ECC — accessible depuis le téléphone et les ordis.

Points d'entrée :
  GET  /health       → santé du service
  POST /auth/register → créer un compte
  POST /auth/login   → s'authentifier
  GET  /             → page d'accueil web
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn, os

from app.auth import SimpleAuth
from app.auth.simple_auth import AuthError

# ── Initialisation ────────────────────────────────────────────────

app = FastAPI(title="Paquebot-ECC", version="0.1.0")
auth = SimpleAuth()  # stockage fichier par défaut

# ── Modèles ───────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=4, max_length=128)
    security_level: str = Field(default="public", pattern=r"^(private|shared|public)$")

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    username: str | None = None
    security_level: str | None = None
    error: str | None = None

# ── Endpoints API ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "paquebot-ecc"}

@app.post("/auth/register", response_model=AuthResponse)
def register(body: RegisterRequest):
    try:
        auth.register_user(body.username, body.password, body.security_level)
        return AuthResponse(
            success=True,
            username=body.username,
            security_level=body.security_level,
        )
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest):
    result = auth.authenticate(body.username, body.password)
    if result["success"]:
        return AuthResponse(
            success=True,
            username=result["username"],
            security_level=result["security_level"],
        )
    raise HTTPException(status_code=401, detail=result["error"])

@app.get("/level/{username}")
def get_level(username: str):
    level = auth.get_security_level(username)
    return {"username": username, "security_level": level}

# ── Pages web ─────────────────────────────────────────────────────

_TEMPLATES = os.path.join(os.path.dirname(__file__), "..", "templates")


def _html(name: str) -> HTMLResponse:
    path = os.path.join(_TEMPLATES, name)
    with open(path) as f:
        return HTMLResponse(content=f.read())


@app.get("/", response_class=HTMLResponse)
def login_page():
    return _html("login.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return _html("dashboard.html")


@app.get("/dashboard/a", response_class=HTMLResponse)
def profil_a():
    return _html("profil_a.html")


@app.get("/dashboard/b", response_class=HTMLResponse)
def profil_b():
    return _html("profil_b.html")


@app.get("/dashboard/c", response_class=HTMLResponse)
def profil_c():
    return _html("profil_c.html")


# ── Fin ───────────────────────────────────────────────────────────