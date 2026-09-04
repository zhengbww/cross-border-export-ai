[English](README.md) | 中文

# Export Market Intelligence Dashboard

## 项目定位

本项目是一个面向中国 HS850760 锂离子蓄电池出口市场的 Streamlit 展示层，用于呈现“AI 驱动的跨境出口市场机会识别与智能决策平台”已经生成的正式分析结果。

Dashboard 本身是只读展示层：不重新训练 KMeans，不重新计算 Opportunity Score，不修改源数据，也不会把尚未完成的 `05_market_opportunity_showcase.ipynb` 当作业务逻辑或数据口径来源。

## 与 Notebook 01–04 的关系

Dashboard 遵循正式分析链路：

1. **Notebook 01 — 数据获取**：从 UN Comtrade 获取中国 HS850760 出口数据，并保存原始数据、处理后数据和年度市场数据。
2. **Notebook 02 — 市场分群与评分**：构建市场级特征，使用既有 KMeans 分群，生成五维评分、Opportunity Score、市场类型和决策层级。
3. **Notebook 03 — 机会更新**：将冻结的 2023 年模型应用到 2024 年数据，输出 Opportunity Score 与排名变化，以及机会跃升市场。
4. **Notebook 04 — 市场验证与决策**：使用目标市场的进口结构，对少数重点市场进行验证，并记录最终策略、决策理由和数据风险字段。

Dashboard 只消费这条链路已经落盘的 CSV 结果。Notebook 05 目前只是未完成的展示草稿，因此不会被用作业务定义或数据规则来源。

## Dashboard 页面

1. **Global Market Opportunity** — 展示 197 个全球市场的整体机会格局，包括 KPI、Top 15 排名、Size Score 与 Growth Score 矩阵、市场类型分布，以及市场类型和决策层级筛选器。
2. **Market Explorer** — 允许选择目的地市场，查看排名、Opportunity Score、市场类型、决策层级、出口额和五维评分，并与全市场平均水平对比。同时直观对比 France 与 Uzbekistan 不同的机会来源。
3. **Opportunity Dynamics** — 展示 2023 → 2024 的 Opportunity Score 变化、排名变化、Top Opportunity Risers，以及 2023 与 2024 排名之间的变化关系。
4. **Validation & Decision** — 展示 Notebook 04 验证的四个市场：France、Uzbekistan、Romania 和 Serbia。内容包括模型信号、进口市场验证、建议策略、决策理由和数据可靠性检查。

## 项目目录结构

```text
cross-border-export-ai/
├─ app/
│  ├─ app.py
│  ├─ README.md
│  └─ README_CN.md
├─ data/
│  ├─ raw/
│  └─ processed/
├─ notebooks/
│  ├─ 01_comtrade_data_acquisition.ipynb
│  ├─ 02_market_segmentation_ml.ipynb
│  ├─ 03_market_opportunity_update.ipynb
│  ├─ 04_market_validation_decision.ipynb
│  └─ outputs/
└─ requirements.txt
```

## `requirements.txt` 的作用

`requirements.txt` 声明 Dashboard 运行所需的轻量依赖：

- `streamlit` — 提供 Web 应用和交互控件
- `pandas` — 负责 CSV 加载和表格数据准备
- `plotly` — 提供交互式图表

将依赖集中写入一个文件，可以让 Windows 环境中的安装过程更稳定、可复现。Dashboard 运行时不需要 Notebook 使用的 API 或机器学习依赖，因为它直接读取已经生成的结果文件。

## Windows PowerShell 安装与启动

请在项目仓库根目录执行：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app/app.py
```

如果 PowerShell 阻止虚拟环境激活，可以只对当前进程放宽执行策略，然后重新激活：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

如果仓库中已经存在 `.venv`，可以跳过第一条创建虚拟环境的命令。激活环境后，也可以直接使用 `streamlit run app/app.py` 启动。

应用会自动寻找项目中的 `notebooks/outputs/` 目录，不依赖机器特定的绝对路径。如果缺少预期文件，或文件字段与正式输出不一致，页面会给出明确错误提示，而不是静默失败。

## 正式数据输入文件

以下 5 个文件应位于 `notebooks/outputs/` 目录：

| 文件 | 在 Dashboard 中的用途 |
|---|---|
| `market_opportunity_ranking_2024.csv` | 2024 年主排名、五维评分、市场类型和决策层级。 |
| `priority_export_markets_2024.csv` | `重点候选`决策层级对应的正式市场清单。 |
| `market_opportunity_change_2023_2024.csv` | 可匹配市场在 2023 → 2024 期间的分数、排名和市场类型变化。 |
| `top_market_opportunity_risers_2024.csv` | 按排名提升幅度排序的 Top 20 市场。 |
| `final_market_validation_decision_2024.csv` | 四个重点市场的最终验证与商业决策表。 |

正式数据链路基于 UN Comtrade 的中国出口统计；Notebook 04 在验证阶段进一步使用目标市场报告的进口数据。Dashboard 只读取这些本地 CSV 结果，不在页面运行时重新调用 API。

## 指标与展示约定

- Opportunity Score 和五个维度均按 0–100 展示，并保留 1 位小数。
- 金额根据数量级使用 `$M` 和 `$B` 展示。
- 增长率和份额使用百分比展示。
- `share_change` 是两个中国供应份额之差，因此按百分点展示。
- Opportunity Score 直接读取结果文件，Dashboard 不重新计算。

## 已知数据限制

- 排名结果包含 197 个市场，但 Saint Kitts and Nevis 和 San Marino 的 Opportunity Score 缺失。这两个市场在 2024 年上半年没有出口记录，相关动量和评分字段不完整；Dashboard 会标记它们，并在按分数排序的图表中排除。
- 动态变化结果只比较 194 个市场，而不是排名表中的全部 197 个市场。这是 Notebook 03 对两个年度模型结果使用内连接的结果；Bermuda、Faroe Isds 和 Nauru 未进入变化表。
- 排名结果同时包含 `segment` 和 `market_segment` 两个字段。由于它们来自 Notebook 02 的不同命名阶段，128/197 行的标签不一致。Dashboard 使用正式最终字段 `market_segment`，忽略旧的 `segment` 字段。
- 四个验证市场中，目标市场报告的中国进口额与中国出口方报告的出口额存在明显双边镜像差异。Notebook 04 将其作为数据质量和解释风险，不将其纳入 Opportunity Score；Dashboard 单独展示 `mirror_gap_pct`、`mirror_similarity` 和 `data_risk`。
- 该模型是动态市场分层与机会监测工具，不是下一年度出口额预测模型。关税、物流、政策、竞争和地缘政治风险仍需结合外部信息进一步验证。
