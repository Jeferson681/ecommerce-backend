param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

function Invoke-Json {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $false)]$Body,
        [Parameter(Mandatory = $false)][hashtable]$Headers
    )

    $headers = @{
        "Accept" = "application/json"
    }

    if ($null -ne $Headers) {
        foreach ($entry in @($Headers.GetEnumerator())) {
            $headers[$entry.Key] = $entry.Value
        }
    }

    if ($null -ne $Body) {
        $headers["Content-Type"] = "application/json"
        $json = $Body | ConvertTo-Json -Depth 10
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -Body $json
    }

    return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers
}

$nonce = (Get-Random -Minimum 10000 -Maximum 99999)
$email = "user+$nonce@example.com"
$password = "Passw0rd!$nonce"

Write-Host "Creating user: $email"
$user = Invoke-Json -Method "POST" -Url "$BaseUrl/users" -Body @{
    first_name = "User"
    last_name  = "Smoke"
    email      = $email
    password   = $password
}

Write-Host "Created user id: $($user.id)"

Write-Host "Logging in..."
$tokens = Invoke-Json -Method "POST" -Url "$BaseUrl/auth/token" -Body @{
    email    = $email
    password = $password
}

if (-not $tokens.access_token) {
    throw "No access_token returned"
}

Write-Host "Access token received (len=$($tokens.access_token.Length))"

Write-Host "Calling /users/me ..."
$me = Invoke-Json -Method "GET" -Url "$BaseUrl/users/me" -Headers @{
    "Authorization" = "Bearer $($tokens.access_token)"
}

Write-Host "Me: $($me.email) (id=$($me.id))"

if ($me.email -ne $email) {
    throw "Expected /users/me email to match created user"
}

Write-Host "OK: auth + me flow works"
