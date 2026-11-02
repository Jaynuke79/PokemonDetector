<#
Installs, exercises, upgrades and uninstalls a built installer on a throwaway
Windows machine. It rewrites the user's PATH, so do not run it on a PC you use.
#>
param(
    [Parameter(Mandatory)][string]$Installer,
    [Parameter(Mandatory)][string]$SampleImage
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest

$Installer = (Resolve-Path -LiteralPath $Installer).Path
$SampleImage = (Resolve-Path -LiteralPath $SampleImage).Path

# A space in the directory is what a profile like C:\Users\First Last would give.
$InstallDir = Join-Path $env:LOCALAPPDATA 'Programs\Pokemon Detector CI'
$WorkDir = Join-Path $env:RUNNER_TEMP 'installer-verification'
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$WebLauncher = Join-Path $InstallDir 'PokemonDetector.exe'
$StartMenuGroup = Join-Path ([Environment]::GetFolderPath('Programs')) 'Pokemon Detector'
$StartupTimeoutSeconds = 300

# The decoy contains the install directory as a substring, and the unexpanded
# variable and REG_EXPAND_SZ type would be lost by a careless rewrite.
$SeededPath = "%USERPROFILE%\poke-seed-first;$InstallDir-decoy;C:\poke-seed-last"
$PathWithApp = "$SeededPath;$InstallDir"

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
    Write-Host "PASS: $Message"
}

function Open-UserEnvironmentKey([bool]$Writable = $false) {
    return [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $Writable)
}

function Get-RawUserPath {
    $key = Open-UserEnvironmentKey
    try {
        return $key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
    } finally { $key.Close() }
}

function Assert-UserPath([string]$Expected, [string]$Context) {
    $actual = Get-RawUserPath
    Assert-True ($actual -ceq $Expected) "$Context`: user PATH is exactly [$Expected], got [$actual]"
    $key = Open-UserEnvironmentKey
    try {
        Assert-True ($key.GetValueKind('Path') -eq [Microsoft.Win32.RegistryValueKind]::ExpandString) "$Context`: user PATH is still REG_EXPAND_SZ"
    } finally { $key.Close() }
}

function Invoke-Setup([string]$Tasks, [string]$Name) {
    $log = Join-Path $WorkDir "setup-$Name.log"
    $arguments = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER /DIR=`"$InstallDir`" /TASKS=`"$Tasks`" /LOG=`"$log`""
    Write-Host "Running setup ($Name): $arguments"
    $elapsed = Measure-Command {
        $script:process = Start-Process -FilePath $Installer -ArgumentList $arguments -Wait -PassThru
    }
    $exitCode = $script:process.ExitCode
    Write-Host "Setup ($Name) took $([int]$elapsed.TotalSeconds)s"
    if ($exitCode -ne 0) { Get-Content -LiteralPath $log | Select-Object -Last 50 | Write-Host }
    Assert-True ($exitCode -eq 0) "setup ($Name) exits 0"
    Assert-True (Test-Path -LiteralPath (Join-Path $InstallDir 'poke.exe')) "setup ($Name) installed poke.exe"
}

function Invoke-FreshPoke([string[]]$PokeArguments) {
    $script = Join-Path $WorkDir 'fresh-poke.ps1'
    @'
param([string]$InstallDir)
$machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
$user = [Environment]::GetEnvironmentVariable('Path', 'User')
$env:Path = "$machine;$user"
$env:POKE_MODELS_DIR = $null
$found = (Get-Command poke -CommandType Application).Source
if ($found -ne (Join-Path $InstallDir 'poke.exe')) { throw "poke resolved to $found" }
& poke @args 2>&1 | ForEach-Object { "$_" }
exit $LASTEXITCODE
'@ | Set-Content -LiteralPath $script
    $elsewhere = Join-Path $WorkDir 'elsewhere'
    New-Item -ItemType Directory -Force -Path $elsewhere | Out-Null
    Push-Location $elsewhere
    try {
        $output = & pwsh -NoProfile -NonInteractive -File $script $InstallDir @PokeArguments
        return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = ($output -join "`n") }
    } finally { Pop-Location }
}

