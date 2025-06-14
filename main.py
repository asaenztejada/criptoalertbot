import os
import time
import requests
from flask import Flask, request

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CMC_API_KEY = os.getenv('CMC_API_KEY')

# CoinMarketCap symbols y ATHs
TOKENS = {
    'BTC': 69000,
    'TAO': 750,
    'VET': 0.28
}

CMC_IDS = {
    'BTC': 'bitcoin',
    'TAO': 'bittensor',
    'VET': 'vechain'
}

app = Flask(__name__)
alerted = {k: False for k in TOKENS}

def get_price(symbol):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
    params = {'symbol': symbol, 'convert': 'USD'}
    res = requests.get(url, headers=headers, params=params)
    try:
        return res.json()['data'][symbol]['quote']['USD']['price']
    except:
        return None

def get_sma_200(symbol):
    return TOKENS[symbol] * 0.92  # simulado, podés conectar otra API de velas si querés SMA real

def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': text})

def check_alerts():
    for symbol in TOKENS:
        price = get_price(symbol)
        sma = get_sma_200(symbol)
        if price and sma and sma > TOKENS[symbol] and not alerted[symbol]:
            send_telegram_message(f"🚨 {symbol}: SMA200 ({sma:.2f}) > ATH ({TOKENS[symbol]}) — Price: ${price:.2f}")
            alerted[symbol] = True

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get("message", {}).get("text") == "/status":
        status_msg = "📊 Estado actual:\n"
        for symbol in TOKENS:
            price = get_price(symbol)
            sma = get_sma_200(symbol)
            if price is None:
                status_msg += f"{symbol}: ❌ No disponible\n"
            else:
                status_msg += f"{symbol}:\n - Precio: ${price:.2f}\n - SMA200: ${sma:.2f}\n - ATH: ${TOKENS[symbol]}\n\n"
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
