import os
import time
import requests
from flask import Flask, request

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

ATH = {
    'bitcoin': 69000,
    'bittensor': 750,
    'vechain': 0.28
}

alerted = {k: False for k in ATH}
app = Flask(__name__)

def get_price(token_id):
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {'ids': token_id, 'vs_currencies': 'usd'}
        data = requests.get(url, params=params).json()
        return data.get(token_id, {}).get('usd', None)
    except:
        return None

def get_sma_200(token_id):
    try:
        url = f'https://api.coingecko.com/api/v3/coins/{token_id}/market_chart'
        params = {'vs_currency': 'usd', 'days': '1500', 'interval': 'daily'}
        data = requests.get(url, params=params).json().get('prices', [])
        prices = [p[1] for p in data]
        if len(prices) < 200:
            return None
        return sum(prices[-200:]) / 200
    except:
        return None

def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
    requests.post(url, data=payload)

def check_alerts():
    for token in ATH:
        price = get_price(token)
        sma = get_sma_200(token)
        if price is None or sma is None:
            continue
        if sma > ATH[token] and not alerted[token]:
            msg = f'🚨 {token.upper()}: SMA200 ({sma:.2f}) > ATH ({ATH[token]})! Price: ${price:.2f}'
            send_telegram_message(msg)
            alerted[token] = True

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get('message', {}).get('text', '')

    if message == "/status":
        status_msg = "📊 Estado actual:\n"
        for token in ATH:
            price = get_price(token)
            sma = get_sma_200(token)
            if price is None or sma is None:
                status_msg += f"{token.upper()}: ❌ Error al obtener datos.\n\n"
                continue
            status_msg += f"{token.upper()}:\n - Precio: ${price:.2f}\n - SMA200: ${sma:.2f}\n - ATH: ${ATH[token]}\n\n"
        send_telegram_message(status_msg)

    return {'ok': True}

if __name__ == '__main__':
    import threading

    def background_loop():
        while True:
            check_alerts()
            time.sleep(3600)

    threading.Thread(target=background_loop).start()
    app.run(host='0.0.0.0', port=8080)