function Start-WebLauncher([string]$Name, [hashtable]$Environment = @{}) {
    $stdout = Join-Path $WorkDir "web-$Name.out.log"
    $stderr = Join-Path $WorkDir "web-$Name.err.log"
    $previous = @{}
    $Environment['POKE_NO_BROWSER'] = '1'
    foreach ($variable in $Environment.Keys) {
        $previous[$variable] = [Environment]::GetEnvironmentVariable($variable)
        [Environment]::SetEnvironmentVariable($variable, $Environment[$variable])
    }
    try {
        $process = Start-Process -FilePath $WebLauncher -WorkingDirectory $WorkDir -NoNewWindow -PassThru `
            -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    } finally {
        foreach ($variable in $previous.Keys) { [Environment]::SetEnvironmentVariable($variable, $previous[$variable]) }
    }
    # Reading Handle keeps ExitCode available after the process ends.
    $null = $process.Handle
    return [pscustomobject]@{ Process = $process; Stdout = $stdout; Stderr = $stderr; Url = $null; Port = 0 }
}

function Show-WebLauncherLogs($Launcher) {
    foreach ($log in @($Launcher.Stdout, $Launcher.Stderr)) {
        Write-Host "--- $log"
        if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log | Write-Host }
    }
}

function Wait-WebLauncherReady($Launcher) {
    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($Launcher.Process.HasExited) {
            Show-WebLauncherLogs $Launcher
            throw "Web launcher exited early with code $($Launcher.Process.ExitCode)"
        }
        if (Test-Path -LiteralPath $Launcher.Stdout) {
            $text = Get-Content -LiteralPath $Launcher.Stdout -Raw
            if ($text -match 'running at (http://127\.0\.0\.1:(\d+))') {
                $Launcher.Url = $Matches[1]
                $Launcher.Port = [int]$Matches[2]
                $health = Invoke-WebRequest -Uri "$($Launcher.Url)/health" -TimeoutSec 30 -SkipHttpErrorCheck
                Assert-True ($health.StatusCode -eq 200) "web launcher /health returns 200 on port $($Launcher.Port)"
                return
            }
        }
        Start-Sleep -Seconds 2
    }
    Show-WebLauncherLogs $Launcher
    throw "Web launcher was not ready within $StartupTimeoutSeconds seconds"
}

function Stop-WebLauncher($Launcher) {
    if (-not $Launcher.Process.HasExited) { Stop-Process -Id $Launcher.Process.Id -Force }
    $Launcher.Process.WaitForExit()
}

function Test-Connects([string]$Address, [int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connect = $client.ConnectAsync($Address, $Port)
        return ($connect.Wait(3000) -and $client.Connected)
    } catch [System.AggregateException] {
        return $false
    } finally { $client.Dispose() }
}

function Assert-OnlyLoopback([int]$Port) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port)
    Assert-True ($listeners.Count -gt 0) "something listens on port $Port"
    $addresses = @($listeners.LocalAddress | Sort-Object -Unique)
    Assert-True (($addresses -join ',') -eq '127.0.0.1') "port $Port listens only on 127.0.0.1, got [$($addresses -join ',')]"

    $others = @(Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
        ForEach-Object { $_.IPAddress })
    Assert-True ($others.Count -gt 0) 'the machine has a non-loopback address to test'
    foreach ($address in $others) {
        Assert-True (-not (Test-Connects $address $Port)) "port $Port is not reachable on $address"
    }
}

function Get-ShortcutDetails([string]$Path) {
    $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($Path)
    return [pscustomobject]@{ Target = $shortcut.TargetPath; WorkingDirectory = $shortcut.WorkingDirectory; Arguments = $shortcut.Arguments }
}

Write-Host '=== Seed the user PATH'
$key = Open-UserEnvironmentKey -Writable $true
try {
    $key.SetValue('Path', $SeededPath, [Microsoft.Win32.RegistryValueKind]::ExpandString)
} finally { $key.Close() }

Write-Host '=== 1. Silent install'
Invoke-Setup -Tasks 'addtopath' -Name 'install'
Assert-UserPath $PathWithApp 'after install'

$webShortcut = Get-ShortcutDetails (Join-Path $StartMenuGroup 'Pokemon Detector.lnk')
Assert-True ($webShortcut.Target -eq $WebLauncher) 'the Start Menu shortcut runs the web launcher'
$cliShortcut = Get-ShortcutDetails (Join-Path $StartMenuGroup 'Pokemon Detector CLI.lnk')
Assert-True ($cliShortcut.Target -ieq $env:ComSpec) 'the CLI shortcut opens a console, not poke.exe'
Assert-True ($cliShortcut.Arguments -like '/K *') 'the CLI shortcut keeps the console open'
Assert-True ($cliShortcut.WorkingDirectory -eq $InstallDir) 'the CLI shortcut starts in the install directory'
Assert-True (Test-Path -LiteralPath (Join-Path $StartMenuGroup 'Uninstall Pokemon Detector.lnk')) 'the Start Menu has an uninstall shortcut'
$desktopIcon = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Pokemon Detector.lnk'
Assert-True (-not (Test-Path -LiteralPath $desktopIcon)) 'no desktop icon without its task'

$bundleFiles = @(Get-ChildItem -LiteralPath $InstallDir -Recurse -File)
$bundleBytes = ($bundleFiles | Measure-Object -Property Length -Sum).Sum
Write-Host ("Installed size: {0:N0} bytes in {1} files" -f $bundleBytes, $bundleFiles.Count)
$strayFiles = @($bundleFiles | Where-Object { $_.Name -like '*Zone.Identifier*' })
Assert-True ($strayFiles.Count -eq 0) 'no Zone.Identifier files were bundled'

Write-Host '=== 2. CLI through the PATH, from another directory'
$result = Invoke-FreshPoke @($SampleImage, '--verbose')
Write-Host $result.Output
Assert-True ($result.ExitCode -eq 0) 'poke exits 0 on the sample image'
$expectedWeights = Join-Path $InstallDir '_internal\models\best_model_fold1.pth'
Assert-True ($result.Output.Contains("Loading weights from: $expectedWeights")) 'poke finds the weights through sys._MEIPASS'
$firstPrediction = ($result.Output -split "`n" | Where-Object { $_ -like 'Class Index:*' } | Select-Object -First 1)
Assert-True ($firstPrediction -match 'Class Name: Gengar,') 'the top prediction is Gengar'

$result = Invoke-FreshPoke @((Join-Path $WorkDir 'no-such-image.png'))
Write-Host $result.Output
Assert-True ($result.ExitCode -ne 0) "poke exits nonzero on a bad path (got $($result.ExitCode))"

Write-Host '=== 3. Web app'
$launcher = Start-WebLauncher -Name 'main'
try {
    Wait-WebLauncherReady $launcher
    Assert-True ($launcher.Port -eq 5000) 'the web launcher uses port 5000 when it is free'

    $index = Invoke-WebRequest -Uri "$($launcher.Url)/" -TimeoutSec 30
    Assert-True ($index.StatusCode -eq 200 -and $index.Content -match '<title>Pokemon Detector</title>') 'GET / renders the bundled template'

    $predictions = (Invoke-RestMethod -Method Post -Uri "$($launcher.Url)/predict" -TimeoutSec 120 -Form @{ file = Get-Item -LiteralPath $SampleImage }).predictions
    $predictions | Format-Table | Out-String | Write-Host
    Assert-True ($predictions[0].class_name -eq 'Gengar') 'POST /predict puts Gengar first'

    Assert-OnlyLoopback $launcher.Port
} finally {
    Show-WebLauncherLogs $launcher
    Stop-WebLauncher $launcher
}

Write-Host '=== 3b. Web app with port 5000 already taken'
# SO_REUSEADDR is the case where a plain bind on Windows would wrongly succeed.
$holder = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 5000)
$holder.Server.SetSocketOption(
    [System.Net.Sockets.SocketOptionLevel]::Socket,
    [System.Net.Sockets.SocketOptionName]::ReuseAddress,
    $true)
$holder.Start()
$launcher = Start-WebLauncher -Name 'port-taken'
try {
    Wait-WebLauncherReady $launcher
    Assert-True ($launcher.Port -ne 5000) "the web launcher moved off the taken port, to $($launcher.Port)"
    Assert-OnlyLoopback $launcher.Port
} finally {
    Show-WebLauncherLogs $launcher
    Stop-WebLauncher $launcher
    $holder.Stop()
}

Write-Host '=== 3c. Web app without its model'
$emptyModels = Join-Path $WorkDir 'empty-models'
New-Item -ItemType Directory -Force -Path $emptyModels | Out-Null
$launcher = Start-WebLauncher -Name 'no-model' -Environment @{ POKE_MODELS_DIR = $emptyModels }
try {
    Assert-True ($launcher.Process.WaitForExit($StartupTimeoutSeconds * 1000)) 'the web launcher exits instead of serving without a model'
    Show-WebLauncherLogs $launcher
    Assert-True ($launcher.Process.ExitCode -eq 1) 'the web launcher exits 1 without a model'
    Assert-True ((Get-Content -LiteralPath $launcher.Stdout -Raw) -match 'could not load its model') 'the web launcher explains the failure'
} finally {
    Stop-WebLauncher $launcher
}

Write-Host '=== 4. Upgrade over the top'
$staleFile = Join-Path $InstallDir '_internal\stale-from-older-version.dll'
Set-Content -LiteralPath $staleFile -Value 'stale'
Invoke-Setup -Tasks 'addtopath' -Name 'upgrade'
Assert-UserPath $PathWithApp 'after upgrade'
Assert-True (-not (Test-Path -LiteralPath $staleFile)) 'upgrading clears files left by the previous version'
$result = Invoke-FreshPoke @($SampleImage)
Assert-True ($result.ExitCode -eq 0 -and $result.Output -match 'Class Name: Gengar,') 'poke still works after the upgrade'

Write-Host '=== 4b. Upgrade with the PATH task unchecked, then checked again'
Invoke-Setup -Tasks '' -Name 'upgrade-no-path'
Assert-UserPath $SeededPath 'after unchecking the PATH task'
Invoke-Setup -Tasks 'addtopath' -Name 'upgrade-path-again'
Assert-UserPath $PathWithApp 'after checking the PATH task again'

Write-Host '=== 5. Silent uninstall'
$uninstaller = Join-Path $InstallDir 'unins000.exe'
Assert-True (Test-Path -LiteralPath $uninstaller) 'unins000.exe exists'
$process = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Wait -PassThru
Assert-True ($process.ExitCode -eq 0) 'the uninstaller exits 0'

# The uninstaller relaunches itself from %TEMP%, so its exit does not mean it is done.
$deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
while ((Test-Path -LiteralPath $InstallDir) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 2 }
if (Test-Path -LiteralPath $InstallDir) {
    Get-ChildItem -LiteralPath $InstallDir -Recurse | Select-Object -First 20 | ForEach-Object { Write-Host $_.FullName }
}
Assert-True (-not (Test-Path -LiteralPath $InstallDir)) 'the install directory is gone'
Assert-True (-not (Test-Path -LiteralPath $StartMenuGroup)) 'the Start Menu group is gone'
Assert-UserPath $SeededPath 'after uninstall'

Write-Host 'All installer checks passed.'
