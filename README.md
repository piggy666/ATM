# ATM (Automated Trading Module)

## 项目简介

ATM是一个基于微服务架构的自动化交易系统，专为数字资产交易设计。系统采用模块化设计，包含信号监听、风险控制、DEX执行、执行监控和资产管理等核心服务，支持多种交易信号格式和交易策略。

## 系统架构

![ATM架构](docs/architecture.png)

系统由以下微服务组成：

- **信号监听服务 (Signal Listener)**: 接收交易信号并转发给风险控制服务
- **风险控制服务 (Risk Controller)**: 评估交易风险并决定是否执行
- **DEX执行器 (DEX Executor)**: 执行去中心化交易所的交易操作
- **执行监控服务 (Execution Monitor)**: 监控交易执行情况
- **资产管理服务 (Asset Manager)**: 管理钱包和资产
- **配置服务 (Config Service)**: 管理系统配置信息

## 主要特点

- **资产管理**：支持钱包账户管理、余额查询、代币转账、多账户切换
- **自动交易执行**：整合信号监听、风控校验、DEX交易执行、链上交易状态监控；内置自动ERC20授权机制
- **配置灵活**：支持测试网与主网环境切换，所有配置集中存储于config.json中，包括端口配置
- **模块化设计**：各服务采用FastAPI构建，分别部署在独立模块中，通过REST API实现服务解耦
- **多信号格式支持**：兼容多种交易信号格式（符号格式、代币符号格式、地址格式）
- **精细化错误处理**：提供详细的错误诊断信息
- **健康监控**：所有服务提供健康检查端点
- **Docker支持**：完整的Docker部署方案
- **开源发布**：项目采用Apache 2.0协议，包含详细开发文档和架构说明

## 项目结构

```
ATM/ 
├── services/ 
│   ├── config_service/    # 配置服务 
│   ├── signal_listener/   # 信号监听服务 
│   ├── risk_controller/   # 风控服务 
│   ├── dex_executor/      # DEX执行服务（含自动授权） 
│   ├── execution_monitor/ # 交易执行监控服务 
│   └── asset_manager/     # 钱包资产管理服务 
├── config.json            # 全局配置：网络参数、自动授权和端口设置 
├── requirements.txt       # 项目依赖
├── Dockerfile             # Docker构建文件
├── docker-compose.yml     # Docker编排配置
├── docker-test.py         # Docker部署测试脚本
├── docker-test-guide.md   # Docker部署测试指南
├── README.md 
├── LICENSE                # Apache 2.0许可证
└── docs/                  # 文档目录
    └── architecture.md    # 系统架构说明
```

## 快速开始

### 前置条件

- Python 3.10+
- Docker和Docker Compose (用于容器化部署)
- 以太坊节点访问 (Infura或其他提供商)

### 配置设置

编辑`config.json`，填写正确的RPC URL、路由合约地址及其它参数：

```json
{
    "network_mode": "testnet",      # 网络模式：testnet或mainnet
    "auto_approve": true,         # 是否自动授权ERC20代币
    "ports": {                    # 各服务端口配置
        "config_service": 52100,
        "signal_listener": 52110,
        "risk_controller": 52120,
        "dex_executor": 52130,
        "execution_monitor": 52140,
        "asset_manager": 52150
    },
    "testnet": {                  # 测试网配置
        "chain_id": 11155111,     # Sepolia测试网
        "rpc_url": "https://sepolia.infura.io/v3/YOUR_INFURA_KEY",
        "router_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    },
    "mainnet": {                  # 主网配置
        "chain_id": 1,
        "rpc_url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
        "router_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    }
}
```

### 本地开发环境设置

```powershell
# 克隆仓库
git clone https://github.com/您的用户名/ATM-Trading-Module.git
cd ATM-Trading-Module

# 创建并激活虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 配置设置
cp services/config.example.json services/config.json
# 编辑config.json设置您的RPC URL和钱包信息
```

### 本地运行

每个服务均可独立启动，例如启动Config Service：

```powershell
uvicorn services.config_service.main:app --host 0.0.0.0 --port 52100
```

### Docker部署

```powershell
# 构建并启动所有服务
docker-compose up -d

# 检查服务状态
docker-compose ps
```

详细的Docker部署指南请参考[docker-test-guide.md](docker-test-guide.md)

## 健康检查

为确保所有服务正常运行，可以使用以下命令检查各服务的健康状态：

```powershell
# 配置服务健康检查
Invoke-RestMethod -Uri "http://localhost:52100/config/network"

# 信号监听服务健康检查
Invoke-RestMethod -Uri "http://localhost:52110/signal/latest"

# 风控服务健康检查
Invoke-RestMethod -Uri "http://localhost:52120/risk/status"

# DEX执行器健康检查
Invoke-RestMethod -Uri "http://localhost:52130/dex/status"

# 执行监控服务健康检查
Invoke-RestMethod -Uri "http://localhost:52140/monitor/status"

# 资产管理服务健康检查
Invoke-RestMethod -Uri "http://localhost:52150/asset/status"
```

## 测试

系统提供了多层次的测试方案：

1. **单元测试**：测试各个服务的核心逻辑
2. **服务测试**：测试单个服务的API功能
3. **集成测试**：测试整个交易流程
4. **Mock服务**：模拟各个核心服务组件，使用Flask实现

```powershell
# 运行单元测试
python -m pytest tests/unit

# 运行Docker部署测试
.\venv\Scripts\Activate.ps1
python docker-test.py
```

## 版本历史

- **v0.1.5**: 增强Docker部署支持和改进错误处理
  - 增强DEX执行器的详细错误诊断
  - 修复Docker兼容性的模块导入问题
  - 添加Docker部署测试指南和配置
  - 改进所有服务的健康检查端点
  - 解决Sepolia测试网集成问题

- **v0.1.4**: 修复服务导入模块问题，增加健康检查端点
- **v0.1.3**: 解决Docker部署中的文件路径问题
- **v0.1.2**: 添加完整的测试方案，支持多种交易信号格式
- **v0.1.1**: 增强DEX执行器功能支持，添加钱包配置，简化测试流程

## 贡献

欢迎提交问题报告和改进建议。如果您想贡献代码，请遵循以下步骤：

1. Fork该仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建一个Pull Request

## 许可证

此项目采用Apache 2.0许可证 - 详情请参见[LICENSE](LICENSE)文件

## 联系方式

项目维护者 - 添加您的联系信息

---

**注意**: 此项目仅用于教育和研究目的，请勿在生产环境中使用未经充分测试的版本。
