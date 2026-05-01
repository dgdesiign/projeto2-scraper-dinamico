import asyncio
import logging
from database import engine, Base, SessionLocal
from models import Processo
from scraper.playwright_scraper import TribunalScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def gerar_numeros_processo(quantidade: int, inicio: int = 1):
    """Gera uma lista de números de processo sequenciais."""
    # Usaremos o padrão i:07d-xx.2025...
    # Precisamos casar com o formato do servidor: aleatório, mas vamos usar range simples.
    # O servidor fake usa números i:07d-rand, então vamos buscar apenas pelos prefixos.
    # Para garantir acerto, vou gerar exatamente os números existentes.
    import random
    random.seed(42)  # Reprodutível
    return [f"{i:07d}-{random.randint(10,99)}.2025.8.26.0100" for i in range(inicio, inicio + quantidade)]

async def run_scraper():
    # Vamos consultar todos os 5.000, mas em lotes de 100 para evitar explosão de RAM
    TOTAL = 5000
    LOTE = 100
    scraper = TribunalScraper()
    await scraper.start()
    db = SessionLocal()
    try:
        for offset in range(0, TOTAL, LOTE):
            numeros_lote = gerar_numeros_processo(LOTE, inicio=offset+1)
            logger.info(f"Processando lote {offset//LOTE + 1}/{(TOTAL//LOTE)} ({len(numeros_lote)} números)")
            dados = await scraper.buscar_varios(numeros_lote)
            logger.info(f"Lote {offset//LOTE + 1}: {len(dados)} registros extraídos")
            
            # Upsert em lote
            for item in dados:
                existente = db.query(Processo).filter_by(numero_processo=item["numero_processo"]).first()
                if existente:
                    for k, v in item.items():
                        setattr(existente, k, v)
                else:
                    db.add(Processo(**item))
            db.commit()
            logger.info(f"Lote {offset//LOTE + 1} persistido.")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro: {e}")
        raise
    finally:
        db.close()
        await scraper.stop()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    logger.info("Iniciando coleta massiva de 5.000 processos...")
    asyncio.run(run_scraper())
    logger.info("Coleta concluída! Execute a API para ver os resultados.")
