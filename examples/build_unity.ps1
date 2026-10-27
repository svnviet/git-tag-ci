param(
    [Parameter(Mandatory)][string]$BuildVersion,
    [Parameter(Mandatory)][string]$OutputDir,
    [string]$ReleaseNotes
)

$unity   = "C:\Program Files\Unity\Hub\Editor\6000.0.xxf1\Editor\Unity.exe"
$project = "D:\Work\MeterProject"   # must match the service WORK_DIR (where tags are checked out)
$log     = "$project\Builds\CI_Release\build.log"

$unityArgs = @(
    "-batchmode", "-nographics", "-quit",
    "-projectPath", "`"$project`"",
    "-executeMethod", "Meter.Editor.CI.ReleaseBuildRunner.BuildWindowsRelease",
    "-buildProfile", "`"Assets/Settings/Build Profiles/Windows Release.asset`"",
    "-buildVersion", $BuildVersion,
    "-buildOutput", "`"$OutputDir\Application.exe`"",
    "-logFile", "`"$log`""
)

$p = Start-Process -FilePath $unity -ArgumentList $unityArgs -Wait -PassThru -NoNewWindow
Write-Host "Unity exit code: $($p.ExitCode)"
if ($p.ExitCode -eq 0 -and $ReleaseNotes -and (Test-Path $ReleaseNotes)) {
    Copy-Item $ReleaseNotes $OutputDir -Force -ErrorAction SilentlyContinue   # make sure the notes sit next to the build
}
if ($p.ExitCode -ne 0) { Get-Content $log -Tail 50; exit $p.ExitCode }
