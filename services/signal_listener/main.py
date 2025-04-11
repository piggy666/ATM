# ATM/services/signal_listener/main.py
import json, os
from fastapi import FastAPI
from router import router

def get_service_port(service_name: str) -> int:
    """
    从位于项目根目录的 config.json 中读取指定服务的端口配置
    本文件相对路径： ATM/services/signal_listener/main.py
    因此 config.json 路径为 "../../config.json"
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)
    ports = cfg.get("ports", {})
    return int(ports.get(service_name, 52110))  # 默认52110

app = FastAPI(title="Signal Listener Service", version="1.0")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    port = get_service_port("signal_listener")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
