import sys
import time
import webbrowser
import threading
from pathlib import Path
import uvicorn

# Asegurar que el directorio del proyecto esté en sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.main import app

def abrir_navegador():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000/")

if __name__ == "__main__":
    print("=" * 60)
    print(" AI-Triage: Sistema Inteligente de Clasificación de Historias Clínicas")
    print(" Iniciando servidor y abriendo panel en tu navegador...")
    print("=" * 60)
    threading.Thread(target=abrir_navegador, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
