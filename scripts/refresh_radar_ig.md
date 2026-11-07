# 本地品牌雷达 · Instagram 公开数据刷新

公司 IG 专业号和 Meta App 还没就绪。在 `NBO_IG_USER_ID` 和 `NBO_IG_ACCESS_TOKEN`
都放进环境变量之前，采集命令只向 stderr 打印「IG 未接通」，然后以状态码 2 退出。

这个时候它不会访问 `graph.facebook.com`，不会写出 `data/radar/ig_snapshot_*.json`，
也不会填粉丝数、帖子数或点赞数。令牌只从环境变量读取，不要写进仓库、不要写进命令行历史以外的文件、不要提交。

站点重建（`python -m nbo.localradar`）**不读** IG 快照。没有这份快照时，
`local_brands.json` 里 IG 相关字段的「演示」标注保持原样。

## 权限（按官方文档，不是猜的）

Business Discovery 参考（更新于 2026-08-12）要求用 **Facebook 用户访问令牌** 调用
`GET /{ig-user-id}?fields=business_discovery.username(USERNAME){...}`，权限是：

| 权限 | 用途 |
| --- | --- |
| `instagram_basic` | 读取 Instagram 专业号资料与媒体 |
| `instagram_manage_insights` | Business Discovery 参考页列出的必需权限 |
| `pages_read_engagement` | 同上 |

如果这个人在主页上的角色是通过 Business Manager 授予的，还要再有其一：

| 权限 | 用途 |
| --- | --- |
| `ads_management` 或 `ads_read` | Business Manager 授予的主页角色额外要求 |

查出「公司自己的 IG 用户 id」走的是另一份入门文档（更新于 2026-06-30）。
那里为了列出主页并读到绑定的 Instagram 专业号，要申请：

| 权限 | 用途 |
| --- | --- |
| `instagram_basic` | 同上 |
| `pages_show_list` | `GET /me/accounts` 列出当前用户能管理的主页 |

`pages_show_list` 不是 Business Discovery 参考页上的调用权限，但没有它就拿不到要写入
`NBO_IG_USER_ID` 的那个 id。App Review 时把上面几项一起申请。

文档：

- [IG User Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery/)（权限与字段，2026-08-12）
- [Business Discovery 指南](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery)（示例为 `graph.facebook.com/v27.0`，2026-08-12）
- [Instagram API with Facebook Login 入门](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/get-started)（`instagram_basic` + `pages_show_list`，2026-06-30）
- [长期用户令牌](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived)（约 60 天；页面写明当前 Graph 版本 v27.0，2026-06-30）

限制（同一参考页）：只能查 **Instagram 专业号**（Business 或 Creator）的公开字段。
个人号会返回错误。年龄限制账号官方不返回数据。本仓库遇到这类错误只记 `status: error`，不补数字。

## 配置（Meta App 就绪之后）

1. 把公司 Instagram 账号切成专业号（Business 或 Creator），并绑到一个 Facebook 主页。
   操作的 Facebook 用户要能在这个主页上执行任务，并且是 Meta App 的管理员、开发者或测试员。
