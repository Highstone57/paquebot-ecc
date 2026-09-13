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
import uvicorn, os, socket, subprocess, time, json

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

import os as _os

_status_cache = {"time": 0, "data": None}


def _check_port(host: str, port: int, timeout: float = 1.5) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except:
        return False


def _read_proc(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except:
        return ""


@app.get("/health")
def health():
    return {"status": "ok", "service": "paquebot-ecc"}


@app.get("/api/status")
def api_status():
    """Statut en direct de tous les services (caché 5s)."""
    global _status_cache
    if _status_cache["data"] and time.time() - _status_cache["time"] < 5:
        return _status_cache["data"]

    hermes = _check_port("127.0.0.1", 8642)
    ido = _check_port("127.0.0.1", 8090)
    ollama = _check_port("127.0.0.1", 11434)
    home_asst = _check_port("127.0.0.1", 8123)

    uptime_h = None
    disk = {}
    ram = {}
    gpu = []
    try:
        upt = _read_proc("/proc/uptime").split()
        if upt:
            uptime_h = round(float(upt[0]) / 3600, 1)
        st = _os.statvfs("/")
        disk = {"total_gb": round(st.f_frsize * st.f_blocks / 1e9, 1),
                "free_gb": round(st.f_frsize * st.f_bfree / 1e9, 1)}
        mem_lines = _read_proc("/proc/meminfo").strip().split("\n")
        mem = {}
        for line in mem_lines:
            if ":" in line:
                k, v = line.split(":", 1)
                val = v.strip().split()
                if val:
                    mem[k] = int(val[0])
        ram = {"total_gb": round(mem.get("MemTotal", 0) / 1e6, 1),
               "avail_gb": round(mem.get("MemAvailable", 0) / 1e6, 1)}
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3)
        for line in r.stdout.strip().split("\n"):
            if line:
                parts = [p.strip() for p in line.split(",")]
                gpu.append({"name": parts[0], "temp": parts[1],
                            "util": parts[2], "mem_used": parts[3], "mem_total": parts[4]})
    except:
        pass

    data = {
        "services": {
            "hermes": {"on": hermes, "port": 8642, "label": "Gateway"},
            "ido": {"on": ido, "port": 8090, "label": "Site IDO"},
            "ollama": {"on": ollama, "port": 11434, "label": "Modèles IA"},
            "home_asst": {"on": home_asst, "port": 8123, "label": "Maison"},
            "app": {"on": True, "port": 8081, "label": "Paquebot-ECC"},
        },
        "system": {"uptime_h": uptime_h, "disk": disk, "ram": ram, "gpu": gpu},
    }
    _status_cache = {"time": time.time(), "data": data}
    return data


@app.get("/api/status/detailed")
def api_status_detailed():
    """Données détaillées pour le Journal de Bord + Console."""
    global _status_cache2
    try:
        _status_cache2
    except:
        _status_cache2 = {"time": 0, "data": None}

    if _status_cache2["data"] and time.time() - _status_cache2["time"] < 10:
        return _status_cache2["data"]

    base = api_status()

    # Ollama : modèles disponibles
    ollama_models = []
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "2",
                            "http://localhost:11434/api/tags"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            d = json.loads(r.stdout)
            for m in d.get("models", []):
                ollama_models.append({
                    "name": m["name"],
                    "size_gb": round(m.get("size", 0) / 1e9, 1),
                })
    except:
        pass

    # GitHub : derniers repos
    github_repos = []
    try:
        r = subprocess.run(["gh", "repo", "list", "Highstone57",
                            "--limit", "5", "--json", "name,description,updatedAt,url"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            github_repos = json.loads(r.stdout)
    except:
        pass

    # Processeur
    cpu = {}
    try:
        load = _read_proc("/proc/loadavg").split()
        if load:
            cpu = {"load_1m": load[0], "load_5m": load[1], "load_15m": load[2]}
    except:
        pass

    data = {
        **base,
        "ollama_models": ollama_models,
        "github_repos": github_repos,
        "cpu": cpu,
    }
    _status_cache2 = {"time": time.time(), "data": data}
    return data

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