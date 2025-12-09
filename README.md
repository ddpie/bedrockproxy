# Bedrock API 全球加速方案

## 概述

本方案利用 AWS CloudFront 和 Lambda@Edge 为 Amazon Bedrock API 提供全球加速和智能路由服务。通过这种设置，我们可以显著提高 API 的访问速度，降低延迟，并实现更灵活的请求处理。

## 为什么使用 CloudFront 进行加速？

1. **全球内容分发网络 (CDN)**: CloudFront 拥有遍布全球的边缘位置，可以大幅减少用户访问 Bedrock API 的延迟。

2. **智能路由**: 通过 Lambda@Edge，我们可以根据请求中的区域信息动态选择客户链接的 Bedrock 终端节点。

3. **安全性增强**: 相对自建Nginx等方案，CloudFront 提供了额外的安全层，包括 DDoS 保护和 SSL/TLS 加密。

4. **动态回源**: 提供动态回源能力，通过亚马逊网络提高性能。

5. **简化的 API 管理**: 通过单一的 CloudFront 分配，我们可以管理对多个区域 Bedrock 终端节点的访问。

## 方案功能

1. **动态区域路由**: 根据请求中的 AWS 凭证自动将请求路由到相应的区域终端节点。

2. **区域验证**: 确保请求只被路由到预定义的有效区域（us-east-1, us-west-2, ap-northeast-1, eu-west-1）。

3. **请求头修改**: 
   - 设置自定义 `User-Agent` 为 "任意描述"。

4. **动态源设置**: 根据解析的区域信息动态设置请求的源。

5. **错误处理和日志记录**: 包含详细的错误处理和日志记录，便于故障排除。

## 工作流程

1. 用户发送请求到 CloudFront 分配。
2. CloudFront 触发 Lambda@Edge 函数。
3. Lambda 函数解析请求中的 Authorization 头，提取区域信息。
4. 验证区域是否在允许列表中。
5. 修改请求头，设置 `User-Agent`。
6. 根据解析的区域信息设置新的源（Bedrock API 终端节点）。
7. 将修改后的请求发送到相应的 Bedrock API 终端节点。
8. Bedrock API 处理请求并返回响应。
9. CloudFront 将响应返回给用户。

## 优势

- **降低延迟**: 通过就近访问 Bedrock API，显著减少响应时间。
- **提高可用性**: 利用 CloudFront 的全球网络，提高服务的整体可用性。
- **灵活性**: 可以轻松添加或移除支持的区域，无需修改客户端代码。
- **成本效益**: 通过优化路由和潜在的缓存，可能降低数据传输成本。

## 注意事项

- 确保 CloudFront 分配和 Lambda@Edge 函数正确配置。
- 监控 CloudFront 和 Lambda@Edge 的性能和错误日志。
- 考虑实施额外的安全措施，如 WAF 规则。
- 关于如何应用层面如何配置的方法，请看 [Howto](./howto.md)
- 目前Cloudfront默认最多60s等待时间，如果需要可以向AWS申请更长的等待时间。

Service: Amazon CloudFront/Region: US East (Northern Virginia)/Limit name: Response timeout per origin


---

## CDK 部署指南

本方案可以通过 AWS CDK (Cloud Development Kit) 快速部署。以下是部署步骤：

1. **准备环境**
   - 确保已安装 Node.js
   - 安装 AWS CDK CLI: `npm install -g aws-cdk`
   - 配置 AWS 凭证: `aws configure`
   - 请选择us-east-1 region部署

2. **克隆项目仓库**
   ```
   git clone <repository-url>
   cd <project-directory>
   ```

3. **安装依赖**
   ```
   npm install
   ```

4. **编译 TypeScript**
   ```
   npm run build
   ```

5. **部署 CDK Stack**
   ```
   cdk synth
   cdk bootstrap --region us-east-1
   cdk deploy --region us-east-1
   ```

   这个命令将会:
   - 创建 CloudFront 分配
   - 部署 Lambda@Edge 函数
   - 设置必要的 IAM 角色和策略
   - 配置其他相关资源

6. **验证部署**
   - 部署完成后，CDK 将输出 CloudFront 分配的 URL
   - 使用此 URL 测试 Bedrock API 的访问

7. **更新和管理**
   - 要更新配置，修改 CDK 代码后运行 `cdk deploy`
   - 要删除所有资源，运行 `cdk destroy`

注意：首次在账户/区域中使用 CDK 时，可能需要运行 `cdk bootstrap` 来设置 CDK 工具包。

---

## 连通性测试

部署完成后，可以使用提供的测试脚本验证代理是否正常工作。

### 使用测试脚本

1. **配置端点地址**
   
   编辑 `test/connectivity_test.py`，将 CloudFront 端点替换为你的实际域名：
   ```python
   CLOUDFRONT_ENDPOINT = "https://YOUR_CLOUDFRONT_DOMAIN"
   ```

2. **安装依赖**
   ```bash
   pip3 install boto3
   ```

3. **运行测试**
   ```bash
   python3 test/connectivity_test.py
   ```

### 测试内容

测试脚本会自动执行以下测试：

- **多区域测试**: us-west-2, us-east-1, ap-northeast-1, eu-west-1
- **多模型测试**: Claude 3.5 Sonnet, Claude Sonnet 4.5, Claude 3 Haiku
- **对比测试**: 同时测试直连 Bedrock 和通过 CloudFront 代理两种方式

### 测试输出

测试脚本会显示：
- 实时测试进度和结果
- 每个请求的响应时间
- 模型响应内容和 Token 使用情况
- 详细的错误信息（如果失败）
- 汇总统计表格

示例输出：
```
╔════════════════════════════════════════════════════════════════════════════════╗
║                      Bedrock CloudFront 代理连通性测试                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

[1] Claude 3.5 Sonnet @ us-west-2
  [直连] 测试 Claude 3.5 Sonnet @ us-west-2... FAIL (ValidationException)
  [代理] 测试 Claude 3.5 Sonnet @ us-west-2... OK (1.67s)
      响应: Hello! How can I assist you today?...
      Token: 输入=8, 输出=30

模型                             区域                   直连         代理         响应时间        
-------------------------------------------------------------------------------------
Claude 3.5 Sonnet              us-west-2            FAIL       OK         1.67s       
...

结论: 代理测试全部通过！
```
