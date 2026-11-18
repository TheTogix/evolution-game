@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title Klip Makinesi

set "REPO=https://raw.githubusercontent.com/TheTogix/evolution-game/claude/gta6-klip-gonderme-34is6s/tools"

echo ============================================
echo    KLIP MAKINESI  (Twitch + Kick)
echo ============================================
echo.

rem ---------- Python ----------
where python >nul 2>&1
if errorlevel 1 (
    echo Python kuruluyor...
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    echo.
    echo Python kuruldu. Bu pencereyi KAPAT ve klip.bat'i TEKRAR AC.
    pause
    exit /b
)

rem ---------- ffmpeg ----------
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ffmpeg kuruluyor...
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    echo.
    echo ffmpeg kuruldu. Bu pencereyi KAPAT ve klip.bat'i TEKRAR AC.
    pause
    exit /b
)

rem ---------- Araclar (her seferinde guncel surum) ----------
echo Araclar guncelleniyor...
curl -s -f -o sohbet_klip.py "%REPO%/sohbet_klip.py"
curl -s -f -o kick_sohbet.py "%REPO%/kick_sohbet.py"
curl -s -f -o reels.py "%REPO%/reels.py"
if not exist sohbet_klip.py (
    echo HATA: sohbet_klip.py indirilemedi. Internet baglantini kontrol et.
    pause
    exit /b
)

echo.
set "LINK="
set /p "LINK=Yayin linkini yapistir (sag tik) ve Enter'a bas: "
if not defined LINK (
    echo Link girmedin.
    pause
    exit /b
)

for /f %%i in ('powershell -nop -c "Get-Date -f yyyyMMdd_HHmm"') do set "ZAMAN=%%i"
set "VIDEO=yayin_%ZAMAN%.mp4"
set "SOHBET=sohbet_%ZAMAN%.json"
set "CIKTI=klipler\%ZAMAN%"

echo "%LINK%" | findstr /i "kick.com" >nul && goto KICK
echo "%LINK%" | findstr /i "twitch.tv" >nul && goto TWITCH
echo Bu link Twitch ya da Kick linki degil.
pause
exit /b

rem ================= TWITCH =================
:TWITCH
if not exist TwitchDownloaderCLI.exe (
    echo TwitchDownloaderCLI indiriliyor...
    powershell -nop -c "$r=Invoke-RestMethod https://api.github.com/repos/lay295/TwitchDownloader/releases/latest; $a=$r.assets | ? { $_.name -match 'CLI.*Windows-x64\.zip' } | select -First 1; Invoke-WebRequest $a.browser_download_url -OutFile tdcli.zip; Expand-Archive tdcli.zip -DestinationPath tdcli -Force; Copy-Item (Get-ChildItem tdcli -Recurse -Filter TwitchDownloaderCLI.exe | select -First 1).FullName .; Remove-Item tdcli,tdcli.zip -Recurse -Force"
)
if not exist TwitchDownloaderCLI.exe (
    echo HATA: TwitchDownloaderCLI indirilemedi.
    pause
    exit /b
)
echo.
echo [1/3] Yayin indiriliyor (uzun surebilir, pencereyi kapatma)...
TwitchDownloaderCLI.exe videodownload --id "%LINK%" -o "%VIDEO%"
if not exist "%VIDEO%" goto HATA_VIDEO
echo.
echo [2/3] Sohbet indiriliyor...
TwitchDownloaderCLI.exe chatdownload --id "%LINK%" -o "%SOHBET%"
if not exist "%SOHBET%" goto HATA_SOHBET
goto KES

rem ================= KICK =================
:KICK
echo Kick araclari hazirlaniyor...
python -m pip install -q -U "yt-dlp[default,curl-cffi]" curl_cffi
echo.
echo [1/3] Yayin indiriliyor (uzun surebilir, pencereyi kapatma)...
python -m yt_dlp --impersonate chrome -f "bv*+ba/b" --merge-output-format mp4 -o "%VIDEO%" "%LINK%"
if not exist "%VIDEO%" goto HATA_VIDEO
echo.
echo [2/3] Sohbet indiriliyor...
python kick_sohbet.py "%LINK%" -o "%SOHBET%"
if not exist "%SOHBET%" goto HATA_SOHBET
goto KES

rem ================= KES =================
:KES
echo.
echo [3/3] Klipler kesiliyor...
python sohbet_klip.py "%VIDEO%" "%SOHBET%" -o "%CIKTI%"
if errorlevel 1 (
    echo HATA: Klipler kesilemedi. Bu pencerenin ekran goruntusunu at.
    pause
    exit /b
)
echo.
echo ============================================
echo  BITTI! Klipler: %CIKTI%
echo ============================================
start "" "%CIKTI%"
pause
exit /b

:HATA_VIDEO
echo.
echo HATA: Yayin indirilemedi. Bu pencerenin ekran goruntusunu at.
pause
exit /b

:HATA_SOHBET
echo.
echo HATA: Sohbet indirilemedi. Bu pencerenin ekran goruntusunu at.
pause
exit /b
