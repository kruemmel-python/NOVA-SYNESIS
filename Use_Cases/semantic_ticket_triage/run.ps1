param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

$null = & (Join-Path $PSScriptRoot "setup.ps1") -ApiBaseUrl $ApiBaseUrl

$flowPath = Join-Path $PSScriptRoot "flow.json"
$flowRequest = Get-Content $flowPath | ConvertFrom-Json

$agents = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/agents"
$supportAgent = $agents | Where-Object { $_.name -eq "support-sink" } | Select-Object -First 1
$salesAgent = $agents | Where-Object { $_.name -eq "sales-sink" } | Select-Object -First 1

if ($null -eq $supportAgent) {
    throw "support-sink was not found after setup"
}

if ($null -eq $salesAgent) {
    throw "sales-sink was not found after setup"
}

$supportAgentId = [int]$supportAgent.agent_id
$salesAgentId = [int]$salesAgent.agent_id

foreach ($node in $flowRequest.nodes) {
    if ($node.node_id -eq "route_to_support") {
        $node.input.target_agent_id = $supportAgentId
    }
    elseif ($node.node_id -eq "route_to_sales") {
        $node.input.target_agent_id = $salesAgentId
    }
}

$flowBody = $flowRequest | ConvertTo-Json -Depth 32

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
