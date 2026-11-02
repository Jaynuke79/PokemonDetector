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
$TempRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }
$WorkDir = Join-Path $TempRoot 'installer-verification'
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$WebLauncher = Join-Path $InstallDir 'PokemonDetector.exe'
$StartMenuGroup = Join-Path ([Environment]::GetFolderPath('Programs')) 'Pokemon Detector'
$StartupTimeoutSeconds = 300
$SetupTimeoutSeconds = 600
$RunningMutexName = 'PokemonDetectorWebLauncher'

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

# Untyped because a [string] parameter would turn $null into an empty string.
function Set-RawUserPath($Value) {
    $key = Open-UserEnvironmentKey -Writable $true
    try {
        if ($null -eq $Value) {
            $key.DeleteValue('Path', $false)
        } else {
            $key.SetValue('Path', $Value, [Microsoft.Win32.RegistryValueKind]::ExpandString)
        }
    } finally { $key.Close() }
}

function Assert-UserPath([string]$Expected, [string]$Context, [string]$Kind = 'ExpandString') {
    $actual = Get-RawUserPath
    Assert-True ($actual -ceq $Expected) "$Context`: user PATH is exactly [$Expected], got [$actual]"
    $key = Open-UserEnvironmentKey
    try {
        Assert-True ($key.GetValueKind('Path').ToString() -eq $Kind) "$Context`: user PATH is $Kind"
    } finally { $key.Close() }
}

function Assert-UserPathMissing([string]$Context) {
    $key = Open-UserEnvironmentKey
    try {
        Assert-True ($key.GetValueNames() -notcontains 'Path') "$Context`: user PATH value does not exist"
    } finally { $key.Close() }
}

function Wait-ProcessExitCode($Process, [string]$Name) {
    $null = $Process.Handle
    if (-not $Process.WaitForExit($SetupTimeoutSeconds * 1000)) {
        Stop-Process -Id $Process.Id -Force
        throw "$Name did not finish within $SetupTimeoutSeconds seconds"
    }
    return $Process.ExitCode
}

function Start-Setup([string]$Tasks, [string]$Name, [string]$Directory) {
    $log = Join-Path $WorkDir "setup-$Name.log"
    $arguments = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER /DIR=`"$Directory`" /TASKS=`"$Tasks`" /LOG=`"$log`""
    Write-Host "Running setup ($Name): $arguments"
    $process = Start-Process -FilePath $Installer -ArgumentList $arguments -PassThru
    $exitCode = Wait-ProcessExitCode $process "Setup ($Name)"
    Write-Host "Setup ($Name) exit code: $exitCode"
    return [pscustomobject]@{ ExitCode = $exitCode; Log = $log }
}

function Invoke-Setup([string]$Tasks, [string]$Name, [string]$Directory = $InstallDir) {
    $setup = Start-Setup $Tasks $Name $Directory
    if ($setup.ExitCode -ne 0 -and (Test-Path -LiteralPath $setup.Log)) {
        Get-Content -LiteralPath $setup.Log | Select-Object -Last 50 | Write-Host
    }
    Assert-True ($setup.ExitCode -eq 0) "setup ($Name) exits 0"
    Assert-True (Test-Path -LiteralPath (Join-Path $Directory 'poke.exe')) "setup ($Name) installed poke.exe"
}

function Test-RunningMutex {
    $mutex = $null
    $exists = [System.Threading.Mutex]::TryOpenExisting($RunningMutexName, [ref]$mutex)
    # Holding this handle open would make setup see the mutex by itself.
    if ($exists) { $mutex.Dispose() }
    return $exists
}

function Get-InstallFingerprint {
    $files = @(Get-ChildItem -LiteralPath $InstallDir -Recurse -File)
    return '{0} files, {1} bytes' -f $files.Count, ($files | Measure-Object -Property Length -Sum).Sum
}

function Assert-PokePredictsGengar([string]$Context) {
    $result = Invoke-FreshPoke @($SampleImage)
    $first = ($result.Output -split "`n" | Where-Object { $_ -like 'Class Index:*' } | Select-Object -First 1)
    Assert-True ($result.ExitCode -eq 0 -and $first -match 'Class Name: Gengar,') "$Context`: poke exits 0 with Gengar first"
}

