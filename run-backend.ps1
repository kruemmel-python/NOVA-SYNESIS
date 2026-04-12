param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$DbPath = "",
    [string]$Workdir = ".",
    [string]$LitModel = "",
    [string]$LitBinary = "",
    [string]$LitBackend = ""
)

$env:PYTHONPATH = "src"

$command = @(
    "-m", "nova_synesis.cli",
    "run-api",
    "--host", $BindHost,
    "--port", $Port,
    "--workdir", $Workdir
)

if ($DbPath -ne "") {
    $command += @("--db-path", $DbPath)
}

if ($LitModel -ne "") {
    $command += @("--lit-model", $LitModel)
}

if ($LitBinary -ne "") {
    $command += @("--lit-binary", $LitBinary)
}

if ($LitBackend -ne "") {
    $command += @("--lit-backend", $LitBackend)
}

python @command
