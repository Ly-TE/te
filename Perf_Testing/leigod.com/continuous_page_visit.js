const fs = require('fs');
const path = require('path');

const PAGE_FILE = path.join(__dirname, 'page.md');
const DEFAULT_DURATION_MINUTES = Number(process.env.DURATION_MINUTES || 60);
const CONCURRENCY = Math.max(1, Number(process.env.CONCURRENCY || 3));
const INTERVAL_MS = Math.max(0, Number(process.env.INTERVAL_MS || 1000));
const TIMEOUT_MS = Math.max(1000, Number(process.env.TIMEOUT_MS || 15000));
const USER_AGENT =
  process.env.USER_AGENT ||
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

function loadUrls(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const urls = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'))
    .map((line) => line.replace(/^[-*+]|^\d+\./, '').trim())
    .filter((line) => /^https?:\/\//i.test(line));

  return [...new Set(urls)];
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function formatMs(ms) {
  if (!Number.isFinite(ms) || ms < 0) {
    return '0ms';
  }

  if (ms < 1000) {
    return `${ms}ms`;
  }

  return `${(ms / 1000).toFixed(2)}s`;
}

async function visitUrl(url, stats) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const start = Date.now();

  try {
    const response = await fetch(url, {
      method: 'GET',
      redirect: 'follow',
      signal: controller.signal,
      headers: {
        'User-Agent': USER_AGENT,
        Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        Pragma: 'no-cache',
      },
    });

    await response.arrayBuffer();
    const duration = Date.now() - start;

    stats.total += 1;
    stats.success += 1;
    stats.totalDuration += duration;
    if (duration > stats.maxDuration) {
      stats.maxDuration = duration;
    }

    console.log(
      `[${new Date().toLocaleString('zh-CN')}] SUCCESS ${response.status} ${formatMs(duration)} ${url}`,
    );
  } catch (error) {
    const duration = Date.now() - start;
    stats.total += 1;
    stats.fail += 1;
    stats.totalDuration += duration;
    if (duration > stats.maxDuration) {
      stats.maxDuration = duration;
    }

    console.error(
      `[${new Date().toLocaleString('zh-CN')}] FAIL ${formatMs(duration)} ${url} -> ${error.message}`,
    );
  } finally {
    clearTimeout(timeout);
  }
}

async function worker(workerId, urls, endTime, stats, nextIndexRef) {
  while (Date.now() < endTime) {
    const url = urls[nextIndexRef.value % urls.length];
    nextIndexRef.value += 1;

    console.log(`worker-${workerId} visiting: ${url}`);
    await visitUrl(url, stats);

    if (Date.now() < endTime && INTERVAL_MS > 0) {
      await sleep(INTERVAL_MS);
    }
  }
}

async function main() {
  if (!fs.existsSync(PAGE_FILE)) {
    throw new Error(`页面列表文件不存在: ${PAGE_FILE}`);
  }

  const urls = loadUrls(PAGE_FILE);
  if (urls.length === 0) {
    throw new Error('page.md 中没有找到可用的 URL，请按每行一个链接填写。');
  }

  const durationMs = DEFAULT_DURATION_MINUTES * 60 * 1000;
  const endTime = Date.now() + durationMs;
  const stats = {
    total: 0,
    success: 0,
    fail: 0,
    totalDuration: 0,
    maxDuration: 0,
  };
  const nextIndexRef = { value: 0 };

  console.log('================ 页面持续访问任务开始 ================');
  console.log(`页面数量: ${urls.length}`);
  console.log(`持续时长: ${DEFAULT_DURATION_MINUTES} 分钟`);
  console.log(`并发数: ${CONCURRENCY}`);
  console.log(`每次请求间隔: ${INTERVAL_MS} ms`);
  console.log(`单次请求超时: ${TIMEOUT_MS} ms`);
  console.log('====================================================');

  const workers = Array.from({ length: CONCURRENCY }, (_, index) =>
    worker(index + 1, urls, endTime, stats, nextIndexRef),
  );

  await Promise.all(workers);

  const averageDuration = stats.total > 0 ? stats.totalDuration / stats.total : 0;
  const successRate = stats.total > 0 ? ((stats.success / stats.total) * 100).toFixed(2) : '0.00';

  console.log('');
  console.log('================ 页面持续访问任务结束 ================');
  console.log(`总请求数: ${stats.total}`);
  console.log(`成功次数: ${stats.success}`);
  console.log(`失败次数: ${stats.fail}`);
  console.log(`成功率: ${successRate}%`);
  console.log(`平均耗时: ${formatMs(Math.round(averageDuration))}`);
  console.log(`最长耗时: ${formatMs(stats.maxDuration)}`);
  console.log('====================================================');
}

main().catch((error) => {
  console.error(`脚本执行失败: ${error.message}`);
  process.exit(1);
});