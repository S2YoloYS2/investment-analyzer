"""
데이터 수집 모듈
- 한국 주식 (pykrx)
- 미국 주식 (yfinance)
- 암호화폐 (ccxt)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

class DataFetcher:
    """데이터 수집 클래스"""
    
    def __init__(self):
        self.korea_tz = pytz.timezone('Asia/Seoul')
        self.us_tz = pytz.timezone('America/New_York')
    
    def get_korea_stock(self, ticker="005930", period="1mo"):
        """
        한국 주식 데이터 가져오기 (최근 거래일 기준)
        
        Args:
            ticker: 종목 코드 (예: "005930" = 삼성전자)
            period: 기간 ("1d", "5d", "1mo", "3mo", "1y")
        
        Returns:
            DataFrame: 주가 데이터
        """
        try:
            # 한국 주식은 .KS 또는 .KQ 추가
            if ticker == "005930":  # 삼성전자
                symbol = f"{ticker}.KS"
            else:
                symbol = f"{ticker}.KS"
            
            # yfinance로 데이터 가져오기
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            
            if df.empty:
                return None
            
            # 최근 거래일 데이터만 (휴장일 제외)
            df = df[df['Volume'] > 0]
            
            return df
            
        except Exception as e:
            print(f"한국 주식 데이터 오류: {e}")
            return None
    
    def get_us_stock(self, ticker="AAPL", period="1mo"):
        """
        미국 주식 데이터 가져오기 (최근 거래일 기준)
        
        Args:
            ticker: 티커 (예: "AAPL" = Apple)
            period: 기간 ("1d", "5d", "1mo", "3mo", "1y")
        
        Returns:
            DataFrame: 주가 데이터
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                return None
            
            # 최근 거래일 데이터만
            df = df[df['Volume'] > 0]
            
            return df
            
        except Exception as e:
            print(f"미국 주식 데이터 오류: {e}")
            return None
    
    def get_crypto(self, symbol="BTC/USDT", timeframe="1d", limit=30):
        """
        암호화폐 데이터 가져오기 (24/7 거래)
        
        Args:
            symbol: 심볼 (예: "BTC/USDT")
            timeframe: 시간봉 ("1m", "5m", "1h", "1d")
            limit: 데이터 개수
        
        Returns:
            DataFrame: 가격 데이터
        """
        try:
            import ccxt
            
            # Bybit 거래소 연결
            exchange = ccxt.bybit()
            
            # OHLCV 데이터 가져오기
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # DataFrame으로 변환
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            )
            
            # 타임스탬프를 날짜로 변환
            df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('Date', inplace=True)
            df.drop('timestamp', axis=1, inplace=True)
            
            return df
            
        except Exception as e:
            print(f"암호화폐 데이터 오류: {e}")
            return None
    
    def get_latest_price(self, ticker, market="us"):
        """
        최신 가격 가져오기 (최근 거래일 기준)
        
        Args:
            ticker: 종목 코드/티커
            market: "korea", "us", "crypto"
        
        Returns:
            dict: {"price": 가격, "change": 변동률, "date": 날짜}
        """
        try:
            if market == "korea":
                df = self.get_korea_stock(ticker, period="5d")
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    return {
                        "price": round(latest['Close'], 0),
                        "change": round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2),
                        "date": latest.name.strftime("%Y-%m-%d"),
                        "volume": int(latest['Volume'])
                    }
            
            elif market == "us":
                df = self.get_us_stock(ticker, period="5d")
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    return {
                        "price": round(latest['Close'], 2),
                        "change": round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2),
                        "date": latest.name.strftime("%Y-%m-%d"),
                        "volume": int(latest['Volume'])
                    }
            
            elif market == "crypto":
                df = self.get_crypto(ticker, timeframe="1d", limit=2)
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    return {
                        "price": round(latest['Close'], 2),
                        "change": round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2),
                        "date": latest.name.strftime("%Y-%m-%d %H:%M"),
                        "volume": round(latest['Volume'], 2)
                    }
            
            return None
            
        except Exception as e:
            print(f"최신 가격 조회 오류: {e}")
            return None


# 테스트용 코드
if __name__ == "__main__":
    fetcher = DataFetcher()
    
    print("=== 삼성전자 ===")
    samsung = fetcher.get_latest_price("005930", "korea")
    if samsung:
        print(f"가격: {samsung['price']:,}원")
        print(f"변동: {samsung['change']}%")
        print(f"날짜: {samsung['date']}")
    
    print("\n=== Apple ===")
    apple = fetcher.get_latest_price("AAPL", "us")
    if apple:
        print(f"가격: ${apple['price']}")
        print(f"변동: {apple['change']}%")
        print(f"날짜: {apple['date']}")
    
    print("\n=== Bitcoin ===")
    btc = fetcher.get_latest_price("BTC/USDT", "crypto")
    if btc:
        print(f"가격: ${btc['price']:,}")
        print(f"변동: {btc['change']}%")
        print(f"날짜: {btc['date']}")
