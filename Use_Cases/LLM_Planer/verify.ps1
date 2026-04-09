param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outputDir = Join-Path $PSScriptRoot "output"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

& (Join-Path $PSScriptRoot "setup.ps1") -ApiBaseUrl $ApiBaseUrl | Out-Null

$cases = @(
    @{
        Name = "prompt_01_smoke_message"
        PromptPath = Join-Path $PSScriptRoot "prompt_01_smoke_message.txt"
        OutputPath = Join-Path $outputDir "prompt1.txt"
        MaxNodes = 2
        Expectation = "file"
    },
    @{
        Name = "prompt_03_memory_roundtrip"
        PromptPath = Join-Path $PSScriptRoot "prompt_03_memory_roundtrip.txt"
        OutputPath = Join-Path $outputDir "prompt3_memory.txt"
        MaxNodes = 4
        Expectation = "memory_file"
    },
    @{
        Name = "prompt_04_resource_notify"
        PromptPath = Join-Path $PSScriptRoot "prompt_04_resource_notify.txt"
        OutputPath = $null
        MaxNodes = 2
        Expectation = "queue_delivery"
    }
)

function Wait-FlowCompletion {
    param(
        [string]$BaseUrl,
        [int]$FlowId,
        [int]$TimeoutSeconds = 20
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $flow = Invoke-RestMethod -Uri "$BaseUrl/flows/$FlowId"
        if ($flow.state -in @("COMPLETED", "FAILED")) {
            return $flow
        }
        Start-Sleep -Milliseconds 400
    } while ((Get-Date) -lt $deadline)

    throw "Flow $FlowId did not finish within $TimeoutSeconds seconds."
}

$results = foreach ($case in $cases) {
    if ($case.OutputPath -and (Test-Path $case.OutputPath)) {
        Remove-Item -LiteralPath $case.OutputPath -Force
    }

    $prompt = Get-Content -LiteralPath $case.PromptPath -Raw
    $plannerBody = @{
        prompt = $prompt
        max_nodes = $case.MaxNodes
    } | ConvertTo-Json -Depth 10

    $planned = Invoke-RestMethod `
        -Method Post `
        -Uri "$ApiBaseUrl/planner/generate-flow" `
        -ContentType "application/json" `
        -Body $plannerBody

    $created = Invoke-RestMethod `
        -Method Post `
        -Uri "$ApiBaseUrl/flows" `
        -ContentType "application/json" `
        -Body ($planned.flow_request | ConvertTo-Json -Depth 20)

    Invoke-RestMethod `
        -Method Post `
        -Uri "$ApiBaseUrl/flows/$($created.flow_id)/run" | Out-Null

    $flow = Wait-FlowCompletion -BaseUrl $ApiBaseUrl -FlowId $created.flow_id

    $outputExists = if ($case.OutputPath) { Test-Path $case.OutputPath } else { $false }
    $outputPreview = if ($case.OutputPath -and $outputExists) {
        Get-Content -LiteralPath $case.OutputPath -Raw
    } else {
        $null
    }

    $deliveredNode = $null
    if ($case.Expectation -eq "queue_delivery") {
        $nodeName = ($flow.nodes.PSObject.Properties | Where-Object {
            $_.Value.handler_name -eq "send_message"
        } | Select-Object -First 1).Name
        if ($nodeName) {
            $deliveredNode = $flow.nodes.$nodeName.output
        }
    }

    [PSCustomObject]@{
        name = $case.Name
        flow_id = $created.flow_id
        state = $flow.state
        output_exists = $outputExists
        output_path = $case.OutputPath
        output_preview = $outputPreview
        queue_delivery = $deliveredNode
        planner_warnings = @($planned.warnings)
        planner_security_approved = $planned.security_report.approved
    }
}

$results | ConvertTo-Json -Depth 20
