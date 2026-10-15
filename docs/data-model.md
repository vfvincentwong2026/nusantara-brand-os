# 数据模型

## 核心实体

- **Store**：门店，包含面积、区域、mudik_offset
- **Shelf**：货架，包含区域、层数、面位宽度、heat_value
- **SKU**：商品，包含条码、内部码、Halal、BPOM、保质期
- **Batch**：批次，包含数量、收货日期、到期日
- **Sales**：销售记录
- **Forecast**：预测结果
- **Replenishment**：补货建议
- **Channel**：渠道点
- **Promotion**：促销活动

## 关系

Store 1—N Shelf
Shelf 1—N SKU（通过 planogram）
SKU 1—N Batch
SKU 1—N Sales
SKU 1—N Forecast
SKU 1—N Replenishment
