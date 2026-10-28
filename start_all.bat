@echo off
echo ======================================================================
echo Starting Automated Institutional Document Compliance and Audit System
echo ======================================================================
echo.
echo [1/3] Launching n8n Automation Webhook Bridge on http://127.0.0.1:5678 ...
start "Institutional Compliance - n8n Webhook Bridge (Port 5678)" cmd /k "python n8n/local_n8n_bridge.py"

timeout /t 2 /nobreak >nul

echo [2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Institutional Compliance - Backend (Port 8000)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Launching Vite Frontend on http://localhost:5173 ...
start "Institutional Compliance - Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo All Systems Initialized Successfully!
echo Frontend Portal : http://localhost:5173
echo Backend API Docs: http://127.0.0.1:8000/docs
echo n8n Webhook URL : http://localhost:5678/webhook/send-otp
echo ======================================================================
echo.
echo Press any key to exit this launcher window (servers continue running in their own windows)...
pause >nul
