# install.ps1 - Install my-novel-v2 skill (Windows)

param(
    [ValidateSet("workbuddy", "claude", "openclaw", "hermes")]
    [string]$Platform = "workbuddy"
)

$SkillName = "my-novel-v2"
$ScriptDir = $PSScriptRoot

switch ($Platform) {
    "workbuddy" {
        $Dest = Join-Path $env:USERPROFILE ".workbuddy\skills\$SkillName"
    }
    "claude" {
        $Dest = Join-Path $env:USERPROFILE ".claude\skills\$SkillName"
    }
    "openclaw" {
        $Dest = Join-Path $env:USERPROFILE ".openclaw\skills\$SkillName"
    }
    "hermes" {
        $Dest = Join-Path $env:USERPROFILE ".hermes\skills\$SkillName"
    }
}

$SkillPath = Join-Path $ScriptDir "SKILL.md"
if (-not (Test-Path $SkillPath)) {
    Write-Error "Error: SKILL.md not found in $ScriptDir"
    exit 1
}

if (Test-Path $Dest) {
    Remove-Item -Path $Dest -Recurse -Force
}

New-Item -ItemType Directory -Path $Dest -Force | Out-Null

Copy-Item (Join-Path $ScriptDir "SKILL.md") -Destination $Dest
Copy-Item (Join-Path $ScriptDir "README.md") -Destination $Dest -ErrorAction SilentlyContinue
Copy-Item (Join-Path $ScriptDir "install.md") -Destination $Dest -ErrorAction SilentlyContinue
Copy-Item (Join-Path $ScriptDir "story.py") -Destination $Dest
Copy-Item (Join-Path $ScriptDir "src_v2") -Destination (Join-Path $Dest "src_v2") -Recurse
if (Test-Path (Join-Path $ScriptDir "docs")) {
    Copy-Item (Join-Path $ScriptDir "docs") -Destination $Dest -Recurse -ErrorAction SilentlyContinue
}

Write-Host "Installed $SkillName to $Dest"
Write-Host "Files: SKILL.md, README.md, install.md, story.py, src_v2/, docs/"

# Hermes专用：创建wrapper脚本，让story命令可用
if ($Platform -eq "hermes") {
    $BinDir = Join-Path $env:USERPROFILE ".local\bin"
    if (-not (Test-Path $BinDir)) {
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    }
    
    $WrapperBat = Join-Path $BinDir "story.bat"
    $WrapperContent = @"
@echo off
REM story.bat - Wrapper for my-novel-skill story.py
set "SKILL_DIR=%USERPROFILE%\.hermes\skills\my-novel-v2"
if exist "%SKILL_DIR%\story.py" (
    REM Try python3 first, then python
    where python3 >nul 2>nul
    if %errorlevel% equ 0 (
        python3 "%SKILL_DIR%\story.py" %*
    ) else (
        python "%SKILL_DIR%\story.py" %*
    )
) else (
    echo Error: my-novel-skill not found at %SKILL_DIR%
    echo Please run install.ps1 hermes first
    exit /b 1
)
"@
    $WrapperContent | Out-File -FilePath $WrapperBat -Encoding ASCII
    
    Write-Host ""
    Write-Host "✅ Hermes installation complete!"
    Write-Host "   - Wrapper script created at: $WrapperBat"
    Write-Host "   - You can now use 'story' command directly!"
    Write-Host ""
    Write-Host "   If 'story' command is not found, add this to your PATH environment variable:"
    Write-Host "   $BinDir"
}
