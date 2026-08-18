[CmdletBinding()]
param(
    [string[]]$CriticalServices = @('WinRM', 'EventLog'),
    [string]$OutputPath = ''
)

$ErrorActionPreference = 'Stop'

function Get-ServiceSnapshot {
    param([string[]]$Names)

    foreach ($serviceName in $Names) {
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($null -eq $service) {
            [pscustomobject]@{
                Name = $serviceName
                Status = 'NotFound'
                Healthy = $false
            }
            continue
        }

        [pscustomobject]@{
            Name = $service.Name
            Status = [string]$service.Status
            Healthy = $service.Status -eq 'Running'
        }
    }
}

$operatingSystem = Get-CimInstance -ClassName Win32_OperatingSystem
$processors = Get-CimInstance -ClassName Win32_Processor
$logicalDisks = Get-CimInstance -ClassName Win32_LogicalDisk -Filter 'DriveType = 3'

$totalMemoryGb = [math]::Round($operatingSystem.TotalVisibleMemorySize / 1MB, 2)
$freeMemoryGb = [math]::Round($operatingSystem.FreePhysicalMemory / 1MB, 2)
$usedMemoryPercent = if ($totalMemoryGb -gt 0) {
    [math]::Round((($totalMemoryGb - $freeMemoryGb) / $totalMemoryGb) * 100, 2)
} else {
    0
}

$diskSnapshot = foreach ($disk in $logicalDisks) {
    $freePercent = if ($disk.Size -gt 0) {
        [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 2)
    } else {
        0
    }

    [pscustomobject]@{
        Device = $disk.DeviceID
        SizeGb = [math]::Round($disk.Size / 1GB, 2)
        FreeGb = [math]::Round($disk.FreeSpace / 1GB, 2)
        FreePercent = $freePercent
        Healthy = $freePercent -ge 15
    }
}

$services = @(Get-ServiceSnapshot -Names $CriticalServices)
$report = [ordered]@{
    SchemaVersion = '1.0'
    CollectedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
    ComputerName = $env:COMPUTERNAME
    OperatingSystem = $operatingSystem.Caption
    UptimeHours = [math]::Round(((Get-Date) - $operatingSystem.LastBootUpTime).TotalHours, 2)
    Cpu = [ordered]@{
        LogicalProcessors = ($processors | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
        AverageLoadPercent = [math]::Round(($processors | Measure-Object -Property LoadPercentage -Average).Average, 2)
    }
    Memory = [ordered]@{
        TotalGb = $totalMemoryGb
        FreeGb = $freeMemoryGb
        UsedPercent = $usedMemoryPercent
        Healthy = $usedMemoryPercent -lt 90
    }
    Disks = @($diskSnapshot)
    Services = $services
}

$report['Healthy'] = (
    $report.Memory.Healthy -and
    -not ($report.Disks | Where-Object { -not $_.Healthy }) -and
    -not ($services | Where-Object { -not $_.Healthy })
)

$json = $report | ConvertTo-Json -Depth 6
if ($OutputPath) {
    $resolvedOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
    $outputDirectory = Split-Path -Parent $resolvedOutput
    if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    }
    Set-Content -LiteralPath $resolvedOutput -Value $json -Encoding utf8
}

$json
