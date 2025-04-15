# ATM 应用 Docker 部署测试指南

## 简介

ATM（Automated Trading Module）是一个微服务架构的自动交易系统，包含信号监听、风控、DEX执行、执行监控和资产管理等服务。本文档提供了如何使用Docker部署和测试ATM系统的详细步骤。

## 前置条件

- 安装Docker和Docker Compose
- 确保Docker服务已经启动
- 网络连接正常，可以访问内网/外网

## 配置准备

1. 复制 `config.example.json` 到 `config.json` 并进行必要的配置，包括：
   - 设置RPC URL（可使用Infura或其他以太坊节点服务）
   - 配置钱包地址和私钥（测试环境中）
   - 确认所有服务端口设置无冲突

## Docker 镜像构建测试

```bash
# 在项目根目录下执行
# 构建 Docker 镜像
docker-compose build
```

## 单个服务测试

```bash
# 启动配置服务进行测试
docker-compose up config_service

# 测试配置服务是否运行正常
curl http://localhost:52100/config/network
```

## 完整系统部署和测试

```bash
# 启动所有服务
docker-compose up -d

# 查看所有服务状态
docker-compose ps
```

## 健康检查

为保证所有服务正常运行，可以使用以下命令检查各服务的健康状态：

```bash
# 配置服务健康检查
curl http://localhost:52100/config/network

# 信号监听服务健康检查
curl http://localhost:52110/signal/latest

# 风控服务健康检查
curl http://localhost:52120/risk/status

# DEX执行器健康检查
curl http://localhost:52130/dex/status

# 执行监控服务健康检查
curl http://localhost:52140/monitor/status

# 资产管理服务健康检查
curl http://localhost:52150/asset/status
```

## 自动化测试

可以使用自动化测试脚本验证整个系统的功能：

```bash
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 运行测试脚本
python docker-test.py
```

## 网络连接问题的备选方案

当遇到网络连接问题导致无法从Docker Hub拉取基础镜像时，可以使用以下备选方案：

### 1. 使用已有镜像启动服务

```bash
# 如果之前已经成功构建过镜像，直接启动容器
docker-compose up -d
```

### 2. 手动更新容器中的代码

当修改了本地代码但无法重新构建镜像时，可以直接将修改后的文件复制到容器中：

```bash
# 针对某个服务的router.py文件
docker cp .\services\<service_name>\router.py atm-<service_name>-1:/app/services/<service_name>/router.py

# 重启特定服务
docker-compose restart <service_name>
```

## 常见问题与解决方案

### 1. ModuleNotFoundError 错误

这通常是由于Docker环境中的导入路径与本地开发环境不同导致的。解决方案：

- 使用绝对导入路径：`from services.service_name.module import function`
- 在导入语句中添加异常处理，支持两种环境：
  ```python
  try:
      from services.service_name.module import function
  except ImportError:
      from .module import function
  ```

### 2. JSON 解析错误

确保所有使用JSON的文件都正确导入了json模块：

```python
import json
```

### 3. 容器无法启动或持续重启

- 查看日志确定具体错误：`docker-compose logs <service_name>`
- 检查配置文件路径是否正确，优先检查`/app/config.json`文件
- 确保配置的网络模式（mainnet/testnet）与RPC URL匹配

## 完整健康检查脚本

在PowerShell中执行以下命令可以一次性检查所有服务的健康状态：

```powershell
$Services = @('config_service', 'signal_listener', 'risk_controller', 'dex_executor', 'execution_monitor', 'asset_manager')
$Ports = @(52100, 52110, 52120, 52130, 52140, 52150)

foreach ($i in 0..5) {
    $Service = $Services[$i]
    $Port = $Ports[$i]
    
    Write-Host "===== 测试 $Service 健康检查 =====" -ForegroundColor Cyan
    
    try {
        $Endpoint = if ($Service -eq 'config_service') {'config/network'}
                   elseif ($Service -eq 'signal_listener') {'signal/latest'}
                   elseif ($Service -eq 'risk_controller') {'risk/status'}
                   elseif ($Service -eq 'dex_executor') {'dex/status'}
                   elseif ($Service -eq 'execution_monitor') {'monitor/status'}
                   else {'asset/status'}
        
        Invoke-RestMethod -Uri "http://localhost:$Port/$Endpoint" -Method Get -TimeoutSec 5 | ConvertTo-Json
    } catch {
        Write-Host "错误: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}
```

## 版本记录

- v0.1.4: 修复了所有服务的导入模块问题，增加了健康检查端点
- v0.1.3: 解决了Docker部署中的文件路径问题
- v0.1.2: 添加了完整的测试方案
- v0.1.1: 增强了DEX执行器的功能支持

## 测试指标

1. **构建测试**
   - 镜像构建成功且无错误
   - 所有依赖包安装正确

2. **启动测试**
   - 所有容器都能正常启动
   - 服务之间的依赖关系正确

3. **功能测试**
   - 配置服务可以返回正确的配置信息
   - 信号监听服务可以接收并处理交易信号
   - DEX执行器可以模拟执行交易

4. **集成测试**
   - 信号从监听到执行到监控的流程完整

## 故障排除

1. **容器无法启动**
   - 检查日志：`docker-compose logs [service_name]`
   - 确认端口是否被占用

2. **服务之间无法通信**
   - 检查服务启动顺序
   - 确认网络配置是否正确

3. **配置问题**
   - 验证 `config.json` 是否格式正确
   - 检查挂载的配置文件路径

## 清理环境

```bash
# 停止所有容器
docker-compose down

# 删除所有已构建的镜像
docker-compose down --rmi all
```
