# 盗版视频状态自动追踪方案

## 一、可通过 API 自动检测的状态

### 1. 视频完全删除
- **检测方式**: `GET /video/{id}` 返回 404 错误
- **状态标记**: `removed`

### 2. 视频变为私密
- **检测方式**: `private` 字段 = `true`
- **状态标记**: `private`

### 3. 视频被密码保护
- **检测方式**: `password_protected` 字段 = `true`
- **状态标记**: `password_protected`

### 4. 视频被平台拒绝
- **检测方式**: `status` 字段 = `rejected`
- **状态标记**: `rejected`

### 5. 地区屏蔽
- **检测方式 A**: 使用 `ams_country` 参数查询，403/451 错误
- **检测方式 B**: 读取 `geoblocking` 数组（如果视频所有者设置了）
- **状态标记**: `geo_blocked` + 具体地区列表

### 6. 视频仍可见
- **检测方式**: API 返回 200 + `private=false` + `published=true` + `status=ready`
- **状态标记**: `active`

## 二、需要人工记录的状态

### 1. 是否已举报
- ❌ **无法通过 API 查询**
- **解决方案**:
  - 方案A: 人工标注举报日期（通过 CSV 上传或系统界面）
  - 方案B: 基于时间推断（假设检测后 N 天内完成举报）

### 2. 举报平台/渠道
- ❌ **无法通过 API 查询**
- **解决方案**: 本地记录 `reported_by` 字段

## 三、实现方案

### API 查询示例

```python
# 查询视频详细状态
def check_video_status(video_id: str) -> Dict:
    """
    查询视频当前状态

    Returns:
        {
            'exists': bool,
            'private': bool,
            'password_protected': bool,
            'status': str,  # ready/processing/rejected/etc
            'published': bool,
            'geoblocking': list,  # e.g. ['deny', 'CN', 'US']
            'views_total': int,
            'updated_time': str,
        }
    """
    url = f"https://api.dailymotion.com/video/{video_id}?fields=private,status,published,password_protected,geoblocking,views_total,updated_time,duration"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return {
            'exists': True,
            **response.json()
        }
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {'exists': False, 'status': 'removed'}
        raise

# 多地区可用性检测
def check_geo_availability(video_id: str, regions: List[str]) -> Dict[str, bool]:
    """
    检测视频在各地区的可用性

    Args:
        video_id: 视频ID
        regions: 地区代码列表，如 ['US', 'CN', 'JP']

    Returns:
        {'US': True, 'CN': False, 'JP': True}
    """
    availability = {}

    for region in regions:
        url = f"https://api.dailymotion.com/video/{video_id}?ams_country={region}&fields=id"
        try:
            response = requests.get(url)
            response.raise_for_status()
            availability[region] = True
        except requests.HTTPError as e:
            if e.response.status_code in [403, 451]:
                availability[region] = False
            else:
                availability[region] = None  # 未知错误

    return availability
```

### 状态推断逻辑

```python
def infer_final_status(video_info: Dict, report_info: Dict) -> str:
    """
    基于 API 数据推断最终状态

    Args:
        video_info: API 返回的视频信息
        report_info: 本地记录的举报信息 {'reported_date': '2025-01-01', 'reported': True}

    Returns:
        最终状态字符串
    """
    # 1. 视频已删除
    if not video_info.get('exists'):
        if report_info.get('reported'):
            return 'removed_after_report'  # 举报后删除
        return 'removed'  # 自然删除

    # 2. 视频被平台拒绝
    if video_info.get('status') == 'rejected':
        return 'rejected_by_platform'

    # 3. 变为私密
    if video_info.get('private'):
        return 'made_private'

    # 4. 密码保护
    if video_info.get('password_protected'):
        return 'password_protected'

    # 5. 地区屏蔽
    blocked_regions = video_info.get('blocked_regions', [])
    if blocked_regions:
        return f"geo_blocked_in_{','.join(blocked_regions)}"

    # 6. 仍然活跃
    if report_info.get('reported'):
        days_since_report = (datetime.now().date() - parse_date(report_info['reported_date'])).days
        if days_since_report >= 7:
            return 'active_needs_followup'  # 需要催办
        else:
            return 'active_pending_action'  # 等待处理中

    return 'active_pending_report'  # 待举报
```

## 四、每日工作流

```
Day 1: 检测新盗版视频
  ↓
  输出: new_detections_2025-01-10.csv
  状态: active_pending_report

Day 2: 团队审核并举报
  ↓
  人工反馈: reported_videos.csv (包含 video_id, reported_date)
  系统更新状态: active_pending_action

Day 3-7: 每日 recheck
  ↓
  自动调用 API 查询状态
  状态自动更新:
    - removed_after_report ✓
    - made_private
    - geo_blocked_in_CN,US
    - active_pending_action (仍在处理中)

Day 8+: 催办提醒
  ↓
  状态: active_needs_followup
  输出: needs_followup_2025-01-17.csv
```

## 五、报告输出格式

### 每日状态报告 CSV

```csv
video_id, title, url, first_detected, days_tracked, current_status, geo_status, views_change, action_needed
x123abc, "盗版剧名 EP1", https://..., 2025-01-01, 10, removed_after_report, "全球删除", -50000, "已下架 ✓"
x456def, "盗版剧名 EP2", https://..., 2025-01-05, 5, made_private, "全球私密", 0, "已变私密"
x789ghi, "盗版剧名 EP3", https://..., 2025-01-08, 2, geo_blocked_in_CN, "CN屏蔽, US/JP可见", +5000, "部分屏蔽，建议全球下架"
xaabbcc, "盗版剧名 EP4", https://..., 2025-01-02, 8, active_needs_followup, "全球可见", +30000, "⚠️ 需要催办"
```

### 按状态分类的报告

- `removed_YYYY-MM-DD.csv` - 成功下架的视频 ✓
- `geo_blocked_YYYY-MM-DD.csv` - 地区屏蔽的视频
- `private_YYYY-MM-DD.csv` - 变为私密的视频
- `needs_followup_YYYY-MM-DD.csv` - 需要催办的视频 ⚠️
- `pending_report_YYYY-MM-DD.csv` - 待举报的新视频

## 六、优势

1. ✅ **最小化人工操作** - 只需记录举报日期，其他状态全自动
2. ✅ **实时追踪** - 每天自动更新所有视频状态
3. ✅ **地区细粒度** - 明确哪些地区可见/屏蔽
4. ✅ **催办提醒** - 自动识别需要 followup 的视频
5. ✅ **热度追踪** - 记录 views 变化，优先处理高热度视频
