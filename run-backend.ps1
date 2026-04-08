param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$DbPath = "",
    [string]$Workdir = "."
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

python @command
