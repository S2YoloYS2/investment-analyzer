"""
데이터 통합 관리 모듈
모든 데이터를 한 곳에서 관리 (충돌 방지)
"""

import yfinance as yf
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List
import streamlit as st


class DataManager:
    """데이터 통합 관리 클래스"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """초기화"""
        self.config = self._load_config(config_path)
        self.cache = {}
        
    def _load_config(self, config_path: str) -> dict:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ 설정 파일 없음: {config_path}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """기본 설정"""
        return {
            'DATA': {
                'default_tickers': ['005930.KS', 'AAPL', 'BTC-USD'],
                'periods': ['1mo', '3mo', '6mo', '1y'],
                'cache_enabled': True,
                'cache_ttl_minutes': 30
            }
        }
    
    @st.cache_data(ttl=1800)
    def get_stock_data(_self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """
        주식 가격 데이터 가져오기
        
        Args:
            ticker: 종목 코드
            period: 기간
        
        Returns:
            DataFrame: OHLCV 데이터
        """
        try:
            print(f"📥 데이터 수집: {ticker} ({period})")
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                print(f"⚠️ 데이터 없음: {ticker}")
                return pd.DataFrame()
            
            # 컬럼명 한글화
            df = df.rename(columns={
                'Open': '시가',
                'High': '고가',
                'Low': '저가',
                'Close': '종가',
                'Volume': '거래량'
            })
            
            return df
            
        except Exception as e:
            print(f"❌ 오류: {ticker} - {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def get_stock_info(_self, ticker: str) -> dict:
        """
        종목 기본 정보
        
        Args:
            ticker: 종목 코드
        
        Returns:
            dict: 종목 정보
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0),
                'currency': info.get('currency', 'USD')
            }
            
        except Exception as e:
            print(f"❌ 정보 가져오기 실패: {ticker}")
            return {'name': ticker}
    
    def get_multiple_stocks(self, tickers: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """여러 종목 데이터"""
        result = {}
        for ticker in tickers:
            df = self.get_stock_data(ticker, period)
            if not df.empty:
                result[ticker] = df
        return result
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache = {}
        st.cache_data.clear()
        print("🗑️ 캐시 초기화 완료")


# 테스트
if __name__ == "__main__":
    print("=" * 50)
    print("📊 데이터 관리자 테스트")
    print("=" * 50)
    
    dm = DataManager()
    
    print("\n1️⃣ 삼성전자 데이터...")
    samsung = dm.get_stock_data("005930.KS", "1mo")
    if not samsung.empty:
        print(f"✅ 성공! {len(samsung)}개 데이터")
        print(samsung.tail(3))
    
    print("\n2️⃣ Apple 정보...")
    info = dm.get_stock_info("AAPL")
    print(f"✅ {info['name']} - {info['sector']}")
    
    print("\n✅ 테스트 완료!")