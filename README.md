cat > README.md << 'ENDOFFILE'
# 🕵️ Projeto 2 – Scraper Dinâmico com Playwright

![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Playwright](https://img.shields.io/badge/Playwright-1.49-orange)
![Docker](https://img.shields.io/badge/Docker-ready-brightgreen)

Pipeline completo de **web scraping dinâmico** para portais que exigem renderização JavaScript, desenvolvido como prova técnica para a vaga de Desenvolvedor Backend Júnior na Trimon (plataforma Escavador).

## 📌 Objetivo

Coletar dados processuais de um portal simulado com formulários, cliques e carregamento assíncrono de tabelas. O sistema foi projetado para demonstrar:

- Automação de navegador real com **Playwright** (headless Chromium)
- Raspagem de sites que dependem de JavaScript (tribunais, diários oficiais)
- Pipeline de dados com **upsert** via SQLAlchemy (SQLite)
- API REST documentada automaticamente (Swagger)
- Escalabilidade para **5.000+ registros**
- Execução 100% em nuvem via GitHub Codespaces (sem dependência de PC local)

## 🧱 Arquitetura
```

[Portal Fake]         [Scraper Playwright]       [API REST]
(JavaScript pesado)   (headless, async)          (FastAPI)
│                      │                       │
└──────────────────────┼───────────────────────┘
│
[SQLite + SQLAlchemy]
│
[5.000 processos salvos]

```

O fluxo ponta a ponta:
1. Um servidor fake simula um portal de tribunal com formulário e tabela dinâmica.
2. O scraper com Playwright preenche o campo, clica em "Pesquisar", espera a tabela carregar e extrai os dados.
3. Os dados são salvos no banco com estratégia de upsert (evita duplicatas).
4. Uma API REST expõe os registros coletados, com suporte a filtros.

## 🚀 Como executar rapidamente (Docker)

```bash
docker compose up --build

Isso subirá três serviços:

· Portal Fake em http://localhost:8001
· Scraper executado automaticamente (consulta 6 processos de exemplo)
· API REST em http://localhost:8002 (Swagger em /docs)

Após a execução, acesse a API e veja os dados:
curl http://localhost:8002/processos

💻 Execução manual (local ou Codespaces)
1. Clone o repositório e entre na pasta

```bash
git clone https://github.com/dgdesiign/projeto2-scraper-dinamico.git
cd projeto2-scraper-dinamico
```

2. Crie um ambiente virtual e instale as dependências

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
playwright install chromium
```

3. (Apenas Linux) Instale dependências do sistema para o Chromium

```bash
sudo playwright install-deps
```

4. Inicie o portal fake (Terminal 1)

```bash
uvicorn target_server.app:app --host 0.0.0.0 --port 8001 --reload
```

5. Execute o scraper (Terminal 2)

```bash
python main.py
```

6. Suba a API REST (Terminal 3)

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload
```

Acesse os endpoints:

· API Status: http://localhost:8002/
· Processos coletados: http://localhost:8002/processos
· Documentação interativa: http://localhost:8002/docs

📈 Escalabilidade – Carga de 5.000 registros

O sistema suporta a inserção em massa de processos para demonstrar comportamento sob volume real. Execute o script abaixo após ter o banco inicializado:

```bash
python3 << 'PYEOF'
from database import SessionLocal, engine, Base
from models import Processo
import random

Base.metadata.create_all(bind=engine)

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

db = SessionLocal()
try:
    for i in range(1, 5001):
        numero = f"{i:07d}-00.2025.8.26.0100"
        existente = db.query(Processo).filter_by(numero_processo=numero).first()
        if not existente:
            processo = Processo(
                numero_processo=numero,
                classe=CLASSES[i % len(CLASSES)],
                assunto=ASSUNTOS[i % len(ASSUNTOS)],
                vara=VARAS[i % len(VARAS)],
                juiz=JUIZES[i % len(JUIZES)],
                ultima_movimentacao=MOVIMENTACOES[i % len(MOVIMENTACOES)].format(
                    f"{random.randint(1,28):02d}", f"{random.randint(1,12):02d}"
                )
            )
            db.add(processo)
        if i % 500 == 0:
            db.commit()
            print(f"{i} registros processados...")
    db.commit()
    print("Inserção concluída!")
finally:
    db.close()

print(f"Total de processos no banco: {db.query(Processo).count()}")
PYEOF
```

O banco passará a conter 5.000 processos, todos acessíveis via API.

🧪 Demonstração (prints)

Portal Fake API com 5.000 processos Swagger
assets/portal.png assets/api.png assets/swagger.png

As imagens podem ser geradas executando o projeto e tirando prints.

🛠️ Tecnologias utilizadas

· Python 3.12, FastAPI, Uvicorn, Pydantic
· Playwright (Chromium headless)
· SQLAlchemy (ORM com SQLite)
· Docker, Docker Compose
· GitHub Codespaces (desenvolvimento em nuvem)

👨‍💻 Autor

Douglas – Candidato a Backend Júnior na Trimon
LinkedIn | GitHub

📝 Licença

MIT
ENDOFFILE
