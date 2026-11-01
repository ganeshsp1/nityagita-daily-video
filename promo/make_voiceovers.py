"""Voiceovers for the promo videos, one clip per line of promo/scripts.json,
with AI4Bharat's Indic Parler-TTS (the voices the app uses). Run it where the
model runs well (a Mac with Apple GPU, or a CUDA GPU), not on CI:

  python3 promo/make_voiceovers.py --out ~/nityagita_promo_voice [--upload]

Writes <out>/<lang>/<video>-<n>.m4a (loudness-normalised AAC). With --upload,
also puts them on R2 under promo/voice/ (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
R2_SECRET_ACCESS_KEY from the environment), where promo/make_promo.py reads
them through the app's storage Worker. Existing clips are skipped, so a
second run only makes what is missing; --redo makes them again.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUCKET = os.environ.get("R2_BUCKET", "bhagavadgitav1")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default="~/nityagita_promo_voice")
    p.add_argument("--langs", nargs="*", help="default: all in scripts.json")
    p.add_argument("--videos", nargs="*", help="default: all")
    p.add_argument("--upload", action="store_true")
    p.add_argument("--redo", action="store_true")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args()

    spec = json.load(open(HERE / "scripts.json", encoding="utf-8"))
    out = Path(args.out).expanduser()
    jobs = []
    for video, v in spec["videos"].items():
        if args.videos and video not in args.videos:
            continue
        for lang, lines in v["lines"].items():
            if args.langs and lang not in args.langs:
                continue
            for n, text in enumerate(lines, 1):
                dst = out / lang / f"{video}-{n}.m4a"
                if args.redo or not dst.exists():
                    jobs.append((lang, video, n, text, dst))
    print(f"{len(jobs)} clips to make")

    if jobs:
        import soundfile as sf
        import torch
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer, set_seed

        device = "cuda:0" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        model_id = "ai4bharat/indic-parler-tts"
        print(f"loading {model_id} on {device}")
        model = ParlerTTSForConditionalGeneration.from_pretrained(model_id).to(device)
        tok = AutoTokenizer.from_pretrained(model_id)
        dtok = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
        sr = model.config.sampling_rate
        for i, (lang, video, n, text, dst) in enumerate(jobs, 1):
            desc = spec["description"].format(speaker=spec["speakers"][lang])
            d = dtok(desc, return_tensors="pt").to(device)
            t = tok(text, return_tensors="pt").to(device)
            set_seed(args.seed)
            with torch.no_grad():
                audio = model.generate(
                    input_ids=d.input_ids, attention_mask=d.attention_mask,
                    prompt_input_ids=t.input_ids, prompt_attention_mask=t.attention_mask,
                    do_sample=True, temperature=1.0, max_new_tokens=1500,
                ).cpu().numpy().squeeze()
            dst.parent.mkdir(parents=True, exist_ok=True)
            wav = dst.with_suffix(".wav")
            sf.write(wav, audio, sr)
            # Even loudness across clips; trim silence at both ends.
            subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
                 "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "loudnorm=I=-16:TP=-1.5:LRA=11",
                 "-ar", "44100", "-c:a", "aac", "-b:a", "128k", str(dst)],
                check=True)
            wav.unlink()
            print(f"[{i}/{len(jobs)}] {lang} {video}-{n}: {text[:50]}", flush=True)

    if args.upload:
        import boto3
        s3 = boto3.client(
            "s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
        files = sorted(out.glob("*/*.m4a"))
        for f in files:
            s3.upload_file(str(f), BUCKET, f"promo/voice/{f.parent.name}/{f.name}",
                           ExtraArgs={"ContentType": "audio/mp4"})
        print(f"uploaded {len(files)} clips to r2://{BUCKET}/promo/voice/")


if __name__ == "__main__":
    main()
