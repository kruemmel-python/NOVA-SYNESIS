param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

$requiredHandlers = @(
    "accounts_receivable_extract",
    "accounts_receivable_generate_letters",
    "accounts_receivable_write_letters",
    "json_serialize",
    "write_file"
)

$handlersResponse = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/handlers"
$availableHandlers = @($handlersResponse.handlers)
$missingHandlers = @($requiredHandlers | Where-Object { $_ -notin $availableHandlers })

if ($missingHandlers.Count -gt 0) {
    throw "Der laufende Backend-Prozess kennt die neuen Rechnungs-Handler noch nicht: $($missingHandlers -join ', '). Backend bitte neu starten."
}

$outputRoot = Join-Path $PSScriptRoot "output"
$billingRoot = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "billing"
$csvLetters = Join-Path $billingRoot "csv"
$dbLetters = Join-Path $billingRoot "db"

$null = New-Item -ItemType Directory -Force -Path $csvLetters
$null = New-Item -ItemType Directory -Force -Path $dbLetters

[pscustomobject]@{
    use_case = "accounts_receivable_reminder"
    api_base_url = $ApiBaseUrl
    required_handlers = $requiredHandlers
    output_root = $outputRoot
    billing_root = $billingRoot
}
