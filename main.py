import asyncio
import logging
from database import engine, Base, SessionLocal
from models import Processo
from scraper.playwright_scraper import TribunalScraper
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações de performance
CONCURRENCY = 5  # Número de abas simultâneas
TOTAL_PROCESSOS = 5000

def obter_processos_coletados():
    """Checkpoint: Verifica no banco quais processos já existem."""
    db = SessionLocal()
    try:
        # Busca apenas a coluna de números para economizar memória
        stmt = select(Processo.numero_processo)
        resultados = db.execute(stmt).scalars().all()
        return set(resultados)
    finally:
        db.close()

def gerar_todos_numeros():
    """Gera a lista completa de 5.000 números seguindo o padrão do servidor."""
    return [f"{i:07d}-00.2025.8.26.0100" for i in range(1, TOTAL_PROCESSOS + 1)]

async def salvar_resultados(dados_lote):
    """Persiste um lote de resultados no banco de dados."""
    if not dados_lote:
        return
    
    db = SessionLocal()
    try:
        for item in dados_lote:
            # Sênior: Upsert simples para SQLite
            existente = db.query(Processo).filter_by(numero_processo=item["numero_processo"]).first()
            if existente:
                for k, v in item.items():
                    setattr(existente, k, v)
            else:
                db.add(Processo(**item))
        db.commit()
        logger.info(f"Salvos {len(dados_lote)} novos registros no banco.")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao persistir lote: {e}")
    finally:
        db.close()

async def run_orchestrator():
    # 1. Checkpoint: O que já fizemos?
    coletados = obter_processos_coletados()
    todos = gerar_todos_numeros()
    
    # Filtra apenas o que falta
    faltantes = [n for n in todos if n not in coletados]
    
    if not faltantes:
        logger.info("Todos os processos já foram coletados! Nada para fazer.")
        return

    logger.info(f"Iniciando coleta. Total: {TOTAL_PROCESSOS} | Já coletados: {len(coletados)} | Restantes: {len(faltantes)}")

    # 2. Inicializa Fila e Scraper
    queue = asyncio.Queue()
    for n in faltantes:
        queue.put_nowait(n)
    
    # Adiciona sinal de parada para os workers
    for _ in range(CONCURRENCY):
        queue.put_nowait(None)

    scraper = TribunalScraper()
    await scraper.start()

    # Callback para salvar resultados assim que o worker extrair
    async def on_results(dados):
        await salvar_resultados(dados)

    # 3. Lança Workers
    workers = [
        asyncio.create_task(scraper.worker(queue, on_results))
        for _ in range(CONCURRENCY)
    ]

    try:
        await asyncio.gather(*workers)
    finally:
        await scraper.stop()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    try:
        asyncio.run(run_orchestrator())
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"Falha catastrófica: {e}")
    finally:
        logger.info("Pipeline finalizado.")
