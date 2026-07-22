## 页面持续访问脚本

### 1. 维护页面列表

把需要访问的页面链接填写到 `page.md`，支持以下格式：

```md
# 每行一个链接，或 markdown 列表都可以
https://www.example.com/
- https://www.example.com/page-a
- https://www.example.com/page-b
1. https://www.example.com/page-c
```

### 2. 运行 1 小时持续访问

```bash
node Perf_Testing/leigod.com/continuous_page_visit.js
```

默认行为：

- 持续 60 分钟
- 3 个并发 worker 循环访问页面列表
- 每次请求后间隔 1000ms
- 单次请求超时 15000ms

### 3. 可选参数

Windows CMD 示例：

```bash
set DURATION_MINUTES=60 && set CONCURRENCY=5 && set INTERVAL_MS=500 && node Perf_Testing/leigod.com/continuous_page_visit.js
```

可用环境变量：

- `DURATION_MINUTES`：持续时长，默认 `60`
- `CONCURRENCY`：并发数，默认 `3`
- `INTERVAL_MS`：每个 worker 每次请求后的间隔，默认 `1000`
- `TIMEOUT_MS`：单次请求超时，默认 `15000`
- `USER_AGENT`：自定义请求头中的 User-Agent

### 4. 输出结果

脚本运行时会实时打印：

- 访问时间
- URL
- HTTP 状态码
- 单次耗时
- 失败原因

结束后会汇总：

- 总请求数
- 成功次数
- 失败次数
- 成功率
- 平均耗时
- 最长耗时