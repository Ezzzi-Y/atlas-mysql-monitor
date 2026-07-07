# Task 7: 仪表盘页面路由与模板

## 任务目标
实现仪表盘页面路由和 Jinja2 模板，创建完整的 Web UI。

## 文件清单
- 修改：`routes/dashboard.py`（Task 5 已创建占位文件）
- 创建：`templates/base.html`
- 创建：`templates/dashboard.html`

## 接口产出
- `GET /`: 返回仪表盘 HTML 页面

## 详细步骤

### Step 1: 实现 routes/dashboard.py
```python
# routes/dashboard.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def dashboard(request: Request):
    """仪表盘页面"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
```

### Step 2: 创建 templates/base.html
```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Atlas MySQL Monitor{% endblock %}</title>
    
    <!-- Pico.css -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    
    <!-- 自定义样式 -->
    <link rel="stylesheet" href="/static/css/custom.css">
</head>
<body>
    <header class="container">
        <nav>
            <ul>
                <li><strong>Atlas MySQL Monitor</strong></li>
            </ul>
            <ul>
                <li>
                    <a href="#" id="theme-toggle" class="outline" role="button">
                        <span id="theme-icon">🌙</span>
                    </a>
                </li>
            </ul>
        </nav>
    </header>
    
    <main class="container">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="container">
        <small>Atlas MySQL Monitor v0.1.0</small>
    </footer>
    
    {% block scripts %}{% endblock %}
    
    <!-- 主题切换脚本 -->
    <script>
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        const html = document.documentElement;
        
        // 从 localStorage 读取主题
        const savedTheme = localStorage.getItem('theme') || 'light';
        html.setAttribute('data-theme', savedTheme);
        themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        
        themeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        });
    </script>
</body>
</html>
```

### Step 3: 创建 templates/dashboard.html
```html
{% extends "base.html" %}

{% block title %}仪表盘 - Atlas MySQL Monitor{% endblock %}

{% block content %}
<!-- 警告横幅 -->
<div id="warning-banner" class="warning-banner" style="display: none;">
    <article>
        <p id="warning-message"></p>
    </article>
</div>

<!-- 状态卡片 -->
<section id="status-section">
    <div class="grid">
        <article>
            <header>状态</header>
            <p id="mysql-status">加载中...</p>
        </article>
        <article>
            <header>运行时间</header>
            <p id="mysql-uptime">--</p>
        </article>
        <article>
            <header>最后采集</header>
            <p id="last-update">--</p>
        </article>
    </div>
</section>

<!-- 指标卡片 -->
<section id="metrics-cards">
    <div class="grid">
        <article>
            <header>连接数</header>
            <p id="threads-connected" class="metric-value">--</p>
        </article>
        <article>
            <header>活跃线程</header>
            <p id="threads-running" class="metric-value">--</p>
        </article>
        <article>
            <header>慢查询</header>
            <p id="slow-queries" class="metric-value">--</p>
        </article>
        <article>
            <header>总 QPS</header>
            <p id="total-qps" class="metric-value">--</p>
        </article>
    </div>
</section>

<!-- QPS 趋势图 -->
<section id="qps-chart-section">
    <article>
        <header>QPS 趋势（最近 24 小时）</header>
        <canvas id="qpsChart"></canvas>
    </article>
</section>

<!-- 连接数趋势图 -->
<section id="connections-chart-section">
    <article>
        <header>连接数趋势（最近 24 小时）</header>
        <canvas id="connectionsChart"></canvas>
    </article>
</section>
{% endblock %}

{% block scripts %}
<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>

<script>
    // 图表实例
    let qpsChart = null;
    let connectionsChart = null;
    
    // 初始化图表
    function initCharts() {
        const qpsCtx = document.getElementById('qpsChart').getContext('2d');
        qpsChart = new Chart(qpsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'SELECT QPS',
                        data: [],
                        borderColor: '#3b82f6',
                        tension: 0.1
                    },
                    {
                        label: 'INSERT QPS',
                        data: [],
                        borderColor: '#22c55e',
                        tension: 0.1
                    },
                    {
                        label: 'UPDATE QPS',
                        data: [],
                        borderColor: '#f97316',
                        tension: 0.1
                    },
                    {
                        label: 'DELETE QPS',
                        data: [],
                        borderColor: '#ef4444',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        const connCtx = document.getElementById('connectionsChart').getContext('2d');
        connectionsChart = new Chart(connCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '连接数',
                        data: [],
                        borderColor: '#8b5cf6',
                        tension: 0.1
                    },
                    {
                        label: '活跃线程',
                        data: [],
                        borderColor: '#06b6d4',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // 更新状态卡片
    async function updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            document.getElementById('mysql-status').textContent = data.message;
            document.getElementById('mysql-uptime').textContent = data.uptime;
            document.getElementById('last-update').textContent = data.last_update || '--';
            document.getElementById('threads-connected').textContent = data.threads_connected;
            document.getElementById('threads-running').textContent = data.threads_running;
            document.getElementById('slow-queries').textContent = data.slow_queries;
            document.getElementById('total-qps').textContent = data.total_qps;
            
            // 处理警告横幅
            const banner = document.getElementById('warning-banner');
            if (!data.connected && data.last_update) {
                banner.style.display = 'block';
                document.getElementById('warning-message').textContent = 
                    `MySQL 连接异常，最后成功采集时间: ${data.last_update}`;
            } else {
                banner.style.display = 'none';
            }
        } catch (error) {
            console.error('获取状态失败:', error);
        }
    }
    
    // 更新图表
    async function updateCharts() {
        try {
            const response = await fetch('/api/metrics?hours=24');
            const data = await response.json();
            
            // 格式化时间标签
            const labels = data.timestamps.map(t => {
                const date = new Date(t);
                return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            });
            
            // 更新 QPS 图表
            qpsChart.data.labels = labels;
            qpsChart.data.datasets[0].data = data.select_qps;
            qpsChart.data.datasets[1].data = data.insert_qps;
            qpsChart.data.datasets[2].data = data.update_qps;
            qpsChart.data.datasets[3].data = data.delete_qps;
            qpsChart.update();
            
            // 更新连接数图表
            connectionsChart.data.labels = labels;
            connectionsChart.data.datasets[0].data = data.threads_connected;
            connectionsChart.data.datasets[1].data = data.threads_running;
            connectionsChart.update();
        } catch (error) {
            console.error('获取指标失败:', error);
        }
    }
    
    // 页面加载后初始化
    document.addEventListener('DOMContentLoaded', () => {
        initCharts();
        updateStatus();
        updateCharts();
        
        // 每 60 秒刷新一次
        setInterval(() => {
            updateStatus();
            updateCharts();
        }, 60000);
    });
</script>
{% endblock %}
```

### Step 4: 运行应用验证页面
```bash
uv run uvicorn main:app --reload
```
访问 `http://localhost:8000/` 应该能看到仪表盘页面（数据为空状态）

### Step 5: 提交代码
```bash
git add routes/dashboard.py templates/
git commit -m "feat: 仪表盘页面"
```

## 全局约束
- Python >= 3.12
- 包管理器：uv（非 pip）
- 所有异步函数使用 `async def` + `await`
- 配置通过 `.env` 文件管理
- 文档使用中文编写
