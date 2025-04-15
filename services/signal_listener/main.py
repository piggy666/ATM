# ATM/services/signal_listener/main.py
import json, os
from fastapi import FastAPI
# 注意：在Docker容器中使用绝对导入而不是相对导入
try:
    from services.signal_listener.router import router
except ImportError:
    # 在本地开发环境中回退使用相对导入
    from .router import router


def get_default_port(service_name: str) -> int:
    """获取服务的默认端口"""
    default_ports = {
        "config_service": 52100,
        "signal_listener": 52110,
        "risk_controller": 52120,
        "dex_executor": 52130,
        "execution_monitor": 52140,
        "asset_manager": 52150
    }
    return default_ports.get(service_name, 52100)
def get_service_port(service_name: str) -> int:
    """
    从位于项目根目录的 config.json 中读取指定服务的端口配置
    本文件相对路径： ATM/services/signal_listener/main.py
    因此 config.json 路径为 "../../config.json"
    """
    # 首先尝试Docker容器中的配置路径
    config_path = "/app/config.json"
    # 检查文件是否真的存在且是文件而不是目录
    if not os.path.isfile(config_path):
        # 本地开发环境的回退路径
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    if os.path.isfile(config_path):
        with open(config_path, "r") as f:
            cfg = json.load(f)
        ports = cfg.get("ports", {})
        return int(ports.get(service_name, get_default_port(service_name)))
    
    # 如果找不到配置文件，使用默认端口
    return get_default_port(service_name)  # 默认52110

app = FastAPI(title="Signal Listener Service", version="1.0")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    port = get_service_port("signal_listener")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
