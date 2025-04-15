"""
ATM系统的集成测试
使用mock服务测试信号处理的完整流程
"""

import os
import sys
import time
import json
import requests
import logging
import argparse
from threading import Thread

# 使用localhost而非127.0.0.1访问服务，保持一致性
os.environ['NO_PROXY'] = '*'

# 添加项目根目录到Python路径
# 确保可以导入测试配置和mock服务
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 导入测试配置和mock服务
from TESTCASES.test_config import TEST_SIGNALS
from TESTCASES.mocks.mock_services import MockRiskController, MockDexExecutor, MockExecutionMonitor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('integration_test')

# 服务端口配置
PORT_CONFIG = {
    "signal_listener": 52110,
    "risk_controller": 52120,
    "dex_executor": 52130,
    "execution_monitor": 52140
}

# 通用请求方法，使用Session和trust_env=False
def make_request(url, method='get', json_data=None, timeout=10):
    """通用请求方法，使用Session和trust_env=False"""
    session = requests.Session()
    session.trust_env = False
    
    try:
        if method.lower() == 'post':
            return session.post(url, json=json_data, timeout=timeout)
        else:
            return session.get(url, timeout=timeout)
    except Exception as e:
        logger.error(f"Request error ({url}): {str(e)}")
        raise e

# 直接使用Flask实现信号监听服务
def run_signal_listener_server(port=52110):
    """运行信号监听服务的模拟服务器"""
    from flask import Flask, request, jsonify
    
    app = Flask("mock_signal_listener")
    
    @app.route('/signal', methods=['POST'])
    def handle_signal():
        signal_data = request.json
        logger.info(f"Received signal: {json.dumps(signal_data, indent=2)}")
        # 调用mock服务处理信号
        try:
            # 先调用风控服务
            risk_url = f"http://localhost:{PORT_CONFIG['risk_controller']}/risk/check"
            risk_response = make_request(
                risk_url,
                method='post',
                json_data=signal_data,
                timeout=5
            ).json()
            
            if risk_response.get("allowed", False):
                # 然后调用DEX执行器
                dex_url = f"http://localhost:{PORT_CONFIG['dex_executor']}/dex/execute"
                dex_response = make_request(
                    dex_url,
                    method='post',
                    json_data=signal_data,
                    timeout=5
                ).json()
                
                tx_hash = dex_response.get("tx_hash", "")
                if tx_hash:
                    # 最后调用执行监控
                    monitor_url = f"http://localhost:{PORT_CONFIG['execution_monitor']}/monitor/tx"
                    monitor_response = make_request(
                        monitor_url,
                        method='post',
                        json_data={"tx_hash": tx_hash, "original_signal": signal_data},
                        timeout=5
                    ).json()
                    
                    return jsonify({
                        "result": {
                            "status": "success",
                            "tx_hash": tx_hash,
                            "monitor_status": monitor_response.get("status", "unknown")
                        }
                    })
                else:
                    return jsonify({
                        "result": {
                            "status": "failed",
                            "reason": "DEX execution failed"
                        }
                    })
            else:
                return jsonify({
                    "result": {
                        "status": "rejected",
                        "reason": risk_response.get("reason", "Risk check failed")
                    }
                })
        except Exception as e:
            logger.error(f"Error processing signal: {str(e)}")
            return jsonify({
                "result": {
                    "status": "error",
                    "error": str(e)
                }
            }), 500
    
    @app.route('/signal/latest', methods=['GET'])
    def get_latest_signal():
        # 简单实现返回一个空对象
        return jsonify({"latest_signal": {}})
    
    logger.info(f"Starting mock signal listener on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_all_services():
    """启动所有模拟服务和信号监听服务"""
    # 创建并启动各个模拟服务
    risk_controller = MockRiskController(port=PORT_CONFIG['risk_controller'])
    dex_executor = MockDexExecutor(port=PORT_CONFIG['dex_executor'])
    execution_monitor = MockExecutionMonitor(port=PORT_CONFIG['execution_monitor'])
    
    risk_controller.start()
    dex_executor.start()
    execution_monitor.start()
    
    # 启动信号监听服务
    signal_thread = Thread(target=run_signal_listener_server, args=(PORT_CONFIG['signal_listener'],))
    signal_thread.daemon = True
    signal_thread.start()
    
    # 等待所有服务启动
    logger.info("Waiting for all services to start...")
    time.sleep(3)  # 等待所有服务启动
    
    return {
        "risk_controller": risk_controller,
        "dex_executor": dex_executor, 
        "execution_monitor": execution_monitor,
        "signal_thread": signal_thread
    }

def test_process_signal(signal_data):
    """发送测试信号并验证处理结果"""
    logger.info(f"Testing with signal: {json.dumps(signal_data, indent=2)}")
    
    try:
        # 发送信号到信号监听服务
        signal_url = f"http://localhost:{PORT_CONFIG['signal_listener']}/signal"
        response = make_request(
            signal_url,
            method='post',
            json_data=signal_data,
            timeout=10
        )
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Signal processing result: {json.dumps(result, indent=2)}")
            
            # 验证结果
            if "status" in result.get("result", {}):
                status = result["result"]["status"]
                if status == "success":
                    logger.info("Test PASSED: Signal processed successfully")
                    return True
                else:
                    logger.error(f"Test FAILED: Signal processing status: {status}")
                    return False
            else:
                logger.error("Test FAILED: No status in response")
                return False
        else:
            logger.error(f"Test FAILED: HTTP Status {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Test FAILED: Exception occurred: {str(e)}")
        return False

def run_all_tests():
    """运行所有测试用例"""
    services = start_all_services()
    logger.info("All services started, running tests...")
    
    # 定义测试用例
    test_cases = [
        {"name": "Symbol Format Test", "data": TEST_SIGNALS["symbol_format"]},
        {"name": "Token Format Test", "data": TEST_SIGNALS["token_format"]},
        {"name": "Address Format Test", "data": TEST_SIGNALS["address_format"]},
        {"name": "With Wallet Test", "data": TEST_SIGNALS["with_wallet"]}
    ]
    
    results = []
    for test_case in test_cases:
        logger.info(f"Running test: {test_case['name']}")
        result = test_process_signal(test_case["data"])
        results.append({
            "name": test_case["name"],
            "passed": result
        })
        time.sleep(1)  # 测试间隔
    
    # 生成测试报告
    logger.info("\n====== Integration Test Report ======")
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    logger.info(f"Tests: {passed}/{total} passed")
    
    for result in results:
        status = "PASSED" if result["passed"] else "FAILED"
        logger.info(f"{result['name']}: {status}")
    
    logger.info("===================================")
    
    return passed == total

def handle_command_line():
    """处理命令行参数"""
    parser = argparse.ArgumentParser(description='ATM System Integration Test')
    parser.add_argument('--signal', choices=['symbol', 'token', 'address', 'wallet'],
                        help='Run a specific test signal')
    args = parser.parse_args()
    
    if args.signal:
        services = start_all_services()
        signal_type = args.signal
        signal_data = TEST_SIGNALS[f"{signal_type}_format"]
        if signal_type == "wallet":
            signal_data = TEST_SIGNALS["with_wallet"]
        
        logger.info(f"Running single test with signal type: {signal_type}")
        test_process_signal(signal_data)
    else:
        run_all_tests()

if __name__ == "__main__":
    handle_command_line()
