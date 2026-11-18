#!/usr/bin/env python3
"""kick_canli.py - Kick canli yayinindan surekli klip cikarir.

- Yayini baslar baslamaz kaydetmeye baslar (eski parcalari silerek diski korur).
- Sohbeti YAYININ BASINDAN itibaren ceker: sen acmadan onceki saatlerdeki
  patlamalari da bulur. Onlarin goruntusunu Kick'in yayin kaydindan sadece
  o bolumu indirerek alir (kayit hazir degilse yayin bitince alir).
- Canli kisimda sohbet patladigi an klibi keser.
- Yayin bitince (ya da Ctrl+C ile durdurunca) kalanlari tamamlar.

Kullanim:
    python kick_canli.py https://kick.com/KANAL
    python kick_canli.py KANAL --once 25 --uzunluk 40 --kat 3

Gereksinim: ffmpeg, yt-dlp (pip install "yt-dlp[default,curl-cffi]"),
ayni klasorde kick_sohbet.py ve sohbet_klip.py.
"""

import argparse
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kick_sohbet as ks  # noqa: E402
import sohbet_klip as sk  # noqa: E402


def simdi():
    return datetime.now(timezone.utc)


def log(*a):
    print(f"[{datetime.now():%H:%M:%S}]", *a, flush=True)


def guvenli(url):
    try:
        return ks.getir(url)
    except SystemExit as e:
        log(f"uyari: {e}")
        return None


def kanal_adi(link):
    link = link.strip()
    if "kick.com" not in link and "/" not in link:
        return link
    yol = urllib.parse.urlparse(link if "//" in link else "https://" + link).path
    parcalar = [p for p in yol.split("/") if p]
    if not parcalar:
        sys.exit("Linkte kanal adi yok. Ornek: https://kick.com/kanaladi")
    return parcalar[0]


def yayin_durumu(slug):
    k = guvenli(f"https://kick.com/api/v2/channels/{slug}")
    if not k:
        return None, None
    ls = k.get("livestream")
    if ls and ls.get("is_live", True):
        return k, ls
    return k, None


def ytdlp_url(slug):
    r = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--impersonate", "chrome", "-q",
         "--no-warnings", "-f", "best", "-g", f"https://kick.com/{slug}"],
        capture_output=True, text=True)
    satirlar = r.stdout.strip().splitlines()
    return satirlar[0] if satirlar else None


# ---------------------------------------------------------------- kayit

class Kayit:
    """Canli yayini 20 sn'lik parcalar halinde kaydeder."""

    def __init__(self, klasor):
        self.klasor = klasor
        self.oturumlar = []
        self.proc = None

    def baslat(self, url):
        d = self.klasor / f"oturum{len(self.oturumlar)}"
        d.mkdir(parents=True, exist_ok=True)
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-i", url, "-c", "copy", "-f", "segment", "-segment_time", "20",
               "-segment_list", str(d / "liste.csv"), "-segment_list_type", "csv",
               "-reset_timestamps", "1", str(d / "p%05d.ts")]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL)
        self.oturumlar.append({"dir": d, "bas": time.time()})

    def calisiyor(self):
        return self.proc is not None and self.proc.poll() is None

    def durdur(self):
        if self.calisiyor():
            self.proc.terminate()
            try:
                self.proc.wait(15)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    @staticmethod
    def parcalar(o):
        liste = o["dir"] / "liste.csv"
        if not liste.exists():
            return []
        out = []
        for satir in liste.read_text(errors="ignore").splitlines():
            p = satir.split(",")
            if len(p) >= 3:
                try:
                    out.append((o["dir"] / p[0], float(p[1]), float(p[2])))
                except ValueError:
                    pass
        # -reset_timestamps ile her parca 0'dan baslar; sureleri topla.
        sonuc, t = [], 0.0
        for dosya, s, e in out:
            sure = e - s
            sonuc.append((dosya, t, t + sure))
            t += sure
        return sonuc

    def kes(self, a, b, gecici):
        """Duvar saati [a,b] araligini kayittan cikarir -> (dosya, ofset)"""
        for o in reversed(self.oturumlar):
            secilen = [(f, s, e) for f, s, e in self.parcalar(o)
                       if o["bas"] + e > a and o["bas"] + s < b]
            if not secilen or not all(f.exists() for f, _, _ in secilen):
                continue
            if o["bas"] + secilen[0][1] > a + 3 or o["bas"] + secilen[-1][2] < b - 3:
                continue
            liste = gecici / "birlestir.txt"
            liste.write_text("".join(f"file '{f.resolve().as_posix()}'\n"
                                     for f, _, _ in secilen))
            hedef = gecici / "parca.ts"
            r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                                "-f", "concat", "-safe", "0", "-i", str(liste),
                                "-c", "copy", str(hedef)], capture_output=True)
            if r.returncode == 0 and hedef.exists():
                return hedef, max(0.0, a - (o["bas"] + secilen[0][1]))
        return None

    def temizle(self, once):
        """Duvar saati 'once'den once biten parcalari siler."""
        for o in self.oturumlar:
            for f, s, e in self.parcalar(o):
                if o["bas"] + e < once and f.exists():
                    try:
                        f.unlink()
                    except OSError:
                        pass


