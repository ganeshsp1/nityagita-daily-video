// Starts the "Daily verse video" GitHub workflow at 06:00 IST.
// Cloudflare cron triggers fire reliably, unlike GitHub's own schedule,
// which is often late or skipped. The GitHub schedule stays as a backup;
// the workflow's posted log prevents double posting.
const WORKFLOW_URL =
  'https://api.github.com/repos/ganeshsp1/nityagita-daily-video/actions/workflows/daily.yml/dispatches';

async function dispatch(env) {
  const res = await fetch(WORKFLOW_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'nityagita-daily-cron',
    },
    body: JSON.stringify({ ref: 'main', inputs: { publish: 'true' } }),
  });
  if (!res.ok) {
    throw new Error(`workflow dispatch failed: ${res.status} ${await res.text()}`);
  }
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },
};
