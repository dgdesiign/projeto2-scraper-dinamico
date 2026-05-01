from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import random

app = FastAPI(title="Simulador Tribunal - 5.000 processos")

HTML_PATH = Path(__file__).resolve().parent / "templates" / "portal.html"
with open(HTML_PATH, "r", encoding="utf-8") as f:
    PORTAL_HTML = f.read()

CLASSES = ["Procedimento Comum", "Execução Fiscal", "Mandado de Segurança",
           "Recurso Inominado", "Monitória", "Cumprimento de Sentença",
           "Embargos de Terceiro", "Ação Rescisória"]
ASSUNTOS = ["Obrigação de Fazer", "IPTU", "Liminar", "Direito do Consumidor",
            "Contrato", "Dano Moral", "Revisão de Benefício", "Despejo"]
VARAS = ["1ª Vara Cível", "2ª Vara Fazenda", "3ª Vara Cível", "Turma Recursal",
         "4ª Vara Cível", "5ª Vara de Família", "Vara da Infância"]
JUIZES = ["Dr. Ricardo Silva", "Dra. Ana Martins", "Dr. Carlos Souza",
          "Dra. Paula Lima", "Dr. Marcos Rocha", "Dra. Fernanda Alves",
          "Dr. Roberto Nunes", "Dra. Juliana Costa"]
MOVIMENTACOES = [
    "Concluso para sentença em {}/{}",
    "Citação expedida em {}/{}",
    "Liminar deferida em {}/{}",
    "Aguardando pauta em {}/{}",
    "Contestação apresentada em {}/{}",
    "Réu citado em {}/{}",
    "Decisão interlocutória em {}/{}",
    "Sentença proferida em {}/{}"
]

# Geração determinística: número sequencial simples, facilmente encontrável
PROCESSOS_DB = []
for i in range(1, 5001):
    numero = f"{i:07d}-00.2025.8.26.0100"  # Ex: 0000001-00.2025...
    PROCESSOS_DB.append({
        "numero": numero,
        "classe": CLASSES[i % len(CLASSES)],
        "assunto": ASSUNTOS[i % len(ASSUNTOS)],
        "vara": VARAS[i % len(VARAS)],
        "juiz": JUIZES[i % len(JUIZES)],
        "mov": MOVIMENTACOES[i % len(MOVIMENTACOES)].format(f"{random.randint(1,28):02d}", f"{random.randint(1,12):02d}")
    })

@app.get("/", response_class=HTMLResponse)
async def portal():
    return PORTAL_HTML

@app.get("/api/consulta")
async def consulta(numero: str = ""):
    import time
    time.sleep(0.3)  # Reduzi latência para acelerar mantendo realismo
    if not numero:
        return []
    termo = numero.lower().strip()
    resultados = [p for p in PROCESSOS_DB if termo in p["numero"].lower()]
    return resultados[:50]
