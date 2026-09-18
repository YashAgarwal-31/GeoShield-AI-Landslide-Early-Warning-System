param(
  [string]$OutputDirectory = "runtime/python"
)

$ErrorActionPreference = "Stop"

$pythonVersion = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if (-not $pythonVersion) {
  throw "Unable to determine Python version."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$outputPath = Join-Path $repoRoot $OutputDirectory
$tempRoot = Join-Path $env:TEMP ("geoshield-python-" + [guid]::NewGuid().ToString("N"))
$embedZip = Join-Path $tempRoot "python-embed.zip"
$getPip = Join-Path $tempRoot "get-pip.py"
$embedUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"

Write-Host "[GeoShield] Preparing self-contained Python $pythonVersion runtime..."
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
if (Test-Path $outputPath) {
  Remove-Item -Recurse -Force $outputPath
}
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null

Invoke-WebRequest -Uri $embedUrl -OutFile $embedZip
Expand-Archive -Path $embedZip -DestinationPath $outputPath -Force

$pth = Get-ChildItem -Path $outputPath -Filter "python*._pth" | Select-Object -First 1
if (-not $pth) {
  throw "Embedded Python path configuration was not found."
}
$pthContent = Get-Content $pth.FullName
$pthContent = $pthContent -replace '^#import site$', 'import site'
Set-Content -Path $pth.FullName -Value $pthContent -Encoding ascii

Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip
$pythonExe = Join-Path $outputPath "python.exe"
& $pythonExe $getPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw "pip bootstrap failed." }

$requirements = Join-Path $repoRoot "backend/requirements.txt"
& $pythonExe -m pip install --no-warn-script-location --disable-pip-version-check -r $requirements
if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed." }

& $pythonExe -m pip check
if ($LASTEXITCODE -ne 0) { throw "Bundled Python dependency validation failed." }

& $pythonExe -c "import fastapi, uvicorn, sqlalchemy, sklearn, xgboost, psycopg; print('GeoShield bundled Python runtime OK')"
if ($LASTEXITCODE -ne 0) { throw "Bundled runtime import verification failed." }

Remove-Item -Recurse -Force $tempRoot
Write-Host "[GeoShield] Self-contained Python runtime ready at $outputPath"
