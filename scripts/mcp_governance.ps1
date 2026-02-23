<#
.SYNOPSIS
    Governance Pre-Execution Hook (Guardrail)
.DESCRIPTION
    Scans input for destructive patterns before allowing execution.
    Should be called by dispatchers or MCP tools before passing raw commands to bash/SQL.
.PARAMETER InputString
    The command or query to be verified.
.EXAMPLE
    .\mcp_governance.ps1 -InputString "DROP TABLE users;"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$InputString
)

$DestructivePatterns = @(
    "(?i)\bDROP\s+(TABLE|DATABASE|INDEX|VIEW)\b",
    "(?i)\bDELETE\s+FROM\b(?!\s+(.*?)\s+WHERE\s+)", # DELETE without WHERE
    "(?i)\bUPDATE\b(?!\s+(.*?)\s+WHERE\s+)",         # UPDATE without WHERE
    "(?i)\bTRUNCATE\s+TABLE\b",
    "rm\s+-rf\s+/",
    "Remove-Item\s+-Recurse\s+-Force\s+['`"]?[A-Za-z]:\\['`"]?"
)

$IsSafe = $true
$ViolatedPattern = ""

foreach ($pattern in $DestructivePatterns) {
    if ($InputString -match $pattern) {
        $IsSafe = $false
        $ViolatedPattern = $pattern
        break
    }
}

if (!$IsSafe) {
    Write-Host "[GOVERNANCE BLOCK] The requested command contains a forbidden destructive pattern: $ViolatedPattern" -ForegroundColor Red
    Write-Host "Execution aborted to protect the workspace and databases." -ForegroundColor Yellow
    exit 1
}

Write-Host "[GOVERNANCE PASS] Command deemed safe." -ForegroundColor Green
exit 0
