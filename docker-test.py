"""
ATM Docker 部署测试脚本

该脚本用于测试 ATM 应用的 Docker 部署
当 Docker 环境可用时，可以运行此脚本执行完整测试
"""

import os
import sys
import time
import json
import subprocess
import requests
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("docker_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('docker_test')

# 当前目录
CURRENT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# 服务端口配置
PORT_CONFIG = {
    "config_service": 52100,
    "signal_listener": 52110,
    "risk_controller": 52120,
    "dex_executor": 52130,
    "execution_monitor": 52140,
    "asset_manager": 52150
}

# 测试信号
TEST_SIGNALS = {
    "symbol_format": {
        "symbol": "ETH/USDT",
        "side": "buy",
        "amount": "0.1"
    },
    "token_format": {
        "token_in": "ETH",
        "token_out": "WETH",
        "amount": "0.01"
    }
}


def check_docker_installed():
    """检查 Docker 是否已安装"""
    try:
        result = subprocess.run(['docker', '--version'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode == 0:
            logger.info(f"Docker installed: {result.stdout.strip()}")
            return True
        else:
            logger.error("Docker not found or not working properly")
            return False
    except Exception as e:
        logger.error(f"Error checking Docker: {str(e)}")
        return False


def check_docker_compose_installed():
    """检查 Docker Compose 是否已安装"""
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode == 0:
            logger.info(f"Docker Compose installed: {result.stdout.strip()}")
            return True
        else:
            logger.error("Docker Compose not found or not working properly")
            return False
    except Exception as e:
        logger.error(f"Error checking Docker Compose: {str(e)}")
        return False


def verify_docker_files():
    """验证 Docker 文件是否存在于正确的位置"""
    dockerfile_path = CURRENT_DIR / "Dockerfile"
    compose_path = CURRENT_DIR / "docker-compose.yml"
    requirements_path = CURRENT_DIR / "requirements.txt"
    config_path = CURRENT_DIR / "config.json"
    
    errors = []
    
    if not dockerfile_path.exists():
        errors.append("Dockerfile not found in project root")
    
    if not compose_path.exists():
        errors.append("docker-compose.yml not found in project root")
    
    if not requirements_path.exists():
        errors.append("requirements.txt not found in project root")
    
    if not config_path.exists():
        errors.append("config.json not found (required for container configuration)")
    
    if errors:
        for error in errors:
            logger.error(error)
        return False
    
    logger.info("All required Docker files exist in correct locations")
    return True


def build_docker_images():
    """构建 Docker 镜像"""
    try:
        logger.info("Building Docker images...")
        result = subprocess.run(['docker-compose', 'build'], 
                               cwd=str(CURRENT_DIR),
                               capture_output=True, 
                               text=True, 
                               check=False)
        
        if result.returncode == 0:
            logger.info("Docker images built successfully")
            return True
        else:
            logger.error(f"Failed to build Docker images: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error building Docker images: {str(e)}")
        return False


def start_docker_services(service=None):
    """启动 Docker 服务"""
    try:
        if service:
            cmd = ['docker-compose', 'up', '-d', service]
            logger.info(f"Starting Docker service: {service}...")
        else:
            cmd = ['docker-compose', 'up', '-d']
            logger.info("Starting all Docker services...")
            
        result = subprocess.run(cmd, 
                               cwd=str(CURRENT_DIR),
                               capture_output=True, 
                               text=True, 
                               check=False)
        
        if result.returncode == 0:
            if service:
                logger.info(f"Docker service {service} started successfully")
            else:
                logger.info("All Docker services started successfully")
            return True
        else:
            logger.error(f"Failed to start Docker services: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error starting Docker services: {str(e)}")
        return False


def check_service_health(service_name):
    """检查服务健康状态"""
    port = PORT_CONFIG.get(service_name)
    if not port:
        logger.error(f"Unknown service: {service_name}")
        return False
    
    try:
        # 根据不同服务选择不同的检查端点
        endpoints = {
            "config_service": f"http://localhost:{port}/config/network",
            "signal_listener": f"http://localhost:{port}/signal/latest",
            "risk_controller": f"http://localhost:{port}/risk/status",
            "dex_executor": f"http://localhost:{port}/dex/status",
            "execution_monitor": f"http://localhost:{port}/monitor/status",
            "asset_manager": f"http://localhost:{port}/asset/status"
        }
        
        endpoint = endpoints.get(service_name)
        response = requests.get(endpoint, timeout=5)
        
        if response.status_code == 200:
            logger.info(f"Service {service_name} is healthy")
            return True
        else:
            logger.error(f"Service {service_name} returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to service {service_name} on port {port}")
        return False
    except Exception as e:
        logger.error(f"Error checking service {service_name}: {str(e)}")
        return False


def test_signal_processing():
    """测试信号处理流程"""
    try:
        logger.info("Testing signal processing with token format signal...")
        response = requests.post(
            f"http://localhost:{PORT_CONFIG['signal_listener']}/signal",
            json=TEST_SIGNALS["token_format"],
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Signal processing result: {json.dumps(result, indent=2)}")
            
            if "status" in result.get("result", {}):
                status = result["result"]["status"]
                if status == "success":
                    logger.info("Signal processing test PASSED")
                    return True
                else:
                    logger.error(f"Signal processing failed with status: {status}")
                    return False
            else:
                logger.error("No status in response")
                return False
        else:
            logger.error(f"HTTP Status {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing signal processing: {str(e)}")
        return False


def stop_docker_services():
    """停止 Docker 服务"""
    try:
        logger.info("Stopping Docker services...")
        result = subprocess.run(['docker-compose', 'down'], 
                               cwd=str(CURRENT_DIR),
                               capture_output=True, 
                               text=True, 
                               check=False)
        
        if result.returncode == 0:
            logger.info("Docker services stopped successfully")
            return True
        else:
            logger.error(f"Failed to stop Docker services: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error stopping Docker services: {str(e)}")
        return False


def run_docker_test():
    """运行 Docker 测试套件"""
    logger.info("\n===== ATM Docker Deployment Test =====\n")
    
    # 检查先决条件
    if not check_docker_installed():
        logger.error("Docker is not installed or not available. Please install Docker first.")
        return False
    
    if not check_docker_compose_installed():
        logger.error("Docker Compose is not installed. Please install Docker Compose first.")
        return False
    
    if not verify_docker_files():
        logger.error("Required Docker files are missing. Please check the error messages above.")
        return False
    
    # 构建 Docker 镜像
    if not build_docker_images():
        logger.error("Failed to build Docker images. Test aborted.")
        return False
    
    try:
        # 首先测试配置服务
        logger.info("\n--- Testing Config Service ---\n")
        if not start_docker_services("config_service"):
            logger.error("Failed to start config service. Test aborted.")
            return False
        
        # 等待服务启动
        time.sleep(5)
        
        if not check_service_health("config_service"):
            logger.error("Config service health check failed. Test aborted.")
            stop_docker_services()
            return False
        
        # 启动所有服务进行完整测试
        logger.info("\n--- Testing All Services ---\n")
        if not start_docker_services():
            logger.error("Failed to start all services. Test aborted.")
            stop_docker_services()
            return False
        
        # 等待所有服务启动
        logger.info("Waiting for all services to start...")
        time.sleep(10)
        
        # 测试每个服务的健康状态
        services_health = {}
        for service in PORT_CONFIG.keys():
            logger.info(f"Checking health of {service}...")
            services_health[service] = check_service_health(service)
            time.sleep(1)
        
        unhealthy_services = [s for s, h in services_health.items() if not h]
        if unhealthy_services:
            logger.error(f"The following services are unhealthy: {', '.join(unhealthy_services)}")
        else:
            logger.info("All services are healthy!")
        
        # 测试信号处理流程
        logger.info("\n--- Testing Signal Processing Flow ---\n")
        if test_signal_processing():
            logger.info("Signal processing test passed successfully!")
        else:
            logger.error("Signal processing test failed")
        
        return all(services_health.values()) and all(unhealthy_services)
    finally:
        # 清理环境
        stop_docker_services()


if __name__ == "__main__":
    if run_docker_test():
        logger.info("\n===== Docker Deployment Test: SUCCESS =====\n")
        sys.exit(0)
    else:
        logger.error("\n===== Docker Deployment Test: FAILED =====\n")
        sys.exit(1)
