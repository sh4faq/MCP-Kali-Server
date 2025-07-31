@echo off
REM Ultra-simple script to start Docker in background

echo 🐳 Starting Docker in background...

REM Build image if it doesn't exist
docker images -q kali-test-ssh:latest >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 🔨 Building image...
    docker build -t kali-test-ssh:latest .
)

REM Remove old container if exists
docker rm -f kali-test-ssh >nul 2>&1

REM Start new container in background
docker run -d --name kali-test-ssh -p 2222:22 -p 4444:4444 -p 4445:4445 -p 8080:8080 kali-test-ssh:latest

REM Wait 8 seconds for SSH to start
echo ⏳ Waiting for SSH (8 seconds)...
timeout /t 8 /nobreak >nul

echo ✅ Docker started in background
echo 📋 SSH: localhost:2222 (testuser:testpass)
echo.
echo 💡 To run tests: 
echo    cd ..
echo    python -m pytest kali\test_ssh_manager.py -v
