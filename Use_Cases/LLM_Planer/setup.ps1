param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

function Get-NovaCollection {
    param(
        [string]$Path
    )

    $result = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl$Path"
    if ($null -eq $result) {
        return @()
    }
    if ($result -is [System.Array]) {
        return $result
    }
    return @($result)
}

function Post-NovaJson {
    param(
        [string]$Path,
        [object]$Body
    )

    Invoke-RestMethod `
        -Method Post `
        -Uri "$ApiBaseUrl$Path" `
        -ContentType "application/json; charset=utf-8" `
        -Body ($Body | ConvertTo-Json -Depth 20)
}

function Get-OrCreateResource {
    param(
        [string]$Type,
        [string]$Endpoint,
        [hashtable]$Metadata
    )

    $resources = Get-NovaCollection -Path "/resources"
    $existing = $resources | Where-Object { $_.endpoint -eq $Endpoint } | Select-Object -First 1
    if ($null -ne $existing) {
        return $existing
    }

    return Post-NovaJson -Path "/resources" -Body @{
        type = $Type
        endpoint = $Endpoint
        metadata = $Metadata
    }
}

function Get-OrCreateMemorySystem {
    param(
        [string]$MemoryId,
        [string]$Type,
        [string]$Backend,
        [hashtable]$Config
    )

    $systems = Get-NovaCollection -Path "/memory-systems"
    $existing = $systems | Where-Object { $_.memory_id -eq $MemoryId } | Select-Object -First 1
    if ($null -ne $existing) {
        return $existing
    }

    return Post-NovaJson -Path "/memory-systems" -Body @{
        memory_id = $MemoryId
        type = $Type
        backend = $Backend
        config = $Config
    }
}

function Get-OrCreateAgent {
    param(
        [string]$Name,
        [string]$Role,
        [object[]]$Capabilities,
        [hashtable]$Communication = $null,
        [string[]]$MemoryIds = @()
    )

    $agents = Get-NovaCollection -Path "/agents"
    $existing = $agents | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if ($null -ne $existing) {
        return $existing
    }

    $body = @{
        name = $Name
        role = $Role
        capabilities = $Capabilities
        memory_ids = $MemoryIds
    }
    if ($null -ne $Communication) {
        $body.communication = $Communication
    }

    return Post-NovaJson -Path "/agents" -Body $body
}

New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot "state") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot "output") | Out-Null

$resource = Get-OrCreateResource `
    -Type "API" `
    -Endpoint "http://127.0.0.1:8552/health" `
    -Metadata @{
        planner_visible = $true
        label = "Local Health API"
        timeout_s = 3.0
        health_method = "GET"
    }

$memory = Get-OrCreateMemorySystem `
    -MemoryId "llm-planner-notes" `
    -Type "LONG_TERM" `
    -Backend "Use_Cases/LLM_Planer/state/llm-planner-notes.db" `
    -Config @{
        planner_visible = $true
        allow_untrusted_ingest = $false
    }

$agent = Get-OrCreateAgent `
    -Name "llm-planner-notify" `
    -Role "sink" `
    -Capabilities @(
        @{
            name = "notify"
            type = "dispatch"
            constraints = @{}
        }
    ) `
    -Communication @{
        protocol = "MESSAGE_QUEUE"
        endpoint = "queue://llm-planner-notify"
        config = @{}
    }

[pscustomobject]@{
    use_case = "LLM_Planer"
    api_base_url = $ApiBaseUrl
    resource_id = $resource.resource_id
    resource_endpoint = $resource.endpoint
    memory_id = $memory.memory_id
    memory_type = $memory.type
    agent_id = $agent.agent_id
    agent_name = $agent.name
}
