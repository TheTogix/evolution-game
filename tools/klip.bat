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

rem ---------- Python (Store yonlendirmesini atla, gercek Python'u bul) ----------
call :PYBUL
if not defined PY (
    echo Python kuruluyor, biraz bekle...
    winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements
    call :PYBUL
)
if not defined PY (
    echo.
    echo HATA: Python kurulamadi. Bu pencereyi kapat, klip.bat'i tekrar ac.
    echo Yine olmazsa bu pencerenin ekran goruntusunu at.
    pause
    exit /b
)
echo Python: %PY%

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
echo Kayitli yayin linki ya da kanal linki yapistirabilirsin.
echo Kanal linki verirsen o kanalin EN SON yayini kullanilir.
set "LINK="
set /p "LINK=Linki yapistir (sag tik) ve Enter'a bas: "
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
echo "%LINK%" | findstr /i "/videos/" >nul
if errorlevel 1 (
    echo.
    echo Bu bir KANAL linki. Twitch'te kanalin "Videolar" sekmesinden
    echo bir yayin ac ve onun linkini yapistir.
    echo Ornek: https://www.twitch.tv/videos/2345678901
    pause
    exit /b
)
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
echo Kick araclari hazirlaniyor (ilk seferde biraz surer)...
%PY% -m pip install -q -U "yt-dlp[default,curl-cffi]" curl_cffi
echo "%LINK%" | findstr /i "/videos/" >nul
if errorlevel 1 (
    echo Kanalin en son yayini araniyor...
    set "BULUNAN="
    for /f "delims=" %%L in ('call %PY% kick_sohbet.py "%LINK%" --son-video') do set "BULUNAN=%%L"
    call :SONLINK
    if not defined LINK2 goto HATA_KANAL
)
echo Yayin: %LINK%
echo.
echo [1/3] Yayin indiriliyor (uzun surebilir, pencereyi kapatma)...
%PY% -m yt_dlp --impersonate chrome -f "bv*+ba/b" --merge-output-format mp4 -o "%VIDEO%" "%LINK%"
if not exist "%VIDEO%" goto HATA_VIDEO
echo.
echo [2/3] Sohbet indiriliyor...
%PY% kick_sohbet.py "%LINK%" -o "%SOHBET%"
if not exist "%SOHBET%" goto HATA_SOHBET
goto KES

rem ================= KES =================
:KES
echo.
echo [3/3] Klipler kesiliyor...
%PY% sohbet_klip.py "%VIDEO%" "%SOHBET%" -o "%CIKTI%"
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

rem ================= YARDIMCILAR =================
:PYBUL
set "PY="
py -3 -c "import sys" >nul 2>&1 && (set "PY=py -3" & exit /b)
python -c "import sys" >nul 2>&1 && (set "PY=python" & exit /b)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%~fD\python.exe" set "PY="%%~fD\python.exe""
if defined PY exit /b
for /d %%D in ("%ProgramFiles%\Python3*") do if exist "%%~fD\python.exe" set "PY="%%~fD\python.exe""
exit /b

:SONLINK
set "LINK2="
if defined BULUNAN (
    set "LINK=%BULUNAN%"
    set "LINK2=1"
)
exit /b

:HATA_KANAL
echo.
echo Kanalin son yayini bulunamadi. Kick'te kanalin "Videolar" sekmesinden
echo bir yayin ac ve onun linkini yapistir.
echo Ornek: https://kick.com/rraenee/videos/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
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
