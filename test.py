import yfinance as yf
import requests
import time
import os
from datetime import datetime

# ==========================================
# 👇 [수정] 토큰을 코드에 직접 적지 않고,
#    환경 변수(os.environ)에서 가져오게 바꿉니다.
# ==========================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

my_portfolio = {
    "환율(USD/KRW) 💵": "KRW=X",  # 이거 한 줄 추가!
    "TQQQ 🇺🇸": "TQQQ",
    "SGOV 🇺🇸": "SGOV",
    "삼성전자우 🇰🇷": "005935.KS",
    "카카오 🇰🇷": "035720.KS"
}

def send_telegram_message(text):
    """메시지를 보내고 결과를 출력하는 함수"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 연결 에러: {e}")

def calculate_rsi(data, window=14):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(com=window-1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window-1, min_periods=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ==========================================
# 1. 오프닝 메시지 전송
# ==========================================
now = datetime.now().strftime("%Y-%m-%d %H:%M")
print(f"🚀 [자산 브리핑 시작] {now}")
send_telegram_message(f"☀️ 굿모닝! 주인님.\n{now} 기준 자산 브리핑을 시작합니다.")

# ==========================================
# 2. 종목별로 분석하고 바로바로 보내기
# ==========================================
for name, ticker in my_portfolio.items():
    print(f"🔄 {name} 분석 중...")
    
    try:
        # 데이터 수집
        data = yf.Ticker(ticker)
        hist = data.history(period="3mo")

        if len(hist) < 14:
            send_telegram_message(f"⚠️ {name}: 데이터가 부족합니다.")
            continue

        # RSI 및 데이터 계산
        hist['RSI'] = calculate_rsi(hist)
        today_close = hist['Close'].iloc[-1]
        yesterday_close = hist['Close'].iloc[-2]
        current_rsi = hist['RSI'].iloc[-1]
        change_pct = ((today_close - yesterday_close) / yesterday_close) * 100

        # 포맷팅
        currency = "₩" if ".KS" in ticker else "$"
        price_fmt = f"{today_close:,.0f}" if ".KS" in ticker else f"{today_close:.2f}"
        icon = "📈" if change_pct > 0 else "📉"
        
        # 상태 판단
        if current_rsi > 70: status = "🔴 과매수 (위험)"
        elif current_rsi < 30: status = "🟢 과매도 (기회)"
        elif current_rsi < 40: status = "🟡 매수대기"
        else: status = "⚪ 중립"

        # 💌 개별 메시지 작성
        message = (
            f"📊 {name}\n"
            f"💰 {currency}{price_fmt} ({change_pct:.2f}% {icon})\n"
            f"🔥 RSI: {current_rsi:.1f} | {status}"
        )
        
        # 🚀 바로 전송!
        send_telegram_message(message)
        
        # 너무 빨리 보내면 텔레그램이 싫어할 수 있으니 1초 쉬기
        time.sleep(1)

    except Exception as e:
        error_msg = f"❌ {name} 분석 중 오류 발생: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

print("✅ 모든 브리핑 완료!")

send_telegram_message("🏁 이상 브리핑을 마칩니다. 오늘도 성투하세요!")
