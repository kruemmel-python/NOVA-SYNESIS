param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

$null = & (Join-Path $PSScriptRoot "setup.ps1") -ApiBaseUrl $ApiBaseUrl

$flowPath = Join-Path $PSScriptRoot "flow.json"
$flowRequest = Get-Content $flowPath | ConvertFrom-Json

function Resolve-AgentIdsFromNames {
    param(
        [object]$FlowRequest,
        [string]$ApiBaseUrl
    )

    $agents = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/agents"

    foreach ($node in $FlowRequest.nodes) {
        if ($node.handler_name -ne "send_message") {
            continue
        }

        $targetName = [string]$node.input.target_agent_name
        if ([string]::IsNullOrWhiteSpace($targetName)) {
            continue
        }

        $targetAgent = $agents | Where-Object { $_.name -eq $targetName } | Select-Object -First 1
        if ($null -eq $targetAgent) {
            throw "Agent '$targetName' was not found while resolving target_agent_name"
        }

        $node.input | Add-Member -NotePropertyName "target_agent_id" -NotePropertyValue ([int]$targetAgent.agent_id) -Force
    }

    return $FlowRequest
}

$flowBody = $flowRequest | ConvertTo-Json -Depth 32

try {
    $createdFlow = Invoke-RestMethod `
        -Method Post `
        -Uri "$ApiBaseUrl/flows" `
        -ContentType "application/json; charset=utf-8" `
        -Body $flowBody
}
catch {
    $detail = $_.ErrorDetails.Message
    if ($detail -and $detail -match "target_agent_id") {
        $resolvedFlow = Resolve-AgentIdsFromNames -FlowRequest $flowRequest -ApiBaseUrl $ApiBaseUrl
        $flowBody = $resolvedFlow | ConvertTo-Json -Depth 32
        $createdFlow = Invoke-RestMethod `
            -Method Post `
            -Uri "$ApiBaseUrl/flows" `
            -ContentType "application/json; charset=utf-8" `
            -Body $flowBody
    }
    else {
        throw
    }
}

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
