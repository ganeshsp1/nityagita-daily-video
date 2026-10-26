# Per-language Instagram accounts

One Instagram account per language, alongside the main **@the_nityagita** (which keeps English, plus Hindi until @the_nityagita_hindi has an audience). Names, bios and labels reuse the translations in `generator/config.json`.

## Checklist
| Lang | Username | Name | Status |
|---|---|---|---|
| `hi` | `the_nityagita_hindi` | Gita Hindi · नित्य गीता | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |
| `ta` | `the_nityagita_tamil` | Gita Tamil · நித்ய கீதா | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |
| `te` | `the_nityagita_telugu` | Gita Telugu · నిత్య గీతా | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |
| `ml` | `the_nityagita_malayalam` | Gita Malayalam · നിത്യ ഗീത | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |
| `kn` | `the_nityagita_kannada` | Gita Kannada · ನಿತ್ಯ ಗೀತಾ | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |
| `mr` | `the_nityagita_marathi` | Gita Marathi · नित्य गीता | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |
| `bn` | `the_nityagita_bengali` | Gita Bengali · নিত্য গীতা | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |
| `or` | `the_nityagita_odia` | Gita Odia · ନିତ୍ୟ ଗୀତା | ☐ created · ☐ Creator · ☐ in Meta app · ☐ secrets saved |

## Guided setup
`python3 tools/instagram_account_helper.py` runs through the steps below for each language not yet done. At each step it opens the page in Chrome and copies the next value to the clipboard; you paste and click. At the end it asks for the token (hidden), checks it belongs to the right account, saves the secrets and can post the two latest videos as starter Reels. Progress is kept in `~/.nityagita_instagram_accounts.json`.

- Specific languages: `python3 tools/instagram_account_helper.py ta te`
- Account already created, only connect it: `python3 tools/instagram_account_helper.py --connect hi`
- Account already connected, only post the intro posts: `python3 tools/instagram_account_helper.py --intro-only hi`

### Pinned intro posts
Each account gets three posts to pin, in the same design as @the_nityagita's: **Welcome**, **Every morning at 6 AM** (what each Reel contains, plus a pointer to @the_nityagita for other languages) and **the app**. `python3 tools/make_intro_posts.py` renders them to `~/Desktop/NityaGita_Instagram/<lang>/` with captions, using text from `generator/intro_posts.json` (have a native speaker check it). The helper posts them in order 3, 2, 1, hosting the images on this repo's `intro-posts` release, and then lists the links to pin in that order so Welcome ends up first. The API can't pin, so pinning is done by hand: post → ⋯ → Pin to your profile.

## Steps for each account
1. **Create it from the main account** so no new email or phone is needed: Instagram app → Profile → ☰ → **Accounts Center → Accounts → Add accounts → Instagram → Create new account**. Pick the username above and choose to share login info with @the_nityagita.
   - Create **2–3 a day**, not all 8 at once. Many new accounts from one device in one sitting often triggers Instagram's spam checks.
   - The app only switches quickly between a handful of logged-in accounts. Extra ones stay in Accounts Center and can be switched to from there.
