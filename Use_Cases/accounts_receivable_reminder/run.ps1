param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552",
    [ValidateSet("csv", "db")]
    [string]$Source = "csv"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

$null = & (Join-Path $PSScriptRoot "setup.ps1") -ApiBaseUrl $ApiBaseUrl

$flowFile = if ($Source -eq "db") { "flow.orders_db.json" } else { "flow.orders_csv.json" }
$flowPath = Join-Path $PSScriptRoot $flowFile
$flowRequest = [System.IO.File]::ReadAllText($flowPath)

$createdFlow = Invoke-RestMethod `
    -Method Post `
    -Uri "$ApiBaseUrl/flows" `
    -ContentType "application/json; charset=utf-8" `
    -Body $flowRequest

$runResult = Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/flows/$($createdFlow.flow_id)/run"
$outputVariant = if ($Source -eq "db") { "db" } else { "csv" }

[pscustomobject]@{
    use_case = "accounts_receivable_reminder"
    source = $Source
    flow_id = $createdFlow.flow_id
    flow_url = "$ApiBaseUrl/flows/$($createdFlow.flow_id)"
    output_files = @(
        "Use_Cases/accounts_receivable_reminder/output/$outputVariant/open-receivables.json",
        "Use_Cases/accounts_receivable_reminder/output/$outputVariant/letters-manifest.json",
        "Use_Cases/accounts_receivable_reminder/output/$outputVariant/letters-summary.txt",
        "billing/$outputVariant/*.docx"
    )
    run_result = $runResult
}
