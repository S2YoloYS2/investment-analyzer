"""
임원 매수 추적 모듈 (Insider Trading Tracker)
SEC Form 4를 분석하여 임원들의 자사주 매수 추적
데이터 소스: SEC EDGAR (공개 데이터, 합법적)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from bs4 import BeautifulSoup


class InsiderTracker:
    """임원 매수 추적 클래스"""
    
    def __init__(self):
        """초기화"""
        self.sec_base_url = "https://www.sec.gov"
        self.headers = {
            'User-Agent': 'Investment Research App contact@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        self.request_delay = 0.11  # SEC Rate Limit: 초당 10 요청
    
    def get_insider_trades(self, ticker: str, months: int = 3) -> pd.DataFrame:
        """
        임원 거래 데이터 가져오기
        
        Args:
            ticker: 종목 코드 (예: 'AAPL')
            months: 조회 기간 (개월)
        
        Returns:
            DataFrame: 임원 거래 내역
        """
        print(f"\n📋 임원 거래 데이터 수집: {ticker} (최근 {months}개월)")
        
        try:
            # 1. CIK 코드 가져오기
            cik = self._get_cik(ticker)
            if not cik:
                print(f"⚠️ CIK 코드를 찾을 수 없습니다: {ticker}")
                return self._empty_dataframe()
            
            # 2. Form 4 목록 가져오기
            form4_list = self._get_form4_list(cik, months)
            if not form4_list:
                print(f"⚠️ Form 4 데이터가 없습니다: {ticker}")
                return self._empty_dataframe()
            
            # 3. 각 Form 4 파싱
            trades = []
            for i, form_url in enumerate(form4_list[:20]):  # 최대 20개
                print(f"  📄 {i+1}/{min(len(form4_list), 20)} 파싱 중...")
                trade_data = self._parse_form4(form_url)
                if trade_data:
                    trades.extend(trade_data)
                time.sleep(self.request_delay)
            
            if not trades:
                return self._empty_dataframe()
            
            # 4. DataFrame 생성
            df = pd.DataFrame(trades)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=False)
            
            print(f"✅ {len(df)}개 임원 거래 수집 완료!")
            return df
            
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            return self._empty_dataframe()
    
    def _get_cik(self, ticker: str) -> Optional[str]:
        """종목 코드로 CIK 코드 찾기"""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(url, headers=self.headers)
            time.sleep(self.request_delay)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            for item in data.values():
                if item['ticker'].upper() == ticker.upper():
                    cik = str(item['cik_str']).zfill(10)
                    print(f"  ✅ CIK 코드: {cik}")
                    return cik
            
            return None
            
        except Exception as e:
            print(f"  ❌ CIK 검색 실패: {str(e)}")
            return None
    
    def _get_form4_list(self, cik: str, months: int) -> List[str]:
        """Form 4 파일 목록 가져오기"""
        try:
            url = f"{self.sec_base_url}/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': '4',
                'dateb': '',
                'owner': 'include',
                'count': 100
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            time.sleep(self.request_delay)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'tableFile2'})
            
            if not table:
                return []
            
            form4_urls = []
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                date_str = cols[3].text.strip()
                try:
                    filing_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if filing_date < cutoff_date:
                        continue
                except:
                    continue
                
                doc_link = cols[1].find('a')
                if doc_link:
                    href = doc_link.get('href')
                    full_url = f"{self.sec_base_url}{href}"
                    form4_urls.append(full_url)
            
            print(f"  ✅ {len(form4_urls)}개 Form 4 발견")
            return form4_urls
            
        except Exception as e:
            print(f"  ❌ Form 4 목록 가져오기 실패: {str(e)}")
            return []
    
    def _parse_form4(self, url: str) -> List[Dict]:
        """Form 4 파일 파싱"""
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            xml_link = None
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if '.xml' in href and 'primary_doc' not in href:
                    xml_link = f"{self.sec_base_url}{href}"
                    break
            
            if not xml_link:
                return []
            
            time.sleep(self.request_delay)
            xml_response = requests.get(xml_link, headers=self.headers)
            
            if xml_response.status_code != 200:
                return []
            
            xml_soup = BeautifulSoup(xml_response.content, 'xml')
            
            owner = xml_soup.find('reportingOwner')
            if not owner:
                return []
            
            insider_name = self._safe_get_text(owner, 'rptOwnerName')
            title = self._safe_get_text(owner, 'officerTitle')
            
            trades = []
            non_derivatives = xml_soup.find_all('nonDerivativeTransaction')
            
            for transaction in non_derivatives:
                date_elem = transaction.find('transactionDate')
                if not date_elem or not date_elem.find('value'):
                    continue
                trade_date = date_elem.find('value').text
                
                code_elem = transaction.find('transactionCode')
                if not code_elem:
                    continue
                trans_code = code_elem.text.strip()
                
                if trans_code != 'P':  # P = 매수만
                    continue
                
                shares_elem = transaction.find('transactionShares')
                shares = float(shares_elem.find('value').text) if shares_elem else 0
                
                price_elem = transaction.find('transactionPricePerShare')
                price = float(price_elem.find('value').text) if price_elem else 0
                
                value = shares * price
                
                trades.append({
                    'date': trade_date,
                    'insider_name': insider_name,
                    'title': title if title else 'N/A',
                    'transaction_type': '매수',
                    'shares': int(shares),
                    'price_per_share': round(price, 2),
                    'value': round(value, 2)
                })
            
            return trades
            
        except Exception as e:
            return []
    
    def _safe_get_text(self, element, tag: str) -> str:
        """XML 요소에서 안전하게 텍스트 추출"""
        found = element.find(tag)
        if found:
            return found.text.strip()
        return "N/A"
    
    def _empty_dataframe(self) -> pd.DataFrame:
        """빈 DataFrame 반환"""
        return pd.DataFrame(columns=[
            'date', 'insider_name', 'title', 'transaction_type',
            'shares', 'price_per_share', 'value'
        ])
    
    def analyze_insider_sentiment(self, df: pd.DataFrame) -> Dict:
        """
        임원 매수 패턴 분석
        
        Args:
            df: 임원 거래 데이터
        
        Returns:
            Dict: 분석 결과
        """
        if df.empty:
            return {
                'signal': '데이터 없음',
                'score': 0,
                'total_buys': 0,
                'total_value': 0,
                'unique_insiders': 0
            }
        
        recent_df = df[df['date'] >= (datetime.now() - timedelta(days=90))]
        
        if recent_df.empty:
            return {
                'signal': '최근 거래 없음',
                'score': 0,
                'total_buys': 0,
                'total_value': 0,
                'unique_insiders': 0
            }
        
        total_buys = len(recent_df)
        total_value = recent_df['value'].sum()
        unique_insiders = recent_df['insider_name'].nunique()
        
        # 점수 계산 (0~100)
        score = 0
        
        # 1. 거래 횟수 (최대 40점)
        if total_buys >= 5:
            score += 40
        elif total_buys >= 3:
            score += 30
        elif total_buys >= 2:
            score += 20
        elif total_buys >= 1:
            score += 10
        
        # 2. 거래 금액 (최대 40점)
        if total_value >= 1000000:
            score += 40
        elif total_value >= 500000:
            score += 30
        elif total_value >= 100000:
            score += 20
        elif total_value > 0:
            score += 10
        
        # 3. 참여 임원 수 (최대 20점)
        if unique_insiders >= 3:
            score += 20
        elif unique_insiders >= 2:
            score += 15
        elif unique_insiders >= 1:
            score += 10
        
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
            'total_buys': total_buys,
            'total_value': total_value,
            'unique_insiders': unique_insiders,
            'avg_value_per_trade': total_value / total_buys if total_buys > 0 else 0
        }


# 테스트
if __name__ == "__main__":
    print("=" * 60)
    print("📋 임원 매수 추적 모듈 테스트")
    print("=" * 60)
    
    tracker = InsiderTracker()
    
    print("\n🍎 Apple 임원 거래 분석...")
    df = tracker.get_insider_trades("AAPL", months=6)
    
    if not df.empty:
        print(f"\n✅ {len(df)}개 거래 발견!")
        print("\n최근 거래:")
        print(df.head(10))
        
        analysis = tracker.analyze_insider_sentiment(df)
        print(f"\n📊 분석 결과:")
        print(f"  신호: {analysis['signal']}")
        print(f"  점수: {analysis['score']}/100")
        print(f"  총 매수 횟수: {analysis['total_buys']}회")
        print(f"  총 매수 금액: ${analysis['total_value']:,.0f}")
        print(f"  참여 임원 수: {analysis['unique_insiders']}명")
    else:
        print("⚠️ 데이터를 가져오지 못했습니다")
    
    print("\n✅ 테스트 완료!")