# ---------------------------------------------------------------- sohbet

class Sohbet:
    def __init__(self, kanal_id, yayin_bas):
        self.kid = kanal_id
        self.bas = yayin_bas
        self.imlec = yayin_bas
        self.gorulen = set()
        self.mesajlar = []  # (yayin ofseti sn, metin)

    def guncelle(self, bitis=None, sinir_sn=None):
        hedef = (bitis or simdi()) - timedelta(seconds=5)
        basla = time.time()
        while self.imlec < hedef:
            iso = self.imlec.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            url = (f"https://kick.com/api/v2/channels/{self.kid}/messages?"
                   + urllib.parse.urlencode({"start_time": iso}))
            veri = guvenli(url) or {}
            for m in (veri.get("data") or {}).get("messages") or []:
                if m.get("id") in self.gorulen or not m.get("created_at"):
                    continue
                self.gorulen.add(m.get("id"))
                ofs = (ks.zaman_oku(m["created_at"]) - self.bas).total_seconds()
                if ofs >= 0:
                    self.mesajlar.append((ofs, ks.emote_temizle(m.get("content"))))
            self.imlec += timedelta(seconds=ks.ADIM)
            time.sleep(0.15)
            if sinir_sn and time.time() - basla > sinir_sn:
                break

    def geride_mi(self):
        return self.imlec < simdi() - timedelta(seconds=30)


def patlamalar(mesajlar, dilim, kesin_son, min_mesaj, kat):
    kova = defaultdict(list)
    for t, m in mesajlar:
        kova[int(t // dilim)].append(m)
    if len(kova) < 8:
        return []
    esik = max(min_mesaj, kat * statistics.median(len(v) for v in kova.values()))
    out = []
    for i, v in sorted(kova.items()):
        n = len(v)
        if (i + 1) * dilim > kesin_son or n < esik:
            continue
        if n < len(kova.get(i - 1, [])) or n < len(kova.get(i + 1, [])):
            continue  # komsu dilim daha yogun: asil zirve orada
        out.append((i * dilim, n, v))
    return out


# ---------------------------------------------------------------- vod

def vod_bul(slug, ls_id, yayin_bas):
    veri = guvenli(f"https://kick.com/api/v2/channels/{slug}/videos")
    if isinstance(veri, dict):
        veri = veri.get("data") or veri.get("videos") or []
    for v in veri or []:
        uuid = (v.get("video") or {}).get("uuid") or v.get("uuid")
        if not uuid:
            continue
        tarih = v.get("start_time") or v.get("created_at")
        ayni = ls_id and v.get("id") == ls_id
        if not ayni and tarih:
            try:
                ayni = abs((ks.zaman_oku(tarih) - yayin_bas).total_seconds()) < 900
            except ValueError:
                ayni = False
        if ayni:
            return f"https://kick.com/{slug}/videos/{uuid}"
    return None


def vod_parca(link, a, b, gecici):
    hedef = gecici / "vod_parca.mp4"
    if hedef.exists():
        hedef.unlink()
    subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--impersonate", "chrome", "-q",
         "--no-warnings", "-f", "bv*+ba/b", "--download-sections",
         f"*{int(a)}-{int(b) + 1}", "--merge-output-format", "mp4",
         "-o", str(hedef), link],
        capture_output=True, text=True)
    return hedef if hedef.exists() and hedef.stat().st_size > 0 else None


# ---------------------------------------------------------------- ana

