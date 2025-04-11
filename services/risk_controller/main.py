# ATM/services/risk_controller/main.py
import json, os
from fastapi import FastAPI
from router import router

def get_service_port(service_name: str) -> int:
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)
    ports = cfg.get("ports", {})
    return int(ports.get(service_name, 52120))

app = FastAPI(title="Risk Controller Service", version="1.0")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    port = get_service_port("risk_controller")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
