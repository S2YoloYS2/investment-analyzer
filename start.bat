@echo off
chcp 65001 >nul
echo ================================================
echo    AI 투자 분석 시스템 시작
echo ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다!
    pause
    exit /b 1
)

echo [1/3] Python 버전 확인...
python --version

echo.
echo [2/3] 필요한 패키지 설치 확인 중...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo.
    echo 처음 실행입니다! 필요한 패키지를 설치할까요?
    echo 약 5-10분 소요됩니다.
    echo.
    set /p install="설치하시겠습니까? (Y/N): "
    if /i "%install%"=="Y" (
        echo.
        echo 패키지 설치 중...
        pip install -r requirements.txt
    )
)

echo.
echo [3/3] 대시보드 실행 중...
echo.
echo ================================================
echo  브라우저가 자동으로 열립니다!
echo  http://localhost:8501
echo ================================================
echo.

cd step3_dashboard
python -m streamlit run dashboard.py --server.port 8510

pause