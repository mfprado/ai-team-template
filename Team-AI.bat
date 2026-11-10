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
if errorlevel 1 goto finish_error

rem GitHub's tool: lets the assistant send change requests to the AI Champion.
set "PATH=%ProgramFiles%\GitHub CLI;%PATH%"
where gh >nul 2>nul
if errorlevel 1 (
  echo Your computer needs GitHub's tool to send changes to your AI Champion for approval.
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

rem The team page: opens in the browser. Keep this window open while you use it.
set PORT=8501
start "" /b cmd /c "timeout /t 8 /nobreak >nul & start http://127.0.0.1:%PORT%"
echo The team page will open in your browser. Close this window when you are done.
uv run --quiet --no-project --python 3.12 --with streamlit==1.41.1 streamlit run .agents\core\facade\app.py --server.headless true --server.port %PORT% --server.address 127.0.0.1 --browser.gatherUsageStats false --client.toolbarMode viewer
exit /b 0

:finish_error
echo.
pause
exit /b 1
