# install.ps1 - Install my-novel-v2 skill (Windows)

param(
    [ValidateSet("workbuddy", "claude", "openclaw")]
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
Copy-Item (Join-Path $ScriptDir "src_v2") -Destination (Join-Path $Dest "src") -Recurse
if (Test-Path (Join-Path $ScriptDir "docs")) {
    Copy-Item (Join-Path $ScriptDir "docs") -Destination $Dest -Recurse -ErrorAction SilentlyContinue
}

Write-Host "Installed $SkillName to $Dest"
Write-Host "Files: SKILL.md, README.md, install.md, story.py, src/, docs/"