class Klipci:
    def __init__(self, a, slug, cikti):
        self.a = a
        self.slug = slug
        self.cikti = cikti
        self.font = sk.font_bul()
        self.yapilan, self.bekleyen = [], []
        self.vod = None
        self.son_vod_deneme = 0.0

    def cakisir(self, bas, bit):
        return any(bas < k["bit"] and k["bas"] < bit
                   for k in self.yapilan + self.bekleyen)

    def render(self, src, bas, bit, k):
        sira = len(self.yapilan) + 1
        ad = f"klip_{sira:02d}_{sk.dosya_adi(k['soz'])}.mp4"
        with tempfile.TemporaryDirectory() as td:
            yazi = None
            if self.font and k["soz"]:
                yazi = Path(td) / "yazi.txt"
                yazi.write_text(sk.baslik_yap(k["soz"]), encoding="utf-8")
            sk.klip_kes(src, sk.ses_var_mi(src), {"bas": bas, "bit": bit},
                        self.a.mod, yazi, self.font, self.cikti / ad)
        k["dosya"] = ad
        self.yapilan.append(k)
        self.ozet_yaz()
        log(f"KLIP HAZIR: {ad}  (yayinin {sk.zaman(k['patlama'])} ani, "
            f"{k['mesaj']} mesaj, \"{k['soz']}\")")

    def isle(self, k, kayit, yayin_bas, vod_dene=True):
        sure = k["bit"] - k["bas"]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a = (yayin_bas + timedelta(seconds=k["bas"])).timestamp()
            b = a + sure
            yerel = kayit.kes(a, b, td) if kayit else None
            try:
                if yerel:
                    src, ofs = yerel
                    self.render(src, ofs, ofs + sure, k)
                    return True
                if not vod_dene:
                    return False
                if not self.vod and time.time() - self.son_vod_deneme > 240:
                    self.son_vod_deneme = time.time()
                    self.vod = vod_bul(self.slug, self.ls_id, yayin_bas)
                    if self.vod:
                        log(f"Yayin kaydi bulundu: {self.vod}")
                if self.vod:
                    parca = vod_parca(self.vod, k["bas"], k["bit"], td)
                    if parca:
                        self.render(parca, 0, sure, k)
                        return True
            except RuntimeError as e:
                log(f"uyari: klip kesilemedi: {e}")
        return False

    def ozet_yaz(self):
        satirlar = ["sira,dosya,yayin_ani,mesaj,soz,durum"]
        for i, k in enumerate(self.yapilan, 1):
            soz = k["soz"].replace('"', "'")
            satirlar.append(f'{i},{k["dosya"]},{sk.zaman(k["patlama"])},'
                            f'{k["mesaj"]},"{soz}",hazir')
        for k in self.bekleyen:
            soz = k["soz"].replace('"', "'")
            satirlar.append(f',,{sk.zaman(k["patlama"])},{k["mesaj"]},"{soz}",'
                            f'yayin kaydi bekleniyor')
        (self.cikti / "ozet.csv").write_text("\n".join(satirlar) + "\n",
                                             encoding="utf-8")

    def tara(self, sohbet, kayit, yayin_bas, canli_son, son=False):
        """Yeni patlamalari bul ve kes. canli_son: elde goruntu olan son ofset."""
        kesin = (sohbet.imlec - yayin_bas).total_seconds()
        for p, n, msgs in patlamalar(sohbet.mesajlar, self.a.dilim, kesin,
                                     self.a.min_mesaj, self.a.kat):
            bas = max(0.0, p - self.a.once)
            bit = bas + self.a.uzunluk
            if bit > canli_son:
                if not son:
                    continue  # henuz yeterli goruntu yok, sonraki turda
                bit = canli_son  # yayin bitti: sona kadar al
                if bit - bas < 15:
                    continue
            if self.cakisir(bas, bit):
                continue
            soz, soz_adet = sk.en_cok_soz(msgs)
            k = {"patlama": p, "bas": bas, "bit": bit, "mesaj": n, "soz": soz}
            log(f"Patlama: yayinin {sk.zaman(p)} ani, {n} mesaj, \"{soz}\"")
            if not self.isle(k, kayit, yayin_bas):
                self.bekleyen.append(k)
                self.ozet_yaz()
                log("  -> goruntu henuz yok, yayin kaydi gelince kesilecek")

    def bekleyenleri_dene(self, yayin_bas):
        kalan = []
        for k in self.bekleyen:
            if not self.isle(k, None, yayin_bas):
                kalan.append(k)
        if len(kalan) != len(self.bekleyen):
            self.bekleyen = kalan
            self.ozet_yaz()


