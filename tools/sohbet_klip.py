#!/usr/bin/env python3
"""sohbet_klip.py - Yayin sohbetinin patladigi anlardan dikey klip keser.

1. INDIR: TwitchDownloader ile yayini (mp4) ve sohbeti (json) indir.
2. SAY:   Sohbet N saniyelik dilimlere bolunur, en yogun anlar bulunur.
3. KES:   Klip, sohbet patlamasindan ONCE baslar (sohbet hep gec tepki verir).
          Her klibe sohbette en cok tekrarlanan soz ad olarak verilir.

Kullanim:
    python sohbet_klip.py yayin.mp4 chat.json
    python sohbet_klip.py yayin.mp4 chat.json -n 10 --once 25 --uzunluk 40
    python sohbet_klip.py yayin.mp4 chat.json --mod blur --yazisiz

Sadece standart kutuphane + ffmpeg/ffprobe kullanir.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

W, H, FPS = 1080, 1920, 30
FONT_ADAYLARI = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


# ---------------------------------------------------------------- sohbet

def sohbet_oku(yol):
    """TwitchDownloader chat.json -> [(saniye, mesaj)]"""
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)
    yorumlar = veri.get("comments", veri if isinstance(veri, list) else [])
    mesajlar = []
    for y in yorumlar:
        t = y.get("content_offset_seconds")
        if t is None:
            continue
        m = y.get("message")
        if isinstance(m, dict):
            metin = m.get("body")
            if metin is None:
                metin = "".join(p.get("text", "") for p in m.get("fragments") or [])
        else:
            metin = m or y.get("text", "")
        mesajlar.append((float(t), str(metin or "")))
    mesajlar.sort()
    return mesajlar


def tr_kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def normalle(metin):
    """'POLİS UÇTUUU!!' ve 'polis uçtu' ayni sayilsin."""
    s = tr_kucuk(unicodedata.normalize("NFC", metin))
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"@\w+", "", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"(.)\1{2,}", r"\1", s)  # uçtuuuu -> uçtu, hahaaaa -> haha
    return " ".join(s.split())


def en_cok_soz(mesajlar):
    gruplar, ornekler = Counter(), {}
    for metin in mesajlar:
        n = normalle(metin)
        if not n or len(n) > 40:
            continue
        gruplar[n] += 1
        ornekler.setdefault(n, Counter())[metin.strip()] += 1
    if not gruplar:
        return "", 0
    soz, adet = gruplar.most_common(1)[0]
    return soz, adet


def patlamalari_bul(mesajlar, dilim, adet, once, uzunluk, video_sure):
    if not mesajlar:
        return []
    son = video_sure or mesajlar[-1][0] + dilim
    kova_say = int(son // dilim) + 1
    kovalar = [[] for _ in range(kova_say)]
    for t, metin in mesajlar:
        i = int(t // dilim)
        if 0 <= i < kova_say:
            kovalar[i].append(metin)

    sirali = sorted(range(kova_say), key=lambda i: len(kovalar[i]), reverse=True)
    secilen = []
    for i in sirali:
        if len(secilen) >= adet or not kovalar[i]:
            break
        patlama = i * dilim
        bas = max(0.0, patlama - once)
        bit = min(son, bas + uzunluk)
        # Ayni olayin komsu dilimlerini tekrar secme.
        if any(bas < s["bit"] and s["bas"] < bit for s in secilen):
            continue
        soz, soz_adet = en_cok_soz(kovalar[i])
        secilen.append({
            "patlama": patlama, "bas": bas, "bit": bit,
            "mesaj": len(kovalar[i]), "soz": soz, "soz_adet": soz_adet,
        })
    return secilen


# ---------------------------------------------------------------- video

def video_suresi(yol):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(yol)],
        capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return None


def ses_var_mi(yol):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(yol)],
        capture_output=True, text=True).stdout.strip()
    return bool(out)


def font_bul():
    for f in FONT_ADAYLARI:
        if Path(f).exists():
            return f
    return None


def filtre_yolu(yol):
    """ffmpeg filtre icinde dosya yolu (Windows 'C:' dahil) kacisi."""
    return str(yol).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def baslik_yap(soz):
    kelimeler = soz.split()
    return " ".join(k[:1].upper().replace("i", "İ") + k[1:] for k in kelimeler)


def dosya_adi(soz):
    tablo = str.maketrans("çğıöşüâî", "cgiosuai")
    s = tr_kucuk(soz).translate(tablo)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40] or "klip"


def klip_kes(video, ses, k, mod, yazi_dosyasi, font, cikti):
    sure = k["bit"] - k["bas"]
    if mod == "blur":
        vf = (f"[0:v]split=2[a][b];"
              f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"boxblur=30:5,eq=brightness=-0.08[bg];"
              f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2")
    else:
        vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}")
    vf += f",fps={FPS},setsar=1"
    if yazi_dosyasi and font:
        vf += (f",drawtext=fontfile='{filtre_yolu(font)}':"
               f"textfile='{filtre_yolu(yazi_dosyasi)}':"
               f"fontsize=84:fontcolor=white:borderw=7:bordercolor=black@0.9:"
               f"x=(w-text_w)/2:y=h*0.13")
    vf += ",format=yuv420p[v]"

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{k['bas']:.3f}", "-t", f"{sure:.3f}", "-i", str(video),
           "-filter_complex", vf, "-map", "[v]"]
    if ses:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-movflags", "+faststart", str(cikti)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-800:])


def zaman(sn):
    sn = int(sn)
    return f"{sn // 3600:d}:{sn % 3600 // 60:02d}:{sn % 60:02d}"


# ---------------------------------------------------------------- ana

def main():
    p = argparse.ArgumentParser(
        description="Sohbetin patladigi anlardan dikey klipler keser.")
    p.add_argument("video", type=Path, help="Yayin videosu (mp4)")
    p.add_argument("sohbet", type=Path, help="TwitchDownloader chat.json")
    p.add_argument("-n", "--adet", type=int, default=10, help="Klip sayisi (10)")
    p.add_argument("--dilim", type=float, default=15, help="Sohbet dilimi, sn (15)")
    p.add_argument("--once", type=float, default=25,
                   help="Klip patlamadan kac sn once baslasin (25)")
    p.add_argument("--uzunluk", type=float, default=40, help="Klip suresi, sn (40)")
    p.add_argument("--mod", choices=["crop", "blur"], default="crop",
                   help="crop: ortadan kirp, blur: tum goruntu + bulanik arka plan")
    p.add_argument("--yazisiz", action="store_true",
                   help="Klibe en cok tekrarlanan sozu yazma")
    p.add_argument("-o", "--cikti", type=Path, default=Path("klipler"))
    p.add_argument("--sadece-liste", action="store_true",
                   help="Kesmeden sadece bulunan anlari yazdir")
    a = p.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("ffmpeg/ffprobe bulunamadi. Kurup PATH'e ekle.")
    for f in (a.video, a.sohbet):
        if not f.exists():
            sys.exit(f"Dosya yok: {f}")

    print("Sohbet okunuyor...")
    mesajlar = sohbet_oku(a.sohbet)
    print(f"  {len(mesajlar)} mesaj")
    sure = video_suresi(a.video)
    klipler = patlamalari_bul(mesajlar, a.dilim, a.adet, a.once, a.uzunluk, sure)
    if not klipler:
        sys.exit("Sohbette mesaj bulunamadi.")

    print(f"\nEn yogun {len(klipler)} an:")
    for i, k in enumerate(klipler, 1):
        print(f"  {i:2d}. {zaman(k['patlama'])}  {k['mesaj']:4d} mesaj  "
              f"\"{k['soz']}\" x{k['soz_adet']}")
    if a.sadece_liste:
        return

    a.cikti.mkdir(parents=True, exist_ok=True)
    ses = ses_var_mi(a.video)
    font = None if a.yazisiz else font_bul()
    if not a.yazisiz and not font:
        print("Uyari: font bulunamadi, klipler yazisiz olacak.")

    # Klip numarasi yayindaki siraya gore degil, yogunluk sirasina gore.
    ozet = ["sira,dosya,patlama,baslangic,bitis,mesaj,soz,soz_adet"]
    with tempfile.TemporaryDirectory() as td:
        for i, k in enumerate(klipler, 1):
            ad = f"klip_{i:02d}_{dosya_adi(k['soz'])}.mp4"
            yazi = None
            if font and k["soz"]:
                yazi = Path(td) / f"yazi{i}.txt"
                yazi.write_text(baslik_yap(k["soz"]), encoding="utf-8")
            print(f"[{i}/{len(klipler)}] {ad}  ({zaman(k['bas'])} - {zaman(k['bit'])})")
            klip_kes(a.video, ses, k, a.mod, yazi, font, a.cikti / ad)
            soz = k["soz"].replace('"', "'")
            ozet.append(f'{i},{ad},{zaman(k["patlama"])},{zaman(k["bas"])},'
                        f'{zaman(k["bit"])},{k["mesaj"]},"{soz}",{k["soz_adet"]}')

    (a.cikti / "ozet.csv").write_text("\n".join(ozet) + "\n", encoding="utf-8")
    print(f"\nBitti: {a.cikti}/ ({len(klipler)} klip + ozet.csv)")


if __name__ == "__main__":
    main()
