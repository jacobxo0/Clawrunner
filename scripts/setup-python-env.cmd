@echo off
rem OpenClaw — Opret/opdater Python venv (projekt ELLER workspace-roden).
rem Standard: brug fælles miljø i OpenClaw-roden. Angiv projektsti som argument for projekt-venv.

setlocal
set "OPENCLAW=%~dp0.."
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%OPENCLAW%"

echo [setup-python-env] Mål: %TARGET%
cd /d "%TARGET%"

if not exist "requirements.txt" (
  if "%TARGET%"=="%OPENCLAW%" (
    echo Ingen requirements.txt i OpenClaw-roden. Kopier fra workspace\projects\nft-arbitrage eller brug install-deps-batched.ps1.
  ) else (
    echo Ingen requirements.txt i %TARGET% — opretter kun venv.
  )
)

if not exist ".venv" (
  echo Opretter .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo FEJL: Kunne ikke oprette venv. Tjek at Python er installeret og i PATH.
    exit /b 1
  )
) else (
  echo .venv findes allerede.
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
if exist "requirements.txt" (
  echo Installerer afhængigheder fra requirements.txt ...
  pip install -r requirements.txt
  if errorlevel 1 exit /b 1
)
echo Ferdig. Aktiver venv med:  .venv\Scripts\activate
endlocal
