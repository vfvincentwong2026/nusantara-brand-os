# 平台架构

Nusantara Brand OS 分为四层：经验层、引擎层、AI 接入层、渲染层。

## 经验层

来自中国零食爆品团队、沃尔玛体系、天猫体系、名创优品的运营方法论，沉淀为规则、评分模型和约束。

## 引擎层

- **补货引擎**：安全库存、ROP、有效提前期
- **预测引擎**： Prophet / LightGBM，斋月因子
- **空间优化**：OR-Tools MILP
- **合规引擎**：BPOM / Halal / SNI 状态机
- **渠道引擎**：铺货、核销、竞品密度

## AI 接入层

通过 MCP、REST、WebSocket 接入开源工具：

- supply-chain-mcp-server
- OmniSupply
- GraphRAG
- Keel
- ChainScope
- SentinelSCM

## 渲染层

- 印尼地图（Mapbox / Deck.gl）
- 2D 平面图（Konva.js）
- 3D 数字孪生（React Three Fiber）
- 货架图（SVG）
- 仪表盘（ECharts）

## 数据流

经验层 → 引擎层 → AI 接入层 → 渲染层。
