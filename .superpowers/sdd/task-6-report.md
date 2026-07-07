# Task 6 实施报告

## 状态
DONE

## 提交记录
- `a8616af` feat: API 路由

## 实施内容
在 `routes/api.py` 中实现两个 API 端点：

- `GET /api/status` — 获取 MySQL 最新状态（用于前端顶部卡片）。当无数据时返回占位值（`"--"`），有数据时计算总 QPS 并格式化运行时间为 `Xd Xh` 格式。
- `GET /api/metrics` — 获取指标历史数据（用于前端图表）。接受 `hours` 查询参数（默认 24，范围 1-168），返回按时间排序的各指标数组。

## 测试结果
使用 FastAPI TestClient 对所有路由进行集成测试，结果如下：

| 端点 | 状态码 | 结果 |
|---|---|---|
| `GET /health` | 200 | `{"status": "ok"}` |
| `GET /api/status` | 200 | 无数据时返回占位响应 |
| `GET /api/metrics` | 200 | 无数据时返回空数组 |
| `GET /api/metrics?hours=48` | 200 | 自定义参数正常工作 |
| `GET /api/metrics?hours=0` | 422 | 参数验证：hours 必须 >= 1 |
| `GET /api/metrics?hours=200` | 422 | 参数验证：hours 必须 <= 168 |
| `GET /docs` | 200 | Swagger 文档页面可访问 |

所有路由均按预期工作，参数验证正确。

## 自检
无问题。实现与任务简报中的代码完全一致，模块导入和路由注册均正常。

## 关注点
无。
