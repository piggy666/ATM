"""
Mocku670du52a1u5b9eu73b0uff0cu7528u4e8eu6a21u62dfu5404u4e2au5faeu670du52a1u7684u884cu4e3a
u8fd9u4e9bu6a21u62dfu670du52a1u53efu4ee5u5728u6d4bu8bd5u4e2du4f7fu7528uff0cu800cu4e0du9700u8981u8fd0u884cu771fu5b9eu7684u670du52a1u5b9eu4f8b
"""

import json
import time
from flask import Flask, request, jsonify
from threading import Thread
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mock_services')

class MockRiskController:
    def __init__(self, port=52120):
        self.app = Flask("mock_risk_controller")
        self.port = port
        self.server_thread = None
        self.setup_routes()
        
        # u6a21u62dfu72b6u6001
        self.allowed_trades = True
        self.recorded_trades = []
    
    def setup_routes(self):
        @self.app.route('/risk/check', methods=['POST'])
        def check_risk():
            signal = request.json
            logger.info(f"[MockRiskController] Received check_risk request: {signal}")
            
            response = {"allowed": self.allowed_trades}
            if not self.allowed_trades:
                response["reason"] = "Risk check failed (Mock)"
            return jsonify(response)
        
        @self.app.route('/risk/record', methods=['POST'])
        def record_trade():
            trade = request.json
            logger.info(f"[MockRiskController] Received record_trade request: {trade}")
            self.recorded_trades.append(trade)
            return jsonify({"recorded": True, "current_daily_volume": len(self.recorded_trades)})
    
    def start(self):
        def run_app():
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = Thread(target=run_app)
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info(f"[MockRiskController] Started on port {self.port}")
        
    def stop(self):
        if self.server_thread:
            # u5728u771fu5b9eu9879u76eeu4e2du9700u8981u6b63u786eu5730u505cu6b62Flaskuff0cu8fd9u91ccu7b80u5316u5904u7406
            logger.info("[MockRiskController] Stopping...")
            self.server_thread = None

class MockDexExecutor:
    def __init__(self, port=52130):
        self.app = Flask("mock_dex_executor")
        self.port = port
        self.server_thread = None
        self.setup_routes()
        
        # u6a21u62dfu72b6u6001
        self.execution_should_succeed = True
        self.executed_trades = []
    
    def setup_routes(self):
        @self.app.route('/dex/execute', methods=['POST'])
        def execute_trade():
            trade = request.json
            logger.info(f"[MockDexExecutor] Received execute_trade request: {trade}")
            self.executed_trades.append(trade)
            
            if self.execution_should_succeed:
                # u751fu6210u4e00u4e2au6a21u62dfu7684u4ea4u6613u54c8u5e0c
                fake_tx_hash = f"0x{'1234567890abcdef' * 4}"
                response = {"status": "submitted", "tx_hash": fake_tx_hash}
            else:
                response = {"status": "failed", "error": "Execution failed (Mock)"}
            
            return jsonify(response)
    
    def start(self):
        def run_app():
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = Thread(target=run_app)
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info(f"[MockDexExecutor] Started on port {self.port}")
        
    def stop(self):
        if self.server_thread:
            logger.info("[MockDexExecutor] Stopping...")
            self.server_thread = None

class MockExecutionMonitor:
    def __init__(self, port=52140):
        self.app = Flask("mock_execution_monitor")
        self.port = port
        self.server_thread = None
        self.setup_routes()
        
        # u6a21u62dfu72b6u6001
        self.tx_statuses = {}
        self.default_status = "confirmed"  # confirmed, pending, failed
    
    def setup_routes(self):
        @self.app.route('/monitor/tx', methods=['POST'])
        def monitor_tx():
            data = request.json
            tx_hash = data.get("tx_hash")
            logger.info(f"[MockExecutionMonitor] Received monitor_tx request: {data}")
            
            # u4f7fu7528u9884u8bbeu72b6u6001u6216u9ed8u8ba4u72b6u6001
            status = self.tx_statuses.get(tx_hash, self.default_status)
            
            response = {
                "status": status,
                "tx_hash": tx_hash,
                "timestamp": int(time.time()),
                "confirmation_blocks": 12 if status == "confirmed" else 0
            }
            
            return jsonify(response)
    
    def start(self):
        def run_app():
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = Thread(target=run_app)
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info(f"[MockExecutionMonitor] Started on port {self.port}")
        
    def stop(self):
        if self.server_thread:
            logger.info("[MockExecutionMonitor] Stopping...")
            self.server_thread = None

# u542fu52a8u6240u6709u6a21u62dfu670du52a1u7684u4fbfu6377u65b9u5f0f
def start_all_mocks():
    mocks = {
        "risk_controller": MockRiskController(),
        "dex_executor": MockDexExecutor(),
        "execution_monitor": MockExecutionMonitor()
    }
    
    for name, mock in mocks.items():
        mock.start()
        logger.info(f"Started {name} mock service")
    
    return mocks

if __name__ == "__main__":
    # u5f53u76f4u63a5u8fd0u884cu6b64u6587u4ef6u65f6uff0cu542fu52a8u6240u6709u6a21u62dfu670du52a1
    mocks = start_all_mocks()
    try:
        logger.info("All mock services started. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping all mock services...")
        for mock in mocks.values():
            mock.stop()
        logger.info("All mock services stopped.")
