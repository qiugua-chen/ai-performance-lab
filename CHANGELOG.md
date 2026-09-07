# 更新日志

本文件记录 AI Performance Lab 的所有重要变更。

## [0.0.1] - 2026-09-07

### 新增

- 经过校验的 YAML 测试规格，用于定义结构化的性能测试输入。
- 行为可控的 FastAPI 示例 API，支持正常、慢响应和错误响应。
- 参数化的 Apache JMeter HTTP 模板。
- 基于 Python 的 JMeter 执行器。
- 对执行成功、超时以及 JMeter 命令不存在的情况进行明确处理。
- 唯一的运行标识和独立的产物目录。
- 测试规格、JMeter 测试计划和 JTL 配置的输入快照，以及拒绝覆盖已有文件的产物写入策略。
- CSV 格式 JTL 文件的解析与结构校验。
- 对正常、空白及损坏的 JTL 文件进行明确处理。
- 确定性计算请求数、每秒请求数（RPS）、成功率和错误率。
- 确定性计算最小、平均和最大响应时间。
- 使用最近秩法（nearest-rank）计算 P50、P90、P95 和 P99。
- 输出 PASS、FAIL 或 INVALID 的确定性规则引擎。
- 结构化规则检查及禁止覆盖写入的评估结果文件。
- 统一的 pytest 测试套件。
- 一条命令执行完整 M0 工作流。
- 对正常、慢响应、错误响应和无效场景进行真实端到端验证。
- M0 验证记录和工程复盘文档。

### 验证

已验证以下真实端到端结果：

| 场景 | 结果 |
|---|---|
| 正常响应 | PASS |
| 慢响应 | FAIL |
| 错误响应 | FAIL |
| 样本不足 | INVALID |

执行完整自动化测试套件：

```powershell
python -m pytest
```

执行完整 M0 工作流：

```powershell
python -m ai_performance_lab run --spec "examples\test_specs\normal-e2e.yaml" --jmeter "D:\tools\apache-jmeter-5.6.3\bin\jmeter.bat" --runs-root "runs" --timeout-seconds 30
```

### 实现范围

版本 `0.0.1` 完成以下里程碑：

```text
M0 — 首次自动化性能测试运行
```

M0 建立了以下执行与评估工作流：

```text
测试规格（Test Spec）
→ JMeter
→ 运行标识（Run ID）
→ JTL
→ 性能指标
→ 规则引擎
→ PASS / FAIL / INVALID
```

### 尚未包含

版本 `0.0.1` 不包含：

- AI 测试规划器；
- AI 结果分析；
- 大语言模型（LLM）集成；
- Prometheus 或 Grafana 集成；
- 自动化报告生成；
- 分布式负载生成；
- Jenkins 集成；
- GitHub Actions 集成；
- 生产可用性保证。
