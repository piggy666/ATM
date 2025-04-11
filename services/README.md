# ATM Automated Trading Module

ATM 是基于 MCP 微服务架构设计的自动交易系统，具备自动交易与资产管理功能。主要特点包括：

- **资产管理**：支持钱包账户管理、余额查询、代币转账、多账户切换。
- **自动交易执行**：整合信号监听、风控校验、DEX 交易执行、链上交易状态监控；内置自动 ERC20 授权机制。
- **配置灵活**：支持测试网与主网环境切换，所有配置集中存储于 config.json 中，包括端口配置，确保用户只需修改单一文件。
- **模块化设计**：各服务采用 FastAPI 构建，分别部署在独立模块中，通过 REST API 实现服务解耦。
- **开源发布**：项目采用 Apache 2.0 协议，包含详细开发文档和架构说明，欢迎开源社区共同维护。

## 项目结构

ATM/ 
├── services/ 
│ ├── config_service/ # 配置服务 
│ ├── signal_listener/ # 信号监听服务 
│ ├── risk_controller/ # 风控服务 
│ ├── dex_executor/ # DEX 执行服务（含自动授权） 
│ ├── execution_monitor/ # 交易执行监控服务 
│ └── asset_manager/ # 钱包资产管理服务 
├── config.json # 全局配置：网络参数、自动授权和端口设置 
├── requirements.txt 
├── Dockerfile 
├── docker-compose.yml 
├── README.md 
├── LICENSE 
└── docs/ 
└── architecture.md # 系统架构说明


## 快速启动

1. **配置**  
   编辑 `config.json`，填写正确的 RPC URL、路由合约地址及其它参数。修改 `"ports"` 以调整各服务端口（默认使用 52100-52150 范围）。

2. **本地运行**  
   每个服务均可独立启动，例如启动 Config Service：
   ```bash
   uvicorn services/config_service/main:app --host 0.0.0.0 --port 52100
