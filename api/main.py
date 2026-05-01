from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import Processo
from typing import Optional

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API de Processos Coletados", version="1.0")

@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/processos"]}

@app.get("/processos")
def listar_processos(
    numero: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Processo)
    if numero:
        query = query.filter(Processo.numero_processo.ilike(f"%{numero}%"))
    processos = query.order_by(Processo.data_consulta.desc()).all()
    
    # Converte manualmente para dicionário evitando problemas de serialização
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
