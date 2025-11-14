"""
AI 투자 분석 시스템 - 임원 매수 추적 대시보드
기존 dashboard.py와 통합
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 페이지 설정 (성능 최적화)
st.set_page_config(
    page_title="AI 투자 분석 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/investment-analyzer',
        'Report a bug': None,
        'About': "AI 기반 투자 분석 시스템 v1.0"
    }
)

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_manager import DataManager
from modules.screener.insider_tracker import InsiderTracker
from modules.screener.analyst_ratings import AnalystTracker
from modules.screener.stock_screener import StockScreener
from modules.macro.market_indicators import MarketIndicators

# 페이지 설정
st.set_page_config(
    page_title="AI 투자 분석 - 임원 매수 추적",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 초기화

# ======================================
# 🎨 공통 함수
# ======================================

def get_signal_emoji(score: float) -> str:
    """점수에 따른 이모지"""
    if score >= 70:
        return "🟢"
    elif score >= 50:
        return "🟡"
    elif score >= 30:
        return "🔴"
    else:
        return "⚫"

def get_signal_text(score: float) -> str:
    """점수에 따른 텍스트"""
    if score >= 70:
        return "강한 매수"
    elif score >= 50:
        return "중립"
    elif score >= 30:
        return "주의"
    else:
        return "신호없음"

def format_signal(score: float) -> str:
    """점수를 신호로 포맷"""
    emoji = get_signal_emoji(score)
    text = get_signal_text(score)
    return f"{emoji} {text}"

def show_loading(message: str):
    """로딩 메시지 표시"""
    return st.spinner(f"⏳ {message}")

@st.cache_resource
def init_system():
    """시스템 초기화"""
    return {
        'data_manager': DataManager(),
        'insider_tracker': InsiderTracker(),
        'analyst_tracker': AnalystTracker(),
        'stock_screener': StockScreener(InsiderTracker(), AnalystTracker()),
        'market_indicators': MarketIndicators()
    }

system = init_system()

# 세션 상태 초기화 (캐싱)
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = {}
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = {}

# 사이드바
with st.sidebar:
    st.title("🎯 종목 분석")
    
    # 도움말
    with st.expander("❓ 사용 방법", expanded=False):
        st.markdown("""
        **1️⃣ 종목 검색**
        - 종목 코드를 입력하세요
        - 미국: AAPL, MSFT, NVDA
        - 한국: 005930.KS, 035420.KS
        
        **2️⃣ 분석 확인**
        - 대시보드에서 결과 확인
        - 각 탭에서 상세 분석
        
        **3️⃣ 관심 종목 추가**
        - 마음에 드는 종목을 저장
        - 나중에 빠르게 다시 분석
        
        **💡 자동 발굴:**
        - '자동 종목 발굴' 탭 이용
        - AI가 유망 종목 추천
        """)
    
    st.markdown("---")
    
    # 종목 검색 (메인)
    st.subheader("🔍 종목 검색")
    
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_input = st.text_input(
            "종목 코드 입력",
            placeholder="예: NVDA, TSLA, 005930.KS",
            label_visibility="collapsed",
            help="분석할 종목 코드를 입력하세요"
        )
    
    with search_col2:
        search_btn = st.button("🔍", use_container_width=True, help="분석 시작", type="primary")
    
    # 검색 실행
    if search_btn and search_input:
        st.session_state.selected_ticker = search_input.upper()
        st.session_state.ticker_changed = True
        st.success(f"✅ {search_input.upper()} 분석!")
        st.rerun()
    
    # 선택된 종목
    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = "AAPL"
    
    selected_ticker = st.session_state.selected_ticker
    
    # 현재 분석 중인 종목 표시
    with st.container():
        st.markdown("**📊 현재 분석 중:**")
        st.info(f"### {selected_ticker}")
        
        # 종목 정보 미리보기
        try:
            stock = yf.Ticker(selected_ticker)
            info = stock.info
            
            if info:
                st.caption(f"**{info.get('longName', selected_ticker)}**")
                current_price = info.get('currentPrice', 0)
                if current_price > 0:
                    prev_close = info.get('previousClose', current_price)
                    change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                    
                    st.metric(
                        "현재가",
                        f"${current_price:.2f}",
                        f"{change_pct:+.2f}%"
                    )
                
                sector = info.get('sector', 'N/A')
                if sector != 'N/A':
                    st.caption(f"섹터: {sector}")
        except:
            pass
    
    st.markdown("---")
    
    # 관심 종목 관리
    st.subheader("⭐ 관심 종목")
    
    # 세션 상태에 관심 종목 저장
    if 'favorite_tickers' not in st.session_state:
        st.session_state.favorite_tickers = ["AAPL", "MSFT", "GOOGL"]
    
    # 현재 종목을 관심 목록에 추가
    if selected_ticker not in st.session_state.favorite_tickers:
        if st.button(f"⭐ {selected_ticker} 관심 종목 추가", use_container_width=True, type="primary"):
            st.session_state.favorite_tickers.append(selected_ticker)
            st.success(f"✅ {selected_ticker} 추가됨!")
            st.rerun()
    else:
        st.success(f"✅ 이미 관심 종목에 있습니다")
    
    # 관심 종목 리스트
    if st.session_state.favorite_tickers:
        st.markdown("**저장된 종목:**")
        
        for ticker in st.session_state.favorite_tickers:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button(ticker, use_container_width=True, key=f"fav_{ticker}"):
                    st.session_state.selected_ticker = ticker
                    st.session_state.ticker_changed = True
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{ticker}", help="삭제"):
                    st.session_state.favorite_tickers.remove(ticker)
                    st.rerun()
    
    st.markdown("---")
    
    # 분석 기간
    st.subheader("📅 분석 기간")
    
    period = st.select_slider(
        "차트 기간",
        options=["1mo", "3mo", "6mo", "1y", "2y"],
        value="6mo",
        help="가격 차트 표시 기간"
    )
    
    st.markdown("---")
    
    # 설정
    st.markdown("## ⚙️ 설정")
    
    if st.button("🗑️ 캐시 초기화", use_container_width=True):
        system['data_manager'].clear_cache()
        st.cache_data.clear()
        st.success("캐시 초기화 완료!")
        st.rerun()
        
    # 분석할 종목 선택 (기본값)
    if '관심_종목' in locals() and 관심_종목:
        selected_ticker = 관심_종목[0]
    else:
        selected_ticker = "AAPL"    

# 메인 헤더
st.markdown('<div class="main-header">📊 AI 투자 분석 시스템</div>', unsafe_allow_html=True)
st.markdown("**임원 매수 추적** - SEC Form 4 분석")
st.markdown("---")

# 진행률
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.progress(0.8, "전체 진행률: 80% (8/10 단계 완료)")

with col2:
    st.metric("완료 단계", "8/10", "+1")

with col3:
    st.metric("다음 단계", "UI 개선")

st.markdown("---")

# 탭 메뉴
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 대시보드",
    "🔍 자동 종목 발굴 ⭐⭐⭐",
    "🌍 시장 분석 ⭐",
    "🎯 임원 매수 추적",
    "📊 애널리스트 평가",
    "📈 기존 대시보드"
])

# 탭 1: 대시보드
with tab1:
    st.header("📊 종합 대시보드")
    
    # 선택된 종목 확인
    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = "AAPL"
    
    selected_ticker = st.session_state.selected_ticker
    
    st.info(f"🎯 **분석 중인 종목: {selected_ticker}**")
    
    with st.spinner(f"📊 {selected_ticker} 데이터 로딩 중..."):
        stock_info = system['data_manager'].get_stock_info(selected_ticker)
        stock_data = system['data_manager'].get_stock_data(selected_ticker, period)
    
    # 종목 정보
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("종목명", stock_info.get('name', selected_ticker)[:20])
    
    with col2:
        current_price = stock_info.get('current_price', 0)
        st.metric(
            "현재가",
            f"${current_price:,.2f}" if current_price else "N/A"
        )
    
    with col3:
        market_cap = stock_info.get('market_cap', 0)
        st.metric(
            "시가총액",
            f"${market_cap/1e9:.1f}B" if market_cap else "N/A"
        )
    
    with col4:
        st.metric("섹터", stock_info.get('sector', 'N/A'))
    
    st.markdown("---")
    
    # 차트
    if not stock_data.empty:
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=stock_data.index,
            open=stock_data['시가'],
            high=stock_data['고가'],
            low=stock_data['저가'],
            close=stock_data['종가'],
            name='가격'
        ))
        
        fig.update_layout(
            title=f"{stock_info.get('name', selected_ticker)} 가격 차트",
            xaxis_title="날짜",
            yaxis_title="가격",
            height=500,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"⚠️ {selected_ticker} 데이터를 가져올 수 없습니다")

# 탭 2: 자동 종목 발굴
with tab2:
    st.header("🔍 자동 종목 발굴")
    st.markdown("**프로그램이 자동으로 유망 종목을 찾아드립니다!**")
    st.markdown("임원 매수 + 애널리스트 평가 + 기술적 모멘텀을 종합 분석합니다.")
    
    st.info("""
    **📊 종합 점수 계산:**
    - 🟢 강한 매수 신호 (70점 이상)
    - 🟡 중립적 신호 (50~69점)
    - 🔴 주의 신호 (30~49점)
    - ⚫ 신호 없음 (30점 미만)
    
    **점수 구성:**
    - 애널리스트 평가 (40%)
    - 임원 매수 신호 (30%)
    - 기술적 모멘텀 (30%)
    """)
    
    st.markdown("---")
    
    # 버튼
col1, col2, col3 = st.columns(3)

with col1:
    us_btn = st.button(
        "🇺🇸 미국 주식 TOP 20",
        use_container_width=True,
        type="primary",
        key="us_scan",
        help="S&P 100 종목 중 TOP 20 분석 (약 1~2분 소요)"
    )

with col2:
    kr_btn = st.button(
        "🇰🇷 한국 주식 TOP 10",
        use_container_width=True,
        key="kr_scan",
        help="주요 한국 종목 TOP 10 분석 (약 30초 소요)"
    )

with col3:
    if st.button(
        "🗑️ 결과 초기화",
        use_container_width=True,
        key="clear_scan",
        help="스캔 결과를 지우고 새로 시작"
    ):
        st.session_state.scan_results = {}
        st.rerun()
    
    # 미국 주식 스캔
    if us_btn:
        st.markdown("### 🇺🇸 미국 주식 분석 중...")
    
        # 진행률 표시
        progress_text = st.empty()
        progress_bar = st.progress(0)
    
        progress_text.markdown("**⏳ S&P 100 종목 스캔 시작...**")
    
        try:
            with show_loading("데이터 수집 및 분석 중"):
                df = system['stock_screener'].quick_scan_us(top_n=20, progress_bar=progress_bar)
        
            progress_bar.empty()
            progress_text.empty()
        
            if not df.empty:
                # 세션에 저장
                st.session_state.scan_results['us'] = df
            
                st.success(f"✅ {len(df)}개 유망 종목 발견! (분석 시간: 1~2분)")
                
                # 상위 3개 하이라이트
                top3_col1, top3_col2, top3_col3 = st.columns(3)
                
                with top3_col1:
                    st.metric("🥇 1위", df.iloc[0]['ticker'], 
                             f"{df.iloc[0]['total_score']:.0f}점")
                
                with top3_col2:
                    if len(df) > 1:
                        st.metric("🥈 2위", df.iloc[1]['ticker'], 
                                 f"{df.iloc[1]['total_score']:.0f}점")
                
                with top3_col3:
                    if len(df) > 2:
                        st.metric("🥉 3위", df.iloc[2]['ticker'], 
                                 f"{df.iloc[2]['total_score']:.0f}점")
                
                st.markdown("---")
                
                # 결과 테이블
                st.subheader("📊 전체 순위")

                # 신호 이모지 추가
                df['signal_emoji'] = df['total_score'].apply(get_signal_emoji)
                df['signal_full'] = df['total_score'].apply(format_signal)

                st.dataframe(
                    df[['rank', 'ticker', 'name', 'total_score', 'signal_full', 
                        'analyst_score', 'insider_score', 'technical_score']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "rank": st.column_config.NumberColumn("순위", width="small"),
                        "ticker": st.column_config.TextColumn("티커", width="small"),
                        "name": st.column_config.TextColumn("종목명", width="medium"),
                        "total_score": st.column_config.ProgressColumn(
                            "종합 점수",
                            format="%.1f",
                            min_value=0,
                            max_value=100,
                            width="medium"
                        ),
                        "signal_full": st.column_config.TextColumn("신호", width="small"),
                        "analyst_score": st.column_config.NumberColumn("애널", format="%.0f", width="small"),
                        "insider_score": st.column_config.NumberColumn("임원", format="%.0f", width="small"),
                        "technical_score": st.column_config.NumberColumn("기술", format="%.0f", width="small")
                    }
                )
                
                # 사용 팁
                st.markdown("---")
                st.info("""
                **💡 사용 팁:**
                1. 종합 점수가 높은 종목을 주목하세요
                2. 여러 지표가 고르게 높은 종목이 좋습니다
                3. 신호가 🟢인 종목을 우선 검토하세요
                4. 사이드바에서 종목을 선택하여 상세 분석하세요
                """)
            
            else:
                st.warning("⚠️ 데이터 수집 실패. 잠시 후 다시 시도해주세요.")
        
        except Exception as e:
            progress_bar.empty()
            st.error(f"❌ 오류 발생: {str(e)}")
    
    # 한국 주식 스캔
    if kr_btn:
        st.markdown("### 🇰🇷 한국 주식 분석 중...")
        st.warning("⏰ 주요 종목 스캔 중... 잠시만 기다려주세요!")
        
        progress_bar = st.progress(0, "스캔 준비 중...")
        
        try:
            df = system['stock_screener'].quick_scan_korea(top_n=10, progress_bar=progress_bar)
            
            progress_bar.empty()
            
            if not df.empty:
                st.success(f"✅ {len(df)}개 유망 종목 발견!")
                
                # 상위 3개
                top3_col1, top3_col2, top3_col3 = st.columns(3)
                
                with top3_col1:
                    st.metric("🥇 1위", df.iloc[0]['name'], 
                             f"{df.iloc[0]['total_score']:.0f}점")
                
                with top3_col2:
                    if len(df) > 1:
                        st.metric("🥈 2위", df.iloc[1]['name'], 
                                 f"{df.iloc[1]['total_score']:.0f}점")
                
                with top3_col3:
                    if len(df) > 2:
                        st.metric("🥉 3위", df.iloc[2]['name'], 
                                 f"{df.iloc[2]['total_score']:.0f}점")
                
                st.markdown("---")
                
                # 결과 테이블
                st.subheader("📊 전체 순위")
                
                st.dataframe(
                    df[['rank', 'ticker', 'name', 'total_score', 'signal', 'technical_score']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "rank": "순위",
                        "ticker": "티커",
                        "name": "종목명",
                        "total_score": st.column_config.NumberColumn("종합 점수", format="%.1f"),
                        "signal": "신호",
                        "technical_score": st.column_config.NumberColumn("기술 점수", format="%.0f")
                    }
                )
                
                st.markdown("---")
                st.info("""
                **💡 참고:**
                한국 주식은 SEC 데이터가 없어 애널리스트/임원 점수가 제외됩니다.
                기술적 분석 점수를 중심으로 평가합니다.
                """)
            
            else:
                st.warning("⚠️ 데이터 수집 실패")
        
        except Exception as e:
            progress_bar.empty()
            st.error(f"❌ 오류 발생: {str(e)}")
    
    # 안내
    if not us_btn and not kr_btn:
        st.info("👆 위의 버튼을 눌러 자동 종목 발굴을 시작하세요!")

# 탭 3: 시장 분석
with tab3:
    st.header("🌍 시장 분석")
    st.markdown("**거시 경제 지표로 시장 전체의 방향성을 파악합니다**")
    st.markdown("VIX 공포 지수와 M2 통화량을 분석하여 투자 타이밍을 판단합니다.")
    
    st.markdown("---")
    
    # 분석 버튼
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 시장 전체의 흐름을 파악하여 투자 전략을 수립하세요")
    
    with col2:
        market_btn = st.button("🔍 분석 시작", use_container_width=True, type="primary", key="market_analysis")
    
    # 분석 실행
    if market_btn:
        with st.spinner("시장 지표 분석 중..."):
            analysis = system['market_indicators'].analyze_market_timing()
        
        st.success("✅ 분석 완료!")
        
        # 종합 판단
        st.markdown("---")
        st.subheader("🎯 종합 시장 판단")
        
        judge_col1, judge_col2 = st.columns([1, 2])
        
        with judge_col1:
            # 점수 게이지
            score = analysis['score']
            
            if score >= 70:
                gauge_color = "green"
            elif score >= 50:
                gauge_color = "blue"
            elif score >= 30:
                gauge_color = "orange"
            else:
                gauge_color = "red"
            
            st.metric("시장 점수", f"{score}/100", analysis['timing'])
        
        with judge_col2:
            st.markdown(f"### {analysis['timing']}")
            st.info(analysis['recommendation'])
            
            st.markdown("**📊 주요 시그널:**")
            for signal in analysis['signals']:
                st.markdown(f"- {signal}")
        
        st.markdown("---")
        
        # VIX 분석
        st.subheader("📊 VIX 공포 지수")
        
        vix_data = analysis['vix_data']
        
        vix_col1, vix_col2 = st.columns([1, 1])
        
        with vix_col1:
            st.metric(
                "현재 VIX",
                f"{vix_data['current']:.2f}",
                vix_data['sentiment']
            )
            st.metric("1개월 평균", f"{vix_data['avg_1m']:.2f}")
            
            st.markdown(f"**해석:** {vix_data['interpretation']}")
        
        with vix_col2:
            # VIX 차트
            if not vix_data['data'].empty:
                import plotly.graph_objects as go
                
                fig_vix = go.Figure()
                
                fig_vix.add_trace(go.Scatter(
                    x=vix_data['data'].index,
                    y=vix_data['data']['Close'],
                    mode='lines',
                    name='VIX',
                    line=dict(color='red', width=2)
                ))
                
                # 기준선
                fig_vix.add_hline(y=20, line_dash="dash", line_color="orange", 
                                 annotation_text="불안 기준선 (20)")
                fig_vix.add_hline(y=30, line_dash="dash", line_color="red", 
                                 annotation_text="공포 기준선 (30)")
                
                fig_vix.update_layout(
                    title="VIX 추이 (최근 1개월)",
                    xaxis_title="날짜",
                    yaxis_title="VIX",
                    height=300
                )
                
                st.plotly_chart(fig_vix, use_container_width=True)
        
        st.markdown("---")
        
        # M2 분석
        st.subheader("💰 M2 통화량")
        
        m2_data = analysis['m2_data']
        
        if m2_data['current'] > 0:
            m2_col1, m2_col2 = st.columns(2)
            
            with m2_col1:
                st.metric(
                    "현재 M2",
                    f"${m2_data['current']:.1f}B",
                    f"{m2_data['change_pct']:+.2f}%"
                )
                st.metric("기준일", m2_data['date'])
            
            with m2_col2:
                st.markdown(f"**상태:** {m2_data['sentiment']}")
                st.info(m2_data['interpretation'])
        else:
            st.warning("""
            ⚠️ M2 데이터를 가져올 수 없습니다.
            
            **FRED API 키 설정 방법:**
            1. https://fred.stlouisfed.org/ 접속
            2. 무료 계정 생성
            3. API 키 발급
            4. config/settings.yaml 파일에 추가
            
            현재는 VIX 지수만으로 분석합니다.
            """)
        
        st.markdown("---")
        
        # 가이드
        st.subheader("💡 해석 가이드")
        
        guide_col1, guide_col2 = st.columns(2)
        
        with guide_col1:
            st.markdown("""
            **📊 VIX 공포 지수:**
            - 0~15: 😊 안정 (매수 적기)
            - 15~20: 😐 보통 (정상)
            - 20~30: 😰 불안 (신중)
            - 30+: 😱 공포 (방어)
            """)
        
        with guide_col2:
            st.markdown("""
            **💰 M2 통화량:**
            - 증가: 🟢 유동성 확대 (긍정)
            - 보합: 🟡 안정적 (중립)
            - 감소: 🔴 유동성 축소 (부정)
            """)
        
        # 업데이트 시간
        st.caption(f"🕐 마지막 업데이트: {vix_data['last_updated']}")
    
    else:
        st.info("👆 위의 '분석 시작' 버튼을 눌러주세요")

# 탭 4: 임원 매수 추적
# 탭 4: 임원 매수 추적
with tab4:
    st.header("🎯 임원 매수 추적")
    
    # 선택된 종목 사용
    selected_ticker = st.session_state.get('selected_ticker', 'AAPL')
    
    st.markdown("**임원들이 자기 회사 주식을 살 때는 내부 정보가 있기 때문입니다!**")
    st.markdown("SEC Form 4 데이터를 분석하여 임원 매수 패턴을 추적합니다.")
    
    st.markdown("---")
    
    # 분석 버튼
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info("💡 미국 주식만 지원됩니다 (SEC 데이터)")
    
    with col2:
        insider_months = st.selectbox("조회 기간", [1, 3, 6, 12], index=1)
    
    with col3:
        analyze_btn = st.button("🔍 분석 시작", use_container_width=True, type="primary")
    
    # 분석 실행
    if analyze_btn:
        if ".KS" in selected_ticker or ".KQ" in selected_ticker:
            st.error("❌ 한국 주식은 SEC 데이터가 없습니다. 미국 주식을 선택해주세요!")
        else:
            with st.spinner(f"{selected_ticker} 임원 거래 데이터 수집 중..."):
                insider_df = system['insider_tracker'].get_insider_trades(
                    selected_ticker.replace('.', '-'),
                    months=insider_months
                )
                
                if not insider_df.empty:
                    analysis = system['insider_tracker'].analyze_insider_sentiment(insider_df)
                    
                    st.success(f"✅ {len(insider_df)}개 임원 거래 발견!")
                    
                    # 신호 카드
                    signal_col1, signal_col2, signal_col3, signal_col4 = st.columns(4)
                    
                    with signal_col1:
                        st.metric("🎯 신호", analysis['signal'])
                    
                    with signal_col2:
                        st.metric("📊 점수", f"{analysis['score']}/100")
                    
                    with signal_col3:
                        st.metric("🔢 매수 횟수", f"{analysis['total_buys']}회")
                    
                    with signal_col4:
                        st.metric("💰 총 매수액", f"${analysis['total_value']/1e6:.1f}M")
                    
                    st.markdown("---")
                    
                    # 상세 데이터
                    st.subheader("📋 상세 거래 내역")
                    
                    display_df = insider_df.copy()
                    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
                    display_df['value'] = display_df['value'].apply(lambda x: f"${x:,.0f}")
                    display_df['shares'] = display_df['shares'].apply(lambda x: f"{x:,}")
                    display_df['price_per_share'] = display_df['price_per_share'].apply(lambda x: f"${x:.2f}")
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "date": "날짜",
                            "insider_name": "임원 이름",
                            "title": "직책",
                            "transaction_type": "거래 유형",
                            "shares": "주식 수",
                            "price_per_share": "주당 가격",
                            "value": "거래 금액"
                        }
                    )
                    
                    # 해석
                    st.markdown("---")
                    st.subheader("💡 해석")
                    
                    if analysis['score'] >= 70:
                        st.success("""
                        **🟢 강한 매수 신호**
                        - 임원들의 활발한 자사주 매수가 관찰됩니다
                        - 회사 내부 전망이 긍정적일 가능성이 높습니다
                        - 추가 기술적 분석과 함께 고려하세요
                        """)
                    elif analysis['score'] >= 50:
                        st.info("""
                        **🟡 중립적 신호**
                        - 일부 임원 매수가 있으나 강도가 약합니다
                        - 다른 지표와 함께 종합적으로 판단하세요
                        """)
                    else:
                        st.warning("""
                        **⚪ 약한 신호**
                        - 최근 임원 매수가 거의 없거나 미미합니다
                        - 이 지표만으로는 판단하기 어렵습니다
                        """)
                
                else:
                    st.warning(f"⚠️ 최근 {insider_months}개월간 임원 매수 데이터가 없습니다")
    else:
        st.info("👆 위의 '분석 시작' 버튼을 눌러주세요")

# 탭 5: 애널리스트 평가
with tab5:
    st.header("📊 애널리스트 평가")
    
    # 선택된 종목 사용
    selected_ticker = st.session_state.get('selected_ticker', 'AAPL')
    
    st.markdown("**월가 애널리스트들의 전문가 의견을 분석합니다!**")
    st.markdown("목표가 상향, 추천 등급 변화 등을 실시간으로 추적합니다.")
    
    # 신호 가이드
    st.info("""
    **📊 신호 해석:**
    - 🟢 강한 매수 신호 (70점 이상) → 매수 추천
    - 🟡 중립적 신호 (50~69점) → 관망
    - 🔴 약한 신호 (30~49점) → 주의 필요
    - ⚫ 신호 없음 (30점 미만) → 데이터 부족
    """)
    
    st.markdown("---")
    
    # 분석 버튼
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 미국 주식은 더 많은 데이터를 제공합니다")
    
    with col2:
        analyst_btn = st.button("🔍 분석 시작", use_container_width=True, type="primary", key="analyst_btn")
    
    # 분석 실행
    if analyst_btn:
        with st.spinner(f"{selected_ticker} 애널리스트 데이터 수집 중..."):
            analyst_data = system['analyst_tracker'].get_analyst_ratings(
                selected_ticker.replace('.KS', '').replace('.KQ', '')
            )
            
            if analyst_data['analyst_count'] > 0:
                analysis = system['analyst_tracker'].analyze_sentiment(analyst_data)
                
                st.success(f"✅ {analyst_data['analyst_count']}명의 애널리스트 의견 수집 완료!")
                
                # 신호 카드
                signal_col1, signal_col2, signal_col3, signal_col4 = st.columns(4)
                
                with signal_col1:
                    st.metric("🎯 신호", analysis['signal'])
                
                with signal_col2:
                    st.metric("📊 점수", f"{analysis['score']}/100")
                
                with signal_col3:
                    upside = analyst_data['target_price']['upside_percent']
                    st.metric("📈 상승 여력", f"{upside:.1f}%")
                
                with signal_col4:
                    st.metric("👥 애널리스트", f"{analyst_data['analyst_count']}명")
                
                st.markdown("---")
                
                # 목표가 정보
                st.subheader("🎯 목표가 분석")
                
                target_col1, target_col2 = st.columns(2)
                
                with target_col1:
                    # 목표가 차트
                    tp = analyst_data['target_price']
                    
                    fig_target = go.Figure()
                    
                    # 현재가
                    fig_target.add_trace(go.Bar(
                        name='현재가',
                        x=['가격'],
                        y=[tp['current']],
                        marker_color='lightblue'
                    ))
                    
                    # 평균 목표가
                    fig_target.add_trace(go.Bar(
                        name='평균 목표가',
                        x=['가격'],
                        y=[tp['target_mean']],
                        marker_color='green'
                    ))
                    
                    # 최고/최저 목표가
                    fig_target.add_trace(go.Scatter(
                        name='목표가 범위',
                        x=['가격', '가격'],
                        y=[tp['target_low'], tp['target_high']],
                        mode='markers',
                        marker=dict(size=10, color='orange'),
                        showlegend=True
                    ))
                    
                    fig_target.update_layout(
                        title="목표가 비교",
                        yaxis_title="가격 ($)",
                        height=400
                    )
                    
                    st.plotly_chart(fig_target, use_container_width=True)
                
                with target_col2:
                    st.markdown("### 📋 상세 정보")
                    
                    st.metric("현재가", f"${tp['current']:.2f}")
                    st.metric("평균 목표가", f"${tp['target_mean']:.2f}", 
                             f"{tp['upside_percent']:.1f}%")
                    st.metric("최고 목표가", f"${tp['target_high']:.2f}")
                    st.metric("최저 목표가", f"${tp['target_low']:.2f}")
                
                st.markdown("---")
                
                # 추천 분포
                st.subheader("👥 애널리스트 추천 분포")
                
                trend = analyst_data['trend']
                
                rec_col1, rec_col2 = st.columns(2)
                
                with rec_col1:
                    # 파이 차트
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['매수', '보유', '매도'],
                        values=[trend['buy'], trend['hold'], trend['sell']],
                        marker_colors=['green', 'yellow', 'red']
                    )])
                    
                    fig_pie.update_layout(
                        title="추천 등급 분포",
                        height=400
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with rec_col2:
                    st.markdown("### 📊 추천 통계")
                    
                    st.metric("매수", f"{trend['buy']}개", 
                             f"{trend['buy']/trend['total']*100:.0f}%" if trend['total'] > 0 else "0%")
                    st.metric("보유", f"{trend['hold']}개",
                             f"{trend['hold']/trend['total']*100:.0f}%" if trend['total'] > 0 else "0%")
                    st.metric("매도", f"{trend['sell']}개",
                             f"{trend['sell']/trend['total']*100:.0f}%" if trend['total'] > 0 else "0%")
                    st.metric("지배적 의견", trend['dominant'])
                
                # 해석
                st.markdown("---")
                st.subheader("💡 종합 해석")
                
                if analysis['score'] >= 70:
                    st.success(f"""
                    **🟢 강한 매수 신호**
                    
                    {chr(10).join(f"- {reason}" for reason in analysis['reasons'])}
                    
                    애널리스트들의 긍정적 전망이 두드러집니다.
                    """)
                elif analysis['score'] >= 50:
                    st.info(f"""
                    **🟡 중립적 신호**
                    
                    {chr(10).join(f"- {reason}" for reason in analysis['reasons'])}
                    
                    전문가 의견이 혼조세를 보입니다.
                    """)
                else:
                    st.warning(f"""
                    **🟠 약한 신호**
                    
                    {chr(10).join(f"- {reason}" for reason in analysis['reasons'])}
                    
                    애널리스트 전망이 제한적입니다.
                    """)
                
                # 업데이트 시간
                st.caption(f"🕐 마지막 업데이트: {analyst_data['last_updated']}")
            
            else:
                st.warning(f"⚠️ {selected_ticker}에 대한 애널리스트 데이터가 없습니다")
    
    else:
        st.info("👆 위의 '분석 시작' 버튼을 눌러주세요")

# 탭 6: 기존 대시보드
with tab6:
    st.header("📈 기존 대시보드")
    st.info("기존 `dashboard.py`를 여기서 실행하려면 import 하세요")
    
    if st.button("🔗 기존 대시보드 열기"):
        st.info("명령 프롬프트에서: `streamlit run step3_dashboard/dashboard.py`")
# 푸터
st.markdown("---")
st.caption("⚠️ 투자 판단의 책임은 투자자 본인에게 있습니다.")
st.caption("📊 데이터 출처: Yahoo Finance, SEC EDGAR")
st.caption(f"🕐 마지막 업데이트: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")