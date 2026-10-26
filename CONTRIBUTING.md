# Contributing

Thanks for helping. Issues and pull requests are welcome: bug fixes, new platforms, better captions, layout or language support.

## Before you start
- **App data is private.** The generator downloads verse text, audio and backgrounds from the Nitya Gita app's storage (`GITA_WORKER_URL` / `GITA_WORKER_TOKEN`), which isn't public. You can work on the publishing scripts, workflows and tools without it. To render videos locally, point the generator at your own data in the same format.
- **Never commit secrets, tokens or app data** (verse JSON, audio, background videos). The repo stores code and configuration only.
- Pull requests from forks don't get this repo's secrets, so CI on a fork never posts anywhere.

## Making a change
1. Fork, create a branch, and keep each pull request focused on one thing.
2. Match the existing style: standard-library Python, short docstrings with a `usage:` line, small scripts.
3. Test what you can locally (`python3 -m py_compile ...`, a dry run of the script). For workflow changes, run the workflow on your fork with **publish** turned off.
4. Describe what changed and how you tested it.

## Translations
Captions, labels and intro-post text live in `generator/config.json` and `generator/intro_posts.json`. Corrections from native speakers are especially welcome.

## License
By contributing, you agree that your contributions are licensed under the [GNU AGPL-3.0](LICENSE), the same as the project.
