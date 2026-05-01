import time
import pytest
import requests
from database import engine, Base, SessionLocal
from models import Processo

BASE_URL = "http://localhost:8002"
TARGET_URL = "http://localhost:8001"

def wait_for_service(url, timeout=10):
    """Espera o serviço responder antes de testar."""
    for _ in range(timeout * 2):
        try:
            requests.get(url, timeout=1)
            return True
        except requests.ConnectionError:
            time.sleep(0.5)
    return False

def test_portal_fake_responde():
    """Verifica se o portal fake está acessível."""
    assert wait_for_service(TARGET_URL), "Portal fake (8001) não está rodando"
    resp = requests.get(TARGET_URL)
    assert resp.status_code == 200
    assert "Portal de Consulta Processual" in resp.text

def test_api_status():
    """Verifica se a API retorna status ok."""
    assert wait_for_service(BASE_URL), "API (8002) não está rodando"
    resp = requests.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_api_processos_endpoint():
    """Testa o endpoint /processos com filtro, mesmo sem scraper (dados pré-existentes)."""
    assert wait_for_service(f"{BASE_URL}/processos?numero=0000001"), "API não respondeu"
    resp = requests.get(f"{BASE_URL}/processos?numero=0000001")
    assert resp.status_code == 200
    data = resp.json()
    # Pode ter dados do Projeto 2 (5 processos) ou dos 5.000
    assert isinstance(data, list)

def test_scraper_executavel():
    """Verifica se o script main.py existe e pode ser executado."""
    import subprocess
    result = subprocess.run(["python", "-c", "import main; print('OK')"], capture_output=True, text=True)
    assert result.returncode == 0
