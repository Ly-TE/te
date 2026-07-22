# k6 压测脚本使用说明

这两个脚本支持通过环境变量配置并发数、循环次数和压测时长。

## 文件说明

- `webapi_rate.js`
- `webapi_norate.js`

## 支持的环境变量

- `MODE`：压测模式，可选 `iterations` 或 `duration`
- `VUS`：并发数
- `ITERATIONS`：当 `MODE=iterations` 时的总循环次数
- `DURATION`：当 `MODE=duration` 时的压测时长，例如 `30s`、`1m`

## 运行示例

### 1、按循环次数执行

```bash
k6 run -e MODE=iterations -e VUS=20 -e ITERATIONS=1100 E:/te/Perf_Testing/webapi_perf/webapi_rate.js
```

> 注意：在 `MODE=iterations` 模式下，k6 要求 `ITERATIONS >= VUS`。脚本中已经做了自动兜底处理：如果你传入的 `ITERATIONS` 小于 `VUS`，脚本会自动按 `VUS` 作为最终循环次数执行。

### 2、按压测时长执行

```bash
k6 run -e MODE=duration -e VUS=50 -e DURATION=60s E:/te/Perf_Testing/webapi_perf/webapi_norate.js
```

## 执行结束后输出内容

脚本执行结束后，会输出以下中文汇总信息：

- 压测模式
- 并发数
- 循环次数
- 压测时长
- 总请求数
- 成功接口数
- 失败接口数
- 平均耗时
- P95 耗时
- 成功率

## 断言说明

脚本中已增加以下断言：

- HTTP 状态码必须为 `200`
- 响应体中的 `code` 不能为 `429`
- 响应体中的 `msg` 不能包含 `x-ratelimit-limit`

如果接口虽然 HTTP 返回成功，但响应体是如下限流内容，也会被断言识别为失败：

```json
{
  "code": 429,
  "msg": "x-ratelimit-limit:ratelimit:58.48.133.41"
}
```