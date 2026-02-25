@echo off
echo Starting CodeMan Backend...
start "CodeMan Backend" cmd /k "cd codeman-backend && python -m uvicorn main:app --reload --port 8000"

echo Starting CodeMan Frontend...
start "CodeMan Frontend" cmd /k "cd codeman-frontend && npm run dev"

echo CodeMan Community Started!
echo Backend: http://127.0.0.1:8000/docs
echo Frontend: http://localhost:5173
pause
