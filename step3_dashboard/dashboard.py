"""
AI 투자 분석 시스템 - 메인 대시보드 (통합 전략 버전)
"""

import streamlit as st
from datetime import datetime
import sys
import os

# 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'step1_stock_finder'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'step2_trade_timing'))

try:
    from data_fetcher import DataFetcher
    from integrated_strategy import IntegratedStrategy
    DATA_AVAILABLE = True
except Exception as e:
    print(f"모듈 로드 오류: {e}")
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
    
    # 데이터 수집기 & 전략 초기화
    if DATA_AVAILABLE:
        fetcher = DataFetcher()
        strategy = IntegratedStrategy()
    
    # 시스템 상태
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="🟢 시스템 상태", value="정상", delta="가동 중")
    
    with col2:
        st.metric(label="📅 마지막 업데이트", value=datetime.now().strftime("%H:%M"))
    
    with col3:
        status = "✅ 통합 전략 로드됨" if DATA_AVAILABLE else "❌ 오류"
        st.metric(label="🎯 전략 상태", value=status)
    
    st.markdown("---")
    
    # 탭 메뉴
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 홈", 
        "📈 주식 분석", 
        "💰 코인 장기", 
        "⚡ 코인 단타",
        "⚙️ 설정"
    ])
    
    # ========================================
    # 홈 탭
    # ========================================
    with tab1:
        st.header("환영합니다! 👋")
        
        st.success("""
        **현재 상태: 3단계 완료! ✅**
        
        통합 매매 전략이 작동하고 있습니다!
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            ### 📈 주식 분석
            
            **기능:**
            - 단기/중기/장기 분석
            - RSI, MACD, 이동평균
            - 한국/미국 주식 지원
            
            **시간봉:** 일봉
            """)
        
        with col2:
            st.info("""
            ### 💰 코인 장기 분석
            
            **기능:**
            - BTC 대비 상대강도
            - VWMA 100일선 타점
            - 종합 점수 판단
            
            **시간봉:** 일봉
            """)
        
        with col3:
            st.info("""
            ### ⚡ 코인 단타 분석
            
            **기능:**
            - RSI 과매도 신호 포착
            - 5분봉 50선 진입
            - 정밀한 익절/손절
            
            **시간봉:** 5분봉
            """)
        
        st.markdown("---")
        
        st.subheader("📋 완료된 기능")
        
        progress_col1, progress_col2 = st.columns(2)
        
        with progress_col1:
            st.markdown("""
            ✅ **1단계: 기본 환경**
            - 폴더 구조
            - 패키지 설치
            - 실행 파일
            
            ✅ **2단계: 데이터 수집**
            - 한국 주식 (삼성전자 등)
            - 미국 주식 (Apple 등)
            - 암호화폐 (BTC, ETH 등)
            - 실시간 가격 차트
            
            ✅ **3단계: 매매 전략**
            - 기술적 지표 (RSI, MACD)
            - 불장단타왕 전략
            - 통합 분석 시스템
            """)
        
        with progress_col2:
            st.markdown("""
            ⏳ **4단계: 대시보드 완성**
            - 실시간 신호 표시
            - 알림 기능
            
            ⏳ **5단계: 종목 발굴**
            - 임원 매수 추적
            - 애널리스트 평가
            
            ⏳ **6단계: 고급 기능**
            - 시장 유동성 분석
            - 백테스팅
            - 자동 매매 연동
            """)
        
        # 진행률 표시
        st.markdown("---")
        st.subheader("📊 전체 진행률")
        st.progress(0.35)
        st.caption("35% 완료 (3.5/10 단계)")
    
    # ========================================
    # 주식 분석 탭
    # ========================================
    with tab2:
        st.header("📈 주식 분석 (일봉)")
        
        if not DATA_AVAILABLE:
            st.error("데이터 모듈을 로드할 수 없습니다.")
            return
        
        # 입력
        col1, col2 = st.columns(2)
        
        with col1:
            market = st.selectbox("시장 선택", ["korea", "us"])
        
        with col2:
            if market == "korea":
                ticker = st.text_input("종목 코드", value="005930", help="예: 005930 (삼성전자)")
            else:
                ticker = st.text_input("티커", value="AAPL", help="예: AAPL (Apple)").upper()
        
        if st.button("🔍 분석 시작", key="stock_analyze"):
            with st.spinner("분석 중..."):
                try:
                    result = strategy.analyze_stock(fetcher, ticker, market)
                    
                    if result and result['analysis']:
                        st.success(f"✅ {ticker} 분석 완료!")
                        
                        # 결과 표시
                        for period_name, analysis in result['analysis'].items():
                            if analysis:
                                with st.expander(f"📅 {period_name} 분석 ({analysis['period']})", expanded=True):
                                    
                                    signal_col1, signal_col2, signal_col3 = st.columns(3)
                                    
                                    with signal_col1:
                                        st.metric(
                                            "종합 판단", 
                                            analysis['overall'],
                                            delta=f"신호 {analysis['buy_score']}/4"
                                        )
                                    
                                    with signal_col2:
                                        rsi_value = analysis['signals']['RSI']['value']
                                        st.metric("RSI", f"{rsi_value:.1f}", delta=analysis['signals']['RSI']['signal'])
                                    
                                    with signal_col3:
                                        ma_signal = analysis['signals']['MA_Cross']['signal']
                                        st.metric("이동평균", ma_signal)
                                    
                                    # 상세 정보
                                    st.markdown("**📊 상세 지표:**")
                                    st.write(f"- MACD: {analysis['signals']['MACD']['signal']}")
                                    st.write(f"- 볼린저밴드: {analysis['signals']['Bollinger']['signal']}")
                    else:
                        st.error("데이터를 가져올 수 없습니다. 티커를 확인하세요.")
                
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    
    # ========================================
    # 코인 장기 탭
    # ========================================
    with tab3:
        st.header("💰 코인 장기 분석 (일봉)")
        
        if not DATA_AVAILABLE:
            st.error("데이터 모듈을 로드할 수 없습니다.")
            return
        
        coin = st.text_input("코인 입력", value="ETH", help="예: ETH, BTC, SOL, XRP 등").upper()
        
        if st.button("🔍 분석 시작", key="crypto_long"):
            symbol = f"{coin}/USDT"
            
            with st.spinner("분석 중..."):
                try:
                    result = strategy.analyze_crypto_longterm(fetcher, symbol)
                    
                    if result:
                        st.success(f"✅ {coin} 분석 완료!")
                        
                        # 종합 판단
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("최종 판단", result['final'])
                        
                        with col2:
                            st.metric("점수", f"{result['score']}/5")
                        
                        with col3:
                            strength_emoji = {
                                '강함': '💪🟢',
                                '약함': '📉🔴',
                                '중립': '⚪'
                            }
                            st.metric(
                                "상대강도", 
                                result['strength']['strength'],
                                delta=f"{result['strength']['score']:+.2f}%"
                            )
                        
                        # 상세 정보
                        st.markdown("---")
                        
                        detail_col1, detail_col2 = st.columns(2)
                        
                        with detail_col1:
                            st.markdown("**📊 상대강도 분석**")
                            st.write(f"- BTC 200일선 대비: {result['strength']['btc_distance']:+.2f}%")
                            st.write(f"- {coin} 200일선 대비: {result['strength']['alt_distance']:+.2f}%")
                        
                        with detail_col2:
                            st.markdown("**📍 진입 타점**")
                            st.write(f"- 현재가: ${result['entry']['current_price']:,.2f}")
                            st.write(f"- VWMA 100: ${result['entry']['vwma_100']:,.2f}")
                            st.write(f"- 거리: {result['entry']['distance_pct']:+.2f}%")
                        
                        # 판단 근거
                        st.markdown("---")
                        st.markdown("**📝 판단 근거:**")
                        for reason in result['reasons']:
                            st.write(reason)
                    
                    else:
                        st.error("데이터를 가져올 수 없습니다.")
                
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    
    # ========================================
    # 코인 단타 탭
    # ========================================
    with tab4:
        st.header("⚡ 코인 단타 분석 (5분봉)")
        
        if not DATA_AVAILABLE:
            st.error("데이터 모듈을 로드할 수 없습니다.")
            return
        
        st.warning("⚠️ 5분봉 분석은 실시간 데이터가 필요합니다. 단타 매매는 높은 리스크를 동반합니다.")
        
        coin = st.text_input("코인 입력", value="BTC", key="scalp_coin", help="예: BTC, ETH, SOL 등").upper()
        
        if st.button("⚡ 분석 시작", key="crypto_scalp"):
            symbol = f"{coin}/USDT"
            
            with st.spinner("5분봉 데이터 분석 중..."):
                try:
                    result = strategy.analyze_scalping(fetcher, symbol)
                    
                    if result:
                        st.success(f"✅ {coin} 단타 분석 완료!")
                        
                        # 현재 상태
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("현재가", f"${result['current_price']:,.2f}")
                        
                        with col2:
                            rsi_color = "🔴" if result['rsi_1h'] > 70 else "🟢" if result['rsi_1h'] < 30 else "⚪"
                            st.metric("1시간 RSI", f"{rsi_color} {result['rsi_1h']:.1f}")
                        
                        with col3:
                            st.metric("50선 기울기", result['slope_50'])
                        
                        with col4:
                            gap_color = "🔴" if result['gap_to_50'] < -3 else "🟢" if abs(result['gap_to_50']) < 1 else "⚪"
                            st.metric("50선 이격도", f"{gap_color} {result['gap_to_50']:+.2f}%")
                        
                        st.markdown("---")
                        
                        # 신호
                        signal_col1, signal_col2 = st.columns(2)
                        
                        with signal_col1:
                            if result['entry_signal']:
                                st.success(f"🟢 **진입 신호: {result['entry_type']}**")
                                for reason in result['entry_reason']:
                                    st.write(f"✓ {reason}")
                            else:
                                st.info("⚪ 진입 신호 없음 - 대기")
                        
                        with signal_col2:
                            if result['exit_signals']:
                                st.warning(f"🔴 **청산 신호: {len(result['exit_signals'])}개**")
                                for signal in result['exit_signals']:
                                    st.write(f"• {signal['level']}: ${signal['target']:,.2f}")
                                    st.caption(f"  {signal['reason']}")
                            else:
                                st.info("포지션 유지")
                        
                        # 주요 가격대
                        st.markdown("---")
                        st.markdown("**📍 주요 가격대:**")
                        
                        price_col1, price_col2, price_col3 = st.columns(3)
                        
                        with price_col1:
                            st.write(f"50선: ${result['sma_50_5m']:,.2f}")
                        
                        with price_col2:
                            st.write(f"100 VWMA: ${result['vwma_100_5m']:,.2f}")
                        
                        with price_col3:
                            st.write(f"200선: ${result['sma_200_5m']:,.2f}")
                    
                    else:
                        st.error("데이터를 가져올 수 없습니다.")
                
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    
    # ========================================
    # 설정 탭
    # ========================================
    with tab5:
        st.header("⚙️ 시스템 설정")
        
        st.subheader("시스템 정보")
        st.code(f"Python 버전: {sys.version.split()[0]}")
        st.code(f"작업 디렉토리: {os.getcwd()}")
        st.code(f"전략 모듈: {'✅ 로드됨' if DATA_AVAILABLE else '❌ 오류'}")
        
        st.markdown("---")
        
        st.subheader("📁 파일 구조")
        st.code("""
investment_local/
├── step1_stock_finder/
│   └── data_fetcher.py
├── step2_trade_timing/
│   ├── technical_indicators.py
│   ├── bull_market_strategy.py
│   └── integrated_strategy.py
├── step3_dashboard/
│   └── dashboard.py (현재 파일)
├── config/
├── data/
├── logs/
├── requirements.txt
└── start.bat
        """)
        
        st.markdown("---")
        
        st.subheader("🔄 데이터 새로고침")
        if st.button("새로고침"):
            st.rerun()
        
        st.markdown("---")
        
        st.subheader("📊 진행 상황")
        st.progress(0.35)
        st.write("35% 완료 (3.5/10 단계)")
        
        with st.expander("단계별 상세"):
            st.markdown("""
            ✅ 1단계: 기본 환경 설정
            ✅ 2단계: 실시간 데이터 수집
            ✅ 3단계: 매매 전략 구현
            ⏳ 4단계: 대시보드 완성
            ⏳ 5단계: 종목 발굴
            ⏳ 6단계: 애널리스트 평가
            ⏳ 7단계: 시장 유동성
            ⏳ 8단계: 자동 알림
            ⏳ 9단계: 백테스팅
            ⏳ 10단계: 최종 완성
            """)
    
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: gray;"><small>AI 투자 분석 시스템 v3.0 (통합 전략 완료!) | 모든 투자 판단은 본인 책임입니다</small></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
