import requests

def send_telegram_alert(token, chat_id, msg):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg})
