param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

$null = & (Join-Path $PSScriptRoot "setup.ps1") -ApiBaseUrl $ApiBaseUrl

$flowPath = Join-Path $PSScriptRoot "flow.json"
$flowRequest = [System.IO.File]::ReadAllText($flowPath).Replace("http://127.0.0.1:8552", $ApiBaseUrl)

$createdFlow = Invoke-RestMethod `
    -Method Post `
    -Uri "$ApiBaseUrl/flows" `
    -ContentType "application/json; charset=utf-8" `
    -Body $flowRequest

$runResult = Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/flows/$($createdFlow.flow_id)/run"
$websocketBase = $ApiBaseUrl -replace "^http", "ws"

[pscustomobject]@{
    use_case = "platform_health_snapshot"
    flow_id = $createdFlow.flow_id
    flow_url = "$ApiBaseUrl/flows/$($createdFlow.flow_id)"
    websocket_url = "$websocketBase/ws/flows/$($createdFlow.flow_id)"
    output_files = @(
        "Use_Cases/platform_health_snapshot/output/latest-health.json",
        "Use_Cases/platform_health_snapshot/output/latest-health-summary.txt"
    )
    run_result = $runResult
}
