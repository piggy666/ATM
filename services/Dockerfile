# ATM/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装编译工具
RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 默认启动 signal_listener（可在 docker-compose 中覆盖 CMD）
CMD ["uvicorn", "services/signal_listener/main:app", "--host", "0.0.0.0", "--port", "52110"]
