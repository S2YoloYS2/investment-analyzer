"""
자동 종목 발굴 시스템
미국/한국 주식을 자동으로 스캔하여 유망 종목 추천
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class StockScreener:
    """자동 종목 발굴 클래스"""
    
    def __init__(self, insider_tracker, analyst_tracker):
        """
        초기화
        
        Args:
            insider_tracker: 임원 매수 추적 인스턴스
            analyst_tracker: 애널리스트 평가 인스턴스
        """
        self.insider_tracker = insider_tracker
        self.analyst_tracker = analyst_tracker
    
    # ======================================
    # 📊 종목 리스트
    # ======================================
    
    def get_sp100_tickers(self) -> List[str]:
        """S&P 100 종목 리스트"""
        # 주요 대형주 100개 (실제로는 API에서 가져오지만 여기선 샘플)
        return [
            # 기술
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ORCL', 'ADBE',
            'CRM', 'CSCO', 'ACN', 'AMD', 'IBM', 'INTC', 'QCOM', 'TXN', 'INTU', 'NOW',
            # 금융
            'BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'AXP', 'BLK',
            'C', 'SCHW', 'USB', 'PNC', 'TFC',
            # 헬스케어
            'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT', 'DHR', 'BMY',
            'AMGN', 'CVS', 'MDT', 'GILD', 'CI',
            # 소비재
            'COST', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'DIS', 'CMCSA',
            'PEP', 'KO', 'PM', 'PG', 'MO',
            # 산업/에너지
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'LIN', 'UPS', 'HON', 'UNP', 'CAT',
            'BA', 'GE', 'MMM', 'DE', 'RTX',
            # 기타
            'NFLX', 'T', 'VZ', 'NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'EXC'
        ]
    
    def get_korea_tickers(self) -> List[str]:
        """한국 주요 종목 리스트"""
        return [
            # 대형주
            '005930.KS',  # 삼성전자
            '000660.KS',  # SK하이닉스
            '035420.KS',  # NAVER
            '035720.KS',  # 카카오
            '051910.KS',  # LG화학
            '006400.KS',  # 삼성SDI
            '207940.KS',  # 삼성바이오로직스
            '068270.KS',  # 셀트리온
            '028260.KS',  # 삼성물산
            '012330.KS',  # 현대모비스
            '005380.KS',  # 현대차
            '000270.KS',  # 기아
            '105560.KS',  # KB금융
            '055550.KS',  # 신한지주
            '086790.KS',  # 하나금융지주
            '017670.KS',  # SK텔레콤
            '032830.KS',  # 삼성생명
            '018260.KS',  # 삼성에스디에스
            '009150.KS',  # 삼성전기
            '010950.KS',  # S-Oil
        ]
    
    # ======================================
    # 🔍 스캔 함수
    # ======================================
    
    def scan_stocks(self, tickers: List[str], market: str = "US", 
                   max_workers: int = 10, progress_bar=None) -> pd.DataFrame:
        """
        종목 스캔 및 점수 계산
        
        Args:
            tickers: 종목 리스트
            market: 시장 ("US" or "KR")
            max_workers: 병렬 처리 수
            progress_bar: Streamlit 진행률 바
        
        Returns:
            DataFrame: 종목별 점수 및 정보
        """
        results = []
        total = len(tickers)
        
        print(f"\n🔍 {market} 시장 스캔 시작: {total}개 종목")
        
        # 병렬 처리로 빠르게 스캔
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(self._analyze_single_stock, ticker, market): ticker 
                for ticker in tickers
            }
            
            completed = 0
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    
                    completed += 1
                    if progress_bar:
                        progress_bar.progress(completed / total, 
                                            f"스캔 중: {completed}/{total} ({ticker})")
                    
                except Exception as e:
                    print(f"  ⚠️ {ticker} 오류: {str(e)}")
        
        if not results:
            return pd.DataFrame()
        
        # DataFrame 생성 및 정렬
        df = pd.DataFrame(results)
        df = df.sort_values('total_score', ascending=False)
        df = df.reset_index(drop=True)
        df['rank'] = range(1, len(df) + 1)
        
        print(f"✅ 스캔 완료: {len(df)}개 종목 분석됨")
        return df
    
    def _analyze_single_stock(self, ticker: str, market: str) -> Dict:
        """단일 종목 분석"""
        try:
            # 기본 정보
            stock = yf.Ticker(ticker)
            info = stock.info
            
            name = info.get('longName', ticker)
            current_price = info.get('currentPrice', 0)
            
            if current_price == 0:
                return None
            
            # 점수 계산
            scores = {
                'ticker': ticker,
                'name': name,
                'current_price': current_price,
                'market': market
            }
            
            # 1. 애널리스트 평가 (미국 주식만)
            if market == "US":
                analyst_score = self._get_analyst_score(ticker)
                insider_score = self._get_insider_score(ticker)
            else:
                analyst_score = 0
                insider_score = 0
            
            # 2. 기술적 지표 (간단 버전)
            technical_score = self._get_technical_score(stock)
            
            # 총점 계산
            total_score = (analyst_score * 0.4 + 
                          insider_score * 0.3 + 
                          technical_score * 0.3)
            
            scores.update({
                'analyst_score': analyst_score,
                'insider_score': insider_score,
                'technical_score': technical_score,
                'total_score': round(total_score, 1),
                'signal': self._get_signal(total_score)
            })
            
            return scores
            
        except Exception as e:
            return None
    
    def _get_analyst_score(self, ticker: str) -> float:
        """애널리스트 점수 (0~100)"""
        try:
            data = self.analyst_tracker.get_analyst_ratings(ticker)
            analysis = self.analyst_tracker.analyze_sentiment(data)
            return analysis['score']
        except:
            return 0
    
    def _get_insider_score(self, ticker: str) -> float:
        """임원 매수 점수 (0~100)"""
        try:
            df = self.insider_tracker.get_insider_trades(ticker, months=3)
            analysis = self.insider_tracker.analyze_insider_sentiment(df)
            return analysis['score']
        except:
            return 0
    
    def _get_technical_score(self, stock) -> float:
        """간단한 기술적 점수 (0~100)"""
        try:
            hist = stock.history(period="3mo")
            if hist.empty:
                return 0
            
            # 간단한 모멘텀 점수
            current = hist['Close'].iloc[-1]
            ma20 = hist['Close'].rolling(20).mean().iloc[-1]
            ma60 = hist['Close'].rolling(60).mean().iloc[-1]
            
            score = 0
            
            # 이평선 정배열
            if current > ma20 > ma60:
                score += 50
            elif current > ma20:
                score += 30
            
            # 상승 추세
            pct_change = ((current - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
            if pct_change > 10:
                score += 30
            elif pct_change > 5:
                score += 20
            elif pct_change > 0:
                score += 10
            
            return min(score, 100)
            
        except:
            return 0
    
    def _get_signal(self, score: float) -> str:
        """점수에 따른 신호"""
        if score >= 70:
            return '🟢 강한 매수'
        elif score >= 50:
            return '🟡 중립'
        elif score >= 30:
            return '🔴 주의'
        else:
            return '⚫ 신호없음'
    
    # ======================================
    # 🎯 빠른 스캔 (TOP 종목만)
    # ======================================
    
    def quick_scan_us(self, top_n: int = 20, progress_bar=None) -> pd.DataFrame:
        """미국 주식 빠른 스캔"""
        tickers = self.get_sp100_tickers()[:50]  # 50개만
        df = self.scan_stocks(tickers, "US", max_workers=10, progress_bar=progress_bar)
        return df.head(top_n) if not df.empty else df
    
    def quick_scan_korea(self, top_n: int = 10, progress_bar=None) -> pd.DataFrame:
        """한국 주식 빠른 스캔"""
        tickers = self.get_korea_tickers()
        df = self.scan_stocks(tickers, "KR", max_workers=5, progress_bar=progress_bar)
        return df.head(top_n) if not df.empty else df


# 테스트
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 자동 종목 발굴 시스템 테스트")
    print("=" * 60)
    
    # 더미 트래커 (실제론 실제 인스턴스 사용)
    from modules.screener.insider_tracker import InsiderTracker
    from modules.screener.analyst_ratings import AnalystTracker
    
    insider = InsiderTracker()
    analyst = AnalystTracker()
    
    screener = StockScreener(insider, analyst)
    
    print("\n🇺🇸 미국 주식 TOP 10 스캔...")
    us_stocks = screener.quick_scan_us(top_n=10)
    
    if not us_stocks.empty:
        print("\n✅ 추천 종목:")
        print(us_stocks[['rank', 'ticker', 'name', 'total_score', 'signal']].to_string(index=False))
    
    print("\n✅ 테스트 완료!")