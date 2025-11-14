"""
애널리스트 평가 추적 모듈
Yahoo Finance 데이터를 사용하여 애널리스트 목표가 및 추천 등급 분석
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import streamlit as st


class AnalystTracker:
    """애널리스트 평가 추적 클래스"""
    
    def __init__(self):
        """초기화"""
        self.cache = {}
    
    @st.cache_data(ttl=3600)  # 1시간 캐시
    def get_analyst_ratings(_self, ticker: str) -> Dict:
        """
        애널리스트 평가 데이터 가져오기
        
        Args:
            ticker: 종목 코드 (예: 'AAPL')
        
        Returns:
            Dict: 애널리스트 평가 정보
        """
        print(f"\n📊 애널리스트 평가 수집: {ticker}")
        
        try:
            stock = yf.Ticker(ticker)
            
            # 1. 추천 등급 (Recommendations)
            recommendations = _self._get_recommendations(stock)
            
            # 2. 목표가 정보
            target_price = _self._get_target_price(stock)
            
            # 3. 애널리스트 수
            analyst_count = _self._get_analyst_count(stock)
            
            # 4. 추천 트렌드 분석
            trend = _self._analyze_trend(recommendations)
            
            result = {
                'recommendations': recommendations,
                'target_price': target_price,
                'analyst_count': analyst_count,
                'trend': trend,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"✅ 애널리스트 데이터 수집 완료!")
            return result
            
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            return _self._empty_result()
    
    def _get_recommendations(self, stock) -> pd.DataFrame:
        """추천 등급 가져오기"""
        try:
            rec = stock.recommendations
            if rec is None or rec.empty:
                return pd.DataFrame()
            
            # 최근 3개월 데이터만
            cutoff = datetime.now() - timedelta(days=90)
            if 'Date' in rec.columns:
                rec = rec[rec['Date'] >= cutoff]
            elif isinstance(rec.index, pd.DatetimeIndex):
                rec = rec[rec.index >= cutoff]
            
            return rec
            
        except:
            return pd.DataFrame()
    
    def _get_target_price(self, stock) -> Dict:
        """목표가 정보 가져오기"""
        try:
            info = stock.info
            
            current_price = info.get('currentPrice', 0)
            target_mean = info.get('targetMeanPrice', 0)
            target_high = info.get('targetHighPrice', 0)
            target_low = info.get('targetLowPrice', 0)
            
            # 상승 여력 계산
            if current_price > 0 and target_mean > 0:
                upside = ((target_mean - current_price) / current_price) * 100
            else:
                upside = 0
            
            return {
                'current': current_price,
                'target_mean': target_mean,
                'target_high': target_high,
                'target_low': target_low,
                'upside_percent': upside
            }
            
        except:
            return {
                'current': 0,
                'target_mean': 0,
                'target_high': 0,
                'target_low': 0,
                'upside_percent': 0
            }
    
    def _get_analyst_count(self, stock) -> int:
        """애널리스트 수 가져오기"""
        try:
            info = stock.info
            return info.get('numberOfAnalystOpinions', 0)
        except:
            return 0
    
    def _analyze_trend(self, recommendations: pd.DataFrame) -> Dict:
        """추천 트렌드 분석"""
        if recommendations.empty:
            return {
                'buy': 0,
                'hold': 0,
                'sell': 0,
                'total': 0,
                'buy_percent': 0,
                'dominant': 'N/A'
            }
        
        try:
            # 최근 추천 등급 집계
            if 'To Grade' in recommendations.columns:
                grade_col = 'To Grade'
            elif 'Action' in recommendations.columns:
                grade_col = 'Action'
            else:
                return self._empty_trend()
            
            grades = recommendations[grade_col].str.lower()
            
            # Buy 계열 카운트
            buy_keywords = ['buy', 'outperform', 'overweight', 'positive']
            buy_count = sum(grades.str.contains('|'.join(buy_keywords), na=False))
            
            # Hold 계열 카운트
            hold_keywords = ['hold', 'neutral', 'equal', 'perform']
            hold_count = sum(grades.str.contains('|'.join(hold_keywords), na=False))
            
            # Sell 계열 카운트
            sell_keywords = ['sell', 'underperform', 'underweight', 'negative']
            sell_count = sum(grades.str.contains('|'.join(sell_keywords), na=False))
            
            total = buy_count + hold_count + sell_count
            
            if total == 0:
                return self._empty_trend()
            
            buy_percent = (buy_count / total) * 100
            
            # 지배적 의견
            if buy_count > hold_count and buy_count > sell_count:
                dominant = '매수 우세'
            elif hold_count > buy_count and hold_count > sell_count:
                dominant = '중립 우세'
            elif sell_count > buy_count and sell_count > hold_count:
                dominant = '매도 우세'
            else:
                dominant = '혼조'
            
            return {
                'buy': buy_count,
                'hold': hold_count,
                'sell': sell_count,
                'total': total,
                'buy_percent': buy_percent,
                'dominant': dominant
            }
            
        except:
            return self._empty_trend()
    
    def _empty_trend(self) -> Dict:
        """빈 트렌드 데이터"""
        return {
            'buy': 0,
            'hold': 0,
            'sell': 0,
            'total': 0,
            'buy_percent': 0,
            'dominant': 'N/A'
        }
    
    def _empty_result(self) -> Dict:
        """빈 결과 반환"""
        return {
            'recommendations': pd.DataFrame(),
            'target_price': {
                'current': 0,
                'target_mean': 0,
                'target_high': 0,
                'target_low': 0,
                'upside_percent': 0
            },
            'analyst_count': 0,
            'trend': self._empty_trend(),
            'last_updated': 'N/A'
        }
    
    def analyze_sentiment(self, data: Dict) -> Dict:
        """
        애널리스트 센티먼트 분석
        
        Args:
            data: get_analyst_ratings 결과
        
        Returns:
            Dict: 분석 결과 (신호, 점수)
        """
        if not data or data.get('analyst_count', 0) == 0:
            return {
                'signal': '데이터 없음',
                'score': 0,
                'reason': '애널리스트 데이터가 없습니다'
            }
        
        score = 0
        reasons = []
        
        # 1. 목표가 상승 여력 (최대 40점)
        upside = data['target_price']['upside_percent']
        if upside >= 20:
            score += 40
            reasons.append(f"높은 상승 여력 (+{upside:.1f}%)")
        elif upside >= 10:
            score += 30
            reasons.append(f"적정 상승 여력 (+{upside:.1f}%)")
        elif upside >= 5:
            score += 20
            reasons.append(f"소폭 상승 여력 (+{upside:.1f}%)")
        elif upside > 0:
            score += 10
            reasons.append(f"미미한 상승 여력 (+{upside:.1f}%)")
        else:
            reasons.append(f"목표가 하회 중 ({upside:.1f}%)")
        
        # 2. 매수 추천 비율 (최대 40점)
        buy_percent = data['trend']['buy_percent']
        if buy_percent >= 70:
            score += 40
            reasons.append(f"강한 매수 추천 ({buy_percent:.0f}%)")
        elif buy_percent >= 50:
            score += 30
            reasons.append(f"매수 추천 우세 ({buy_percent:.0f}%)")
        elif buy_percent >= 30:
            score += 20
            reasons.append(f"혼조 ({buy_percent:.0f}%)")
        else:
            reasons.append(f"매수 추천 약함 ({buy_percent:.0f}%)")
        
        # 3. 애널리스트 수 (최대 20점)
        analyst_count = data['analyst_count']
        if analyst_count >= 20:
            score += 20
            reasons.append(f"충분한 커버리지 ({analyst_count}명)")
        elif analyst_count >= 10:
            score += 15
            reasons.append(f"적정 커버리지 ({analyst_count}명)")
        elif analyst_count >= 5:
            score += 10
            reasons.append(f"제한적 커버리지 ({analyst_count}명)")
        else:
            reasons.append(f"낮은 커버리지 ({analyst_count}명)")
        
        # 신호 판정
        if score >= 70:
            signal = '🟢 강한 매수 신호'
        elif score >= 50:
            signal = '🟡 중립적 신호'
        elif score >= 30:
            signal = '🟠 약한 신호'
        else:
            signal = '⚪ 신호 없음'
        
        return {
            'signal': signal,
            'score': score,
            'reasons': reasons
        }


# 테스트
if __name__ == "__main__":
    print("=" * 60)
    print("📊 애널리스트 평가 추적 모듈 테스트")
    print("=" * 60)
    
    tracker = AnalystTracker()
    
    print("\n🍎 Apple 애널리스트 평가...")
    data = tracker.get_analyst_ratings("AAPL")
    
    if data['analyst_count'] > 0:
        print(f"\n✅ 애널리스트 수: {data['analyst_count']}명")
        print(f"\n📈 목표가 정보:")
        print(f"  현재가: ${data['target_price']['current']:.2f}")
        print(f"  평균 목표가: ${data['target_price']['target_mean']:.2f}")
        print(f"  상승 여력: {data['target_price']['upside_percent']:.1f}%")
        
        print(f"\n👥 추천 분포:")
        trend = data['trend']
        print(f"  매수: {trend['buy']}개")
        print(f"  보유: {trend['hold']}개")
        print(f"  매도: {trend['sell']}개")
        print(f"  지배적 의견: {trend['dominant']}")
        
        # 분석
        analysis = tracker.analyze_sentiment(data)
        print(f"\n📊 종합 분석:")
        print(f"  신호: {analysis['signal']}")
        print(f"  점수: {analysis['score']}/100")
        print(f"  이유:")
        for reason in analysis['reasons']:
            print(f"    - {reason}")
    else:
        print("⚠️ 데이터를 가져오지 못했습니다")
    
    print("\n✅ 테스트 완료!")