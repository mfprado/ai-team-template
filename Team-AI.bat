@echo off
rem Team launcher for Windows: double-click to open the team folder.
rem Installs what is needed the first time, then prepares this computer.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
echo Opening your team folder...

rem Git: keeps the team folder in sync.
where git >nul 2>nul
if errorlevel 1 (
  echo Your computer needs Git to keep the team folder in sync.
  set /p ANSWER=Install it now? [y/n] 
  if /i "!ANSWER:~0,1!"=="y" goto install_git
  if /i "!ANSWER:~0,1!"=="s" goto install_git
  goto finish_error
)
goto check_uv

:install_git
winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
echo When the installation finishes, open this file again.
goto finish_error

:check_uv
rem uv: installs and runs the right Python. Installed automatically the first time.
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo Installing the tools your team folder needs, one time only...
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul
  where uv >nul 2>nul
  if errorlevel 1 (
    echo The installation failed. Check your internet connection and try again, or ask your AI Champion.
    goto finish_error
  )
)
uv python install 3.12 --quiet >nul 2>nul

uv run --quiet --no-project --python 3.12 .agents\core\facade\setup.py
echo.
pause
exit /b 0

:finish_error
echo.
pause
exit /b 1
