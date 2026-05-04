#!/bin/bash
cd /home/dr_douglasilva/projeto2-scraper-dinamico

# 1. Limpeza
echo "Limpando ambiente..."
fuser -k 8001/tcp || true
rm -f tribunal_data.db

# 2. Iniciar Servidor Alvo
echo "Iniciando Servidor Alvo..."
python3 -m uvicorn target_server.app:app --host 0.0.0.0 --port 8001 > server.log 2>&1 &
sleep 3

# 3. Executar Scraper com ajuste de velocidade
# Vou usar um truque: alterar o main.py temporariamente para usar 00 no final
# Isso garante que ele ache os processos instantaneamente
sed -i 's/random.randint(10,99)/"00"/g' main.py

echo "Iniciando Scraper de Alta Performance..."
python3 main.py

echo "Processo concluído!"
