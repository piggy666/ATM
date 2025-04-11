# ATM 系统测试方案

本文档详细介绍了 ATM (自动交易模块) 系统的测试方案、测试用例和执行指南。

## 测试环境准备

### 1. 虚拟环境与依赖

已经创建了虚拟环境，并安装了测试所需的所有依赖。使用以下命令激活虚拟环境：

```powershell
# 在项目根目录下执行
.\venv\Scripts\Activate.ps1
```

如果需要安装额外的依赖，使用以下命令：

```powershell
pip install -r services/requirements.txt
pip install pytest pytest-mock requests-mock flask
```

### 2. 测试钱包配置

测试使用的钱包信息已经在 `config.json` 中配置：

```json
"wallet": {
  "address": "0x8456562E8f91C9f791335f60388E2F777AE077eB",
  "private_key": "62a030db1bf7e52c98f89a20f554a581c427f884d65fe39c5a9de0a495162e0f"
}
```

**注意**：这个钱包仅用于测试目的，不应包含真实资产，且不应提交到版本控制系统中。

## 测试结构

测试方案包含三个主要部分：

1. **单元测试**：独立测试各个服务的核心功能
2. **mock服务**：模拟各个微服务的行为，用于集成测试
3. **集成测试**：测试整个系统的端到端流程

### 文件结构

```
TESTCASES/
├── mocks/                        # 模拟服务实现
│   └── mock_services.py          # 模拟风控、执行和监控服务
├── unit_tests/                   # 单元测试
│   ├── signal_listener/          # 信号监听服务测试
│   │   └── test_signal_logic.py  # 信号处理逻辑测试
│   ├── dex_executor/             # DEX执行器测试
│   │   └── test_dex_logic.py     # 交易执行逻辑测试
│   ├── risk_controller/          # 风控服务测试
│   │   └── test_risk_logic.py    # 风控逻辑测试
│   └── execution_monitor/        # 执行监控服务测试
│       └── test_monitor_logic.py # 交易监控逻辑测试
├── integration_test.py           # 系统集成测试
├── test_config.py                # 测试配置和工具函数
├── wallet_create.py              # 测试钱包创建工具
└── README.md                     # 测试文档
```

## 运行测试

### 单元测试

运行单个模块的测试：

```powershell
# 运行信号监听服务的测试
python -m pytest TESTCASES\unit_tests\signal_listener\test_signal_logic.py -v

# 运行DEX执行器的测试
python -m pytest TESTCASES\unit_tests\dex_executor\test_dex_logic.py -v

# 运行风控服务的测试
python -m pytest TESTCASES\unit_tests\risk_controller\test_risk_logic.py -v

# 运行监控服务的测试
python -m pytest TESTCASES\unit_tests\execution_monitor\test_monitor_logic.py -v
```

运行所有单元测试：

```powershell
python -m pytest TESTCASES\unit_tests\ -v
```

### 集成测试

运行集成测试将启动所有模拟服务和信号监听服务，并发送测试信号：

```powershell
python TESTCASES\integration_test.py
```

测试特定类型的信号：

```powershell
# 测试符号格式的信号 (例如 BTC/USDT)
python TESTCASES\integration_test.py --signal symbol

# 测试代币符号格式的信号 (例如 token_in=USDT, token_out=WBTC)
python TESTCASES\integration_test.py --signal token

# 测试地址格式的信号 (使用合约地址)
python TESTCASES\integration_test.py --signal address

# 测试包含钱包信息的信号
python TESTCASES\integration_test.py --signal wallet
```

### 启动 Mock 服务

如果需要单独启动模拟服务用于手动测试，可以执行：

```powershell
python TESTCASES\mocks\mock_services.py
```

这将启动以下服务：
- 风控服务 (RiskController): http://localhost:52120
- DEX执行器 (DexExecutor): http://localhost:52130
- 执行监控 (ExecutionMonitor): http://localhost:52140

## 测试用例说明

### 信号监听服务测试

1. **符号处理测试**：验证系统能否正确解析 BTC/USDT 格式的交易对到 token_in 和 token_out
2. **信号验证测试**：验证系统能否识别无效的信号格式
3. **完整流程测试**：验证信号处理的端到端流程，包括风控检查、DEX执行和交易监控
4. **异常处理测试**：验证各种异常情况的处理逻辑

### DEX执行器测试

1. **代币符号解析测试**：验证系统能否将代币符号解析为合约地址
2. **网络配置加载测试**：验证根据指定网络加载正确的配置
3. **钱包配置测试**：验证系统能否从配置文件和信号中获取钱包信息
4. **参数验证测试**：验证缺少必要参数时的错误处理

### 风控服务测试

1. **交易额度限制测试**：验证单笔交易额度限制功能
2. **日限额测试**：验证每日累计交易量限制功能
3. **冷却期测试**：验证交易冷却期限制功能
4. **日重置测试**：验证每日交易量重置功能
5. **交易记录测试**：验证交易记录功能

### 执行监控测试

1. **交易监控测试**：验证交易监控功能
2. **状态查询测试**：验证交易状态查询功能

## 常见问题与解决方案

### 1. 找不到模块或导入错误

**问题**：运行测试时出现 `ModuleNotFoundError: No module named 'xxx'`

**解决方案**：
- 确保激活了虚拟环境 `.\venv\Scripts\Activate.ps1`
- 确保安装了所有依赖 `pip install -r services/requirements.txt`
- 确保从项目根目录运行测试命令

### 2. 地址解析错误

**问题**：测试过程中出现地址解析或校验错误

**解决方案**：
- 检查 `config.json` 中的代币地址映射是否正确
- 确保测试中使用的代币符号与配置文件中的大小写匹配

### 3. Web3 连接失败

**问题**：与区块链网络交互时出现连接错误

**解决方案**：
- 检查 `config.json` 中的 RPC URL 是否有效
- 确保 Infura API 密钥有效并具有足够的使用配额
- 考虑更换为另一个 RPC 提供商或使用本地节点

### 4. 单元测试失败但集成测试通过

**问题**：单元测试失败，但集成测试却通过

**解决方案**：
- 单元测试可能使用了不同的模拟行为
- 检查测试代码中的断言条件是否过于严格
- 考虑更新单元测试中的期望值以匹配实际行为

### 5. 交易执行超时

**问题**：在集成测试中，交易执行步骤超时

**解决方案**：
- 增加超时时间 `requests.post(..., timeout=30)`
- 检查 DEX 执行器配置和模拟响应速度
- 验证网络连接和服务状态

## 测试覆盖率

要生成测试覆盖率报告，需要安装 `pytest-cov` 包：

```powershell
pip install pytest-cov
```

然后运行：

```powershell
python -m pytest --cov=services TESTCASES\unit_tests\
```

这将生成覆盖率报告，显示代码的测试覆盖情况。

## 连接真实区块链网络测试

要在真实区块链网络上进行测试，需要：

1. 获取测试网代币
   - 访问水龙头网站获取测试币（如Goerli ETH）
   - 例如：https://goerlifaucet.com/

2. 修改配置文件添加真实钱包地址和私钥

3. 在测试网上部署或使用现有的代币合约

4. 运行以下命令进行真实网络测试：

```powershell
# 先确保修改了配置文件中的网络设置为 testnet
python TESTCASES\integration_test.py --signal token
```

**警告**：永远不要在主网上使用包含真实资产的钱包进行测试。
