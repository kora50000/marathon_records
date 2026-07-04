import os
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 텔레그램 설정 데이터
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def get_top_60_trading_value():
    """네이버 금융에서 코스피/코스닥 거래대금 상위 종목을 수집하여 상위 60개 추출"""
    print("거래대금 상위 종목 수집 중...")
    
    # 코스피 거래대금 상위
    url_kospi = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
    # 코스닥 거래대금 상위
    url_kosdaq = "https://finance.naver.com/sise/sise_quant.naver?sosok=1"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    stock_list = []
    
    for url in [url_kospi, url_kosdaq]:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'type_2'})
        
        if not table:
            continue
            
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 12:
                continue
            
            # 종목명 및 링크 분석
            a_tag = cols[1].find('a')
            if not a_tag:
                continue
                
            name = a_tag.text.strip()
            code = a_tag['href'].split('code=')[-1]
            
            # 거래대금 (단위: 백만)
            try:
                trading_value = int(cols[7].text.strip().replace(',', ''))
            except ValueError:
                continue
                
            stock_list.append({
                'code': code,
                'name': name,
                'trading_value': trading_value
            })
            
    # 전체 리스트를 거래대금 기준으로 내림차순 정렬 후 상위 60개 추출
    df = pd.DataFrame(stock_list)
    df = df.sort_values(by='trading_value', ascending=False).head(60)
    return df.to_dict('records')

def get_provisional_supply_demand(code, name):
    """각 종목의 14:30 투자자별 장중 잠정 매매동향 수집"""
    url = f"https://finance.naver.com/item/frgn.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # '장중 잠정' 테이블 탐색
    tables = soup.find_all('table', {'class': 'type_2'})
    
    # 보통 페이지 하단 혹은 중간에 있는 잠정동향 테이블 추출
    target_table = None
    for t in tables:
        th_tags = t.find_all('th')
        th_texts = [th.text.strip() for th in th_tags]
        if '장중잠정' in th_texts or '외국인' in th_texts and '기관' in th_texts:
            # 테이블 요약정보나 구조로 잠정 테이블 타겟팅
            if '외국인계' in t.text or '기관합계' in t.text:
                target_table = t
                break
                
    if not target_table:
        return None
        
    try:
        rows = target_table.find_all('tr')
        # 잠정 데이터가 기재된 행 분석 (네이버 금융 구조 기준)
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                # 외국인 잠정치, 기관 잠정치 숫자 파싱
                # 네이버 양식에 맞춰 순매수 수량/금액 파싱 (플러스/마이너스 부호 처리)
                # 장중잠정치는 통상 거래소 기준 거래량(주)으로 집계됨
                frgn_text = cols[1].text.strip().replace(',', '')
                inst_text = cols[3].text.strip().replace(',', '')
                
                # 상승/하락 부호(붉은색/푸른색 클래스) 처리
                frgn_val = int(frgn_text) if frgn_text.replace('-', '').isdigit() else 0
                inst_val = int(inst_text) if inst_text.replace('-', '').isdigit() else 0
                
                # 텍스트에 마이너스 기호가 누락되었으나 파란색 글씨인 경우 예외처리 등을 포함하여 정제
                if 'nv01' in cols[1].get('class', []): frgn_val = -abs(frgn_val)
                if 'nv01' in cols[3].get('class', []): inst_val = -abs(inst_val)
                
                return {
                    'name': name,
                    'foreign': frgn_val,
                    'institution': inst_val,
                    'total': frgn_val + inst_val
                }
    except Exception as e:
        print(f"{name} 수급 분석 중 오류 발생: {e}")
        
    return None

def send_telegram_message(message):
    """결과를 텔레그램으로 전송"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)

def main():
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    top_stocks = get_top_60_trading_value()
    
    selected_stocks = []
    print("상위 60개 종목 잠정 수급 분석 중...")
    
    for stock in top_stocks:
        data = get_provisional_supply_demand(stock['code'], stock['name'])
        if data and data['total'] > 0:
            selected_stocks.append(data)
            
    # 결과를 메시지로 포맷팅
    if not selected_stocks:
        message = f"📅 *{today_str} 14:30 수급 알림*\n\n거래대금 상위 60개 종목 중 [외인+기관] 합산 순매수 플러스인 종목이 없습니다."
    else:
        message = f"📅 *{today_str} 14:30 수급 알림*\n"
        message += f"🔥 *거래대금 상위 60위 중 외인+기관 합산 플러스 기업*\n\n"
        message += f"| 종목명 | 외인잠정 | 기관잠정 | 합산수급 |\n"
        message += f"| :--- | :---: | :---: | :---: |\n"
        
        # 합산 수급이 높은 순서대로 정렬해서 출력
        selected_stocks = sorted(selected_stocks, key=lambda x: x['total'], reverse=True)
        
        for s in selected_stocks:
            # 수치가 보기 편하게 기호 추가
            f_sign = f"+{s['foreign']:,}" if s['foreign'] > 0 else f"{s['foreign']:,}"
            i_sign = f"+{s['institution']:,}" if s['institution'] > 0 else f"{s['institution']:,}"
            t_sign = f"+{s['total']:,}" if s['total'] > 0 else f"{s['total']:,}"
            
            message += f"| {s['name']} | {f_sign} | {i_sign} | *{t_sign}* |\n"
            
        message += f"\n💡 _주의: 거래소 발표 장중 잠정치(주 단위) 기준이므로 장 마감 확정치와 다를 수 있으며, 차트와 과거 수급을 함께 분석해 보세요._"

    print("텔레그램 발송 완료!")
    send_telegram_message(message)

if __name__ == "__main__":
    main()
  
