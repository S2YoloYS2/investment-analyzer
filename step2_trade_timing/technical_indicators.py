"""
기술적 지표 계산 모듈
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- 이동평균선 (Moving Average)
- 볼린저 밴드 (Bollinger Bands)
"""

import pandas as pd
import numpy as np

class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def calculate_rsi(df, period=14):
        """
        RSI (Relative Strength Index) 계산
        
        Args:
            df: DataFrame with 'Close' column
            period: RSI 기간 (기본 14일)
        
        Returns:
            Series: RSI 값 (0-100)
        """
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_moving_average(df, periods=[20, 60]):
        """
        이동평균선 계산
        
        Args:
            df: DataFrame with 'Close' column
            periods: 이동평균 기간 리스트
        
        Returns:
            dict: {기간: 이동평균값}
        """
        result = {}
        for period in periods:
            result[f'MA{period}'] = df['Close'].rolling(window=period).mean()
        
        return result
    
    @staticmethod
    def calculate_macd(df, fast=12, slow=26, signal=9):
        """
        MACD 계산
        
        Args:
            df: DataFrame with 'Close' column
            fast: 빠른 EMA 기간
            slow: 느린 EMA 기간
            signal: 시그널 라인 기간
        
        Returns:
            dict: {'MACD': MACD선, 'Signal': 시그널선, 'Histogram': 히스토그램}
        """
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return {
            'MACD': macd,
            'Signal': signal_line,
            'Histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(df, period=20, std_dev=2):
        """
        볼린저 밴드 계산
        
        Args:
            df: DataFrame with 'Close' column
            period: 이동평균 기간
            std_dev: 표준편차 배수
        
        Returns:
            dict: {'Upper': 상단밴드, 'Middle': 중간밴드, 'Lower': 하단밴드}
        """
        middle = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'Upper': upper,
            'Middle': middle,
            'Lower': lower
        }
    
    @staticmethod
    def get_trading_signals(df):
        """
        매매 신호 생성
        
        Args:
            df: DataFrame with price data
        
        Returns:
            dict: 매매 신호 정보
        """
        # RSI 계산
        rsi = TechnicalIndicators.calculate_rsi(df)
        latest_rsi = rsi.iloc[-1] if not rsi.empty else None
        
        # 이동평균선 계산
        ma = TechnicalIndicators.calculate_moving_average(df, [20, 60])
        
        # MACD 계산
        macd = TechnicalIndicators.calculate_macd(df)
        
        # 볼린저 밴드 계산
        bb = TechnicalIndicators.calculate_bollinger_bands(df)
        
        # 신호 판단
        signals = {
            'RSI': {
                'value': latest_rsi,
                'signal': '과매도' if latest_rsi and latest_rsi < 30 else '과매수' if latest_rsi and latest_rsi > 70 else '중립'
            },
            'MA_Cross': {
                'MA20': ma['MA20'].iloc[-1] if not ma['MA20'].empty else None,
                'MA60': ma['MA60'].iloc[-1] if not ma['MA60'].empty else None,
                'signal': '상승' if ma['MA20'].iloc[-1] > ma['MA60'].iloc[-1] else '하락'
            },
            'MACD': {
                'value': macd['MACD'].iloc[-1] if not macd['MACD'].empty else None,
                'signal_line': macd['Signal'].iloc[-1] if not macd['Signal'].empty else None,
                'signal': '매수' if macd['MACD'].iloc[-1] > macd['Signal'].iloc[-1] else '매도'
            },
            'Bollinger': {
                'upper': bb['Upper'].iloc[-1] if not bb['Upper'].empty else None,
                'middle': bb['Middle'].iloc[-1] if not bb['Middle'].empty else None,
                'lower': bb['Lower'].iloc[-1] if not bb['Lower'].empty else None,
                'current_price': df['Close'].iloc[-1],
                'signal': '과매수' if df['Close'].iloc[-1] > bb['Upper'].iloc[-1] else '과매도' if df['Close'].iloc[-1] < bb['Lower'].iloc[-1] else '중립'
            }
        }
        
        return signals
    
    @staticmethod
    def get_multi_timeframe_analysis(fetcher, ticker, market):
        """
        다중 시간대 분석 (단기/중기/장기)
        
        Args:
            fetcher: DataFetcher 인스턴스
            ticker: 종목 코드
            market: 시장 ("korea", "us", "crypto")
        
        Returns:
            dict: 각 시간대별 분석 결과
        """
        periods = {
            '단기': '1mo',
            '중기': '3mo',
            '장기': '1y'
        }
        
        results = {}
        
        for period_name, period_code in periods.items():
            try:
                if market == "korea":
                    df = fetcher.get_korea_stock(ticker, period=period_code)
                elif market == "us":
                    df = fetcher.get_us_stock(ticker, period=period_code)
                elif market == "crypto":
                    limits = {'1mo': 30, '3mo': 90, '1y': 365}
                    df = fetcher.get_crypto(ticker, timeframe="1d", limit=limits[period_code])
                
                if df is not None and not df.empty:
                    signals = TechnicalIndicators.get_trading_signals(df)
                    
                    # 매수 신호 점수 계산
                    buy_score = 0
                    if signals['RSI']['signal'] == '과매도':
                        buy_score += 1
                    if signals['MA_Cross']['signal'] == '상승':
                        buy_score += 1
                    if signals['MACD']['signal'] == '매수':
                        buy_score += 1
                    if signals['Bollinger']['signal'] == '과매도':
                        buy_score += 1
                    
                    # 종합 판단
                    if buy_score >= 3:
                        overall = '강력 매수'
                        color = '🟢'
                    elif buy_score >= 2:
                        overall = '매수'
                        color = '🟡'
                    elif buy_score == 1:
                        overall = '관망'
                        color = '⚪'
                    else:
                        overall = '매도'
                        color = '🔴'
                    
                    results[period_name] = {
                        'signals': signals,
                        'buy_score': buy_score,
                        'overall': overall,
                        'color': color,
                        'period': period_code
                    }
                else:
                    results[period_name] = None
                    
            except Exception as e:
                print(f"{period_name} 분석 오류: {e}")
                results[period_name] = None
        
        return results
    
    @staticmethod
    def add_all_indicators(df):
        """
        모든 지표를 DataFrame에 추가
        
        Args:
            df: DataFrame with price data
        
        Returns:
            DataFrame: 지표가 추가된 DataFrame
        """
        df_copy = df.copy()
        
        # RSI
        df_copy['RSI'] = TechnicalIndicators.calculate_rsi(df)
        
        # 이동평균선
        ma = TechnicalIndicators.calculate_moving_average(df, [20, 60])
        for key, value in ma.items():
            df_copy[key] = value
        
        # MACD
        macd = TechnicalIndicators.calculate_macd(df)
        df_copy['MACD'] = macd['MACD']
        df_copy['MACD_Signal'] = macd['Signal']
        df_copy['MACD_Histogram'] = macd['Histogram']
        
        # 볼린저 밴드
        bb = TechnicalIndicators.calculate_bollinger_bands(df)
        df_copy['BB_Upper'] = bb['Upper']
        df_copy['BB_Middle'] = bb['Middle']
        df_copy['BB_Lower'] = bb['Lower']
        
        return df_copy


# 테스트용 코드
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    ti = TechnicalIndicators()
    
    print("=== 삼성전자 다중 시간대 분석 ===\n")
    
    results = ti.get_multi_timeframe_analysis(fetcher, "005930", "korea")
    
    for period_name, analysis in results.items():
        if analysis:
            print(f"{'='*50}")
            print(f"📅 {period_name} 관점 ({analysis['period']})")
            print(f"{'='*50}")
            print(f"📊 RSI: {analysis['signals']['RSI']['value']:.2f} - {analysis['signals']['RSI']['signal']}")
            print(f"📈 이동평균: {analysis['signals']['MA_Cross']['signal']}")
            print(f"🎯 MACD: {analysis['signals']['MACD']['signal']}")
            print(f"📉 볼린저밴드: {analysis['signals']['Bollinger']['signal']}")
            print(f"\n{analysis['color']} 종합 판단: {analysis['overall']} (신호 {analysis['buy_score']}/4)")
            print()
        else:
            print(f"{period_name}: 데이터 없음\n")
