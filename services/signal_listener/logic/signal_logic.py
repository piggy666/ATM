# ATM/services/signal_listener/logic/signal_logic.py
import requests

LAST_SIGNAL = None

def handle_signal(signal: dict):
    global LAST_SIGNAL
    LAST_SIGNAL = signal
    # 将信号转发给 Risk Controller 进行风控校验
    try:
        response = requests.post("http://risk_controller:52120/risk/check", json=signal, timeout=5)
        result = response.json()
    except Exception as e:
        result = {"error": str(e)}
    return result

def get_latest_signal():
    return LAST_SIGNAL
