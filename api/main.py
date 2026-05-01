from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import Processo
from typing import Optional
import time

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="API de Processos Coletados", version="2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/health")
def healthcheck():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/processos", "/health"]}

@app.get("/processos")
@limiter.limit("10/minute")
def listar_processos(
    request: Request,
    numero: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Processo)
    if numero:
        query = query.filter(Processo.numero_processo.ilike(f"%{numero}%"))
    processos = query.order_by(Processo.data_consulta.desc()).limit(100).all()
    resultados = []
    for p in processos:
        resultados.append({
            "id": p.id,
            "numero_processo": p.numero_processo,
            "classe": p.classe,
            "assunto": p.assunto,
            "vara": p.vara,
            "juiz": p.juiz,
            "ultima_movimentacao": p.ultima_movimentacao,
            "data_consulta": p.data_consulta.isoformat() if p.data_consulta else None
        })
    return resultados
