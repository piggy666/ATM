"""
ATMu7cfbu7edfu7684u96c6u6210u6d4bu8bd5
u4f7fu7528mocku670du52a1u6d4bu8bd5u4fe1u53f7u5904u7406u7684u5b8cu6574u6d41u7a0b
"""

import os
import sys
import time
import json
import requests
import logging
import argparse
from threading import Thread

# u6dfbu52a0u9879u76eeu6839u76eeu5f55u5230Pythonu8defu5f84
# u786eu4fddu53efu4ee5u5bfcu5165u6d4bu8bd5u914du7f6eu548cu6a21u62dfu670du52a1
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# u5bfcu5165u6d4bu8bd5u914du7f6eu548cmocku670du52a1
from TESTCASES.test_config import TEST_SIGNALS
from TESTCASES.mocks.mock_services import MockRiskController, MockDexExecutor, MockExecutionMonitor

# u914du7f6eu65e5u5fd7
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('integration_test')

def run_signal_listener_server(port=52110):
    """u8fd0u884cu4fe1u53f7u76d1u542cu670du52a1u7684u6a21u62dfu670du52a1u5668"""
    # u8fd9u91ccu5c06u5b9eu9645u4f7fu7528u771fu5b9eu7684SignalListeneru670du52a1u4ee3u7801
    # u6211u4eecu5c06u4f7fu7528fastapiu542fu52a8u670du52a1
    import uvicorn
    from fastapi import FastAPI
    from services.signal_listener.router import router as signal_router
    
    app = FastAPI()
    app.include_router(signal_router)
    
    # u542fu52a8u670du52a1
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


def start_all_services():
    """u542fu52a8u6240u6709u7684u6a21u62dfu670du52a1u548cu771fu5b9eu7684u4fe1u53f7u76d1u542cu670du52a1"""
    # u521bu5efau5e76u542fu52a8u5404u4e2au6a21u62dfu670du52a1
    risk_controller = MockRiskController(port=52120)
    dex_executor = MockDexExecutor(port=52130)
    execution_monitor = MockExecutionMonitor(port=52140)
    
    risk_controller.start()
    dex_executor.start()
    execution_monitor.start()
    
    # u542fu52a8u4fe1u53f7u76d1u542cu670du52a1
    signal_thread = Thread(target=run_signal_listener_server, args=(52110,))
    signal_thread.daemon = True
    signal_thread.start()
    
    # u7b49u5f85u6240u6709u670du52a1u542fu52a8
    logger.info("Waiting for all services to start...")
    time.sleep(3)  # u7b49u5f85u6240u6709u670du52a1u542fu52a8
    
    return {
        "risk_controller": risk_controller,
        "dex_executor": dex_executor, 
        "execution_monitor": execution_monitor,
        "signal_thread": signal_thread
    }


def test_process_signal(signal_data):
    """u53d1u9001u6d4bu8bd5u4fe1u53f7u5e76u9a8cu8bc1u5904u7406u7ed3u679c"""
    logger.info(f"Testing with signal: {json.dumps(signal_data, indent=2)}")
    
    try:
        # u53d1u9001u4fe1u53f7u5230u4fe1u53f7u76d1u542cu670du52a1
        response = requests.post(
            "http://localhost:52110/signal",
            json=signal_data,
            timeout=10
        )
        
        # u68c0u67e5u54cdu5e94
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Signal processing result: {json.dumps(result, indent=2)}")
            
            # u9a8cu8bc1u7ed3u679c
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
    """u8fd0u884cu6240u6709u6d4bu8bd5u7528u4f8b"""
    services = start_all_services()
    logger.info("All services started, running tests...")
    
    # u5b9au4e49u6d4bu8bd5u7528u4f8b
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
        time.sleep(1)  # u6d4bu8bd5u95f4u9694
    
    # u6253u5370u6d4bu8bd5u62a5u544a
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
    """u5904u7406u547du4ee4u884cu53c2u6570"""
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
