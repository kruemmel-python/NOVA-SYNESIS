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
        [string[]]$MemoryIds
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
        memory_ids = $MemoryIds
    }
}

$memory = Get-OrCreateMemorySystem `
    -MemoryId "ops-long-term" `
    -Type "LONG_TERM" `
    -Backend "Use_Cases/platform_health_snapshot/state/ops-long-term.db"

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

[pscustomobject]@{
    use_case = "platform_health_snapshot"
    api_base_url = $ApiBaseUrl
    memory_id = $memory.memory_id
    memory_type = $memory.type
    agent_id = $agent.agent_id
    agent_name = $agent.name
}
