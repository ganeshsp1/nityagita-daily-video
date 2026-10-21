# Nitya Gita: daily verse videos

Every morning (06:00 IST) a GitHub Actions job builds the [Nitya Gita](https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita) app's "verse of the day" as a vertical video in several languages, attaches the videos to a release, and posts them to YouTube Shorts (and Instagram Reels once configured).

The video matches the in-app status video: same verse of the day, card layout, recitation and meaning audio, and ffmpeg filter graph. Verse data, audio and backgrounds are downloaded from the app's storage at run time. **No app data is stored in this repo.**

## Layout
| Path | What |
|---|---|
| `generator/make_video.py` | Builds one video plus its localized title, caption and hashtags (`meta.json`) |
| `generator/config.json` | Languages, labels, hashtags, post templates |
| `publish/youtube_upload.py` | Uploads a Short (YouTube Data API, resumable upload) |
| `publish/instagram_post.py` | Publishes a Reel (Instagram API with Instagram Login) |
| `tools/get_youtube_token.py` | One-time helper to get the YouTube refresh token |
| `posted/YYYY-MM.jsonl` | Log of what was posted, written by the workflow |

## Settings (repo → Settings → Secrets and variables → Actions)
| Name | Type | Notes |
|---|---|---|
| `GITA_WORKER_URL` | variable | App storage Worker URL |
| `GITA_WORKER_TOKEN` | secret | Read token the app uses |
| `VIDEO_LANGS` | variable | Optional, e.g. `ml hi ta te` (default from config) |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | secrets | YouTube upload. Step skipped until set |
| `YT_PRIVACY` | variable | `private` (default) → `public` once you're happy |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | secrets | Instagram. Step skipped until set |

### YouTube (one time)
Uses the app's Google Cloud project `srimad-bhagawad-gita`, where YouTube Data API v3 is already enabled.
1. [Google Auth Platform → Branding](https://console.cloud.google.com/auth/branding?project=srimad-bhagawad-gita): set the app name and support email (skip if already set).
2. [Audience](https://console.cloud.google.com/auth/audience?project=srimad-bhagawad-gita): User type **External**, then **Publish app** so it's *In production*. Otherwise refresh tokens expire after 7 days.
3. [Clients](https://console.cloud.google.com/auth/clients?project=srimad-bhagawad-gita) → **Create client** → **Desktop app**, named e.g. "Shorts uploader".
4. In Terminal: `python3 tools/get_youtube_token.py`. Paste the client ID and secret when asked, then sign in with the Google account that owns the channel and pick the channel. Google shows "hasn't verified this app": choose **Advanced → Go to …**, since it's your own app. The script saves all three secrets to this repo without printing them.

### Instagram (one time, after creating the account)
1. Switch the account to **Professional → Creator** (or Business).
2. At [developers.facebook.com](https://developers.facebook.com/), create an app and add the **Instagram** product (API setup with Instagram Login).
3. Add the account as an Instagram tester and accept the invite in the Instagram app.
4. Generate a token with `instagram_business_basic` and `instagram_business_content_publish`, then exchange it for a **long-lived token** (valid 60 days).
5. Save `IG_USER_ID` and `IG_ACCESS_TOKEN` as repo secrets. Token auto-refresh is still TODO.

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