2. 在 [Meta for Developers](https://developers.facebook.com/) 建一个 Business 类型的 App，
   加上 Facebook Login for Business。入门文档的默认设置可以先不动。
3. 用 Facebook Login for Business 申请这些权限：`instagram_basic`、`pages_show_list`、
   `pages_read_engagement`、`instagram_manage_insights`。主页角色若来自 Business Manager，
   再加上 `ads_read`（或 `ads_management`）。开发阶段可用 Graph API Explorer 生成短期用户令牌；
   要给没有 App 角色的人用，需要 App Review 通过后把 App 切到 Live。
4. 拿 IG 用户 id（入门文档第 4–5 步，版本号与当时文档一致，下面按 v27.0 写）：

   ```bash
   curl -sS "https://graph.facebook.com/v27.0/me/accounts?access_token=$SHORT_LIVED_USER_TOKEN"
   curl -sS "https://graph.facebook.com/v27.0/PAGE_ID?fields=instagram_business_account&access_token=$SHORT_LIVED_USER_TOKEN"
   ```

   响应里 `instagram_business_account.id` 就是 `NBO_IG_USER_ID`。这是公司自己的专业号 id，
   不是被抓品牌的 id。

5. 把短期用户令牌换成长期用户令牌（约 60 天）。这一步要带 App Secret，只能在本机跑，
   不要把 Secret 或换出来的令牌写进仓库、CI 日志或聊天：

   ```bash
   curl -sS "https://graph.facebook.com/v27.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_LIVED_USER_TOKEN"
   ```

   过期的短期令牌不能再换，只能重新登录。Business Discovery 用的是这个 **用户** 令牌，
   不是主页令牌，也不是 App Secret。

6. 只在当前 shell 里导出，然后抓取：

   ```bash
   export NBO_IG_USER_ID="上一步的 instagram_business_account.id"
   export NBO_IG_ACCESS_TOKEN="长期用户令牌"
   python -m nbo.localradar.igsnapshot --out-dir data/radar
   ```

   成功时 stdout 是一行摘要（文件名、抓取时间、来源、成功/错误/跳过条数）。
   快照写到 `data/radar/ig_snapshot_<WIB 日期>.json`。令牌不在文件里。

未导出变量时：

```bash
python -m nbo.localradar.igsnapshot
# stderr: IG 未接通。未设置 NBO_IG_USER_ID 或 NBO_IG_ACCESS_TOKEN，未请求 Instagram Graph API，未写入快照。
# 退出码 2，目录里不会多出 ig_snapshot_*.json
```

## 抓什么、不抓什么

handle 来自 `data/radar/brand_list_*.json`（默认用文件名最新的一份）里非空的 `ig_handle`。
能对上 `repo_id` 或品牌名的，快照 key 用雷达 id（例如 `ID-01`、`ID-11`）；
对不上的用 `list-<品牌名>`，避免把清单里已记下的号丢掉。

清单里 `ig_handle` 为 null 的品牌不请求。`nbo.localradar.BRANDS` 里的 `ig`
即使填了演示号也不使用。例如清单将 Richeese Factory、Sour Sally、Roti'O 标成
「未找到可信来源」，就不会去请求种子里的 `@richeesefactory`、`@soursally`、`@rotiocomalang`。
记下的字符串如果不是一个 Instagram 用户名（有空格、斜杠、链接），记 `invalid_handle`，不改写、不请求。

每个已记录的用户名请求一次。字段与官方示例同一写法：

```text
business_discovery.username(USERNAME){followers_count,media_count,media.limit(12){timestamp,like_count,comments_count,permalink}}
```

近期媒体只取第一页（最多 12 条）。接口若省略 `like_count`（例如隐藏点赞），快照里是 `null`，不是 0。
不计算互动率，不补粉丝。

## 错误和限流

| 情况 | 行为 | 退出码 |
| --- | --- | --- |
| 缺环境变量 | 不请求、不写文件，stderr 含「IG 未接通」 | 2 |
| 令牌无效、权限不足，或本公司 id 不是专业号（Graph `code` 190 / 10 / 200 等，或 HTTP 401/403） | 立刻停止，不写文件 | 4 |
| 限流：HTTP 429，或 Graph `code` 4、17、32、613、80002 | 立刻停止，不再请求后面的品牌，不写文件 | 3 |
| 单个 handle 不存在或不是专业号（例如 `code` 110） | 该品牌 `status: error`，没有粉丝/媒体数字；其他品牌继续 | 0（文件仍写出） |
| 网络失败，或 HTTP 5xx | 立刻停止，不写文件 | 1 |

不自动重试。限流后再跑会继续打满额度。

## 快照形状

与 `x_snapshot_*.json` 一样，顶层有抓取时间和来源。数字只出现在 `status: ok` 的品牌上。
下面的尖括号是字段位置，不是样例数据，也不要把它当成抓取结果提交。

```json
{
  "schema": "nbo.radar.ig_snapshot/v1",
  "platform": "instagram",
  "fetched_at": "<UTC>",
  "fetched_at_local": "<WIB, UTC+7>",
  "source": "Instagram Graph API business_discovery",
  "graph_version": "v27.0",
  "queried_ig_user_id": "<NBO_IG_USER_ID>",
  "ig_calls_used": "<实际 HTTP 次数>",
  "brands": {
    "ID-01": {
      "seed_handle": "@kopikenangan.id",
      "username": "kopikenangan.id",
      "handle_source": "brand_list.ig_handle",
      "status": "ok",
      "account": {
        "followers_count": "<接口原值>",
        "media_count": "<接口原值>"
      },
      "media": [
        {
          "timestamp": "<接口原值>",
          "like_count": "<接口原值或 null>",
          "comments_count": "<接口原值或 null>",
          "permalink": "<接口原值>"
        }
      ]
    }
  },
  "skipped": [
    {"id": "ID-05", "brand": "Richeese Factory", "reason": "未记录 handle"}
  ]
}
```

## 检查

```bash
PYTHONPATH=src python -m pytest tests/test_localradar_ig.py tests/test_localradar_x.py -q
```

有真实快照之后，把 `data/radar/ig_snapshot_*.json` 单独开 PR。不要把令牌、App Secret
或 `.env` 加进去。合并用普通 merge，不要 force-push。在另一次改动把快照接进
`build_localradar` 之前，页面继续显示现在的演示标注。
