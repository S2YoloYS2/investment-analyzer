# 🎯 AI 투자 분석 시스템

AI 기반 주식 투자 분석 도구 - 임원 매수 추적, 애널리스트 평가, 자동 종목 발굴

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ 주요 기능

### 🔍 종목 검색
- 실시간 종목 분석
- 미국/한국 주식 지원
- 관심 종목 관리

### 🤖 자동 종목 발굴
- AI 추천 TOP 20
- S&P 100 종목 스캔
- 종합 점수 순위

### 📊 임원 매수 추적
- SEC Form 4 분석
- 내부자 거래 패턴
- 매수 신호 점수화

### 💡 애널리스트 평가
- 목표가 분석
- 추천 등급 집계
- 전문가 의견 종합

### 🌍 시장 분석
- VIX 공포 지수
- M2 통화량 (선택)
- 시장 타이밍 판단

## 🚀 시작하기

### 필수 요구사항
- Python 3.12 이상
- pip

### 설치
```bash
git clone https://github.com/yourusername/investment-analyzer.git
cd investment-analyzer
pip install -r requirements.txt
```

### 실행
```bash
streamlit run step3_dashboard/dashboard_insider.py
```

또는 Windows:
```bash
start_insider.bat
```

## 📖 사용 방법

1. **종목 검색**: 사이드바에서 종목 코드 입력 (예: AAPL, NVDA)
2. **분석 시작**: 🔍 버튼 클릭하여 전체 분석 실행
3. **상세 확인**: 각 탭에서 심층 분석 결과 확인
4. **관심 종목**: ⭐ 버튼으로 즐겨찾기 저장

## 🛠️ 기술 스택

- **Backend**: Python 3.12
- **Frontend**: Streamlit
- **데이터**: yfinance, pandas
- **시각화**: Plotly
- **API**: Yahoo Finance, SEC EDGAR

## 📊 데이터 소스

- **Yahoo Finance**: 주가, 재무 정보 (무료)
- **SEC EDGAR**: 내부자 거래 (무료)
- **FRED API**: 거시 경제 지표 (선택, 무료)

## 🎯 점수 체계

### 종합 점수 계산
- 애널리스트 평가: 40%
- 임원 매수: 30%
- 기술적 모멘텀: 30%

### 신호 해석
- 🟢 70점 이상: 강한 매수
- 🟡 50-69점: 중립
- 🔴 30-49점: 주의
- ⚫ 30점 미만: 신호없음

## 📱 화면 구성

### 1. 대시보드
- 종목 개요
- 가격 차트
- 주요 지표

### 2. 자동 종목 발굴
- 미국 TOP 20
- 한국 TOP 10
- AI 추천

### 3. 시장 분석
- VIX 지수
- M2 통화량
- 종합 판단

### 4. 임원 매수 추적
- Form 4 분석
- 거래 패턴
- 매수 신호

### 5. 애널리스트 평가
- 목표가 분석
- 추천 등급
- 전문가 의견

## ⚠️ 주의사항

- 본 시스템은 투자 참고 도구이며, 투자 권유가 아닙니다
- 모든 투자 결정은 본인의 책임입니다
- 과거 데이터는 미래 수익을 보장하지 않습니다

## 📝 라이선스

MIT License

## 👤 개발자

AI 투자 분석 시스템 개발팀

## 🤝 기여

이슈 및 풀 리퀘스트는 언제나 환영합니다!

## 📮 문의

프로젝트 관련 문의: GitHub Issues

---

⭐ 프로젝트가 도움이 되셨다면 Star를 눌러주세요!
```

**저장:**
- 파일명: `README.md`
- 위치: `C:\Users\tlqls\Documents\investment_local\README.md`

---

### 파일 3: requirements.txt 확인

**기존 파일 확인:**
```
C:\Users\tlqls\Documents\investment_local\requirements.txt
```

**내용이 다음과 같은지 확인:**
```
streamlit==1.28.0
yfinance==0.2.32
pandas==2.1.3
plotly==5.18.0
requests==2.31.0
pyyaml==6.0.1
python-dotenv==1.0.0