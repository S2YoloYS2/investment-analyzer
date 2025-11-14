@echo off
chcp 65001 > nul
title AI 투자 분석 - 임원 매수 추적

echo ============================================
echo 🤖 AI 투자 분석 시스템 - 임원 매수 추적
echo ============================================
echo.

cd /d "%~dp0"

echo 📁 작업 디렉토리: %CD%
echo.

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다!
    pause
    exit /b 1
)

echo ✅ Python 확인 완료
python --version
echo.

REM 패키지 확인
pip show beautifulsoup4 >nul 2>&1
if errorlevel 1 (
    echo 📥 새 패키지 설치 중...
    pip install beautifulsoup4 lxml pyyaml python-dotenv tqdm python-dateutil --quiet
    echo ✅ 패키지 설치 완료!
)

echo.
echo ============================================
echo 🚀 임원 매수 추적 대시보드 실행
echo ============================================
echo.
echo 💡 브라우저가 자동으로 열립니다
echo 🛑 종료: Ctrl+C
echo.

REM 브라우저 자동 오픈
start http://localhost:8501

REM Streamlit 실행
streamlit run step3_dashboard/dashboard_insider.py --server.headless false --browser.serverAddress localhost

pause