def main():
    p = argparse.ArgumentParser(description="Kick canli yayinindan surekli klip cikarir.")
    p.add_argument("kanal", help="Kanal linki ya da adi (orn. https://kick.com/kanal)")
    p.add_argument("--once", type=float, default=25, help="Patlamadan kac sn once (25)")
    p.add_argument("--uzunluk", type=float, default=40, help="Klip suresi sn (40)")
    p.add_argument("--dilim", type=float, default=15, help="Sohbet dilimi sn (15)")
    p.add_argument("--kat", type=float, default=3.0,
                   help="Ortalamanin kac kati mesaj patlama sayilsin (3)")
    p.add_argument("--min-mesaj", type=int, default=10,
                   help="Bir dilimde en az kac mesaj olsun (10)")
    p.add_argument("--mod", choices=["crop", "blur"], default="crop")
    p.add_argument("--vod-bekle", type=float, default=20,
                   help="Yayin bitince kaydi kac dk beklesin (20)")
    p.add_argument("-o", "--cikti", type=Path, default=Path("klipler"))
    a = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg bulunamadi.")
    slug = kanal_adi(a.kanal)

    k, ls = yayin_durumu(slug)
    while not ls:
        if k is None:
            log("Kanal bilgisi alinamadi, 60 sn sonra tekrar denenecek...")
        else:
            log(f"{slug} su an yayinda degil. Yayin baslayinca otomatik basliyorum...")
        time.sleep(60)
        k, ls = yayin_durumu(slug)

    yayin_bas = ks.zaman_oku(ls.get("start_time") or ls.get("created_at"))
    cikti = a.cikti / f"{slug}_{yayin_bas.astimezone():%Y%m%d_%H%M}"
    cikti.mkdir(parents=True, exist_ok=True)
    gecen = simdi() - yayin_bas
    log(f"{slug} YAYINDA: \"{ls.get('session_title', '')}\"")
    log(f"Yayin {int(gecen.total_seconds() // 3600)} saat "
        f"{int(gecen.total_seconds() % 3600 // 60)} dk once basladi.")
    log(f"Klipler buraya: {cikti.resolve()}")
    log("Durdurmak icin Ctrl+C. (Durdurunca kalanlari tamamlar.)")

    kayit = Kayit(cikti / "_kayit")
    url = k.get("playback_url") or ytdlp_url(slug)
    if url:
        kayit.baslat(url)
        log("Canli kayit basladi.")
    else:
        log("uyari: canli goruntu adresi alinamadi; sadece yayin kaydindan kesilecek.")

    sohbet = Sohbet(k.get("id"), yayin_bas)
    klipci = Klipci(a, slug, cikti)
    klipci.ls_id = ls.get("id")
    son_durum = time.time()
    durduruldu = False
    log("Gecmis sohbet taraniyor (yayinin basindan itibaren)...")

    try:
        while True:
            dongu = time.time()
            sohbet.guncelle(sinir_sn=45)
            canli_son = (simdi() - yayin_bas).total_seconds() - 15
            klipci.tara(sohbet, kayit, yayin_bas, canli_son)
            if sohbet.geride_mi():
                ilerleme = (sohbet.imlec - yayin_bas) / (simdi() - yayin_bas)
                log(f"Gecmis taraniyor: %{int(100 * ilerleme)}  "
                    f"({len(sohbet.mesajlar)} mesaj, {len(klipci.yapilan)} klip)")
            else:
                klipci.bekleyenleri_dene(yayin_bas)

            # Gelecekteki klipler icin gereken parcalari koru, eskileri sil.
            kesin = (sohbet.imlec - yayin_bas).total_seconds()
            sakla = kesin - a.dilim - a.once - 90
            kayit.temizle((yayin_bas + timedelta(seconds=sakla)).timestamp())

            if time.time() - son_durum > 60:
                son_durum = time.time()
                k2, ls2 = yayin_durumu(slug)
                if k2 is not None and not ls2:
                    log("Yayin bitti.")
                    break
                if ls2 and not kayit.calisiyor():
                    url = (k2 or {}).get("playback_url") or ytdlp_url(slug)
                    if url:
                        log("Kayit koptu, yeniden baslatiliyor...")
                        kayit.baslat(url)

            if not sohbet.geride_mi():
                time.sleep(max(0, 20 - (time.time() - dongu)))
    except KeyboardInterrupt:
        durduruldu = True
        log("Durduruldu, kalanlar tamamlaniyor... (tekrar Ctrl+C = hemen cik)")

    bitis = simdi()
    kayit.durdur()
    try:
        sohbet.guncelle(bitis=bitis)
        klipci.tara(sohbet, kayit, yayin_bas,
                    (bitis - yayin_bas).total_seconds() - 5, son=True)
        bekle_son = time.time() + (0 if durduruldu else a.vod_bekle * 60)
        klipci.bekleyenleri_dene(yayin_bas)
        while klipci.bekleyen and time.time() < bekle_son:
            log(f"{len(klipci.bekleyen)} klip yayin kaydini bekliyor...")
            time.sleep(120)
            klipci.son_vod_deneme = 0
            klipci.bekleyenleri_dene(yayin_bas)
    except KeyboardInterrupt:
        pass

    shutil.rmtree(cikti / "_kayit", ignore_errors=True)
    klipci.ozet_yaz()
    log(f"BITTI: {len(klipci.yapilan)} klip hazir -> {cikti.resolve()}")
    if klipci.bekleyen:
        log(f"{len(klipci.bekleyen)} an icin yayin kaydi bulunamadi (ozet.csv'de). "
            f"Kayit Kick'e dusunce klip.bat'ta 'bitmis yayin' ile kesebilirsin.")


if __name__ == "__main__":
    main()