function Assert-WebPredictsGengar($Launcher, [string]$Context) {
    $health = Invoke-WebRequest -Uri "$($Launcher.Url)/health" -TimeoutSec 30 -SkipHttpErrorCheck
    Assert-True ($health.StatusCode -eq 200) "$Context`: /health returns 200"
    $predictions = (Invoke-RestMethod -Method Post -Uri "$($Launcher.Url)/predict" -TimeoutSec 120 -Form @{ file = Get-Item -LiteralPath $SampleImage }).predictions
    Assert-True ($predictions[0].class_name -eq 'Gengar') "$Context`: POST /predict puts Gengar first"
}

function Test-CanTakePortWithReuse([int]$Port) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    $listener.Server.SetSocketOption(
        [System.Net.Sockets.SocketOptionLevel]::Socket,
        [System.Net.Sockets.SocketOptionName]::ReuseAddress,
        $true)
    try {
        $listener.Start()
        return $true
    } catch [System.Net.Sockets.SocketException] {
        return $false
    } finally { $listener.Stop() }
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

function Invoke-SilentUninstall {
    $uninstaller = Join-Path $InstallDir 'unins000.exe'
    Assert-True (Test-Path -LiteralPath $uninstaller) 'unins000.exe exists'
    $process = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -PassThru
    $exitCode = Wait-ProcessExitCode $process 'Uninstaller'
    Assert-True ($exitCode -eq 0) 'the uninstaller exits 0'

    # The uninstaller relaunches itself from %TEMP%, so its exit does not mean it is done.
    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    while ((Test-Path -LiteralPath $InstallDir) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 2 }
    if (Test-Path -LiteralPath $InstallDir) {
        Get-ChildItem -LiteralPath $InstallDir -Recurse | Select-Object -First 20 | ForEach-Object { Write-Host $_.FullName }
    }
    Assert-True (-not (Test-Path -LiteralPath $InstallDir)) 'the install directory is gone'
    Assert-True (-not (Test-Path -LiteralPath $StartMenuGroup)) 'the Start Menu group is gone'
}

Write-Host '=== Seed the user PATH'
Set-RawUserPath $SeededPath

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
Assert-True ($result.ExitCode -eq 2) "poke exits 2 on a bad path (got $($result.ExitCode))"

Write-Host '=== 3. Web app'
$launcher = Start-WebLauncher -Name 'main'
try {
    Wait-WebLauncherReady $launcher
    Assert-True ($launcher.Port -eq 5000) 'the web launcher uses port 5000 when it is free'

    $index = Invoke-WebRequest -Uri "$($launcher.Url)/" -TimeoutSec 30
    Assert-True ($index.StatusCode -eq 200 -and $index.Content -match '<title>Pokemon Detector</title>') 'GET / renders the bundled template'

    Assert-WebPredictsGengar $launcher 'web app'
    Assert-OnlyLoopback $launcher.Port
    Assert-True (-not (Test-CanTakePortWithReuse $launcher.Port)) 'another process cannot bind the port with SO_REUSEADDR while the app runs'
    Assert-True (Test-RunningMutex) 'the web launcher holds its mutex'

    Write-Host '=== 3a. Upgrade and uninstall while the web app runs'
    $before = Get-InstallFingerprint
    $setup = Start-Setup -Tasks 'addtopath' -Name 'while-running' -Directory $InstallDir
    if (Test-Path -LiteralPath $setup.Log) { Get-Content -LiteralPath $setup.Log | Select-Object -Last 15 | Write-Host }
    Assert-True ($setup.ExitCode -ne 0) "setup refuses to run while the app runs (exit code $($setup.ExitCode))"
    Assert-True ((Get-InstallFingerprint) -eq $before) "the refused upgrade left the install intact ($before)"
    Assert-WebPredictsGengar $launcher 'after the refused upgrade'
    Assert-PokePredictsGengar 'after the refused upgrade'
    Assert-UserPath $PathWithApp 'after the refused upgrade'

    $process = Start-Process -FilePath (Join-Path $InstallDir 'unins000.exe') -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -PassThru
    $exitCode = Wait-ProcessExitCode $process 'Uninstaller while running'
    Write-Host "Uninstaller while the app runs, exit code: $exitCode"
    # The uninstaller relaunches itself from %TEMP%, so give that copy time to act.
    Start-Sleep -Seconds 30
    Assert-True ((Get-InstallFingerprint) -eq $before) "the uninstaller left the install intact ($before)"
    Assert-WebPredictsGengar $launcher 'after the refused uninstall'
    Assert-PokePredictsGengar 'after the refused uninstall'
    Assert-UserPath $PathWithApp 'after the refused uninstall'
    Assert-True (Test-Path -LiteralPath (Join-Path $StartMenuGroup 'Pokemon Detector.lnk')) 'the refused uninstall left the Start Menu group'
} finally {
    Show-WebLauncherLogs $launcher
    Stop-WebLauncher $launcher
}
Assert-True (-not (Test-RunningMutex)) 'the mutex goes away with the web launcher'

