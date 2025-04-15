# ATM 系统架构设计

## 架构概述

本 ATM 系统采用 MCP 微服务架构，将自动交易和资产管理功能拆分为多个服务：
- **Config Service**：集中加载和提供全局配置，包括网络参数、自动授权、端口配置等；
- **Signal Listener**：接收外部交易信号，并调用风险控制及交易执行服务；
- **Risk Controller**：校验交易信号是否合法（额度、冷却、日限等），并记录交易统计；
- **DEX Executor**：调用去中心化交易所合约执行 swap 交易，内置自动授权（approve）机制；
- **Execution Monitor**：监控链上交易状态，返回交易确认或失败信息；
- **Asset Manager**：管理钱包账户，提供余额查询、转账及账户切换等功能。

## 网络切换

通过 `config.json` 中 `network_mode` 字段，系统可在测试网与主网之间切换。各服务在启动时均从 Config Service 动态获取对应网络参数（chain_id、rpc_url、router_address 等），实现配置与代码的解耦。

## 自动授权机制

当 `auto_approve` 配置为 true 且交易涉及 ERC20 代币时，DEX Executor 自动检测当前账户与 DEX 路由合约之间的授权额度，不足时自动发起 ERC20 approve 交易，保证交易顺利执行。

## 端口统一配置

所有服务端口配置在 `config.json` 的 `"ports"` 部分进行统一设置。各服务启动时会从配置文件读取自身对应的端口号，无需用户手动修改代码文件。

## 部署方式

各服务均采用 FastAPI 编写，可独立运行或使用 Docker Compose 同时启动。所有服务使用统一配置和端口映射，确保方便部署及后期扩展。

## 未来扩展

未来 ATM 系统可支持：
- 多币种及多资产管理（包含传统金融资产）；
- 多交易所接入（DEX 和 CEX）；
- 前端可视化钱包界面；
- 更复杂的风控和 AI 交易模块。

