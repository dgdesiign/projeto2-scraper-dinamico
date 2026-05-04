#!/bin/bash
cd /home/dr_douglasilva/projeto2-scraper-dinamico
fuser -k 8001/tcp || true
python3 -m uvicorn target_server.app:app --host 0.0.0.0 --port 8001 > server.log 2>&1 &
sleep 5
python3 main.py
