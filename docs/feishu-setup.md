# 飞书集成设置指南

## 功能说明

系统会每天自动：
1. 检测新的盗版视频
2. 检查已知视频的状态（是否下架）
3. 将数据上传到飞书在线表格
4. 发送通知卡片到群里

## 设置步骤

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击"创建企业自建应用"
3. 填写应用信息：
   - 应用名称：盗版监测助手
   - 应用描述：每日盗版视频检测和追踪
   - 上传应用图标（可选）

4. 创建后，记录：
   - `App ID`
   - `App Secret`

### 2. 配置应用权限

在应用后台 → "权限管理" → 开通以下权限：

**必需权限：**
- `sheets:spreadsheet` - 查看、编辑、创建和删除电子表格
- `im:message` - 获取与发送单聊、群组消息
- `im:message:send_as_bot` - 以应用的身份发消息

权限配置后，点击"创建版本"并发布上线。

### 3. 创建飞书表格

1. 在飞书云文档中，创建一个新的"电子表格"
2. 命名为：`盗版监测报告`
3. 从URL中提取 `spreadsheet_token`：
   ```
   https://bytedance.feishu.cn/sheets/shtcnXXXXXXXXXXXXXXXXXXX
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^
                                      这部分就是 spreadsheet_token
   ```

4. 设置表格权限：
   - 点击右上角"分享"
   - 添加机器人为协作者（搜索应用名称）
   - 给予"可编辑"权限

### 4. 创建群机器人（用于通知）

1. 在需要接收通知的飞书群里
2. 点击群设置 → 群机器人 → 添加机器人
3. 选择你刚创建的应用
4. 记录群的 `chat_id`（或使用 Webhook URL）

**可选：使用简单 Webhook（不需要应用）**
- 添加"自定义机器人"
- 复制 Webhook URL（类似 `https://open.feishu.cn/open-apis/bot/v2/hook/xxx`）

### 5. 配置 GitHub Secrets

访问 GitHub 仓库：`https://github.com/你的用户名/col-piracy/settings/secrets/actions`

添加以下 Secrets：

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `FEISHU_APP_ID` | 应用 ID | 应用后台"凭证与基础信息" |
| `FEISHU_APP_SECRET` | 应用密钥 | 应用后台"凭证与基础信息" |
| `FEISHU_SPREADSHEET_TOKEN` | 表格 Token | 从表格 URL 提取 |
| `FEISHU_WEBHOOK` | Webhook URL（可选） | 群机器人设置或自定义机器人 |

### 6. 测试运行

1. 访问 GitHub Actions：`https://github.com/你的用户名/col-piracy/actions`
2. 选择 "Daily Piracy Detection" workflow
3. 点击 "Run workflow" → "Run workflow"
4. 等待运行完成（约 30-40 分钟）

运行成功后：
- 飞书表格会新增两个 sheet：`YYYY-MM-DD 新检测` 和 `YYYY-MM-DD 状态追踪`
- 群里会收到通知卡片，点击可直接打开表格

## 数据说明

### 新检测 Sheet

每天新发现的盗版视频：

| 列名 | 说明 |
|-----|------|
| platform | 平台（dailymotion） |
| video_id | 视频ID |
| title | 视频标题 |
| url | 视频链接 |
| uploader | 上传者 |
| duration_sec | 时长（秒） |
| score | 匹配分数 |
| status | 状态（new/existing） |

### 状态追踪 Sheet

所有已知视频的追踪状态：

| 列名 | 说明 |
|-----|------|
| platform | 平台 |
| video_id | 视频ID |
| title | 视频标题 |
| url | 视频链接 |
| uploader | 上传者 |
| first_seen | 首次检测日期 |
| days_tracked | 已追踪天数 |
| api_status | API状态（active/removed/private） |
| last_checked | 最后检查时间 |
| action_needed | 需要的操作 |

**action_needed 说明：**
- `需要举报` - 新检测到的视频（< 2天）
- `假设已举报，等待处理` - 已检测 2-6 天
- `需要催办 ⚠️` - 超过 7 天仍未下架
- `已下架 ✓` - 视频已被删除
- `已变私密 ✓` - 视频已设为私密
- `已加密码保护 ✓` - 视频已加密

## 定期清理

飞书表格会累积每天的 sheet，建议：
- 保留最近 7-14 天的数据用于对比
- 手动删除更早的 sheet
- 历史数据可在 GitHub Actions artifacts 中下载

## 故障排查

### 表格没有更新
- 检查 GitHub Actions 是否运行成功
- 检查应用权限是否正确配置
- 检查表格是否给了机器人编辑权限

### 没有收到通知
- 检查 `FEISHU_WEBHOOK` 是否配置
- 检查机器人是否在群里
- 查看 GitHub Actions 日志中的错误信息

### Secrets 配置错误
- 检查 Secret 名称是否完全匹配（区分大小写）
- 检查 App Secret 是否正确复制（没有多余空格）
- 检查 spreadsheet_token 是否正确提取
