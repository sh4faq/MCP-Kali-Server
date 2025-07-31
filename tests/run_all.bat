@echo off
REM Script to run Docker + Tests in one command

echo 🚀 Docker + SSH Tests - Simple Solution
echo =====================================

REM Step 1: Start Docker
echo 1️⃣ Starting Docker...
cd docker
call start.bat

REM Step 2: Configure and run tests
echo.
echo 2️⃣ Running tests...
cd ..
REM Docker is the only supported configuration
python -m pytest kali\test_ssh_manager.py -v --tb=short

echo.
echo ✅ Tests completed!

REM Step 3: Stop Docker
echo.
echo 3️⃣ Stopping container...
docker stop kali-test-ssh >nul 2>&1
docker rm kali-test-ssh >nul 2>&1
echo ✅ Docker stopped

echo.
pause
