<#
.SYNOPSIS
Prints a read-only reconciliation report for PRProgress.

.DESCRIPTION
Queries pull requests created by t-melanichen@microsoft.com across the Xbox,
Xbox.Streaming, and Xbox.Services Azure DevOps projects, compares them with
PRProgress\README.md and the referenced per-PR files, and reports:
Tracked, Missing-meaningful, Junk, and Status-drift.

The script does not edit repository files. It writes a CSV copy of the report to
$env:TEMP for easy sorting/filtering.

.USAGE
pwsh -File scripts\sync-pr-progress.ps1

.PREREQUISITES
Azure CLI with the azure-devops extension and either an active `az login` session
or AZURE_DEVOPS_EXT_PAT set to a PAT with PR read access.
#>

[CmdletBinding()]
param(
    [string]$Organization = "https://dev.azure.com/microsoft/",
    [string]$Creator = "t-melanichen@microsoft.com",
    [string[]]$Projects = @("Xbox", "Xbox.Streaming", "Xbox.Services"),
    [int]$Top = 300
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

try {
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $script:OutputEncoding = [Console]::OutputEncoding
} catch {
    Write-Warning "Could not set UTF-8 console encoding: $($_.Exception.Message)"
}

function Get-RepoRoot {
    $root = (& git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $root) {
        return $root.Trim()
    }

    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function ConvertFrom-AzJson {
    param([string]$Json)

    if ([string]::IsNullOrWhiteSpace($Json)) {
        return @()
    }

    # az can emit a leading "WARNING: ..." line (e.g. console-encoding warning) into the
    # captured output; strip anything before the first JSON token so ConvertFrom-Json works.
    $start = $Json.IndexOfAny([char[]]@('[', '{'))
    if ($start -lt 0) {
        return @()
    }
    $Json = $Json.Substring($start)

    $value = $Json | ConvertFrom-Json
    if ($null -eq $value) {
        return @()
    }

    if ($value -is [System.Array]) {
        return @($value)
    }

    return @($value)
}

function Get-LiveStatus {
    param($Pr)

    $status = ""
    if ($null -ne $Pr.status) {
        $status = [string]$Pr.status
    }

    $isDraft = $false
    if ($null -ne $Pr.PSObject.Properties["isDraft"] -and $null -ne $Pr.isDraft) {
        $isDraft = [bool]$Pr.isDraft
    }

    switch -Regex ($status.ToLowerInvariant()) {
        "^completed$" { return "Merged" }
        "^abandoned$" { return "Abandoned" }
        "^active$" {
            if ($isDraft) {
                return "Draft"
            }
            return "Active"
        }
        default {
            if ($status.Length -gt 0) {
                return $status.Substring(0, 1).ToUpperInvariant() + $status.Substring(1)
            }
            return "Unknown"
        }
    }
}

function Get-PrId {
    param($Pr)

    foreach ($name in @("pullRequestId", "pullRequestId".ToLowerInvariant(), "id")) {
        if ($null -ne $Pr.PSObject.Properties[$name] -and $null -ne $Pr.$name) {
            return [int]$Pr.$name
        }
    }

    throw "Could not find PR id in Azure DevOps response."
}

function Get-RepoName {
    param($Pr)

    if ($null -ne $Pr.repository -and $null -ne $Pr.repository.name) {
        return [string]$Pr.repository.name
    }

    if ($null -ne $Pr.PSObject.Properties["repositoryName"] -and $null -ne $Pr.repositoryName) {
        return [string]$Pr.repositoryName
    }

    return ""
}

function Test-JunkTitle {
    param(
        [string]$Title,
        [string]$LiveStatus
    )

    $normalized = (($Title -replace "\s+", " ").Trim()).ToLowerInvariant()
    $exactJunk = @("g", "unused pr", "remove hyphen", "test", "testing", "wip")
    if ($exactJunk -contains $normalized) {
        return $true
    }

    if ($normalized.Length -le 3) {
        return $true
    }

    if ($LiveStatus -eq "Abandoned" -and $normalized -match "^(unused|remove hyphen|placeholder|temp|scratch)\b") {
        return $true
    }

    return $false
}

function Get-ReadmeTrackedPrs {
    param([string]$ReadmePath)

    $tracked = @{}
    $lines = Get-Content -LiteralPath $ReadmePath -Encoding UTF8
    foreach ($line in $lines) {
        if ($line -match "^\|\s*(\d+)\s*\|\s*(\d{6,})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|.*\]\((\.\/[^)]+)\)") {
            $id = [int]$matches[2]
            $tracked[$id] = [pscustomobject]@{
                Number = $matches[1].Trim()
                Area = $matches[3].Trim()
                Repo = $matches[4].Trim()
                ReadmeStatus = $matches[5].Trim()
                Link = $matches[6].Trim()
            }
        }
    }

    return $tracked
}

function Get-AbandonedReadmePrs {
    # PR ids intentionally recorded WITHOUT an individual file, under the
    # "## Superseded / abandoned PRs" section of PRProgress/README.md.
    param([string]$ReadmePath)

    $abandoned = @{}
    $inSection = $false
    foreach ($line in (Get-Content -LiteralPath $ReadmePath -Encoding UTF8)) {
        if ($line -match "^#{1,6}\s") {
            $inSection = ($line -match "(?i)superseded|abandoned")
            continue
        }
        if ($inSection -and $line -match "^\|\s*(\d{6,})\s*\|") {
            $abandoned[[int]$matches[1]] = $true
        }
    }

    return $abandoned
}

function Get-NormalizedStatus {
    # Collapse qualifiers so "Active (in review)" compares equal to "Active".
    param([string]$Status)

    if ([string]::IsNullOrWhiteSpace($Status)) {
        return ""
    }

    return ($Status -replace "\(.*?\)", "").Trim()
}

function Get-TrackedFileStatus {
    param(
        [string]$RepoRoot,
        $Entry
    )

    $relative = $Entry.Link
    if ($relative.StartsWith("./")) {
        $relative = $relative.Substring(2)
    }

    $filePath = Join-Path (Join-Path $RepoRoot "PRProgress") $relative
    if (-not (Test-Path -LiteralPath $filePath)) {
        return [pscustomobject]@{
            FilePath = $filePath
            Exists = $false
            Status = ""
        }
    }

    $status = ""
    foreach ($line in (Get-Content -LiteralPath $filePath -Encoding UTF8)) {
        if ($line -match "^\s*-\s+\*\*Status:\*\*\s*(.+?)\s*$") {
            $status = $matches[1].Trim()
            break
        }
    }

    return [pscustomobject]@{
        FilePath = $filePath
        Exists = $true
        Status = $status
    }
}

$repoRoot = Get-RepoRoot
$readmePath = Join-Path $repoRoot "PRProgress\README.md"
if (-not (Test-Path -LiteralPath $readmePath)) {
    throw "Could not find PRProgress\README.md under $repoRoot"
}

$tracked = Get-ReadmeTrackedPrs -ReadmePath $readmePath
$abandoned = Get-AbandonedReadmePrs -ReadmePath $readmePath
$livePrs = @()

foreach ($project in $Projects) {
    Write-Host "Querying $project..." -ForegroundColor Cyan
    $json = & az repos pr list --organization $Organization --project $project --creator $Creator --status all --top $Top -o json 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "az repos pr list failed for project '$project' (az exit $LASTEXITCODE). Ensure 'az login' is active and the azure-devops extension is installed."
    }

    foreach ($pr in (ConvertFrom-AzJson -Json ($json -join [Environment]::NewLine))) {
        $livePrs += [pscustomobject]@{
            Project = $project
            Pr = $pr
        }
    }
}

$rows = @()
foreach ($item in $livePrs | Sort-Object { Get-PrId $_.Pr }) {
    $id = Get-PrId $item.Pr
    $title = ""
    if ($null -ne $item.Pr.title) {
        $title = [string]$item.Pr.title
    }

    $repo = Get-RepoName $item.Pr
    $liveStatus = Get-LiveStatus $item.Pr
    $classification = "Missing-meaningful"
    $readmeStatus = ""
    $fileStatus = ""
    $notes = ""

    if ($tracked.ContainsKey($id)) {
        $classification = "Tracked"
        $readmeStatus = $tracked[$id].ReadmeStatus
        $fileInfo = Get-TrackedFileStatus -RepoRoot $repoRoot -Entry $tracked[$id]
        $fileStatus = $fileInfo.Status
        if (-not $fileInfo.Exists) {
            $notes = "README link target missing"
        }

        $liveNorm = Get-NormalizedStatus $liveStatus
        if (($readmeStatus -ne "" -and (Get-NormalizedStatus $readmeStatus) -ne $liveNorm) -or ($fileStatus -ne "" -and (Get-NormalizedStatus $fileStatus) -ne $liveNorm)) {
            $classification = "Status-drift"
            $notes = ("README={0}; file={1}; live={2}" -f $readmeStatus, $fileStatus, $liveStatus)
        }
    } elseif ($abandoned.ContainsKey($id)) {
        $classification = "Abandoned (recorded)"
        $notes = "Recorded in README Superseded/abandoned section (no per-PR file by design)"
    } elseif (Test-JunkTitle -Title $title -LiveStatus $liveStatus) {
        $classification = "Junk"
    }

    $rows += [pscustomobject]@{
        Classification = $classification
        PR = $id
        LiveStatus = $liveStatus
        ReadmeStatus = $readmeStatus
        FileStatus = $fileStatus
        Project = $item.Project
        Repo = $repo
        Title = $title
        Notes = $notes
    }
}

$csvPath = Join-Path $env:TEMP ("pr-progress-reconciliation-{0}.csv" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
$rows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "PRProgress reconciliation report" -ForegroundColor Green
Write-Host ("Repo: {0}" -f $repoRoot)
Write-Host ("CSV:  {0}" -f $csvPath)
Write-Host ""

foreach ($classification in @("Tracked", "Abandoned (recorded)", "Missing-meaningful", "Junk", "Status-drift")) {
    $groupRows = @($rows | Where-Object { $_.Classification -eq $classification })
    Write-Host ("== {0} ({1}) ==" -f $classification, $groupRows.Count) -ForegroundColor Yellow
    if ($groupRows.Count -eq 0) {
        Write-Host "None"
    } else {
        $groupRows |
            Sort-Object PR |
            Format-Table PR, LiveStatus, ReadmeStatus, FileStatus, Project, Repo, Title, Notes -AutoSize -Wrap
    }
    Write-Host ""
}

