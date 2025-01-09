# deploy_ovpn_server_on_win10-11.ps1

# Define paths
$scriptDir = Get-Location
$openvpnConfigDir = "C:\Program Files\OpenVPN\config"
$newServerDirPath = Join-Path $scriptDir "server"
$batchFilePath = "C:\Program Files\OpenVPN\config\server\start_openvpn.bat"  # Updated path
$newServerConfPath = Join-Path $newServerDirPath "server.conf"
$existingServerDirPath = Join-Path $openvpnConfigDir "server"
$existingServerConfPath = Join-Path $existingServerDirPath "server.conf"
$ccdDir = Join-Path $newServerDirPath "ccd"
$openvpnExePath = "C:\Program Files\OpenVPN\bin\openvpn.exe"
$taskName = "Start OpenVPN Server Batch"

# Ensure the new server.conf file exists
Write-Host "Looking for server.conf at: $newServerConfPath"
if (-Not (Test-Path $newServerConfPath)) {
    Write-Host "Error: New server.conf not found in the server directory."
    exit 1
}

# Create the OpenVPN config server directory if it doesn't exist
if (-Not (Test-Path $existingServerDirPath)) {
    Write-Host "Creating server directory in OpenVPN config directory."
    New-Item -Path $existingServerDirPath -ItemType Directory -Force
}

# Copy the new server.conf file
Write-Host "Copying server.conf to the OpenVPN server directory..."
Copy-Item $newServerConfPath -Destination $existingServerConfPath -Force

# Copy the ccd directory if it exists
if (Test-Path $ccdDir) {
    Write-Host "Copying CCD directory to OpenVPN server directory..."
    Copy-Item "$ccdDir" -Destination "$existingServerDirPath" -Recurse -Force
} else {
    Write-Host "Warning: CCD directory not found. Skipping this step."
}

# Find the correct OpenVPN service name
$openvpnServiceName = (Get-Service | Where-Object { $_.Name -like "*openvpn*" } | Select-Object -First 1).Name

if (-Not $openvpnServiceName) {
    Write-Host "Error: OpenVPN service not found. Make sure OpenVPN is installed and registered as a service."
    exit 1
}

# Start and configure OpenVPN service
Start-Service $openvpnServiceName
Set-Service $openvpnServiceName -StartupType Automatic -PassThru

# Enable IP routing in Windows
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" -Name "IPEnableRouter" -Value 1 -Type DWord

# Enable and start Routing and Remote Access service
Write-Host "Enabling and starting the Routing and Remote Access service..."
Set-Service RemoteAccess -StartupType Automatic
Start-Service RemoteAccess -ErrorAction Stop
Write-Host "Successfully enabled and started the Routing and Remote Access service."

# Create the OpenVPN config server directory if it doesn't exist
$serverBatchDir = "C:\Program Files\OpenVPN\config\server"
if (-Not (Test-Path $serverBatchDir)) {
    Write-Host "Creating directory for batch file..."
    New-Item -Path $serverBatchDir -ItemType Directory -Force
}

# Create the batch file to start OpenVPN
Write-Host "Creating batch file to start OpenVPN..."
$batchContent = @"
@echo off
cd "C:\Program Files\OpenVPN\config\server\"
"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "server.conf"
"@
Set-Content -Path $batchFilePath -Value $batchContent -Force

# Remove existing scheduled task if it exists
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Existing scheduled task '$taskName' has been removed."
} catch {
    Write-Host "No existing task found with name '$taskName'."
}

# Create a scheduled task to run the batch file at startup
Write-Host "Creating a scheduled task to start OpenVPN on system boot..."
$taskAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batchFilePath`""
$taskTrigger = New-ScheduledTaskTrigger -AtStartup
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$taskPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

# Attempt to register the task
try {
    Register-ScheduledTask -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -Principal $taskPrincipal -TaskName $taskName -Description "Start OpenVPN using batch file at system startup"
    Write-Host "Scheduled task to start OpenVPN at boot has been created."
} catch {
    Write-Host "Error creating scheduled task: $_"
    exit 1
}

Write-Host "OpenVPN server setup completed successfully."
