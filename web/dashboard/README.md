# SKU 去化大屏

- 库存列表
- FEFO 批次
- 临期预警
- 缺货风险
- 补货建议

## 运行

```bash
# 1. 生成数据（引擎层 SQLite -> dashboard.json）
python -m nbo.db seed   # 首次：灌入三档门店 + 零食演示数据
python -m nbo.dashboard --db nbo.db --store store-jkt-2000 --out web/dashboard/data/dashboard.json

# 2. 启动（fetch 不能用 file:// 打开，需本地服务器）
cd web/dashboard && python -m http.server 8763
# 浏览器打开 http://localhost:8763
```

- 纯静态页（ECharts 已 vendor 本地），可直接部署 Cloudflare Pages
- 演示数据场景：SKU002 临期批次+临期证书、SKU003 证书过期、SKU004 高周转低库存、SKU005 缺货

