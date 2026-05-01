from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from database import Base

class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_processo = Column(String(50), unique=True, nullable=False, index=True)
    classe = Column(String(100))
    assunto = Column(String(255))
    vara = Column(String(100))
    juiz = Column(String(100))
    ultima_movimentacao = Column(Text)
    data_consulta = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Processo {self.numero_processo}>"
