"""
불장단타왕 매매 전략
- TOTAL3 기반 시장 방향성 판단
- 상대강도 스크리닝
- VWMA 100일선 진입/청산
"""

import pandas as pd
import numpy as np

class BullMarketStrategy:
    """불장단타왕 전략"""
    
    def __init__(self):
        self.market_regime = None  # 'bull', 'bear', 'neutral'
    
    # ========================================
    # 1단계: 시장 방향성 (TOTAL3)
    # ========================================
    
    def analyze_total3(self, df_total3):
        """
        TOTAL3 분석으로 알트코인 시장 전체 판단
        
        Args:
            df_total3: TOTAL3 OHLCV 데이터
        
        Returns:
            dict: 시장 판단 결과
        """
        # 이동평균선 계산
        sma_50 = df_total3['Close'].rolling(window=50).mean()
        sma_200 = df_total3['Close'].rolling(window=200).mean()
        sma_400 = df_total3['Close'].rolling(window=400).mean()
        
        current_price = df_total3['Close'].iloc[-1]
        
        # 현재 위치
        above_50 = current_price > sma_50.iloc[-1]
        above_200 = current_price > sma_200.iloc[-1]
        above_400 = current_price > sma_400.iloc[-1]
        
        # 정배열 확인 (50 > 200 > 400)
        is_golden_cross = sma_50.iloc[-1] > sma_200.iloc[-1] > sma_400.iloc[-1]
        
        # 시장 판단
        if above_400 and is_golden_cross:
            regime = '강세장'  # 알트코인 매수 적극
            signal = 'LONG'
        elif above_200:
            regime = '상승장'  # 알트코인 매수 가능
            signal = 'LONG'
        elif current_price < sma_50.iloc[-1]:
            regime = '하락장'  # 매도 또는 관망
            signal = 'SHORT'
        else:
            regime = '중립'
            signal = 'NEUTRAL'
        
        self.market_regime = regime
        
        return {
            'regime': regime,
            'signal': signal,
            'current_price': current_price,
            'sma_50': sma_50.iloc[-1],
            'sma_200': sma_200.iloc[-1],
            'sma_400': sma_400.iloc[-1],
            'is_golden_cross': is_golden_cross
        }
    
    # ========================================
    # 2단계: 상대강도 스크리닝
    # ========================================
    
    def calculate_relative_strength(self, df_btc, df_alt):
        """
        비트코인 대비 알트코인 상대강도 계산
        
        Args:
            df_btc: 비트코인 OHLCV
            df_alt: 알트코인 OHLCV
        
        Returns:
            dict: 상대강도 분석
        """
        # 이동평균선 계산
        btc_sma_200 = df_btc['Close'].rolling(window=200).mean()
        alt_sma_200 = df_alt['Close'].rolling(window=200).mean()
        
        # 현재가와 200일선 거리 (%)
        btc_distance = ((df_btc['Close'].iloc[-1] - btc_sma_200.iloc[-1]) / btc_sma_200.iloc[-1]) * 100
        alt_distance = ((df_alt['Close'].iloc[-1] - alt_sma_200.iloc[-1]) / alt_sma_200.iloc[-1]) * 100
        
        # 상대강도 판단
        if alt_distance > btc_distance:
            strength = '강함'  # 매수 후보
            score = (alt_distance - btc_distance)
        elif alt_distance < btc_distance:
            strength = '약함'  # 매도 후보
            score = (alt_distance - btc_distance)
        else:
            strength = '중립'
            score = 0
        
        return {
            'strength': strength,
            'score': score,
            'btc_distance': btc_distance,
            'alt_distance': alt_distance,
            'btc_above_200': df_btc['Close'].iloc[-1] > btc_sma_200.iloc[-1],
            'alt_above_200': df_alt['Close'].iloc[-1] > alt_sma_200.iloc[-1]
        }
    
    # ========================================
    # 3단계: VWMA 100일선 타점
    # ========================================
    
    def calculate_vwma(self, df, period=100):
        """
        거래량 가중 이동평균 (VWMA) 계산
        
        Args:
            df: OHLCV 데이터
            period: 기간
        
        Returns:
            Series: VWMA 값
        """
        vwma = (df['Close'] * df['Volume']).rolling(window=period).sum() / df['Volume'].rolling(window=period).sum()
        return vwma
    
    def get_entry_signal(self, df):
        """
        진입 신호 판단 (VWMA 100일선 기반)
        
        Args:
            df: OHLCV 데이터
        
        Returns:
            dict: 진입 신호
        """
        # VWMA 계산
        vwma_100 = self.calculate_vwma(df, 100)
        
        # 이동평균선 계산
        sma_25 = df['Close'].rolling(window=25).mean()
        sma_50 = df['Close'].rolling(window=50).mean()
        sma_200 = df['Close'].rolling(window=200).mean()
        
        current_price = df['Close'].iloc[-1]
        vwma_current = vwma_100.iloc[-1]
        
        # 거리 계산 (%)
        distance_to_vwma = ((current_price - vwma_current) / vwma_current) * 100
        
        # 매수 신호
        buy_signal = False
        buy_reason = []
        
        # 조건 1: VWMA 지지 (±1% 범위)
        if -1 <= distance_to_vwma <= 1:
            buy_signal = True
            buy_reason.append('VWMA 100일선 지지')
        
        # 조건 2: VWMA 상향 돌파 후 재지지
        if current_price > vwma_current and df['Close'].iloc[-2] < vwma_100.iloc[-2]:
            buy_signal = True
            buy_reason.append('VWMA 돌파 후 재지지')
        
        # 매도 신호
        sell_signal = False
        sell_reason = []
        
        # 조건 1: 25일선 저항
        if current_price >= sma_25.iloc[-1] * 0.99:
            sell_signal = True
            sell_reason.append('25일선 저항')
        
        # 조건 2: VWMA 하방 이탈 (손절)
        if current_price < vwma_current * 0.98:
            sell_signal = True
            sell_reason.append('VWMA 손절 (-2%)')
        
        return {
            'current_price': current_price,
            'vwma_100': vwma_current,
            'distance_pct': distance_to_vwma,
            'sma_25': sma_25.iloc[-1],
            'sma_50': sma_50.iloc[-1],
            'sma_200': sma_200.iloc[-1],
            'buy_signal': buy_signal,
            'buy_reason': buy_reason,
            'sell_signal': sell_signal,
            'sell_reason': sell_reason
        }
    
    # ========================================
    # 통합 전략
    # ========================================
    
    def full_analysis(self, df_total3, df_btc, df_alt):
        """
        전체 3단계 분석 통합
        
        Args:
            df_total3: TOTAL3 데이터
            df_btc: 비트코인 데이터
            df_alt: 알트코인 데이터
        
        Returns:
            dict: 종합 판단
        """
        # 1단계: 시장 방향성
        market = self.analyze_total3(df_total3)
        
        # 2단계: 상대강도
        strength = self.calculate_relative_strength(df_btc, df_alt)
        
        # 3단계: 진입 타점
        entry = self.get_entry_signal(df_alt)
        
        # 종합 판단
        final_signal = 'HOLD'
        final_reason = []
        
        # 매수 조건 통합
        if (market['signal'] == 'LONG' and 
            strength['strength'] == '강함' and 
            entry['buy_signal']):
            final_signal = 'BUY'
            final_reason.append(f"시장: {market['regime']}")
            final_reason.append(f"상대강도: {strength['strength']} ({strength['score']:.2f}%)")
            final_reason.extend(entry['buy_reason'])
        
        # 매도 조건
        elif entry['sell_signal']:
            final_signal = 'SELL'
            final_reason.extend(entry['sell_reason'])
        
        # 관망 조건
        elif market['signal'] == 'SHORT':
            final_signal = 'HOLD'
            final_reason.append(f"시장 하락장: 관망")
        
        return {
            'signal': final_signal,
            'reason': final_reason,
            'market_analysis': market,
            'strength_analysis': strength,
            'entry_analysis': entry
        }


