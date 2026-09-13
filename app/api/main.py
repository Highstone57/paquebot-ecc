"""API REST de Paquebot-ECC — accessible depuis le téléphone et les ordis.

Points d'entrée :
  GET  /health       → santé du service
  POST /auth/register → créer un compte
  POST /auth/login   → s'authentifier
  GET  /             → page d'accueil web
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

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

# ── Page web ──────────────────────────────────────────────────────

# Page d'accueil embarquée
INDEX_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Paquebot-ECC</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0d1117; color: #c9d1d9;
    font-family: system-ui, -apple-system, sans-serif;
    padding: 1rem;
    min-height: 100vh;
    display: flex; flex-direction: column;
  }
  .container { max-width: 800px; margin: 0 auto; width: 100%; }
  header { padding: 2rem 0; text-align: center; }
  h1 { font-size: 2rem; }
  h1 span { background: linear-gradient(135deg, #58a6ff, #bc8cff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .subtitle { color: #8b949e; margin-top: .5rem; }
  .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 12px;
    padding: 1.5rem; margin: 1rem 0;
  }
  .card h2 { font-size: 1.1rem; margin-bottom: 1rem; color: #f0f6fc; }
  label { display: block; margin: .8rem 0 .3rem; color: #8b949e; font-size: .85rem; }
  input, select {
    width: 100%; padding: .7rem;
    background: #0d1117; border: 1px solid #30363d; border-radius: 8px;
    color: #f0f6fc; font-size: 1rem;
  }
  button {
    width: 100%; margin-top: 1rem; padding: .7rem;
    background: #238636; border: none; border-radius: 8px;
    color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer;
  }
  button:hover { background: #2ea043; }
  .result { margin-top: 1rem; padding: 1rem; border-radius: 8px; font-size: .9rem; }
  .success { background: rgba(63,185,80,.1); border: 1px solid #3fb950; }
  .error { background: rgba(248,81,73,.1); border: 1px solid #f85149; }
  .status { text-align: center; color: #8b949e; font-size: .8rem; margin-top: 2rem; }
  nav { display: flex; gap: 1rem; margin-bottom: 1rem; }
  nav a { color: #58a6ff; text-decoration: none; font-size: .9rem; }
  nav a:hover { text-decoration: underline; }
  .json { font-family: monospace; font-size: .8rem; white-space: pre-wrap; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>&#x1F6A2; <span>Paquebot-ECC</span></h1>
    <p class="subtitle">Construit avec le workflow ECC (Everything Claude Code)</p>
  </header>

  <nav>
    <a href="/health">&#x1F3A5; /health</a>
    <a href="#" onclick="showTab('login')">&#x1F511; Connexion</a>
    <a href="#" onclick="showTab('register')">&#x1F4CB; Inscription</a>
  </nav>

  <div id="login-card" class="card">
    <h2>&#x1F511; Connexion</h2>
    <label>Nom d'utilisateur</label>
    <input id="login-user" placeholder="alice">
    <label>Mot de passe</label>
    <input id="login-pass" type="password" placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022">
    <button onclick="login()">Se connecter</button>
    <div id="login-result" class="result" style="display:none;"></div>
  </div>

  <div id="register-card" class="card" style="display:none;">
    <h2>&#x1F4CB; Inscription</h2>
    <label>Nom d'utilisateur</label>
    <input id="reg-user" placeholder="alice">
    <label>Mot de passe</label>
    <input id="reg-pass" type="password" placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022">
    <label>Niveau de sécurité</label>
    <select id="reg-level">
      <option value="public">&#x1F310; Public</option>
      <option value="shared">&#x1F91D; Partagé</option>
      <option value="private">&#x1F512; Privé</option>
    </select>
    <button onclick="register()">Créer mon compte</button>
    <div id="reg-result" class="result" style="display:none;"></div>
  </div>

  <div class="status">
    <span id="health-status">&#x23F3; Vérification...</span>
  </div>
</div>

<script>
function showTab(tab) {
  document.getElementById('login-card').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('register-card').style.display = tab === 'register' ? 'block' : 'none';
}

async function api(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return { ok: res.ok, data };
}

function showResult(el, data) {
  el.style.display = 'block';
  if (data.success || data.detail === undefined) {
    el.className = 'result success';
    el.innerHTML = '<strong>&#x2705; OK</strong><br><div class="json">' + JSON.stringify(data, null, 2) + '</div>';
  } else {
    el.className = 'result error';
    el.innerHTML = '<strong>&#x274C; Erreur</strong><br>' + (data.detail || 'Inconnue');
  }
}

async function login() {
  const { ok, data } = await api('/auth/login', {
    username: document.getElementById('login-user').value,
    password: document.getElementById('login-pass').value,
  });
  showResult(document.getElementById('login-result'), ok ? data : data);
}

async function register() {
  const { ok, data } = await api('/auth/register', {
    username: document.getElementById('reg-user').value,
    password: document.getElementById('reg-pass').value,
    security_level: document.getElementById('reg-level').value,
  });
  showResult(document.getElementById('reg-result'), ok ? data : data);
}

// Health check
fetch('/health').then(r => r.json()).then(d => {
  document.getElementById('health-status').innerHTML = '&#x2705; ' + d.service + ' \u2014 ' + d.status;
}).catch(() => {
  document.getElementById('health-status').innerHTML = '&#x274C; Hors ligne';
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=INDEX_HTML)