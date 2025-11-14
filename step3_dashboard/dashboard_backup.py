"""
AI 투자 분석 시스템 - 메인 대시보드 (데이터 표시 버전)
"""

import streamlit as st
from datetime import datetime
import sys
import os

# 데이터 수집 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'step1_stock_finder'))

try:
    from data_fetcher import DataFetcher
    DATA_AVAILABLE = True
except:
    DATA_AVAILABLE = False

st.set_page_config(
    page_title="AI 투자 분석 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📊 AI 투자 분석 시스템")
    st.markdown("---")
    
    # 데이터 수집기 초기화
    if DATA_AVAILABLE:
        fetcher = DataFetcher()
        
        # 실제 데이터 가져오기
        samsung_data = fetcher.get_latest_price("005930", "korea")
        apple_data = fetcher.get_latest_price("AAPL", "us")
        btc_data = fetcher.get_latest_price("BTC/USDT", "crypto")
    else:
        samsung_data = None
        apple_data = None
        btc_data = None
    
    # 시스템 상태
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="🟢 시스템 상태", value="정상", delta="가동 중")
    
    with col2:
        st.metric(label="📅 마지막 업데이트", value=datetime.now().strftime("%H:%M"))
    
    with col3:
        st.metric(label="🎯 분석 종목 수", value="3개", delta="데이터 수집 중")
    
    st.markdown("---")
    
    # 실시간 데이터 표시
    st.header("📈 실시간 시장 데이터")
    
    market_col1, market_col2, market_col3 = st.columns(3)
    
    with market_col1:
        st.subheader("🇰🇷 삼성전자")
        if samsung_data:
            st.metric(
                label=f"현재가 ({samsung_data['date']})",
                value=f"{samsung_data['price']:,.0f}원",
                delta=f"{samsung_data['change']:+.2f}%"
            )
            st.caption(f"거래량: {samsung_data['volume']:,}")
        else:
            st.info("데이터 로딩 중...")
    
    with market_col2:
        st.subheader("🇺🇸 Apple")
        if apple_data:
            st.metric(
                label=f"현재가 ({apple_data['date']})",
                value=f"${apple_data['price']:.2f}",
                delta=f"{apple_data['change']:+.2f}%"
            )
            st.caption(f"거래량: {apple_data['volume']:,}")
        else:
            st.info("데이터 로딩 중...")
    
    with market_col3:
        st.subheader("💰 Bitcoin")
        if btc_data:
            st.metric(
                label=f"현재가 ({btc_data['date']})",
                value=f"${btc_data['price']:,.2f}",
                delta=f"{btc_data['change']:+.2f}%"
            )
            st.caption(f"거래량: {btc_data['volume']:,.2f}")
        else:
            st.info("데이터 로딩 중...")
    
    st.markdown("---")
    
    # 차트 섹션
    st.header("📊 가격 차트")
    
    # 기간 선택
    period_options = {
        "1개월": "1mo",
        "3개월": "3mo",
        "6개월": "6mo",
        "1년": "1y"
    }
    
    selected_period_name = st.radio(
        "차트 기간 선택",
        options=list(period_options.keys()),
        horizontal=True,
        index=0
    )
    
    selected_period = period_options[selected_period_name]
    
    chart_tabs = st.tabs(["삼성전자", "Apple", "Bitcoin"])
    
    with chart_tabs[0]:
        if DATA_AVAILABLE:
            with st.spinner("차트 로딩 중..."):
                df = fetcher.get_korea_stock("005930", period=selected_period)
                if df is not None and not df.empty:
                    st.line_chart(df['Close'])
                    
                    # 추가 정보
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("최고가", f"{df['High'].max():,.0f}원")
                    with col2:
                        st.metric("최저가", f"{df['Low'].min():,.0f}원")
                    with col3:
                        st.metric("평균가", f"{df['Close'].mean():,.0f}원")
                    with col4:
                        change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                        st.metric("기간 수익률", f"{change_pct:+.2f}%")
                else:
                    st.warning("차트 데이터를 불러올 수 없습니다.")
        else:
            st.info("데이터 수집 모듈을 로드할 수 없습니다.")
    
    with chart_tabs[1]:
        if DATA_AVAILABLE:
            with st.spinner("차트 로딩 중..."):
                df = fetcher.get_us_stock("AAPL", period=selected_period)
                if df is not None and not df.empty:
                    st.line_chart(df['Close'])
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("최고가", f"${df['High'].max():.2f}")
                    with col2:
                        st.metric("최저가", f"${df['Low'].min():.2f}")
                    with col3:
                        st.metric("평균가", f"${df['Close'].mean():.2f}")
                    with col4:
                        change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                        st.metric("기간 수익률", f"{change_pct:+.2f}%")
                else:
                    st.warning("차트 데이터를 불러올 수 없습니다.")
        else:
            st.info("데이터 수집 모듈을 로드할 수 없습니다.")
    
    with chart_tabs[2]:
        if DATA_AVAILABLE:
            with st.spinner("차트 로딩 중..."):
                # 암호화폐는 limit으로 조정
                period_limits = {
                    "1mo": 30,
                    "3mo": 90,
                    "6mo": 180,
                    "1y": 365
                }
                limit = period_limits[selected_period]
                
                df = fetcher.get_crypto("BTC/USDT", timeframe="1d", limit=limit)
                if df is not None and not df.empty:
                    st.line_chart(df['Close'])
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("최고가", f"${df['High'].max():,.2f}")
                    with col2:
                        st.metric("최저가", f"${df['Low'].min():,.2f}")
                    with col3:
                        st.metric("평균가", f"${df['Close'].mean():,.2f}")
                    with col4:
                        change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                        st.metric("기간 수익률", f"{change_pct:+.2f}%")
                else:
                    st.warning("차트 데이터를 불러올 수 없습니다.")
        else:
            st.info("데이터 수집 모듈을 로드할 수 없습니다.")
    
    st.markdown("---")
    
    # 탭 메뉴
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈", "🔍 종목 발굴", "📈 매매 신호", "⚙️ 설정"])
    
    with tab1:
        st.header("환영합니다! 👋")
        
        st.success("""
        **현재 상태: 2단계 진행 중! ✅**
        
        실시간 데이터 수집이 작동하고 있습니다!
        """)
        
        st.info("""
        ### 완료된 기능:
        1. ✅ 기본 환경 설정
        2. ✅ 실시간 데이터 수집
        3. ✅ 가격 차트 표시
        
        ### 다음 단계:
        4. ⏳ 종목 발굴 기능
        5. ⏳ 매매 신호 생성
        """)
        
        # 지원 시장
        st.subheader("지원 시장")
        markets = st.columns(3)
        
        with markets[0]:
            st.info("🇰🇷 **한국 주식**\n\nKOSPI, KOSDAQ\n\n✅ 실시간 연동")
        
        with markets[1]:
            st.info("🇺🇸 **미국 주식**\n\nNYSE, NASDAQ\n\n✅ 실시간 연동")
        
        with markets[2]:
            st.info("💰 **크립토시장**\n\nBybit\n\n✅ 실시간 연동")
    
    with tab2:
        st.header("🔍 종목 발굴 시스템")
        st.warning("⏳ 개발 예정")
        
        st.markdown("""
        ### 예정된 기능:
        
        1. **임원 매수 추적**
           - CEO, CFO 등 내부자 거래 모니터링
           - 유망 종목 탐색 및 신호 포착
           
        2. **애널리스트 평가**
           - 목표 주가 상향 추적
           - 투자의견 변경 알림 제공
           
        3. **시장 유동성 분석**
           - M2 통화량 모니터링
           - 역레포 잔액 분석
        
        ### 📝 참고사항:
        - 주식 시장 휴장일에는 최근 거래일 데이터로 분석합니다
        - 공휴일에는 마지막 시장 개장일의 정보를 표시합니다
        """)
    
    with tab3:
        st.header("📈 매매 신호 시스템")
        st.warning("⏳ 개발 예정")
        
        st.markdown("""
        ### 예정된 기능:
        
        1. **기술적 지표**
           - RSI (과매수/과매도 지표)
           - 이동평균선 (추세 확인)
           - MACD (모멘텀 지표)
           
        2. **머신러닝 신호**
           - 로렌츠한 분류 (AI 패턴 인식)
           - KNN 알고리즘 (유사 패턴 분석)
           
        3. **자동 알림**
           - 매수 타이밍 알림
           - 손절/익절 알림
        """)
    
    with tab4:
        st.header("⚙️ 시스템 설정")
        st.subheader("시스템 정보")
        st.code(f"Python 버전: {sys.version.split()[0]}")
        st.code(f"작업 디렉토리: {os.getcwd()}")
        st.code(f"데이터 수집: {'✅ 정상' if DATA_AVAILABLE else '❌ 오류'}")
        
        st.subheader("알림 설정")
        notification = st.checkbox("알림 활성화", value=True)
        if notification:
            st.multiselect("알림 방법 선택", ["콘솔", "텔레그램", "이메일"], default=["콘솔"])
        
        st.subheader("데이터 업데이트 주기")
        update_interval = st.selectbox("종목 발굴 업데이트", ["5분", "30분", "1시간", "1일"], index=3)
        
        st.subheader("데이터 수집 설정")
        st.info("**주식 시장 휴장 시**: 가장 최근 거래일의 데이터를 자동으로 사용합니다.")
        
        if st.button("🔄 데이터 새로고침"):
            st.rerun()
    
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: gray;"><small>AI 투자 분석 시스템 v2.0 (데이터 연동 완료!) | 모든 투자 판단은 본인 책임입니다</small></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
