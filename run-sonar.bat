@echo off
echo ========================================
echo MedTrack SonarQube Analysis Runner
echo ========================================
echo.

REM Check if SonarQube is running
echo [1/4] Checking if SonarQube is running...
docker ps | findstr sonarqube >nul 2>&1
if errorlevel 1 (
    echo SonarQube is not running. Starting it now...
    docker-compose --profile sonar up -d sonarqube-db sonarqube
    echo.
    echo Waiting for SonarQube to start (this may take 2-3 minutes)...
    timeout /t 120 /nobreak >nul
) else (
    echo SonarQube is already running.
)

echo.
echo [2/4] Verifying SonarQube is ready...
:wait_loop
curl -s http://localhost:9090/api/system/status | findstr "UP" >nul 2>&1
if errorlevel 1 (
    echo Still waiting for SonarQube...
    timeout /t 10 /nobreak >nul
    goto wait_loop
)
echo SonarQube is ready!

echo.
echo [3/4] Running SonarQube Scanner...
docker run --rm ^
    --network=backend ^
    -v "%cd%:/usr/src" ^
    -w /usr/src ^
    sonarsource/sonar-scanner-cli ^
    -Dsonar.host.url=http://sonarqube:9000 ^
    -Dsonar.login=admin ^
    -Dsonar.password=admin

echo.
echo [4/4] Analysis Complete!
echo.
echo ========================================
echo Open your browser and go to:
echo   http://localhost:9090
echo.
echo Login with: admin / admin
echo (You will be prompted to change password on first login)
echo ========================================
pause
