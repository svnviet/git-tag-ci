param(
    [Parameter(Mandatory)][string]$BuildVersion,   # tag name, e.g. U_Master_GUI2609_1026
    [Parameter(Mandatory)][string]$OutputDir,      # OUTPUT_DIR/<tag>
    [Parameter(Mandatory)][string]$LogFile,        # Unity log, OUTPUT_DIR/<tag>/build.log
    [string]$ReleaseNotes                          # OUTPUT_DIR/<tag>/ReleaseNote.md
)

$p = Start-Process -FilePath $unity -ArgumentList $unityArgs -Wait -PassThru -NoNewWindow
Write-Host "Unity exit code: $($p.ExitCode)"
if ($p.ExitCode -ne 0) { Get-Content $LogFile -Tail 50; exit $p.ExitCode }
