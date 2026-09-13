#!/usr/bin/env python3
"""Point d'entrée pour le serveur Paquebot-ECC."""
import sys
sys.path.insert(0, '/home/vianey/dev/paquebot-ecc')
from app.api.main import app
import uvicorn

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8081, log_level='info')