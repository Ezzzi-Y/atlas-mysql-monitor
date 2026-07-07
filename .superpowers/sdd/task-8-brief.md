# Task 8: 自定义样式

## 任务目标
创建自定义 CSS 样式文件，增强仪表盘的视觉效果。

## 文件清单
- 修改：`static/css/custom.css`（Task 7 已创建）

## 详细步骤

### Step 1: 创建 custom.css
```css
/* static/css/custom.css */

/* 指标数值样式 */
.metric-value {
    font-size: 2rem;
    font-weight: bold;
    text-align: center;
    margin: 0;
}

/* 警告横幅 */
.warning-banner article {
    background-color: #fef3c7;
    border-left: 4px solid #f59e0b;
}

/* 暗色主题下的警告横幅 */
[data-theme="dark"] .warning-banner article {
    background-color: #451a03;
    border-left-color: #f59e0b;
}

/* 图表容器 */
canvas {
    max-height: 300px;
}

/* 状态卡片网格 */
.grid article {
    margin-bottom: 0;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .metric-value {
        font-size: 1.5rem;
    }
}
```

### Step 2: 提交代码
```bash
git add static/
git commit -m "feat: 自定义样式"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
