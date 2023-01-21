# Sample script to install Python and pip under Windows
# Authors: Olivier Grisel, Jonathan Helmus, Kyle Kastner, and Alex Willmer
# License: CC0 1.0 Universal: https://creativecommons.org/publicdomain/zero/1.0/

$BASE_URL = "https://www.python.org/ftp/python/"

$PYTHON_PRERELEASE_REGEX = @"
(?x)
(?<major>\d+)
\.
(?<minor>\d+)
\.
(?<micro>\d+)
(?<prerelease>[a-z]{1,2}\d+)
"@


function Download ($filename, $url) {
    $webclient = New-Object System.Net.WebClient

    $basedir = $pwd.Path + "\"
    $filepath = $basedir + $filename
    if (Test-Path $filename) {
        Write-Host "Reusing" $filepath
        return $filepath
    }

    # Download and retry up to 3 times in case of network transient errors.
    Write-Host "Downloading" $filename "from" $url
    $retry_attempts = 2
    for ($i = 0; $i -lt $retry_attempts; $i++) {
        try {
            $webclient.DownloadFile($url, $filepath)
            break
        }
        Catch [Exception]{
            Start-Sleep 1
        }
    }
    if (Test-Path $filepath) {
        Write-Host "File saved at" $filepath
    } else {
        # Retry once to get the error message if any at the last try
        $webclient.DownloadFile($url, $filepath)
    }
    return $filepath
}


function ParsePythonVersion ($python_version) {
    if ($python_version -match $PYTHON_PRERELEASE_REGEX) {
        return ([int]$matches.major, [int]$matches.minor, [int]$matches.micro,
                $matches.prerelease)
    }
    $version_obj = [version]$python_version
    return ($version_obj.major, $version_obj.minor, $version_obj.build, "")
}


function DownloadPython ($python_version, $platform_suffix) {
    $major, $minor, $micro, $prerelease = ParsePythonVersion $python_version

    # Only Python 3.6.1+ is supported
    $dir = "$major.$minor.$micro"
    $ext = "exe"
    if ($platform_suffix) {
        $platform_suffix = "-$platform_suffix"
    }

    $filename = "python-$python_version$platform_suffix.$ext"
    $url = "$BASE_URL$dir/$filename"
    $filepath = Download $filename $url
    return $filepath
}


function InstallPython ($python_version, $architecture, $python_home) {
    Write-Host "Installing Python" $python_version "for" $architecture "bit architecture to" $python_home
    if (Test-Path $python_home) {
        Write-Host $python_home "already exists, skipping."
        return $false
    }

    if ($architecture -eq "32") {
        $platform_suffix = ""
    } else {
        $platform_suffix = "amd64"
    }

    $installer_path = DownloadPython $python_version $platform_suffix
    Write-Host "Installing $installer_path to $python_home"

    $installer_ext = [System.IO.Path]::GetExtension($installer_path)
    $install_log = $python_home + ".log"

    if ($installer_ext -eq '.msi') {
        Write-Host "MSI installer is not supported"
    } else {
        $uninstaller_path = DownloadPython 3.6.8 $platform_suffix
        InstallPythonEXE $installer_path $python_home $install_log $uninstaller_path
    }

    if (Test-Path $python_home) {
        Write-Host "Python $python_version ($architecture) installation complete"
    } else {
        Write-Host "Failed to install Python in $python_home"
        Get-Content -Path $install_log
        Exit 1
    }
}


function InstallPythonEXE ($exepath, $python_home, $install_log, $unexepath) {
    $uninstall_args = "/log C:\Python36-x64.log /quiet /uninstall InstallAllUsers=1 TargetDir=C:\Python36-x64\"
    RunCommand $unexepath $uninstall_args
    $install_args = "/log $install_log /quiet InstallAllUsers=1 TargetDir=$python_home\"
    RunCommand $exepath $install_args
}


function RunCommand ($command, $command_args) {
    Write-Host $command $command_args
    Start-Process -FilePath $command -ArgumentList $command_args -Wait -Passthru
}


function main () {
    if ($env:PYTHON_VERSION -eq "3.6.1") {
        InstallPython $env:PYTHON_VERSION $env:PYTHON_ARCH $env:PYTHON
    }
}

main
