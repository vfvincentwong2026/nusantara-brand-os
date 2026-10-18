# BPOM 公开数据可爬性验证报告

> 验证时间：2026-10-19 · 验证人：Kimi Work · 结论：**可用，推荐作为合规看板数据源**

## 结论

BPOM 官方查询站 `https://cekbpom.pom.go.id` 的搜索数据接口可程序化访问，返回 JSON，字段覆盖合规看板所需的全部维度：**注册号、产品名、品牌、持证公司、制造商、状态（有效/撤市）、注册到期日、Halal 证书关联字段**。

## 接口规格（实测）

| 项 | 值 |
|---|---|
| 入口页 | `GET https://cekbpom.pom.go.id/all-produk?query=<关键词>` |
| 数据接口 | `POST https://cekbpom.pom.go.id/produk-dt/all` |
| 认证 | Laravel CSRF：先 GET 入口页拿 `XSRF-TOKEN` Cookie，解码后放 `X-XSRF-TOKEN` 请求头 |
| 必要请求头 | `X-Requested-With: XMLHttpRequest`、`Referer: <入口页>` |
| 请求参数 | DataTables 协议：`draw` / `start` / `length` / `search[value]` |
| 响应 | JSON：`recordsTotal`、`recordsFiltered`、`data[]` |

## 实测样例（关键词 chitato）

- `recordsTotal`: 675,750（全库在册）；`recordsFiltered`: 41（关键词命中）
- 单条记录关键字段：
  - `PRODUCT_REGISTER`: `MD 272831023097`（BPOM 注册号）
  - `PRODUCT_BRANDS`: `Chitato`，`PRODUCT_NAME`: 产品全称
  - `STATUS`: `Berlaku`（有效）/ 撤市另有状态值
  - `REGISTRAR`: `PT INDOFOOD FORTUNA MAKMUR` + NPWP + 地址（持证人链路）
  - `MANUFACTURER_NAME` / 地址（制造商链路）
  - `PRODUCT_EXPIRED`: `2026-08-15`（**到期日 → 到期预警可自动化**）
  - `PRODUCT_QR`: GS1 二维码内容
  - `PRODUCT_ID_HALAL` / `CERTIFICATE_ID_HALAL`（Halal 证书关联，多为 null，Halal 需另源）

## 访问注意

1. **CSRF token 每次会话获取**，cookie jar 流程即可，无登录、无验证码（截至验证日）
2. **节奏控制**：建议 ≤1 req/s，加 User-Agent；批量任务放 Cloudflare Workers 定时拉取或本地批处理写 D1，勿前端直连（CSRF 与 CORS 均不允许）
3. **不做全库镜像**（尊重服务负载），按品牌/持证人关键词拉取自己关心的 SKU 即可
4. 接口无官方 SLA，属非公开承诺端点——接入层做字段校验 + 失败告警，结构变更时快速感知

## 对合规引擎的落地映射

| 合规看板需求 | BPOM 字段 |
|---|---|
| BPOM 注册状态 | `STATUS`（Berlaku / Ditarik） |
| 注册号 | `PRODUCT_REGISTER` |
| 持证公司链路 | `REGISTRAR` + `REGISTRAR_NPWP` + 地址 |
| 制造商链路 | `MANUFACTURER_NAME` + 地址 |
| 到期预警 | `PRODUCT_EXPIRED` |
| 撤市监控 | 状态变更 + `DELETED_DATE` |

**缺口**：Halal 认证状态在 BPOM 数据中大部分为空，需接 MUI / LPPOM 数据源（另案调研）。童装/部分快消的 SNI 属 BSN 体系，不在 BPOM 库内。
