"""
거시 경제 지표 분석 모듈
시장 전체의 방향성을 판단
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests
import streamlit as st


class MarketIndicators:
    """거시 경제 지표 분석 클래스"""
    
    def __init__(self, fred_api_key: Optional[str] = None):
        """
        초기화
        
        Args:
            fred_api_key: FRED API 키 (선택, 없으면 VIX만 사용)
        """
        self.fred_api_key = fred_api_key
        self.fred_base_url = "https://api.stlouisfed.org/fred/series/observations"
    
    # ======================================
    # 📊 VIX 공포 지수
    # ======================================
    
    @st.cache_data(ttl=3600)
    def get_vix(_self) -> Dict:
        """
        VIX 공포 지수 가져오기
        
        Returns:
            Dict: VIX 데이터 및 해석
        """
        print("\n📊 VIX 데이터 수집 중...")
        
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="1mo")
            
            if hist.empty:
                return _self._empty_vix()
            
            current_vix = hist['Close'].iloc[-1]
            avg_vix = hist['Close'].mean()
            
            # VIX 해석
            if current_vix < 15:
                sentiment = "😊 안정"
                color = "green"
                interpretation = "시장이 매우 안정적입니다. 위험 자산 투자 적기입니다."
            elif current_vix < 20:
                sentiment = "😐 보통"
                color = "blue"
                interpretation = "시장이 평온한 상태입니다. 정상적인 투자 환경입니다."
            elif current_vix < 30:
                sentiment = "😰 불안"
                color = "orange"
                interpretation = "시장에 불안 요소가 있습니다. 신중한 투자가 필요합니다."
            else:
                sentiment = "😱 공포"
                color = "red"
                interpretation = "시장이 극도로 불안합니다. 방어적 포지션을 고려하세요."
            
            return {
                'current': round(current_vix, 2),
                'avg_1m': round(avg_vix, 2),
                'sentiment': sentiment,
                'color': color,
                'interpretation': interpretation,
                'data': hist,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ VIX 오류: {str(e)}")
            return _self._empty_vix()
    
    def _empty_vix(self) -> Dict:
        """빈 VIX 데이터"""
        return {
            'current': 0,
            'avg_1m': 0,
            'sentiment': 'N/A',
            'color': 'gray',
            'interpretation': '데이터를 가져올 수 없습니다.',
            'data': pd.DataFrame(),
            'last_updated': 'N/A'
        }
    
    # ======================================
    # 💰 M2 통화량 (FRED API)
    # ======================================
    
    @st.cache_data(ttl=86400)  # 24시간 캐시
    def get_m2(_self) -> Dict:
        """
        M2 통화량 데이터 가져오기 (FRED API)
        
        Returns:
            Dict: M2 데이터 및 해석
        """
        if not _self.fred_api_key:
            return _self._empty_m2()
        
        print("\n💰 M2 데이터 수집 중...")
        
        try:
            # FRED API 호출
            params = {
                'series_id': 'M2SL',
                'api_key': _self.fred_api_key,
                'file_type': 'json',
                'limit': 12  # 최근 12개월
            }
            
            response = requests.get(_self.fred_base_url, params=params)
            
            if response.status_code != 200:
                return _self._empty_m2()
            
            data = response.json()
            observations = data.get('observations', [])
            
            if not observations:
                return _self._empty_m2()
            
            # 최근 데이터
            latest = observations[-1]
            prev = observations[-2] if len(observations) > 1 else observations[-1]
            
            current_m2 = float(latest['value'])
            prev_m2 = float(prev['value'])
            
            # 변화율
            change_pct = ((current_m2 - prev_m2) / prev_m2) * 100
            
            # 해석
            if change_pct > 2:
                sentiment = "🟢 강한 확장"
                interpretation = "유동성이 크게 증가하고 있습니다. 위험 자산에 긍정적입니다."
            elif change_pct > 0:
                sentiment = "🟢 완만한 확장"
                interpretation = "유동성이 증가하고 있습니다. 투자에 우호적인 환경입니다."
            elif change_pct > -2:
                sentiment = "🟡 보합"
                interpretation = "유동성이 안정적입니다. 중립적인 시장 환경입니다."
            else:
                sentiment = "🔴 축소"
                interpretation = "유동성이 감소하고 있습니다. 신중한 투자가 필요합니다."
            
            return {
                'current': current_m2,
                'change_pct': round(change_pct, 2),
                'sentiment': sentiment,
                'interpretation': interpretation,
                'date': latest['date'],
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ M2 오류: {str(e)}")
            return _self._empty_m2()
    
    def _empty_m2(self) -> Dict:
        """빈 M2 데이터"""
        return {
            'current': 0,
            'change_pct': 0,
            'sentiment': 'N/A',
            'interpretation': 'FRED API 키가 필요합니다.',
            'date': 'N/A',
            'last_updated': 'N/A'
        }
    
    # ======================================
    # 🎯 종합 시장 분석
    # ======================================
    
    def analyze_market_timing(self) -> Dict:
        """
        종합 시장 타이밍 분석
        
        Returns:
            Dict: 종합 판단 및 점수
        """
        print("\n🎯 시장 타이밍 분석 중...")
        
        # 데이터 수집
        vix_data = self.get_vix()
        m2_data = self.get_m2()
        
        score = 0
        signals = []
        
        # 1. VIX 분석 (최대 50점)
        vix = vix_data['current']
        if vix > 0:
            if vix < 15:
                score += 50
                signals.append("✅ VIX 매우 낮음 (안정)")
            elif vix < 20:
                score += 35
                signals.append("✅ VIX 보통 (평온)")
            elif vix < 30:
                score += 20
                signals.append("⚠️ VIX 높음 (불안)")
            else:
                score += 0
                signals.append("❌ VIX 매우 높음 (공포)")
        
        # 2. M2 분석 (최대 50점)
        m2_change = m2_data['change_pct']
        if m2_change != 0:
            if m2_change > 2:
                score += 50
                signals.append("✅ M2 강한 증가")
            elif m2_change > 0:
                score += 35
                signals.append("✅ M2 완만한 증가")
            elif m2_change > -2:
                score += 20
                signals.append("⚠️ M2 보합")
            else:
                score += 0
                signals.append("❌ M2 감소")
        else:
            # M2 데이터 없으면 VIX만으로 판단
            score = score * 2  # VIX 점수를 2배로
        
        # 종합 판단
        if score >= 70:
            timing = "🟢 강한 매수 타이밍"
            recommendation = "지금은 위험 자산 투자에 좋은 시기입니다."
        elif score >= 50:
            timing = "🟡 중립적 타이밍"
            recommendation = "정상적인 투자 환경입니다. 선별적 투자를 고려하세요."
        elif score >= 30:
            timing = "🔴 주의 필요"
            recommendation = "시장 불확실성이 있습니다. 신중하게 접근하세요."
        else:
            timing = "⚫ 방어적 자세"
            recommendation = "현재는 방어적 포지션을 유지하는 것이 좋습니다."
        
        return {
            'score': score,
            'timing': timing,
            'recommendation': recommendation,
            'signals': signals,
            'vix_data': vix_data,
            'm2_data': m2_data
        }


# 테스트
if __name__ == "__main__":
    print("=" * 60)
    print("🌍 거시 지표 분석 테스트")
    print("=" * 60)
    
    # API 키 없이 테스트 (VIX만)
    indicators = MarketIndicators()
    
    print("\n📊 VIX 분석...")
    vix = indicators.get_vix()
    print(f"현재 VIX: {vix['current']}")
    print(f"심리: {vix['sentiment']}")
    print(f"해석: {vix['interpretation']}")
    
    print("\n🎯 시장 타이밍 분석...")
    analysis = indicators.analyze_market_timing()
    print(f"점수: {analysis['score']}/100")
    print(f"판단: {analysis['timing']}")
    print(f"추천: {analysis['recommendation']}")
    
    print("\n✅ 테스트 완료!")