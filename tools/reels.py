#!/usr/bin/env python3
"""Otomatik reels yapici.

Bir klasordeki oyun kliplerini analiz eder, en hareketli/gurultulu anlari
secer ve dikey (1080x1920) 60 saniyelik bir reels videosu olusturur.

Kullanim:
    python3 tools/reels.py klipler/ -o reels.mp4
    python3 tools/reels.py klipler/ -o reels.mp4 --muzik muzik.mp3 --baslik "GTA 6 anlari"
    python3 tools/reels.py klipler/ --mod blur --sure 30 --kesit 2.5

Gereksinim: ffmpeg ve ffprobe.
"""

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VIDEO_UZANTILARI = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
W, H, FPS = 1080, 1920, 30
FONT_ADAYLARI = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


def calistir(cmd, yakala=True):
    sonuc = subprocess.run(cmd, capture_output=yakala, text=True)
    if sonuc.returncode != 0:
        sys.stderr.write(sonuc.stderr or "")
        raise RuntimeError("Komut basarisiz: " + " ".join(cmd[:6]) + " ...")
    return sonuc


def bilgi(yol):
    out = calistir([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(yol),
    ]).stdout
    veri = json.loads(out)
    sure = float(veri["format"].get("duration", 0))
    ses_var = any(s["codec_type"] == "audio" for s in veri["streams"])
    return sure, ses_var


def saniye_basina(degerler, sure):
    """(zaman, deger) listesini saniye kovalarina ortalar."""
    n = max(1, math.ceil(sure))
    toplam, sayi = [0.0] * n, [0] * n
    for t, v in degerler:
        i = min(n - 1, max(0, int(t)))
        toplam[i] += v
        sayi[i] += 1
    return [toplam[i] / sayi[i] if sayi[i] else 0.0 for i in range(n)]


def hareket_skoru(yol, sure):
    """Kareler arasi sahne degisimi skorunu (hareket olcusu) saniye basina dondurur."""
    out = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(yol), "-an",
        "-vf", "fps=10,scale=160:-2,select='gte(scene,0)',"
               "metadata=print:key=lavfi.scene_score:file=-",
        "-f", "null", "-",
    ], capture_output=True, text=True).stdout
    degerler, t = [], None
    for satir in out.splitlines():
        m = re.search(r"pts_time:([\d.]+)", satir)
        if m:
            t = float(m.group(1))
        m = re.search(r"lavfi\.scene_score=([\d.]+)", satir)
        if m and t is not None:
            degerler.append((t, float(m.group(1))))
    return saniye_basina(degerler, sure)


def ses_skoru(yol, sure):
    """Anlik ses yuksekligini (LUFS) saniye basina dondurur."""
    out = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(yol), "-vn",
        "-af", "ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file=-",
        "-f", "null", "-",
    ], capture_output=True, text=True).stdout
    degerler, t = [], None
    for satir in out.splitlines():
        m = re.search(r"pts_time:([\d.]+)", satir)
        if m:
            t = float(m.group(1))
        m = re.search(r"lavfi\.r128\.M=(-?[\d.]+|-inf)", satir)
        if m and t is not None:
            v = -70.0 if m.group(1) == "-inf" else max(-70.0, float(m.group(1)))
            degerler.append((t, v))
    return saniye_basina(degerler, sure)


def normalize(liste):
    if not liste:
        return liste
    lo, hi = min(liste), max(liste)
    if hi - lo < 1e-9:
        return [0.5] * len(liste)
    return [(x - lo) / (hi - lo) for x in liste]


def analiz_et(klipler):
    sonuclar = []
    for yol in klipler:
        sure, ses_var = bilgi(yol)
        if sure < 1.0:
            continue
        print(f"  analiz: {yol.name} ({sure:.1f} sn)")
        hareket = normalize(hareket_skoru(yol, sure))
        ses = normalize(ses_skoru(yol, sure)) if ses_var else [0.0] * len(hareket)
        # Hareket biraz daha agir basar: oyun kliplerinde aksiyon gorunur.
        skor = [0.6 * h + 0.4 * s for h, s in zip(hareket, ses)]
        sonuclar.append({"yol": yol, "sure": sure, "ses": ses_var, "skor": skor})
    return sonuclar


