# GitHub Actions 自动化检测配置指南

## 快速开始

### 1. 启用GitHub Actions

已创建工作流文件：`.github/workflows/daily-detection.yml`

**当前配置：**
- ✅ 每天UTC 1:00 (北京时间9:00) 自动运行
- ✅ 使用GitHub Artifacts存储state
- ✅ 支持手动触发
- ✅ 每周日额外运行recheck

### 2. 配置Secrets（如果需要通知）

进入 GitHub Repository → Settings → Secrets and variables → Actions

根据你选择的通知方式添加相应的secrets：

#### Email通知
```
EMAIL_USERNAME = your-email@gmail.com
EMAIL_PASSWORD = your-app-password
```

#### Slack通知
```
SLACK_BOT_TOKEN = xoxb-your-token
SLACK_CHANNEL_ID = C01234567
```

#### 钉钉通知
```
DINGTALK_WEBHOOK = https://oapi.dingtalk.com/robot/send?access_token=xxx
```

#### 飞书通知
```
FEISHU_WEBHOOK = https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

### 3. 选择并配置通知方式

从 `.github/workflows/notification-examples.yml` 中选择一个通知方式，复制到 `daily-detection.yml` 的最后一步。

例如，使用钉钉通知：
```yaml
- name: Send DingTalk Notification
  env:
    DINGTALK_WEBHOOK: ${{ secrets.DINGTALK_WEBHOOK }}
  run: |
    NEW_COUNT=$(wc -l < reports/new_detections_*.csv)
    curl -X POST "$DINGTALK_WEBHOOK" \
      -H 'Content-Type: application/json' \
      -d "{...}"
```

## State管理方案对比

### 方案1: GitHub Artifacts（当前）
**优点：**
- ✅ 简单，无需额外配置
- ✅ 自动管理，90天保留期
- ✅ 不污染Git历史

**缺点：**
- ⚠️ 有90天限制
- ⚠️ 不适合长期存储

**适用场景：** 小型项目，短期使用

### 方案2: Git存储（备选）
将state提交到Git仓库：

```yaml
- name: Commit state
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add state/dailymotion_videos.json
    git commit -m "Update state: $(date)"
    git push
```

**优点：**
- ✅ 永久保存
- ✅ 有完整历史记录

**缺点：**
- ❌ 会让repo变大（2-3MB/天）
- ❌ 污染Git历史

### 方案3: 数据库（推荐长期）
使用PostgreSQL/MySQL存储state：

**优点：**
- ✅ 最稳定，适合生产环境
- ✅ 支持复杂查询
- ✅ 支持并发访问

**缺点：**
- ⚠️ 需要额外设置数据库
- ⚠️ 需要修改代码

参考我们之前讨论的PostgreSQL迁移方案。

## 运行频率配置

### 每天运行（当前）
```yaml
schedule:
  - cron: '0 1 * * *'  # 每天 UTC 1:00
```

### 每周运行（节省成本）
```yaml
schedule:
  - cron: '0 1 * * 1'  # 每周一 UTC 1:00
```

### 工作日运行
```yaml
schedule:
  - cron: '0 1 * * 1-5'  # 周一到周五
```

## 监控和调试

### 查看运行历史
访问：`https://github.com/YOUR_USERNAME/col-piracy/actions`

### 手动触发运行
1. 进入 Actions 标签
2. 选择 "Daily Piracy Detection"
3. 点击 "Run workflow"

### 下载报告
1. 进入具体的运行记录
2. 滚动到底部 "Artifacts"
3. 下载 `detection-reports-XXX`

## 成本估算

### GitHub Actions 免费额度
- 公开仓库：**无限制**
- 私有仓库：**2000分钟/月**

### 单次运行时间
- 检测脚本：~40-60分钟
- Recheck脚本：~10-20分钟

### 月度消耗（每天运行）
- 30天 × 60分钟 = **1800分钟**
- 在免费额度内 ✓

## 故障处理

### State丢失
如果Artifacts过期或丢失：
```bash
# 从备份恢复
cp state/dailymotion_videos.json.backup_YYYYMMDD state/dailymotion_videos.json
git add state/
git commit -m "Restore state from backup"
git push
```

### 检测失败
1. 查看Actions日志找到错误
2. 常见问题：
   - API rate limit → 增加sleep时间
   - 内存不足 → 降低per_term_limit
   - 网络超时 → 重试或手动运行

## 下一步优化

1. **迁移到数据库** - 更稳定的state管理
2. **添加监控告警** - 检测失败时通知
3. **自动分析报告** - 生成统计图表
4. **智能去重** - 减少误报

## 需要帮助？

查看完整文档或提issue：
- 主README: `README.md`
- 实现计划: `docs/implementation_plan.md`
