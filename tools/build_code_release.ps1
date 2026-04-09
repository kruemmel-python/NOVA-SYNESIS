param(
    [string]$Version = "v1.0.5",
    [string]$OutputDirectory = "release"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputRoot = Join-Path $repoRoot $OutputDirectory
$stagingRoot = Join-Path $outputRoot "staging"
$packageName = "nova-synesis-$Version-code-only"
$packageRoot = Join-Path $stagingRoot $packageName
$archivePath = Join-Path $outputRoot "$packageName.zip"

if (Test-Path $packageRoot) {
    Remove-Item -LiteralPath $packageRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null

$includePaths = @(
    ".env.example",
    ".gitignore",
    "Dockerfile",
    "LICENSE",
    "pyproject.toml",
    "README.md",
    "run-backend.cmd",
    "run-backend.ps1",
    "Anweisung.md",
    "uml_V3.mmd",
    "src",
    "tests",
    "tools",
    "Use_Cases",
    "frontend/index.html",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/.env.example",
    "frontend/tsconfig.json",
    "frontend/tsconfig.app.json",
    "frontend/tsconfig.node.json",
    "frontend/vite.config.ts",
    "frontend/vite.config.js",
    "frontend/vite.config.d.ts",
    "frontend/src"
)

$excludeRegex = @(
    [regex]'(^|[\\/])__pycache__([\\/]|$)',
    [regex]'(^|[\\/])\.pytest_cache([\\/]|$)',
    [regex]'(^|[\\/])node_modules([\\/]|$)',
    [regex]'(^|[\\/])dist([\\/]|$)',
    [regex]'(^|[\\/])output([\\/]|$)',
    [regex]'(^|[\\/])state([\\/]|$)',
    [regex]'\.(pyc|pyo|pyd|db|sqlite|sqlite3)$',
    [regex]'(^|[\\/])release([\\/]|$)',
    [regex]'(^|[\\/])LIT([\\/]).+\.(litertlm|exe)$'
)

function Test-IncludedPath {
    param(
        [string]$RelativePath
    )

    foreach ($pattern in $excludeRegex) {
        if ($pattern.IsMatch($RelativePath)) {
            return $false
        }
    }
    return $true
}

function Get-RepoRelativePath {
    param(
        [string]$BasePath,
        [string]$FullPath
    )

    $resolvedBase = [System.IO.Path]::GetFullPath($BasePath)
    $resolvedFull = [System.IO.Path]::GetFullPath($FullPath)

    if (-not $resolvedFull.StartsWith($resolvedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path '$resolvedFull' is outside base path '$resolvedBase'"
    }

    $relative = $resolvedFull.Substring($resolvedBase.Length).TrimStart('\', '/')
    return $relative
}

foreach ($relativePath in $includePaths) {
    $sourcePath = Join-Path $repoRoot $relativePath
    if (-not (Test-Path $sourcePath)) {
        continue
    }

    if ((Get-Item $sourcePath) -is [System.IO.DirectoryInfo]) {
        Get-ChildItem -LiteralPath $sourcePath -Recurse -File | ForEach-Object {
            $fullPath = $_.FullName
            $relative = Get-RepoRelativePath -BasePath $repoRoot -FullPath $fullPath
            if (-not (Test-IncludedPath -RelativePath $relative)) {
                return
            }

            $targetPath = Join-Path $packageRoot $relative
            $targetDir = Split-Path -Parent $targetPath
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            Copy-Item -LiteralPath $fullPath -Destination $targetPath -Force
        }
    }
    else {
        $relative = Get-RepoRelativePath -BasePath $repoRoot -FullPath $sourcePath
        if (-not (Test-IncludedPath -RelativePath $relative)) {
            continue
        }

        $targetPath = Join-Path $packageRoot $relative
        $targetDir = Split-Path -Parent $targetPath
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    }
}

if (Test-Path $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}

Compress-Archive -Path $packageRoot -DestinationPath $archivePath -Force

[pscustomobject]@{
    version = $Version
    archive = $archivePath
    package_root = $packageRoot
}
