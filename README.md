# nusantara-brand-os
Brand Landing OS for Indonesia · 食品 · 服装 · 新零食 · 快消
# 🇮🇩 Nusantara Brand OS

> **印尼品牌落地作战平台 · 可视化渲染 + 工具引擎 + 开源 AI 接入**
> 食品 · 服装 · 新零食 · 快消

<div align="center">

<p>
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="License" />
  <img src="https://img.shields.io/badge/PRs-Welcome-2563EB?style=flat-square&logo=github&logoColor=white" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Three.js-r160-000000?style=flat-square&logo=three.js&logoColor=white" alt="Three.js" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/DB-SQLite_→_D1-336791?style=flat-square&logo=sqlite&logoColor=white" alt="DB" />
  <img src="https://img.shields.io/badge/AI-Open_Source-8B5CF6?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="AI Open Source" />
</p>

<p>
  <i>📺 Demo 动图（P1 可视化阶段补齐）：数字孪生 · 渠道地图 · SKU 去化 · 补货模拟 · 斋月需求曲线</i>
</p>

</div>

---

## 📖 项目简介

**Nusantara Brand OS** 是一个面向印尼市场的品牌落地一体化可视化平台。

我们不自己造 AI 模型，不重复造轮子，而是：

- **渲染层**：地图、2D 平面图、3D 数字孪生、货架图、热力图、仪表盘
- **引擎层**：补货、预测、空间优化、合规、渠道、生命周期
- **AI 层**：接入 OmniSupply、GraphRAG、supply-chain-mcp-server、Keel、ChainScope 等开源工具
- **经验层**：把中国零食爆品团队、沃尔玛体系、天猫体系、名创优品的方法论，变成平台里的规则、看板和引擎

> **核心价值：把中国顶级零售经验，翻译成印尼本地可执行动作的可视化作战平台。**

---

## 🧠 团队能力 × 平台模块

| 团队背景 | 核心能力 | 平台模块 | 沉淀方式 |
|----------|----------|----------|----------|
| **中国零食最知名团队** | 爆品策划、口味本地化、品类创新 | 选品看板、口味偏好分析、斋月礼盒策划 | 规则引擎 + 评分模型 |
| **沃尔玛团队及体系** | 供应链、WMS、门店运营、补货体系 | 补货引擎、WMS 可视化、门店数字孪生 | 安全库存 / ROP 模型 |
| **天猫体系** | 电商运营、流量投放、数据化选品 | 线上渠道看板、达人矩阵、直播 ROI | 渠道指标 + 数据看板 |
| **名创优品** | 选品、供应链、线下连锁、陈列管理 | 空间优化、货架图、SKU 去化、门店督导 | MILP 约束 + 陈列规则 |

> **你们缺的不是能力，是“载体”。这个平台把隐性经验变成印尼本地团队能直接用的显性工具。**

---

## 🏗 平台架构

```mermaid
graph TD
    subgraph 经验层
        T1[零食爆品团队]
        T2[沃尔玛体系]
        T3[天猫体系]
        T4[名创优品]
    end

    subgraph 引擎层
        E1[补货引擎]
        E2[预测引擎]
        E3[空间优化]
        E4[合规引擎]
        E5[渠道引擎]
    end

    subgraph AI接入层
        A1[OmniSupply]
        A2[GraphRAG]
        A3[supply-chain-mcp-server]
        A4[Keel / SentinelSCM]
        A5[ChainScope]
    end

    subgraph 渲染层
        R1[印尼地图]
        R2[2D平面图]
        R3[3D数字孪生]
        R4[货架图]
        R5[仪表盘]
    end

    T1 & T2 & T3 & T4 --> E1 & E2 & E3 & E4 & E5
    E1 & E2 & E3 & E4 & E5 --> A1 & A2 & A3 & A4 & A5
    A1 & A2 & A3 & A4 & A5 --> R1 & R2 & R3 & R4 & R5
```

---

## 🧩 核心模块

### 1. 合规看板
- BPOM / Halal / SNI 状态跟踪
- 认证到期预警
- 持证人链路可视化

### 2. 渠道地图
- Warung / Alfamart / Indomaret / 商场铺货
- 竞品密度
- TikTok GO 核销热力

### 3. 门店数字孪生
- 500㎡ / 2,000㎡ / 5,000㎡ 三档印尼主流门店
- 2D 平面图 + 3D 视图 + 货架图
- 编辑一次，双端同步

### 4. SKU 去化大屏
- 库存、FEFO、临期、缺货风险
- 批次、保质期、冷链温度
- 补货建议

### 5. 补货模拟器
- `LT_eff = LT_mean + k × σ_LT`
- 斋月因子、Mudik 效应
- 秒级输出补货方案

### 6. 空间优化器
- MILP 求解货架面位
- 单位面积利润 vs 缺货风险
- 优化前后对比

