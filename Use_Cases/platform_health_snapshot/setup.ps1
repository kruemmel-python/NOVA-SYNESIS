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
        [string]$Backend,
        [hashtable]$Config = @{}
    )

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
        [string[]]$MemoryIds,
        [hashtable]$Communication = $null
    )

    $agents = Get-NovaCollection -Path "/agents"
    $existing = $agents | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if ($null -ne $existing) {
        return $existing
    }

    return Post-NovaJson -Path "/agents" -Body @{
        name = $Name
        role = $Role
        capabilities = $Capabilities
        communication = $Communication
        memory_ids = $MemoryIds
    }
}

$memory = Get-OrCreateMemorySystem `
    -MemoryId "ops-long-term" `
    -Type "LONG_TERM" `
    -Backend "Use_Cases/platform_health_snapshot/state/ops-long-term.db" `
    -Config @{
        planner_visible = $false
    }

$agent = Get-OrCreateAgent `
    -Name "ops-archiver" `
    -Role "operator" `
    -Capabilities @(
        @{
            name = "ops_fetch"
            type = "operations"
            constraints = @{}
        },
        @{
            name = "ops_archive"
            type = "operations"
            constraints = @{}
        }
    ) `
    -MemoryIds @("ops-long-term")

$notifyAgent = Get-OrCreateAgent `
    -Name "ops-notify" `
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
        endpoint = "queue://ops-notify"
        config = @{}
    } `
    -MemoryIds @()

[pscustomobject]@{
    use_case = "platform_health_snapshot"
    api_base_url = $ApiBaseUrl
    memory_id = $memory.memory_id
    memory_type = $memory.type
    agent_id = $agent.agent_id
    agent_name = $agent.name
    notify_agent_id = $notifyAgent.agent_id
    notify_agent_name = $notifyAgent.name
}
