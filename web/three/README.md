# 3D 数字孪生

基于 Three.js（ES Module + importmap，免构建，依赖全部 vendor 本地）。

- 三档门店切换：500㎡ / 2,000㎡ / 5,000㎡
- 货架按层数拔高（每层 0.35m），区域着色 + 热力模式
- 点击货架高亮并显示详情（区域/层数/热力/坐标）
- 轨道控制（拖拽旋转/滚轮缩放）+ 自动漫游

数据源：与 2D 编辑器共享 `web/twin/data/planogram-*.json`。

线上：https://nusantara-brand-os.pages.dev/three/
