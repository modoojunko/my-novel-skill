# install.ps1 - Install my-novel skill for WorkBuddy (Windows)
param(
    [ValidateSet("workbuddy", "claude", "openclaw")]
    [string]$Platform = "workbuddy"
)

$ErrorActionPreference = "Stop"
$SkillName = "my-novel"

switch ($Platform) {
    "workbuddy" {
        $DestDir = Join-Path $env:USERPROFILE ".workbuddy\skills\$SkillName"
    }
    "claude" {
        $DestDir = Join-Path $env:USERPROFILE ".claude\skills\$SkillName"
    }
    "openclaw" {
        $DestDir = Join-Path $env:USERPROFILE ".openclaw\skills\$SkillName"
    }
}

$SrcDir = $PSScriptRoot

if (-not (Test-Path "$SrcDir\SKILL.md")) {
    Write-Error "SKILL.md not found in $SrcDir"
    exit 1
}

# Clean destination if exists
if (Test-Path $DestDir) {
    Remove-Item -Recurse -Force $DestDir
}

# Copy core files only
New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
Copy-Item "$SrcDir\SKILL.md" "$DestDir\"
Copy-Item "$SrcDir\story.py" "$DestDir\"
Copy-Item "$SrcDir\src" "$DestDir\src" -Recurse

Write-Host "Installed $SkillName to $DestDir"
Write-Host "Files: SKILL.md, story.py, src/"
