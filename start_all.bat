@echo off
echo ======================================================================
echo Starting Automated Institutional Document Compliance and Audit System
echo ======================================================================
echo.
echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Institutional Compliance - Backend (Port 8000)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Launching Vite Frontend on http://localhost:5173 ...
start "Institutional Compliance - Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo Systems Initialized Successfully!
echo Frontend: http://localhost:5173
echo Backend API Docs: http://127.0.0.1:8000/docs
echo ======================================================================
echo.
echo Press any key to exit this launcher window (servers continue running in their own windows)...
pause >nul
