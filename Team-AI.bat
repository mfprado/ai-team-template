@echo off
rem Team launcher for Windows: double-click to open the team folder.
rem Installs what is needed the first time, then prepares this computer.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
rem Main steps and installer output also go to .git\launch.log (hidden, never shared), so the assistant can read it
rem instead of asking the person to copy the window.
set "LOG=.git\launch.log"
echo Opening your team folder... (%date% %time%, Windows)> "%LOG%"
echo Opening your team folder...

rem Git: keeps the team folder in sync.
where git >nul 2>nul
if errorlevel 1 (
  echo Your computer needs Git to keep the team folder in sync.
  echo Git is missing.>> "%LOG%"
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
  echo Installing uv.>> "%LOG%"
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex" >> "%LOG%" 2>&1
  where uv >nul 2>nul
  if errorlevel 1 (
    echo The installation failed. Check your internet connection and try again, or ask your AI Champion.
    echo uv installation failed.>> "%LOG%"
    goto finish_error
  )
)
uv python install 3.12 --quiet >> "%LOG%" 2>&1

uv run --quiet --no-project --python 3.12 --with pillow==11.0.0 .agents\system\facade\setup.py > "%LOG%.setup" 2>&1
set SETUP_ERROR=%errorlevel%
type "%LOG%.setup"
type "%LOG%.setup" >> "%LOG%"
del "%LOG%.setup" >nul 2>nul
if not "%SETUP_ERROR%"=="0" goto finish_error
echo Setup finished.>> "%LOG%"

rem GitHub's tool: lets the assistant share changes with the team.
set "PATH=%ProgramFiles%\GitHub CLI;%PATH%"
where gh >nul 2>nul
if errorlevel 1 (
  echo Your computer needs GitHub's tool to share your changes with the team.
  set /p ANSWER2=Install it now? [y/n] 
  if /i "!ANSWER2:~0,1!"=="y" winget install --id GitHub.cli -e --source winget --accept-package-agreements --accept-source-agreements
  if /i "!ANSWER2:~0,1!"=="s" winget install --id GitHub.cli -e --source winget --accept-package-agreements --accept-source-agreements
)
where gh >nul 2>nul
if not errorlevel 1 (
  gh auth status --hostname github.com >nul 2>nul
  if errorlevel 1 (
    echo Now sign in to GitHub in the browser window that opens, one time only.
    gh auth login --hostname github.com --git-protocol https --web
  )
  gh auth setup-git --hostname github.com >nul 2>nul
)

rem The team page: opens in the browser, at this team's own address (several teams can be open).
rem Keep this window open while you use it.
echo Launcher finished.>> "%LOG%"
uv run --quiet --no-project --python 3.12 --with streamlit==1.41.1 .agents\system\facade\page.py
exit /b 0

:finish_error
echo.
pause
exit /b 1
