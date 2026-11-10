# 本地品牌雷达 · X 公开数据每日刷新

雷达（`web/trend/` → `web/trend/data/local_brands.json`）的 **热度** 与 **X 官方号指标** 来自
`data/radar/x_snapshot_YYYY-MM-DD.json`；其余字段（IG/TikTok、粉丝(万)/播放/赞/转发/互动率/30 天增速/缺口分、潜力小店）
仍是演示估算，每个品牌的 `provenance` 字段逐项标注（`x_public` / `demo_estimate` / `mixed` / `missing` / `pending`）。
快照里还没有的追踪品牌会标成 `pending_x`，X 粉丝和提及留空，等到下一次刷新写入后再变成实抓。

## 分两步

### 1. 抓取（由 Grok Bot 用内置 X 公开读取工具完成，无 API key）

每个品牌约 1–2 次调用。品牌数以 `nbo.localradar.BRANDS` 的实际条目为准（当前 17），不要写死 12。限额 30 次/分钟、1000 次/天。

先列出本次要抓的 handle，不要只抄上一份快照里已经有的 `resolved_handle`：

```bash
python -m nbo.localradar --refresh-plan
```

`in_snapshot: false` 的品牌必须纳入本次抓取。以本次 `--refresh-plan` 的输出为准，不要只抄上一份说明。当前最新快照还没有这 5 家：ID-13 Point Coffee `@pointcoffeeid`、ID-14 Excelso `@ExcelsoCoffee`、ID-15 Anomali Coffee `@anomalicoffee`、ID-16 Djournal Coffee `@DJOURNALcoffee`、ID-17 Maxx Coffee `@maxxcoffeeID`。`mentions_query` 为 null 时按品牌名新写查询，提及量和粉丝数只写工具返回值，不要填估算数字。

| 内容 | 工具 | 参数要点 |
| --- | --- | --- |
| 官方号资料（粉丝、帖数） | `get_users_by_usernames` | 一次传入 `refresh_plan` 里 `include_in_user_lookup: true` 的全部 `x_handle`（已核实号 + 快照里还没有的新品牌），`user.fields=created_at,description,public_metrics,verified,location` |
| 近 30 天发帖与互动 | `get_users_posts` | `id`=用户 id，`start_time`=30 天前，`exclude=retweets`，`post.fields=created_at,public_metrics`（单页最多 25 条） |
| 近 7 天全网提及量 | `get_posts_counts_recent` | 已在快照里的品牌沿用 `mentions_query`；新品牌现写查询。`granularity=day`（语言过滤用 `lang:id`，不是 `lang:in`） |

规则：只写 X 返回的原始数字；handle 不存在/不合法/指向无关账号时照实写 `handle_status`，
只有显示名与简介明确匹配时才写 `resolved_handle`。

把结果按上一份快照的结构写成新文件 `data/radar/x_snapshot_<今天>.json`（字段：`fetched_at`、`x_calls_used`、
`brands.<ID>.handle_status / resolved_handle / account / posts_30d / last_post_at / mentions_7d`）。
新快照的 `brands` 必须覆盖 `refresh_plan` 里的每一个 id，包括 `in_snapshot: false` 的品牌（当前是 ID-13..ID-17）。漏掉的品牌重建后仍是 `pending_x`。不要改写已有的 `x_snapshot_*.json`，也不要为还没抓到的品牌补粉丝或提及。

### 2. 重建 JSON（纯 Python，离线）

```bash
pip install -e ".[dev]"
python -m nbo.localradar --db nbo.db --out web/trend/data/local_brands.json \
    --x-snapshot data/radar/x_snapshot_$(date +%F).json
pytest tests/test_localradar_x.py -q
```

不带 `--x-snapshot` 时默认取 `data/radar/` 下文件名最新的一份（`scripts/deploy.py` 就是这样调用的）；`--no-x` 输出纯演示数据。

### 3. 发布

新建分支提交 `data/radar/x_snapshot_*.json` + `web/trend/data/local_brands.json`，开 PR，合并到 `main` 后
GitHub Pages 工作流自动部署。

## 热度公式

```
heat = round(100 * log10(1 + m7) / log10(1 + 2000), 1)，上限 100
m7   = 近 7 天 X 上提及该品牌的帖子数（排除转推）
```

只用真实输入；原演示热度保存在 `heat_demo`。`value_score` = 热度(实抓)×0.4 + 缺口均值(演示)×0.4 + 增速(演示)×0.2，标记为 `mixed`。
提及量受查询词噪声影响，快照里每个品牌带 `mentions_7d.noise`（low/medium）与 `note`。
