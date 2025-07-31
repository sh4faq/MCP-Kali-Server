@echo off
echo 🐳 Docker SSH Test Environment
echo =====================================

REM Step 1: Start Docker
echo 1️⃣ Starting Docker (persistent)...
echo 🚀 Starting Docker in background...

REM Go to docker directory and start
cd docker
call start.bat
cd ..

echo ✅ Docker started and running
echo 🔗 SSH: localhost:2222 (testuser:testpass)
echo.
echo 💡 To run tests manually:
echo    python -m pytest kali\test_ssh_manager.py -v
echo.
echo 💡 To stop container later:
echo    docker stop kali-test-ssh
echo    docker rm kali-test-ssh
echo.
echo ⚠️  Container will remain running until manually stopped
pause