2. **Fill in the profile:** paste the name, bio and link below (Edit profile → Links → Add external link), and set the profile picture.
3. **Make it a Creator account:** Settings → **Account type and tools → Switch to professional account → Creator**, category *Education* or *Spiritual leader*/*Public figure*.
4. **Post a little by hand first:** a profile picture and 1–3 posts (for example, share the latest automated reel from @the_nityagita) before automation starts. Brand-new empty accounts that suddenly post through the API are more likely to be flagged.
5. **Add it to the Meta app:** developers.facebook.com/apps → your app → **Instagram → API setup with Instagram login → Generate access tokens → Add account**. Log in as the new account, then **Generate token** and copy it.
6. **Save the secrets:** run the command under that language below, then paste the token. It saves `IG_USER_ID_<LANG>` and `IG_ACCESS_TOKEN_<LANG>`. Skip the GitHub token prompt (`IG_REFRESH_PAT` is already set). The weekly refresh covers the new token automatically.
7. **Check it:** `gh secret list -R ganeshsp1/nityagita-daily-video | grep _TA` (with the language's code). The next 06:00 IST run posts that language to the new account.
8. **Threads (optional):** the Threads profile comes with the Instagram account. Create it in the Threads app, then run `python3 tools/save_meta_secrets.py threads --lang <code>`.
9. **Cross-promote:** for the first couple of weeks, keep @the_nityagita posting all languages, and mention each new handle in a story or pinned post so existing followers can move. After that, set `"shared_account_languages": {"instagram": ["en", "hi"]}` in `generator/config.json` to stop posting the other languages to the main account.

The bio links carry a Play Store `referrer` (`utm_source=instagram`, `utm_campaign=<lang>`). Installs from each account should then show up per campaign in Play Console's acquisition reports.

## Profiles
### hi: @the_nityagita_hindi
- **Name:** Gita Hindi · नित्य गीता
- **Bio:**
  ```
  🙏 भगवद्गीता · आज का श्लोक
  🕕 Daily 6 AM IST · Sanskrit + हिंदी
  📲 ऐप डाउनलोड करें 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dhi
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang hi`

### ta: @the_nityagita_tamil
- **Name:** Gita Tamil · நித்ய கீதா
- **Bio:**
  ```
  🙏 பகவத் கீதை · இன்றைய ஸ்லோகம்
  🕕 Daily 6 AM IST · Sanskrit + தமிழ்
  📲 செயலியை பதிவிறக்கவும் 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dta
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang ta`

### te: @the_nityagita_telugu
- **Name:** Gita Telugu · నిత్య గీతా
- **Bio:**
  ```
  🙏 భగవద్గీత · నేటి శ్లోకం
  🕕 Daily 6 AM IST · Sanskrit + తెలుగు
  📲 యాప్‌ని డౌన్‌లోడ్ చేయండి 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dte
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang te`

### ml: @the_nityagita_malayalam
- **Name:** Gita Malayalam · നിത്യ ഗീത
- **Bio:**
  ```
  🙏 ഭഗവദ്ഗീത · ഇന്നത്തെ ശ്ലോകം
  🕕 Daily 6 AM IST · Sanskrit + മലയാളം
  📲 ആപ്പ് ഡൗൺലോഡ് ചെയ്യുക 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dml
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang ml`

### kn: @the_nityagita_kannada
- **Name:** Gita Kannada · ನಿತ್ಯ ಗೀತಾ
- **Bio:**
  ```
  🙏 ಭಗವದ್ಗೀತೆ · ಇಂದಿನ ಶ್ಲೋಕ
  🕕 Daily 6 AM IST · Sanskrit + ಕನ್ನಡ
  📲 ಅಪ್ಲಿಕೇಶನ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dkn
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang kn`

### mr: @the_nityagita_marathi
- **Name:** Gita Marathi · नित्य गीता
- **Bio:**
  ```
  🙏 भगवद्गीता · आजचा श्लोक
  🕕 Daily 6 AM IST · Sanskrit + मराठी
  📲 ॲप डाउनलोड करा 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dmr
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang mr`

### bn: @the_nityagita_bengali
- **Name:** Gita Bengali · নিত্য গীতা
- **Bio:**
  ```
  🙏 ভগবদ্গীতা · আজকের শ্লোক
  🕕 Daily 6 AM IST · Sanskrit + বাংলা
  📲 অ্যাপ ডাউনলোড করুন 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dbn
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang bn`

### or: @the_nityagita_odia
- **Name:** Gita Odia · ନିତ୍ୟ ଗୀତା
- **Bio:**
  ```
  🙏 ଭଗବଦ୍ଗୀତା · ଆଜିର ଶ୍ଲୋକ
  🕕 Daily 6 AM IST · Sanskrit + ଓଡ଼ିଆ
  📲 ଆପ୍ ଡାଉନଲୋଡ୍ କରନ୍ତୁ 👇
  ```
- **Link:** https://play.google.com/store/apps/details?id=com.ganesh.srimad_bhagvad_gita&referrer=utm_source%3Dinstagram%26utm_medium%3Dbio%26utm_campaign%3Dor
- **Save secrets:** `python3 tools/save_instagram_secrets.py --lang or`
