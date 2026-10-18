# 2D 平面图编辑器

基于 Konva.js（已 vendor 本地，免构建），与 3D 视图共享同一份 planogram JSON。

- 三档门店切换：500㎡ / 2,000㎡ / 5,000㎡
- 拖拽货架、属性编辑（坐标/尺寸/层数）
- 区域色带（食品 / 非食品 / 生鲜 / 服装）+ 热力图叠加
- 导出 / 导入 planogram JSON（编辑后在 3D 页加载同一文件即同步）

布局由 `python -m nbo.twin --db nbo.db --out-dir web/twin/data` 生成（口径见 `src/nbo/twin/__init__.py`）。

## 运行

```bash
cd web/floorplan && python -m http.server 8765   # 需从仓库根起服务以访问 ../twin/data
```

线上：https://nusantara-brand-os.pages.dev/floorplan/