def kesit_sec(analizler, hedef, kesit):
    """Tum kliplerden en yuksek skorlu, cakismayan kesitleri secer."""
    adaylar = []
    for ki, a in enumerate(analizler):
        skor, sure = a["skor"], a["sure"]
        bas, son = 0.5, sure - 0.5  # cok bas/son kisimlari atla
        t = bas
        while t + kesit <= son:
            i0, i1 = int(t), max(int(t) + 1, int(math.ceil(t + kesit)))
            pencere = skor[i0:i1] or [0.0]
            adaylar.append((sum(pencere) / len(pencere), ki, t))
            t += 0.5
    adaylar.sort(reverse=True)

    gereken = math.ceil(hedef / kesit)
    # Tek bir klibin her seyi kaplamasini engelle: klip basina adil pay.
    toplam_sure = sum(a["sure"] for a in analizler)
    limit = {
        ki: max(1, math.ceil(gereken * a["sure"] / toplam_sure) + 1)
        for ki, a in enumerate(analizler)
    }
    secilen, kullanim = [], {}
    for skor, ki, t in adaylar:
        if len(secilen) >= gereken:
            break
        if kullanim.get(ki, 0) >= limit[ki]:
            continue
        if any(k == ki and abs(t - s) < kesit for _, k, s in secilen):
            continue
        secilen.append((skor, ki, t))
        kullanim[ki] = kullanim.get(ki, 0) + 1
    # Eksik kaldiysa once limitsiz, sonra kismi cakismaya izin vererek doldur.
    for bosluk in (kesit, kesit * 0.5):
        for skor, ki, t in adaylar:
            if len(secilen) >= gereken:
                break
            if any(k == ki and abs(t - s) < bosluk for _, k, s in secilen):
                continue
            secilen.append((skor, ki, t))

    # Hikaye akisi icin klip sirasi ve zamana gore diz.
    secilen.sort(key=lambda x: (x[1], x[2]))
    return [(ki, t) for _, ki, t in secilen]


def video_filtresi(mod, sure):
    fade = f"fade=t=in:st=0:d=0.12,fade=t=out:st={max(0, sure - 0.12):.3f}:d=0.12"
    if mod == "blur":
        return (
            f"[0:v]split=2[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=30:5,eq=brightness=-0.08[bg];"
            f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps={FPS},setsar=1,format=yuv420p,{fade}[v]"
        )
    return (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"fps={FPS},setsar=1,format=yuv420p,{fade}[v]"
    )


def kesit_render(kaynak, ses_var, bas, sure, mod, cikti):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{bas:.3f}", "-t", f"{sure:.3f}", "-i", str(kaynak)]
    if not ses_var:
        cmd += ["-f", "lavfi", "-t", f"{sure:.3f}",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    ses_giris = "0:a" if ses_var else "1:a"
    filtre = video_filtresi(mod, sure) + (
        f";[{ses_giris}]aresample=48000,aformat=channel_layouts=stereo,"
        f"afade=t=in:st=0:d=0.08,afade=t=out:st={max(0, sure - 0.08):.3f}:d=0.08[a]"
    )
    cmd += ["-filter_complex", filtre, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-t", f"{sure:.3f}", str(cikti)]
    calistir(cmd)


def font_bul():
    for f in FONT_ADAYLARI:
        if Path(f).exists():
            return f
    return None


def drawtext_kacis(metin):
    return (metin.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "’").replace("%", "\\%"))


def birlestir(parcalar, cikti, hedef, muzik, baslik, gecici):
    liste = gecici / "liste.txt"
    liste.write_text("".join(f"file '{p.as_posix()}'\n" for p in parcalar))
    ham = gecici / "ham.mp4"
    calistir(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
              "-f", "concat", "-safe", "0", "-i", str(liste), "-c", "copy", str(ham)])

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(ham)]
    if muzik:
        cmd += ["-stream_loop", "-1", "-i", str(muzik)]

    vf = "[0:v]null"
    font = font_bul()
    if baslik and font:
        vf = (f"[0:v]drawtext=fontfile={font}:text='{drawtext_kacis(baslik)}':"
              f"fontsize=78:fontcolor=white:borderw=6:bordercolor=black@0.85:"
              f"x=(w-text_w)/2:y=h*0.12:enable='lt(t,3.5)':"
              f"alpha='if(lt(t,3),1,max(0,(3.5-t)/0.5))'")
    vf += f",fade=t=out:st={hedef - 0.6:.3f}:d=0.6[v]"

    if muzik:
        af = (f"[0:a]volume=0.35[oyun];[1:a]volume=0.9,"
              f"afade=t=out:st={hedef - 1.5:.3f}:d=1.5[muz];"
              f"[oyun][muz]amix=inputs=2:duration=first:normalize=0,"
              f"loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        af = (f"[0:a]afade=t=out:st={hedef - 1:.3f}:d=1,"
              f"loudnorm=I=-14:TP=-1.5:LRA=11[a]")

    cmd += ["-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", "-t", f"{hedef:.3f}", str(cikti)]
    calistir(cmd)


