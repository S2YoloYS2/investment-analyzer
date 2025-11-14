"""
통합 매매 전략
- 주식: 일봉 기준 기술적 분석
- 코인 장기: TOTAL3 + 상대강도 + VWMA (일봉)
- 코인 단타: RSI 과매도 + 5분봉 50선 (5분봉)
"""

import pandas as pd
import numpy as np
from bull_market_strategy import BullMarketStrategy
from technical_indicators import TechnicalIndicators

class IntegratedStrategy:
    """통합 매매 전략"""
    
    def __init__(self):
        self.long_term = BullMarketStrategy()
        self.indicators = TechnicalIndicators()
    
    # ========================================
    # 코인 단타 전략 (5분봉)
    # ========================================
    
    def analyze_scalping(self, fetcher, symbol):
        """
        코인 단타 전략 분석
        
        Args:
            fetcher: DataFetcher 인스턴스
            symbol: 코인 심볼 (예: "BTC/USDT")
        
        Returns:
            dict: 단타 분석 결과
        """
        # 1시간봉 데이터 (RSI 확인)
        df_1h = fetcher.get_crypto(symbol, timeframe="1h", limit=50)
        
        # 5분봉 데이터 (진입 타점)
        df_5m = fetcher.get_crypto(symbol, timeframe="5m", limit=100)
        
        if df_1h is None or df_5m is None:
            return None
        
        # RSI 계산 (1시간봉)
        rsi_1h = self.indicators.calculate_rsi(df_1h, period=14)
        current_rsi = rsi_1h.iloc[-1] if not rsi_1h.empty else None
        
        # 5분봉 지표 계산
        sma_50_5m = df_5m['Close'].rolling(window=50).mean()
        vwma_100_5m = self.long_term.calculate_vwma(df_5m, 100)
        sma_200_5m = df_5m['Close'].rolling(window=200).mean()
        sma_25_5m = df_5m['Close'].rolling(window=25).mean()
        
        current_price = df_5m['Close'].iloc[-1]
        
        # 50선 기울기 계산 (최근 5개 캔들)
        slope_50 = sma_50_5m.iloc[-1] - sma_50_5m.iloc[-6]
        slope_direction = "상승" if slope_50 > 0 else "하락" if slope_50 < 0 else "횡보"
        
        # 이격도 계산
        gap_to_50 = ((current_price - sma_50_5m.iloc[-1]) / sma_50_5m.iloc[-1]) * 100
        
        # ========================================
        # 진입 신호 판단
        # ========================================
        
        entry_signal = False
        entry_type = None
        entry_reason = []
        
        # 조건 1: 정석 매수 (RSI 과매도 + 50선 지지)
        if current_rsi and current_rsi <= 30:
            if slope_direction in ["상승", "횡보"]:
                if -1 <= gap_to_50 <= 1:  # 50선 근처
                    entry_signal = True
                    entry_type = "정석 매수"
                    entry_reason.append(f"1시간 RSI 과매도 ({current_rsi:.1f})")
                    entry_reason.append(f"5분봉 50선 지지")
                    entry_reason.append(f"50선 기울기: {slope_direction}")
        
        # 조건 2: 급락 매수 (RSI 극과매도 + 큰 이격도)
        if current_rsi and current_rsi <= 25:
            if gap_to_50 < -3:  # 50선에서 3% 이상 하락
                entry_signal = True
                entry_type = "급락 매수"
                entry_reason.append(f"1시간 RSI 극과매도 ({current_rsi:.1f})")
                entry_reason.append(f"50선 이격도: {gap_to_50:.2f}%")
                entry_reason.append("분할 매수 권장")
        
        # ========================================
        # 청산 신호 판단
        # ========================================
        
        exit_signals = []
        
        # 1차 익절: 100 VWMA
        distance_to_vwma = ((current_price - vwma_100_5m.iloc[-1]) / vwma_100_5m.iloc[-1]) * 100
        if -1 <= distance_to_vwma <= 1:
            exit_signals.append({
                'level': '1차 익절',
                'target': vwma_100_5m.iloc[-1],
                'reason': '100 VWMA 저항'
            })
        
        # 2차 익절: 200선
        distance_to_200 = ((current_price - sma_200_5m.iloc[-1]) / sma_200_5m.iloc[-1]) * 100
        if -1 <= distance_to_200 <= 1:
            exit_signals.append({
                'level': '2차 익절',
                'target': sma_200_5m.iloc[-1],
                'reason': '200선 저항'
            })
        
        # 손절: 50선 하방 이탈
        if gap_to_50 < -2:
            exit_signals.append({
                'level': '손절',
                'target': sma_50_5m.iloc[-1] * 0.98,
                'reason': '50선 이탈'
            })
        
        return {
            'symbol': symbol,
            'timeframe': '5분봉',
            'current_price': current_price,
            'rsi_1h': current_rsi,
            'sma_50_5m': sma_50_5m.iloc[-1],
            'vwma_100_5m': vwma_100_5m.iloc[-1],
            'sma_200_5m': sma_200_5m.iloc[-1],
            'slope_50': slope_direction,
            'gap_to_50': gap_to_50,
            'entry_signal': entry_signal,
            'entry_type': entry_type,
            'entry_reason': entry_reason,
            'exit_signals': exit_signals
        }
    
    # ========================================
    # 주식 분석 (일봉)
    # ========================================
    
    def analyze_stock(self, fetcher, ticker, market):
        """
        주식 일봉 분석
        
        Args:
            fetcher: DataFetcher 인스턴스
            ticker: 종목 코드
            market: "korea" 또는 "us"
        
        Returns:
            dict: 주식 분석 결과
        """
        # 다중 시간대 분석
        results = self.indicators.get_multi_timeframe_analysis(fetcher, ticker, market)
        
        return {
            'ticker': ticker,
            'market': market,
            'timeframe': '일봉',
            'analysis': results
        }
    
    # ========================================
    # 코인 장기 분석 (일봉)
    # ========================================
    
    def analyze_crypto_longterm(self, fetcher, symbol):
        """
        코인 장기 전략 분석 (일봉)
        
        Args:
            fetcher: DataFetcher 인스턴스
            symbol: 코인 심볼
        
        Returns:
            dict: 장기 분석 결과
        """
        # 비트코인 vs 알트코인
        df_btc = fetcher.get_crypto("BTC/USDT", timeframe="1d", limit=200)
        df_alt = fetcher.get_crypto(symbol, timeframe="1d", limit=200)
        
        if df_btc is None or df_alt is None:
            return None
        
        # 상대강도 분석
        strength = self.long_term.calculate_relative_strength(df_btc, df_alt)
        
        # 진입 타점 (VWMA)
        entry = self.long_term.get_entry_signal(df_alt)
        
        # 점수 계산
        score = 0
        reasons = []
        
        if strength['strength'] == '강함':
            score += 2
            reasons.append(f"✓ BTC 대비 상대강도 우위")
        
        if entry['buy_signal']:
            score += 3
            reasons.append("✓ VWMA 매수 타점")
        
        if entry['sell_signal']:
            score -= 3
            reasons.append("✗ 손절/익절 구간")
        
        # 최종 판단
        if score >= 4:
            final = "강력 매수"
        elif score >= 2:
            final = "매수 고려"
        elif score >= 0:
            final = "관망"
        else:
            final = "매도/관망"
        
        return {
            'symbol': symbol,
            'timeframe': '일봉',
            'strength': strength,
            'entry': entry,
            'score': score,
            'final': final,
            'reasons': reasons
        }


