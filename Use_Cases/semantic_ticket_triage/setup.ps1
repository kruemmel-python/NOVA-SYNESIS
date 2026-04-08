param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8552"
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

function Get-NovaJson {
    param(
        [string]$Path
    )

    Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl$Path"
}

function Get-NovaCollection {
    param(
        [string]$Path
    )

    $result = Get-NovaJson -Path $Path
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
        -Body ($Body | ConvertTo-Json -Depth 32)
}

function Get-OrCreateMemorySystem {
    param(
        [string]$MemoryId,
        [string]$Type,
        [string]$Backend
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
        config = @{}
    }
}

function Get-OrCreateAgent {
    param(
        [string]$Name,
        [string]$Role,
        [object[]]$Capabilities,
        [object]$Communication = $null,
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

$memory = Get-OrCreateMemorySystem `
    -MemoryId "triage-vector" `
    -Type "VECTOR" `
    -Backend "Use_Cases/semantic_ticket_triage/state/triage-vector.db"

$routerAgent = Get-OrCreateAgent `
    -Name "triage-router" `
    -Role "router" `
    -Capabilities @(
        @{
            name = "semantic_triage"
            type = "routing"
            constraints = @{}
        },
        @{
            name = "triage_reporting"
            type = "reporting"
            constraints = @{}
        },
        @{
            name = "message_dispatch"
            type = "messaging"
            constraints = @{}
        }
    ) `
    -Communication @{
        protocol = "MESSAGE_QUEUE"
        endpoint = "queue://triage-router"
        config = @{}
    } `
    -MemoryIds @("triage-vector")

$supportSink = Get-OrCreateAgent `
    -Name "support-sink" `
    -Role "support" `
    -Capabilities @() `
    -Communication @{
        protocol = "MESSAGE_QUEUE"
        endpoint = "queue://support"
        config = @{}
    }

$salesSink = Get-OrCreateAgent `
    -Name "sales-sink" `
    -Role "sales" `
    -Capabilities @() `
    -Communication @{
        protocol = "MESSAGE_QUEUE"
        endpoint = "queue://sales"
        config = @{}
    }

[pscustomobject]@{
    use_case = "semantic_ticket_triage"
    api_base_url = $ApiBaseUrl
    memory_id = $memory.memory_id
    memory_type = $memory.type
    router_agent_id = $routerAgent.agent_id
    router_agent_name = $routerAgent.name
    support_sink_id = $supportSink.agent_id
    support_sink_name = $supportSink.name
    sales_sink_id = $salesSink.agent_id
    sales_sink_name = $salesSink.name
}
