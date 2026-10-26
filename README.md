# Nitya Gita: daily verse videos

Every morning at 06:00 IST a Cloudflare Worker cron (`cloudflare/`) starts a GitHub Actions job that builds the [Nitya Gita](https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita) app's "verse of the day" as a vertical video in several languages, attaches the videos to a release, and posts them to YouTube Shorts (and Instagram Reels once configured).

The video matches the in-app status video: same verse of the day, card layout, recitation and meaning audio, and ffmpeg filter graph. Verse data, audio and backgrounds are downloaded from the app's storage at run time. **No app data is stored in this repo.**

## Layout
| Path | What |
|---|---|
| `generator/make_video.py` | Builds one video plus its localized title, caption and hashtags (`meta.json`) |
| `generator/config.json` | Languages, labels, hashtags, post templates |
| `publish/youtube_upload.py` | Uploads a Short (YouTube Data API, resumable upload) |
| `publish/instagram_post.py` | Publishes a Reel (Instagram API with Instagram Login) |
| `publish/accounts.py` | Picks each language's account (its own or the shared one) |
| `tools/get_youtube_token.py` | One-time helper to get the YouTube refresh token |
| `posted/YYYY-MM.jsonl` | Log of what was posted, written by the workflow |
| `docs/instagram-accounts.md` | Checklist and profile text for the per-language Instagram accounts |
| `cloudflare/` | Cron Worker that starts the workflow at 06:00 IST (GitHub's own schedule, at 07:23 and 08:53 IST, is only a backup) |

## Settings (repo → Settings → Secrets and variables → Actions)
| Name | Type | Notes |
|---|---|---|
| `GITA_WORKER_URL` | variable | App storage Worker URL |
| `GITA_WORKER_TOKEN` | secret | Read token the app uses |
| `VIDEO_LANGS` | variable | Optional, e.g. `ml hi ta te` (default from config) |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | secrets | YouTube upload. Step skipped until set |
| `YT_PRIVACY` | variable | `public` (default), `unlisted` or `private` |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | secrets | Instagram. Step skipped until set |
| `IG_REFRESH_PAT` | secret | Fine-grained GitHub token (this repo, Secrets read/write) for weekly token refresh |

### Separate accounts per language
Any language can have its own YouTube channel, Instagram account, Facebook Page or Threads account. Add the same secrets with the language code appended, e.g. `YT_REFRESH_TOKEN_TA`, `IG_USER_ID_TA` + `IG_ACCESS_TOKEN_TA`, `FB_PAGE_ID_TA` + `FB_PAGE_TOKEN_TA`, `THREADS_USER_ID_TA` + `THREADS_TOKEN_TA`. The helpers below save them for you when given `--lang ta`. YouTube channels reuse the shared OAuth client, so only the refresh token is per language.

Languages without their own account keep posting to the shared one. To stop that for a platform, list the languages that may still use the shared account in `generator/config.json`, e.g. `"shared_account_languages": {"instagram": ["en", "hi"]}`. A platform that isn't listed lets every language use it.

Suggested setup for a new YouTube channel: in YouTube, create a channel (Brand Account) under the same Google account, then `YT_CLIENT_ID=... YT_CLIENT_SECRET=... python3 tools/get_youtube_token.py --lang ta` and pick the new channel. Each new Instagram account needs **Add account** in the Meta app (step 3 below), then `python3 tools/save_instagram_secrets.py --lang ta`. Facebook and Threads: `python3 tools/save_meta_secrets.py facebook --lang ta`.

### YouTube (one time)
Uses the app's Google Cloud project `srimad-bhagawad-gita`, where YouTube Data API v3 is already enabled.
1. [Google Auth Platform → Branding](https://console.cloud.google.com/auth/branding?project=srimad-bhagawad-gita): set the app name and support email (skip if already set).
2. [Audience](https://console.cloud.google.com/auth/audience?project=srimad-bhagawad-gita): User type **External**, then **Publish app** so it's *In production*. Otherwise refresh tokens expire after 7 days.
3. [Clients](https://console.cloud.google.com/auth/clients?project=srimad-bhagawad-gita) → **Create client** → **Desktop app**, named e.g. "Shorts uploader".
4. In Terminal: `python3 tools/get_youtube_token.py`. Paste the client ID and secret when asked, then sign in with the Google account that owns the channel and pick the channel. Google shows "hasn't verified this app": choose **Advanced → Go to …**, since it's your own app. The script saves all three secrets to this repo without printing them.

### Instagram (one time, after creating the account)
1. In the Instagram app: **Settings → Account type and tools → Switch to professional account → Creator**.
2. At [developers.facebook.com/apps](https://developers.facebook.com/apps/), **Create app** → use case **"Manage messaging & content on Instagram"** → create.
3. In the app: **Instagram → API setup with Instagram login → Generate access tokens → Add account**, then log in to the Instagram account and **Generate token**. Copy it.
4. Optional, for auto-refresh: create a [fine-grained GitHub token](https://github.com/settings/personal-access-tokens/new) for **only this repo** with **Secrets: Read and write**.
5. In Terminal: `python3 tools/save_instagram_secrets.py`. Paste the Instagram token (and the GitHub token if you made one). It checks the token, finds the account ID and saves `IG_USER_ID`, `IG_ACCESS_TOKEN` (and `IG_REFRESH_PAT`) without printing them.

The *Refresh Instagram token* workflow renews every Instagram and Threads token (shared and per language) every Monday when `IG_REFRESH_PAT` is set.

### Cloudflare trigger (one time)
1. Give a fine-grained GitHub token (this repo only) **Actions: Read and write**. You can add it to the `nityagita-ig-refresh` token.
2. `cd cloudflare && npx wrangler secret put GITHUB_TOKEN`, then paste the token.

## Running by hand
Actions → *Daily verse video* → **Run workflow**. Optional inputs are date, languages and publish on/off.

Locally (needs ffmpeg, Chrome and Dart):
```sh
export GITA_WORKER_URL=... GITA_WORKER_TOKEN=...
python3 generator/make_video.py --date 2026-10-21 --lang ml --out work/ml
```

## Safety in a public repo
- Secrets are only available to scheduled and manual runs, never to pull requests from forks.
- Downloads go to the runner's temp folder and are never uploaded as artifacts.
- Logs print only the verse reference and post links.
