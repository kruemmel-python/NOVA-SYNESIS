param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

$null = & (Join-Path $PSScriptRoot "setup.ps1") -ApiBaseUrl $ApiBaseUrl

$flowPath = Join-Path $PSScriptRoot "flow.json"
$flowBody = Get-Content $flowPath -Raw

$createdFlow = Invoke-RestMethod `
    -Method Post `
    -Uri "$ApiBaseUrl/flows" `
    -ContentType "application/json; charset=utf-8" `
    -Body $flowBody

$runResult = Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/flows/$($createdFlow.flow_id)/run"
$websocketBase = $ApiBaseUrl -replace "^http", "ws"

[pscustomobject]@{
    use_case = "semantic_ticket_triage"
    flow_id = $createdFlow.flow_id
    flow_url = "$ApiBaseUrl/flows/$($createdFlow.flow_id)"
    websocket_url = "$websocketBase/ws/flows/$($createdFlow.flow_id)"
    output_files = @(
        "Use_Cases/semantic_ticket_triage/output/latest-triage-summary.txt",
        "Use_Cases/semantic_ticket_triage/output/dispatch-support.txt",
        "Use_Cases/semantic_ticket_triage/output/dispatch-sales.txt"
    )
    run_result = $runResult
}
