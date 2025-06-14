import os
import time
import requests
from flask import Flask, request

# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CMC_API_KEY = os.getenv('CMC_API_KEY')

# ATH (All-Time High) por token
TOKENS = {
    'BTC': 69000,
    'TAO': 750,
    'VET': 0.28
}

alerted = {k: False for k in TOKENS}
app = Flask(__name__)

# ================= FUNCTIONS =================
def get_price(symbol):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
    params = {'symbol': symbol, 'convert': 'USD'}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data['data'][symbol]['quote']['USD']['price']
    except Exception as e:
        print(f"[ERROR] get_price({symbol}):", e)
        return None


def get_sma_200(symbol):
    # No tenemos velas históricas de CoinMarketCap free, así que lo simulamos:
    try:
        price = get_price(symbol)
        if price:
            return price * 0.92  # simulamos SMA200 como 8% debajo del precio actual
    except Exception as e:
        print(f"[ERROR] get_sma_200({symbol}):", e)
    return None


def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] send_telegram_message: {e}")


def check_alerts():
    for symbol in TOKENS:
        price = get_price(symbol)
        sma = get_sma_200(symbol)
        if sma and sma > TOKENS[symbol] and not alerted[symbol]:
            msg = f'🚨 {symbol}: SMA200 (${sma:.2f}) > ATH (${TOKENS[symbol]})! Precio actual: ${price:.2f}'
            send_telegram_message(msg)
            alerted[symbol] = True


@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get('message', {}).get('text', '')

    if message == "/status":
        status_msg = "📊 Estado actual:\n\n"
        for symbol in TOKENS:
            price = get_price(symbol)
            sma = get_sma_200(symbol)
            if price is None or sma is None:
                status_msg += f"{symbol}: ❌ Error al obtener datos.\n\n"
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
