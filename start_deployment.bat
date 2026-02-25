@echo off
setlocal EnableDelayedExpansion

title CodeMan Community Launcher

echo ==========================================================
echo               CodeMan Community One-Click Start
echo ==========================================================
echo.

:: --- 1. Environment Check ---
echo [1/4] Checking Environment...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)
python --version

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/npm is not installed or not in PATH.
    echo Please install Node.js 14+ and add it to PATH.
    pause
    exit /b 1
)
echo Node.js found.

:: --- 2. Backend Setup & Launch ---
echo.
echo [2/4] Setting up Backend...

if not exist "codeman-backend" (
    echo [ERROR] Directory 'codeman-backend' not found!
    pause
    exit /b 1
)

cd codeman-backend

:: Create venv if missing
if not exist "venv" (
    echo - Creating Python virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install dependencies
echo - Installing/Updating Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies might have failed to install.
)

:: Launch Backend in a new window
echo - Launching Backend Server (Port 8000)...
start "CodeMan Backend" cmd /k "title CodeMan Backend && echo Starting Uvicorn... && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

cd ..

:: --- 3. Frontend Setup & Launch ---
echo.
echo [3/4] Setting up Frontend...

if not exist "codeman-frontend" (
    echo [ERROR] Directory 'codeman-frontend' not found!
    pause
    exit /b 1
)

cd codeman-frontend

:: Install npm packages if missing
if not exist "node_modules" (
    echo - Installing Frontend dependencies (this may take a while)...
    call npm install
)

:: Launch Frontend in a new window
echo - Launching Frontend Server (Port 5173)...
start "CodeMan Frontend" cmd /k "title CodeMan Frontend && echo Starting Vite... && npm run dev -- --host 0.0.0.0"

cd ..

:: --- 4. Final Info ---
echo.
echo [4/4] Getting Local Network Info...
echo.
echo ==========================================================
echo                 Services Started!
echo ==========================================================
echo.
echo [Local Access]
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000/docs (API Docs)
echo.
echo [LAN Access - Share this with your phone]
ipconfig | findstr "IPv4"
echo.
echo   Frontend: http://<YOUR_IP>:5173
echo   Backend:  http://<YOUR_IP>:8000
echo.
echo ==========================================================
echo  * Close the two popped-up windows to stop the servers.
echo  * Press any key to exit this launcher.
echo ==========================================================
pause >nul
