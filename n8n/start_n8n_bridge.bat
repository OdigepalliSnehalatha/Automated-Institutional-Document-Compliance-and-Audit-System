@echo off
title n8n Automation Webhook Bridge (Port 5678)
echo ======================================================================
echo Starting n8n Automation Webhook Bridge on http://127.0.0.1:5678
echo ======================================================================
cd ..
python n8n/local_n8n_bridge.py
pause