Write-Host '=== 3b. Web app with port 5000 already taken'
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
    Assert-True ((Get-Content -LiteralPath $launcher.Stdout -Raw) -match 'cannot start without its model') 'the web launcher explains the failure'
} finally {
    Stop-WebLauncher $launcher
}

Write-Host '=== 4. Upgrade over the top'
$staleFile = Join-Path $InstallDir '_internal\stale-from-older-version.dll'
Set-Content -LiteralPath $staleFile -Value 'stale'
Invoke-Setup -Tasks 'addtopath' -Name 'upgrade'
Assert-UserPath $PathWithApp 'after upgrade'
Assert-True (-not (Test-Path -LiteralPath $staleFile)) 'upgrading clears files left by the previous version'
Assert-PokePredictsGengar 'after the upgrade'

Write-Host '=== 4b. Upgrade with the PATH task unchecked, then checked again'
Invoke-Setup -Tasks '' -Name 'upgrade-no-path'
Assert-UserPath $SeededPath 'after unchecking the PATH task'
Invoke-Setup -Tasks 'addtopath' -Name 'upgrade-path-again'
Assert-UserPath $PathWithApp 'after checking the PATH task again'

Write-Host '=== 4c. PATH edge cases, each added then removed by setup'
$upperDir = $InstallDir.ToUpperInvariant()
$pathCases = @(
    @{ Name = 'missing'; Seed = $null; AfterAdd = $InstallDir; AddKind = 'String'; AfterRemove = $null }
    @{ Name = 'empty'; Seed = ''; AfterAdd = $InstallDir; AddKind = 'ExpandString'; AfterRemove = $null }
    @{ Name = 'trailing-separator'; Seed = 'C:\poke-a;'; AfterAdd = "C:\poke-a;$InstallDir"; AddKind = 'ExpandString'; AfterRemove = 'C:\poke-a' }
    @{ Name = 'different-case'; Seed = "C:\poke-a;$upperDir"; AfterAdd = "C:\poke-a;$upperDir"; AddKind = 'ExpandString'; AfterRemove = 'C:\poke-a' }
    @{ Name = 'backslash-suffix'; Seed = "C:\poke-a;$InstallDir\;C:\poke-b"; AfterAdd = "C:\poke-a;$InstallDir\;C:\poke-b"; AddKind = 'ExpandString'; AfterRemove = 'C:\poke-a;C:\poke-b' }
)
foreach ($case in $pathCases) {
    Set-RawUserPath $case.Seed
    Invoke-Setup -Tasks 'addtopath' -Name "path-$($case.Name)-add"
    Assert-UserPath $case.AfterAdd "$($case.Name), task checked" -Kind $case.AddKind
    Invoke-Setup -Tasks '' -Name "path-$($case.Name)-remove"
    if ($null -eq $case.AfterRemove) {
        Assert-UserPathMissing "$($case.Name), task unchecked"
    } else {
        Assert-UserPath $case.AfterRemove "$($case.Name), task unchecked" -Kind $case.AddKind
    }
}
Set-RawUserPath $PathWithApp

Write-Host '=== 5. Silent uninstall'
Invoke-SilentUninstall
Assert-UserPath $SeededPath 'after uninstall'

Write-Host '=== 5b. Reinstall onto a missing PATH value, then uninstall'
Set-RawUserPath $null
Invoke-Setup -Tasks 'addtopath' -Name 'reinstall'
Assert-UserPath $InstallDir 'after reinstalling onto a missing value' -Kind 'String'
Invoke-SilentUninstall
Assert-UserPathMissing 'after uninstalling from a missing value'

Write-Host "=== 6. Install into another app's folder"
$foreignDir = Join-Path $WorkDir 'another app'
$foreignFile = Join-Path $foreignDir '_internal\foreign-runtime.dll'
New-Item -ItemType Directory -Force -Path (Split-Path $foreignFile) | Out-Null
Set-Content -LiteralPath $foreignFile -Value 'foreign'
Invoke-Setup -Tasks '' -Name 'foreign-folder' -Directory $foreignDir
Assert-True (Test-Path -LiteralPath $foreignFile) "setup keeps another app's _internal files"

Write-Host 'All installer checks passed.'