### 7. 风险监控
- 地缘、关税、物流中断
- 合规风险、供应商风险
- 开源工具接入：Keel、TG-RRNet、SentinelSCM

---

## 🤖 开源 AI 工具接入

| 工具 | 用途 | 接入方式 | 状态 |
|------|------|----------|------|
| **BPOM 公开数据** | 食品注册状态/到期日/持证人链路 | cekbpom.pom.go.id 接口（已验证可爬，见 docs/BPOM_DATA_SOURCE.md） | ✅ 已验证，客户端在 `src/nbo/bpom/` |
| **supply-chain-mcp-server** | UN Comtrade / 世界银行数据 | MCP | ⏳ 待接入 |
| **OmniSupply** | 多智能体供应链分析 | API / 自部署 | ⏳ 待接入 |
| **GraphRAG** | 供应商-产品-合规知识图谱 | Neo4j（先用 NetworkX 起步） | ⏳ V2 |
| **Scope.Vantage** | HHI 集中度风险 | AWS Bedrock | 🧊 V2 冻结 |
| **Keel** | AI 交付风险情报 | 多智能体 | 🧊 V2 冻结 |
| **ChainScope** | 全球供应链可视化 | 仪表盘组件 | 🧊 V2 冻结 |
| **SentinelSCM** | 多智能体控制塔 | LangGraph | 🧊 V2 冻结 |
| **SynthFirm** | 货运需求模拟 | 基于 Agent | 🧊 V2 冻结 |
| **InventOpt / SupplyNetPy** | 物流网络仿真 | 离散事件 | 🧊 V2 冻结 |

> AI 工具接入层整体冻结至 V2（PM 评估决策 #3）：当前阶段先把引擎层与可视化做扎实。

---

## 🛠 技术栈

| 模块 | 技术 |
|------|------|
| 前端框架 | React 18 + TypeScript + Vite |
| 2D 平面图 | Konva.js / SVG |
| 3D 数字孪生 | React Three Fiber + Drei |
| 地图 | Mapbox / Deck.gl |
| 图表 | ECharts / D3 |
| 网络图 | VisuallyJs |
| 状态管理 | Zustand / Redux |
| 后端 | FastAPI → 已定 Cloudflare：Python 引擎层批处理 → D1 → Pages（P1 落地，见 docs/PM_EVALUATION.md） |
| 数据库 | PostgreSQL + PostGIS → D1（本地开发用 SQLite，表结构同源） |
| 缓存 | Redis（P1 按需） |
| 优化求解 | OR-Tools (MILP) |
| 需求预测 | Prophet / LightGBM |
| 部署 | Cloudflare Pages + Railway / Fly.io |

---

## 🚀 快速开始

### 环境要求

- Python ≥ 3.10
- Node.js ≥ 18
- PostgreSQL ≥ 15 + PostGIS
- Docker（推荐）

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/vfvincentwong2026/nusantara-brand-os.git
cd nusantara-brand-os

# 2. 安装（引擎层纯 Python 标准库 + pytest）
pip install -e ".[dev]"

# 3. 初始化本地 SQLite 并灌入三档门店种子数据
python -m nbo.db migrate && python -m nbo.db seed

# 4. 跑测试（Windows 无 make 可直接用本组命令；make install/test 等价）
```

> 原 README 中的 `docker compose up` / `make dev`（FastAPI + PostGIS + 前端）为 P1 目标形态，
> 已按 PM 评估（docs/PM_EVALUATION.md）改为 Cloudflare 栈：Python 引擎层本地批处理 → D1 → Pages 渲染。
> 当前可运行的是引擎层 + 数据管线；API 与前端骨架在 P1 搭建。

### 引擎层示例（已可运行）

```python
from datetime import date
from nbo import StoreProfile, Batch
from nbo.replenishment import ReplenishmentEngine
from nbo.lifecycle import FEFOManager
from nbo.compliance import Certification, ComplianceEngine

# 补货建议：Java 岛门店
eng = ReplenishmentEngine()
print(eng.suggest(avg_daily_demand=10, demand_std=5, lt_mean=10, lt_std=2, island_region="java"))

# FEFO：先到期先出
m = FEFOManager()
batches = [Batch("b1", "sku1", "s1", 10, "2026-01-01", "2026-11-01")]
print(m.near_expiry(batches[0], days_threshold=90))

# 合规：三证状态机 + 到期预警
comp = ComplianceEngine(warn_days=90)
comp.add(Certification(cert_type="BPOM", cert_no="MD 123", holder="PT Contoh",
                       sku_id="sku1", expiry_date="2026-12-01", status="valid"))
