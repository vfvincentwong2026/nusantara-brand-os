# PM 评估与完善计划（2026-10-19）

## 结论

定位成立、文档资产质量高，但仓库处于"README 过度承诺、骨架不可运行"状态。先让仓库诚实可跑，再按 P0→P2 推进。AI 工具接入层冻结至 V2。

## 成立的部分

1. **定位与四层架构成立**：经验→引擎→AI→渲染的"载体"思路正确，四支中国团队经验沉淀方向清晰。
2. **市场参数文档是最高价值资产**：三档门店基准、跨岛 LT 系数表（Java k=0.5 → Papua k=1.5）、合规要点、节庆日历，直接可用。
3. **补货引擎数学正确**：SS = z·σ·√LT_eff、ROP = d̄·LT_eff + SS，k 系数表与文档一致，可以此为基础。
4. **前端技术选型成熟**：R3F / Konva / Deck.gl / ECharts 均为社区主流，无选型风险。

## 必须修正的决策

| # | 问题 | 修正 |
|---|------|------|
| 1 | **后端栈与 Owner 生态冲突**：FastAPI + PostGIS + Railway，而既有项目全是 Cloudflare 全家桶 | 改 Cloudflare：Pages + Workers + D1。OR-Tools/Prophet 跑不了 Edge，拆为「Python 计算层（本地/批处理出结果）→ 写 D1 → Pages 渲染」，与四层架构天然吻合。PostGIS 在渠道点位量级（万级）纯属过重，Deck.gl 前端渲染即可 |
| 2 | **README 过度承诺**：demo.gif 破图、BrandTwin 不存在、make 全部不可运行（缺 pyproject.toml / api/ / tests/ / web/package.json） | P0 先修 README 诚实化 + 补工程骨架，对外观感即产品力 |
| 3 | **AI 接入层是纯 PPT**：9 个开源工具无一验证可用，Scope.Vantage 需 AWS Bedrock、SentinelSCM 需 LangGraph，当前阶段过重 | 冻结至 V2。唯一例外：GraphRAG 供应商图谱可提前（但先用 NetworkX + 前端可视化，不急着上 Neo4j） |
| 4 | **斋月因子 2.5 是拍脑袋**：单一对数未分品类 | 改为「品类 × 节庆」分层因子表，先按经验值起步、用真实销售数据回归校准（预测引擎 v1 的校准闭环） |
| 5 | **缺数据通路**：sales/sku_import.csv 模板在但无解析器、无校验、无入库。真实落地第一步是数据从 POS/Excel 进来 | P0 做 import 管线：CSV → schema 校验 → 入库，这决定一切引擎是否有米下锅 |
| 6 | **合规引擎缺失但 MVP 列为核心**：只有 compliance.md 文档，无状态机、无到期预警 | 合规状态机（BPOM/Halal/SNI 三证 × 状态 × 到期日 + 预警规则）是纯日期逻辑，性价比最高的 P0 模块 |
| 7 | **价格/成本字段缺**：schema 无 price/cost/tax 字段，PPN 11% 无处挂 | SKU/Batch 加 cost、sell_price、ppn 字段；报价口径可复用 Atelier `lib/quote.ts` 的 Owner 确认系数经验 |
| 8 | **与 WarungScout 双头风险**：渠道地图的 Warung 点位若自建数据，与 WarungScout 评分网络重复 | 渠道地图 v1 直接消费 WarungScout 数据模型（评分、坐标），Brand OS 不另建 Warung 库 |
| 9 | **种子数据缺 500/5,000㎡**，README 目录树失实 | P0 补齐 |

## 修订版计划

### P0 — 让仓库诚实可跑（1–2 周）

1. README 诚实化：删/补 demo.gif、BrandTwin 示例改"目标 API"标注、模块真实状态表
2. 补 `pyproject.toml`、`tests/`（补货/FEFO/日历先上测试），`make install/test` 跑通；API 与 web 骨架推迟到 P1 需求明确再建
3. 补 500/5,000㎡ 种子数据；integrations 补齐或删 keel/chainscope 引用
4. **数据导入管线**：CSV 模板 → JSON Schema 校验 → SQLite（本地 dev）/ D1（部署）
5. **合规引擎 v1**：三证状态机 + 到期预警，纯 Python + 测试

### P1 — MVP 可视化（3–6 周）

1. SKU 去化大屏：库存 + FEFO + 临期 + 补货建议（ECharts，读引擎输出 JSON）
2. 渠道地图 v1：Warung 点位 + 竞品密度（Deck.gl，数据接 WarungScout）
3. 预测引擎 v1：季节性基线 × 品类节庆因子 → Forecast 表，建立「预测 vs 实际」校准看板
4. 后端定 Cloudflare Workers + D1，或按 Owner 拍板另行决定

### P2 — 数字孪生 + 优化（2 个月+）

1. 2D 平面图编辑器（Konva）+ 3D 孪生（R3F），共享 planogram JSON（README 里"编辑一次双端同步"的正确实现顺序：先 2D，后 3D 只读渲染，再同步）
2. 空间优化 MILP（OR-Tools，本地 Python 层出方案）

### V2 冻结区（恢复评估后再动）

AI 工具矩阵接入。唯一例外：供应商-合规图谱（GraphRAG 思路，NetworkX 起步）。

## 待 Owner 拍板（3 项）

1. **后端栈**：Cloudflare 全家桶（推荐，与 Villa/Atelier/LexNusa 生态一致）还是保留 FastAPI + PG 独立部署？
2. **第一落地品类**：建议零食先行（团队经验最强、合规路径最清晰：BPOM+Halal）。
3. **合规数据来源**：BPOM/Halal 进度手工录入起步，还是调研自动化数据源（BPOM 公开查询可爬性待验证）？
