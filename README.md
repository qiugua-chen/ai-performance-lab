# AI Performance Lab

[简体中文](README.md) | [English](README.en.md)

一个基于测试证据进行性能评估的开源性能工程平台。

## 项目状态

当前版本：`0.0.1`

M0 — 首次自动化性能测试运行：已完成并通过验证。

M0 建立了不依赖 AI 的性能测试执行闭环，使用固定算法计算指标并按规则评估结果：

```text
测试规格（Test Spec）
→ JMeter
→ 运行标识（Run ID）
→ JTL
→ 性能指标
→ 规则引擎
→ PASS / FAIL / INVALID
```

相同有效样本与配置会得到相同的指标和评估结果；实际压测数据仍随运行环境变化。M0 不包含 AI 测试规划和 AI 结果分析。

## M0 功能

- 经过校验的 YAML 测试规格
- 行为可控的 FastAPI 示例服务
- 固定的参数化 JMeter 模板
- 基于 Python 的 JMeter 执行器
- 唯一的运行标识和独立的产物目录
- CSV 格式 JTL 文件的解析与校验
- 确定性的性能指标计算
- PASS / FAIL / INVALID 规则评估
- 一条命令执行完整自动化测试套件
- 一条命令执行真实的 M0 工作流

## 环境要求

- Python 3.11 或更高版本
- 与 Apache JMeter 5.6.x 兼容的 Java
- Apache JMeter 5.6.x
- Windows PowerShell、Linux shell 或其他受支持的终端

M0 首次验证使用的环境：

- Windows
- Python 3.11.5
- Apache JMeter 5.6.3

## 安装

创建虚拟环境：

```shell
python -m venv .venv
```

在 Windows PowerShell 中激活虚拟环境：

```powershell
& ".\.venv\Scripts\Activate.ps1"
```

安装项目：

```shell
python -m pip install -e .
```

确认当前使用的解释器：

```shell
python -c "import sys; print(sys.executable)"
```

## 启动示例 API 服务

```shell
python -m uvicorn examples.demo_api.main:app --host 127.0.0.1 --port 8001
```

M0 提供以下接口：

```text
GET /api/normal
GET /api/slow
GET /api/error
```

## 执行完整的 M0 工作流

Windows 环境示例：

```powershell
python -m ai_performance_lab run --spec "examples\test_specs\normal-e2e.yaml" --jmeter "D:\tools\apache-jmeter-5.6.3\bin\jmeter.bat" --runs-root "runs" --timeout-seconds 30
```

每次执行都会创建唯一的运行目录：

```text
runs/
└── RUN-.../
    ├── test-spec.yaml
    ├── test-plan.jmx
    ├── jtl-save.properties
    ├── result.jtl
    ├── jmeter.log
    ├── metrics.json
    ├── evaluation.json
    └── run.json
```

本地运行产物不纳入 Git 版本控制。

## 评估状态

| 状态 | 含义 |
|---|---|
| PASS | 证据有效，且所有指标均满足阈值要求 |
| FAIL | 证据有效，但至少一项指标未满足阈值要求 |
| INVALID | 证据不足或存在内部不一致 |

命令退出码：

| 结果 | 退出码 |
|---|---|
| PASS | 0 |
| FAIL | 1 |
| INVALID | 2 |
| 执行流水线错误 | 10 |

## 运行测试

执行完整自动化测试套件：

```shell
python -m pytest
```

测试套件无需启动示例 API 服务、执行真实的 JMeter 进程或访问网络。

## M0 验证

完整的 M0 验收记录见 [M0 验证记录](docs/m0-validation.md)。

## 当前限制

M0 的当前功能范围与限制如下：

- 单一 JMeter 执行引擎
- HTTP GET 示例场景
- CSV 格式的 JTL 输入
- 本地文件系统产物存储
- 单次运行级别的汇总指标
- 确定性的阈值规则
- 不包含 AI 测试规划
- 不包含 AI 结果分析
- 不包含 Prometheus 监控
- 不包含报告生成
- 不包含 Jenkins 或 GitHub Actions 集成

## 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。