print([w.cert_no for w in comp.warnings(date(2026, 10, 19))])
```

### 数据导入管线（已可运行）

```bash
# CSV -> schema 校验 -> SQLite；模板见 data/templates/
python -c "from nbo.importer import import_csv; print(import_csv('data/templates/sales_import.csv', 'sales', 'nbo.db', 'sales'))"
```

---

## 📁 项目结构

```text
nusantara-brand-os/
├── data/
│   ├── schemas/                  # 统一数据模型
│   └── seeds/                    # 三档门店种子数据
│       ├── store_500sqm.json
│       ├── store_2000sqm.json
│       └── store_5000sqm.json
├── src/
│   └── nbo/
│       ├── model/                # 实体与数据模型（StoreProfile / SKU / Batch）
│       ├── forecast/             # 需求预测引擎（移动平均 × 斋月因子，v1）
│       ├── replenishment/        # 补货引擎（安全库存 / ROP / 有效提前期）✅ 有测试
│       ├── space/                # 空间-存量优化（MILP 占位，P2 接 OR-Tools）
│       ├── lifecycle/            # FEFO / 临期预警 ✅ 有测试
│       ├── compliance/           # 三证状态机 + 到期预警（BPOM/Halal/SNI）✅ 有测试
│       ├── calendar/             # 印尼节庆日历 ✅ 有测试
│       ├── bpom/                 # BPOM 公开数据客户端 ✅ 有测试
│       ├── importer/             # CSV → schema 校验 → SQLite ✅ 有测试
│       └── db/                   # SQLite 本地库：migrate / seed ✅
├── web/
│   ├── floorplan/                # 2D 平面图编辑器（P2，README 为规格）
│   ├── three/                    # 3D 数字孪生渲染（P2，README 为规格）
│   └── dashboard/                # SKU 去化大屏（P1，README 为规格）
├── integrations/
│   ├── mcp/                      # supply-chain-mcp-server
│   ├── omnisupply/
│   └── graphrag/
├── tests/
├── docs/
│   ├── assets/                   # README 图像与 GIF（P1 补齐）
│   ├── architecture.md
│   ├── store-scale-benchmarks.md
│   ├── indonesia-market-notes.md
│   ├── data-model.md
│   ├── compliance.md
│   ├── PM_EVALUATION.md          # PM 评估与 P0-P2 修订计划
│   ├── BPOM_DATA_SOURCE.md       # BPOM 公开数据接口验证报告
│   └── playbooks/                # 零食/快消/服装落地手册
├── .github/workflows/
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 🗺 路线图

| 阶段 | 时间 | 内容 | 状态 |
|------|------|------|------|
| **P0** | 0–0.5 月 | 工程骨架可跑 + 数据导入管线 + 合规引擎 v1 + BPOM 数据验证 | ✅ 完成（2026-10-19） |
| **MVP** | 0.5–3 月 | SKU 去化大屏 + 渠道地图 v1 + 预测引擎 v1（Cloudflare 栈） | ✅ 完成（2026-10-19） |
| **V1** | 3–6 月 | 2D 平面图 + 3D 数字孪生 + 品类×节庆因子校准 | ⏳ 计划中 |
| **V2** | 6–12 月 | MILP 空间优化 + AI 工具矩阵接入 + 印尼试点 | ⏳ 计划中 |

---

## 🤝 贡献指南

欢迎提交 PR 和 Issue。请遵循以下约定：

- **分支命名**：`feat/`、`fix/`、`docs/`、`chore/`
- **提交信息**：遵循 [Conventional Commits](https://www.conventionalcommits.org/)
- **代码风格**：ESLint + Prettier（前端），Ruff + Black（Python）
- **测试**：新增功能需附带测试用例
- **文档**：新增模块需更新对应 `docs/` 文件

### Issue 标签

| 标签 | 说明 |
|------|------|
| `compliance` | BPOM / Halal / SNI 相关 |
| `channel` | 渠道铺货、TikTok GO |
| `replenishment` | 补货引擎、安全库存 |
| `3d` | 数字孪生、Three.js |
| `ai-integration` | 开源 AI 工具接入 |
| `data-model` | 数据模型与 Schema |

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- 视觉与展示范式参考：[ChargeNexus Showcase](https://github.com/vfvincentwong2026/charge-nexus-showcase)
- 印尼市场参数参考：APPBI 行业报告、Alfamidi / Alfasupermarket / Hypermart 公开数据
- 开源零售与供应链社区：Prophet、OR-Tools、React Three Fiber
- 开源 AI 工具：OmniSupply、GraphRAG、supply-chain-mcp-server、Keel、ChainScope、SentinelSCM、SynthFirm、InventOpt 等
- 中国零食、沃尔玛、天猫、名创优品团队经验沉淀

---

<div align="center">

**Nusantara Brand OS — 让中国零售经验，在印尼可执行。**

**Nusantara Brand OS — Let Chinese retail expertise become executable in Indonesia.**

</div>