# 테스트용 코드
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    strategy = BullMarketStrategy()
    
    print("=" * 60)
    print("🔥 불장단타왕 전략 분석")
    print("=" * 60)
    
    # 사용자 입력
    print("\n📝 분석할 코인을 입력하세요 (예: ETH, XRP, SOL, DOGE)")
    print("   여러 개 입력 시 쉼표로 구분 (예: ETH,XRP,SOL)")
    print()
    
    coin_input = input("코인 티커: ").strip().upper()
    
    if not coin_input:
        print("❌ 코인을 입력하지 않았습니다. 기본값 ETH로 분석합니다.")
        coins = ["ETH"]
    else:
        coins = [c.strip() for c in coin_input.split(",")]
    
    print("\n" + "=" * 60)
    
    # 각 코인 분석
    for coin in coins:
        symbol = f"{coin}/USDT"
        
        print(f"\n{'='*60}")
        print(f"💎 {coin} 분석")
        print(f"{'='*60}")
        
        try:
            # 비트코인 vs 알트코인 상대강도
            print(f"\n[1단계] 상대강도 분석 (BTC vs {coin})")
            df_btc = fetcher.get_crypto("BTC/USDT", timeframe="1d", limit=200)
            df_alt = fetcher.get_crypto(symbol, timeframe="1d", limit=200)
            
            if df_btc is not None and df_alt is not None and not df_alt.empty:
                strength = strategy.calculate_relative_strength(df_btc, df_alt)
                
                # 상대강도 색상
                strength_emoji = {
                    '강함': '💪🟢',
                    '약함': '📉🔴',
                    '중립': '⚪'
                }
                
                print(f"{strength_emoji[strength['strength']]} {coin} 강도: {strength['strength']}")
                print(f"📊 상대강도 점수: {strength['score']:+.2f}%")
                print(f"🟡 BTC 200일선 대비: {strength['btc_distance']:+.2f}%")
                print(f"🔵 {coin} 200일선 대비: {strength['alt_distance']:+.2f}%")
                
                # 진입 타점 분석
                print(f"\n[2단계] 진입 타점 분석 ({coin})")
                entry = strategy.get_entry_signal(df_alt)
                
                print(f"💵 현재가: ${entry['current_price']:,.2f}")
                print(f"📍 VWMA 100: ${entry['vwma_100']:,.2f}")
                print(f"📏 VWMA 거리: {entry['distance_pct']:+.2f}%")
                print(f"📈 25일선: ${entry['sma_25']:,.2f}")
                print(f"📈 50일선: ${entry['sma_50']:,.2f}")
                print(f"📈 200일선: ${entry['sma_200']:,.2f}")
                
                print(f"\n🟢 매수 신호: {'예' if entry['buy_signal'] else '아니오'}")
                if entry['buy_reason']:
                    for reason in entry['buy_reason']:
                        print(f"   ✓ {reason}")
                
                print(f"🔴 매도 신호: {'예' if entry['sell_signal'] else '아니오'}")
                if entry['sell_reason']:
                    for reason in entry['sell_reason']:
                        print(f"   ✓ {reason}")
                
                # 종합 판단
                print(f"\n{'='*60}")
                print(f"🎯 {coin} 종합 판단")
                print(f"{'='*60}")
                
                # 점수 계산
                total_score = 0
                reasons = []
                
                if strength['strength'] == '강함':
                    total_score += 2
                    reasons.append(f"✓ BTC 대비 상대강도 우위 (+{strength['score']:.2f}%)")
                
                if entry['buy_signal']:
                    total_score += 3
                    reasons.append("✓ VWMA 매수 타점 도달")
                
                if entry['sell_signal']:
                    total_score -= 3
                    reasons.append("✗ 손절/익절 구간")
                
                if strength['alt_above_200']:
                    total_score += 1
                    reasons.append("✓ 200일선 위 (상승 추세)")
                
                # 최종 신호
                if total_score >= 4:
                    final = "🟢 강력 매수"
                elif total_score >= 2:
                    final = "🟡 매수 고려"
                elif total_score >= 0:
                    final = "⚪ 관망"
                else:
                    final = "🔴 매도/관망"
                
                print(f"\n{final} (점수: {total_score}/6)")
                print(f"\n📝 판단 근거:")
                for reason in reasons:
                    print(f"  {reason}")
                
            else:
                print(f"❌ {coin} 데이터를 가져올 수 없습니다.")
                print(f"   티커가 올바른지 확인하세요. (예: ETH, XRP, SOL)")
        
        except Exception as e:
            print(f"❌ {coin} 분석 중 오류 발생: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 분석 완료!")
    print("=" * 60)