def main():
    p = argparse.ArgumentParser(description="Kliplerden otomatik dikey reels yapar.")
    p.add_argument("klasor", type=Path, help="Kliplerin oldugu klasor")
    p.add_argument("-o", "--cikti", type=Path, default=Path("reels.mp4"))
    p.add_argument("--sure", type=float, default=60.0, help="Reels suresi (sn)")
    p.add_argument("--kesit", type=float, default=3.0, help="Her kesitin suresi (sn)")
    p.add_argument("--mod", choices=["crop", "blur"], default="crop",
                   help="crop: ortadan kirp, blur: tum goruntu + bulanik arka plan")
    p.add_argument("--muzik", type=Path, help="Arka plan muzigi (mp3/wav/m4a)")
    p.add_argument("--baslik", help="Ilk 3 saniyede gorunecek baslik")
    a = p.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("ffmpeg/ffprobe bulunamadi.")
    klipler = sorted(f for f in a.klasor.iterdir()
                     if f.suffix.lower() in VIDEO_UZANTILARI)
    if not klipler:
        sys.exit(f"{a.klasor} icinde video bulunamadi.")

    print(f"{len(klipler)} klip bulundu, analiz ediliyor...")
    analizler = analiz_et(klipler)
    if not analizler:
        sys.exit("Kullanilabilir klip yok (hepsi 1 saniyeden kisa).")

    secim = kesit_sec(analizler, a.sure, a.kesit)
    if not secim:
        sys.exit("Klipler cok kisa; --kesit degerini dusurmeyi dene.")

    # Kesit surelerini toplam tam hedef olacak sekilde ayarla.
    sureler = [a.kesit] * len(secim)
    toplam = sum(sureler)
    if toplam > a.sure:
        sureler[-1] -= toplam - a.sure
    hedef = min(a.sure, sum(sureler))
    if hedef < a.sure:
        print(f"Uyari: yeterli goruntu yok, reels {hedef:.1f} sn olacak.")

    print(f"{len(secim)} kesit seciliyor, render ediliyor ({a.mod})...")
    with tempfile.TemporaryDirectory() as td:
        gecici = Path(td)
        parcalar = []
        for i, ((ki, bas), sure) in enumerate(zip(secim, sureler)):
            k = analizler[ki]
            parca = gecici / f"p{i:03d}.mp4"
            print(f"  [{i + 1}/{len(secim)}] {k['yol'].name} @ {bas:.1f} sn")
            kesit_render(k["yol"], k["ses"], bas, sure, a.mod, parca)
            parcalar.append(parca)
        print("Birlestiriliyor...")
        birlestir(parcalar, a.cikti, hedef, a.muzik, a.baslik, gecici)

    print(f"Hazir: {a.cikti} ({hedef:.1f} sn, {W}x{H})")


if __name__ == "__main__":
    main()