# 테스트용 코드
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    strategy = IntegratedStrategy()
    
    print("=" * 70)
    print("🎯 통합 매매 전략 분석")
    print("=" * 70)
    
    # 분석 타입 선택
    print("\n분석 타입을 선택하세요:")
    print("1. 📈 주식 분석 (일봉)")
    print("2. 📅 코인 장기 분석 (일봉)")
    print("3. ⚡ 코인 단타 분석 (5분봉)")
    print("4. 🔄 코인 종합 분석 (장기 + 단타)")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        # 주식 분석
        print("\n=== 📈 주식 분석 ===")
        market = input("시장 선택 (korea/us): ").strip().lower()
        
        if market == "korea":
            ticker = input("종목 코드 (예: 005930): ").strip()
        else:
            ticker = input("티커 (예: AAPL): ").strip().upper()
        
        result = strategy.analyze_stock(fetcher, ticker, market)
        
        print(f"\n{'='*70}")
        print(f"📊 {ticker} 분석 결과")
        print(f"{'='*70}")
        
        for period, analysis in result['analysis'].items():
            if analysis:
                print(f"\n📅 {period} 관점:")
                print(f"  {analysis['color']} {analysis['overall']} (신호 {analysis['buy_score']}/4)")
    
    elif choice == "2":
        # 코인 장기 분석
        print("\n=== 📅 코인 장기 분석 (일봉) ===")
        coin = input("코인 티커 (예: ETH): ").strip().upper()
        symbol = f"{coin}/USDT"
        
        result = strategy.analyze_crypto_longterm(fetcher, symbol)
        
        if result:
            print(f"\n{'='*70}")
            print(f"📊 {coin} 장기 분석 (일봉)")
            print(f"{'='*70}")
            
            print(f"\n💪 상대강도: {result['strength']['strength']}")
            print(f"📊 점수: {result['score']}/5")
            print(f"🎯 판단: {result['final']}")
            print(f"\n근거:")
            for reason in result['reasons']:
                print(f"  {reason}")
    
    elif choice == "3":
        # 코인 단타 분석
        print("\n=== ⚡ 코인 단타 분석 (5분봉) ===")
        coin = input("코인 티커 (예: BTC): ").strip().upper()
        symbol = f"{coin}/USDT"
        
        result = strategy.analyze_scalping(fetcher, symbol)
        
        if result:
            print(f"\n{'='*70}")
            print(f"⚡ {coin} 단타 분석 (5분봉)")
            print(f"{'='*70}")
            
            print(f"\n💵 현재가: ${result['current_price']:,.2f}")
            print(f"📊 1시간 RSI: {result['rsi_1h']:.1f}")
            print(f"📈 5분봉 50선: ${result['sma_50_5m']:,.2f}")
            print(f"📉 50선 기울기: {result['slope_50']}")
            print(f"📏 50선 이격도: {result['gap_to_50']:+.2f}%")
            
            print(f"\n🟢 진입 신호: {'예' if result['entry_signal'] else '아니오'}")
            if result['entry_signal']:
                print(f"   타입: {result['entry_type']}")
                for reason in result['entry_reason']:
                    print(f"   ✓ {reason}")
            
            if result['exit_signals']:
                print(f"\n🔴 청산 신호:")
                for signal in result['exit_signals']:
                    print(f"   {signal['level']}: ${signal['target']:,.2f} - {signal['reason']}")
    
    elif choice == "4":
        # 코인 종합 분석
        print("\n=== 🔄 코인 종합 분석 ===")
        coin = input("코인 티커 (예: ETH): ").strip().upper()
        symbol = f"{coin}/USDT"
        
        print(f"\n{'='*70}")
        print(f"💎 {coin} 종합 분석")
        print(f"{'='*70}")
        
        # 장기 분석
        print(f"\n📅 [장기 전략] 일봉 분석")
        print("=" * 70)
        longterm = strategy.analyze_crypto_longterm(fetcher, symbol)
        
        if longterm:
            print(f"💪 상대강도: {longterm['strength']['strength']}")
            print(f"🎯 판단: {longterm['final']} (점수 {longterm['score']}/5)")
        
        # 단타 분석
        print(f"\n⚡ [단타 전략] 5분봉 분석")
        print("=" * 70)
        scalping = strategy.analyze_scalping(fetcher, symbol)
        
        if scalping:
            print(f"📊 1시간 RSI: {scalping['rsi_1h']:.1f}")
            print(f"🟢 진입 신호: {'예 (' + scalping['entry_type'] + ')' if scalping['entry_signal'] else '아니오'}")
            
            if scalping['exit_signals']:
                print(f"🔴 청산 신호: {len(scalping['exit_signals'])}개")
        
        # 종합 추천
        print(f"\n{'='*70}")
        print(f"🎯 최종 추천")
        print(f"{'='*70}")
        
        if longterm and scalping:
            if longterm['score'] >= 2 and scalping['entry_signal']:
                print("🟢 강력 매수 추천!")
                print("  • 장기 전략: 긍정적")
                print("  • 단타 전략: 진입 타점 도달")
            elif longterm['score'] >= 2:
                print("🟡 장기 포지션 고려")
                print("  • 장기: 긍정적")
                print("  • 단타: 타점 대기")
            elif scalping['entry_signal']:
                print("🟡 단타 진입 고려")
                print("  • 단타: 진입 타점")
                print("  • 장기: 보통")
            else:
                print("⚪ 관망 권장")
    
    print("\n" + "=" * 70)
    print("✅ 분석 완료!")
    print("=" * 70)
