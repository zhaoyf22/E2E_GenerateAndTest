param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [ValidateSet("platform", "service", "cli", "frontend", "backend")]
    [string]$Profile = "platform",
    [switch]$WithCI,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$SuiteRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $SuiteRoot "testforge.py"

if (-not (Test-Path $Cli)) {
    throw "testforge.py not found at $Cli"
}

$argsList = @($Cli, "init", "--target", $Target, "--profile", $Profile)
if ($WithCI) { $argsList += "--with-ci" }
if ($Force) { $argsList += "--force" }

Write-Host "Installing TestForge into $Target (profile=$Profile)..."
python @argsList

Write-Host ""
Write-Host "Next:"
Write-Host "  cd $Target"
Write-Host "  python testforge/testforge.py doctor"
Write-Host "  python testforge/testforge.py pack"
