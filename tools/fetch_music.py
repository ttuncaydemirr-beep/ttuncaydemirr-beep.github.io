#!/usr/bin/env python3
"""Zarfla davetiye müziklerini indirir, kısaltır ve sitenin src/music/ klasörüne yazar.

Yalnızca src/music/manifest.json'daki (telif kaydı onaylı) parçalar işlenir; başka kaynak YOKTUR.
Telif kaydı: Zarfla uygulama deposu docs/music_licenses.md.

Her parça için:
  1) download_url'den indirilir (genel bir User-Agent ile; kişisel bilgi gönderilmez),
  2) source_sha1 doluysa indirilen dosyanın SHA-1'i karşılaştırılır (uyuşmazsa iş DURUR),
  3) ffmpeg: start saniyesinden itibaren en çok 90 sn, 2 sn açılış + 4 sn kapanış geçişi,
     ses seviyesi eşitleme (loudnorm, -20 LUFS: davetli sayfasında kısık başlasın), 44.1 kHz stereo,
     96 kbps MP3; dosyaya başlık/sanatçı/lisans etiketi yazılır,
  4) çıktının sha256'sı ve süresi manifest.json'a kaydedilir.
Çalıştırma: python3 tools/fetch_music.py [--only <id>] [--force]
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUSIC = ROOT / "src" / "music"
MANIFEST = MUSIC / "manifest.json"
MAX_SEC = 90.0
FADE_IN = 2.0
FADE_OUT = 4.0
UA = "DemirGamesStudio-MusicFetch/1.1 (https://ttuncaydemirr-beep.github.io/; static site build) python-urllib"


def sh(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def probe_duration(p):
    out = sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p))
    return float(out.strip())


def digest(p, algo):
    h = hashlib.new(algo)
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dst):
    """Wikimedia hız sınırına (429) saygılı indirme: her dosyadan önce bekler, 429/5xx'te artan beklemeyle tekrar dener."""
    import time, urllib.error
    time.sleep(6)
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(dst, "wb") as f:
                while True:
                    b = r.read(1 << 16)
                    if not b:
                        break
                    f.write(b)
            return
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 7:
                raise
            ra = e.headers.get("Retry-After") if e.headers else None
            wait = int(ra) if ra and ra.isdigit() else 30 * (attempt + 1)
            print(f"  {e.code}; {wait} sn bekleniyor (deneme {attempt + 1}/8)", flush=True)
            time.sleep(min(wait, 300))


def process(t, force=False):
    out = MUSIC / t["file"]
    if out.exists() and t.get("sha256") and not force and digest(out, "sha256") == t["sha256"]:
        print(f"= {t['id']}: güncel")
        return
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src.bin"
        print(f"↓ {t['id']}: {t['download_url']}")
        download(t["download_url"], src)
        want = (t.get("source_sha1") or "").strip().lower()
        if want:
            got = digest(src, "sha1")
            if got != want:
                sys.exit(f"HATA {t['id']}: kaynak SHA-1 uyuşmuyor ({got} != {want}). Dosya değişmiş olabilir; telif kaydını yeniden doğrulayın.")
        start = float(t.get("start") or 0)
        total = probe_duration(src)
        length = max(5.0, min(MAX_SEC, total - start))
        fade_out_at = max(0.0, length - FADE_OUT)
        af = (f"afade=t=in:st=0:d={FADE_IN},afade=t=out:st={fade_out_at:.2f}:d={FADE_OUT},"
              "loudnorm=I=-20:TP=-2:LRA=11")
        comment = f"License: {t['license']} {t['license_url']} | Source: {t['source_page']} | Trimmed and faded by Demir Games Studio"
        tmp_out = Path(td) / "out.mp3"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(src),
            "-vn", "-map_metadata", "-1", "-af", af, "-ac", "2", "-ar", "44100",
            "-c:a", "libmp3lame", "-b:a", "96k",
            "-metadata", f"title={t['title']}",
            "-metadata", f"artist={t['performer']}",
            "-metadata", f"composer={t['composer']}",
            "-metadata", f"comment={comment}",
            str(tmp_out),
        ], check=True)
        out.write_bytes(tmp_out.read_bytes())
    t["sha256"] = digest(out, "sha256")
    t["duration"] = round(probe_duration(out), 2)
    print(f"✓ {t['id']}: {t['duration']} sn, {out.stat().st_size // 1024} KB, sha256 {t['sha256'][:12]}…")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="yalnız bu kimlik")
    ap.add_argument("--force", action="store_true", help="güncel olsa da yeniden üret")
    a = ap.parse_args()
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids = set()
    for t in m["tracks"]:
        if t["id"] in ids or not t["id"].replace("-", "").isalnum() or t["file"] != t["id"] + ".mp3":
            sys.exit(f"HATA: geçersiz/tekrarlanan kimlik {t['id']}")
        ids.add(t["id"])
        if a.only and t["id"] != a.only:
            continue
        process(t, a.force)
    # Manifest dışı mp3 kalmasın (yalnız onaylı liste yayımlanır)
    for f in MUSIC.glob("*.mp3"):
        if f.stem not in ids:
            print(f"- listede olmayan dosya silindi: {f.name}")
            f.unlink()
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
