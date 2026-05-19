param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

function Get-StatusCodeFromException($err) {
    try { return [int]$err.Exception.Response.StatusCode.value__ } catch { return -1 }
}

Write-Host "== Smoke test /users on $BaseUrl =="

# 1) healthz
try {
    $h = Invoke-RestMethod -Uri "$BaseUrl/healthz" -Method Get
    Write-Host "GET /healthz -> 200 status=$($h.status)"
}
catch {
    $sc = Get-StatusCodeFromException $_
    Write-Host "GET /healthz -> $sc (failed)"
    throw
}

# 2) create
$email = "smoke$([int](Get-Random -Minimum 100000 -Maximum 999999))@example.com"
$createBody = @{ first_name = "Smoke"; last_name = "Test"; email = $email; password = "Passw0rd!" } | ConvertTo-Json
try {
    $created = Invoke-RestMethod -Uri "$BaseUrl/users" -Method Post -ContentType "application/json" -Body $createBody
    $id = [int]$created.id
    Write-Host "POST /users -> 201 id=$id email=$($created.email)"
}
catch {
    $sc = Get-StatusCodeFromException $_
    Write-Host "POST /users -> $sc (failed)"
    throw
}

# 3) list and locate
try {
    $users = Invoke-RestMethod -Uri "$BaseUrl/users" -Method Get
    $found = $users | Where-Object { $_.email -eq $email } | Select-Object -First 1
    Write-Host "GET /users -> 200 count=$($users.Count) foundId=$($found.id)"
}
catch {
    $sc = Get-StatusCodeFromException $_
    Write-Host "GET /users -> $sc (failed)"
    throw
}

# 4) patch
$patchBody = @{ is_active = $false } | ConvertTo-Json
try {
    $updated = Invoke-RestMethod -Uri "$BaseUrl/users/$id" -Method Patch -ContentType "application/json" -Body $patchBody
    Write-Host "PATCH /users/$id -> 200 is_active=$($updated.is_active)"
}
catch {
    $sc = Get-StatusCodeFromException $_
    Write-Host "PATCH /users/$id -> $sc (failed)"
    throw
}

# 5) get
try {
    $get = Invoke-RestMethod -Uri "$BaseUrl/users/$id" -Method Get
    Write-Host "GET /users/$id -> 200 name=$($get.first_name) $($get.last_name) active=$($get.is_active)"
}
catch {
    $sc = Get-StatusCodeFromException $_
    Write-Host "GET /users/$id -> $sc (failed)"
    throw
}

# 6) delete
try {
    Invoke-RestMethod -Uri "$BaseUrl/users/$id" -Method Delete
    Write-Host "DELETE /users/$id -> 204"
}
catch {
    $sc = Get-StatusCodeFromException $_
    Write-Host "DELETE /users/$id -> $sc (failed)"
    throw
}

# 7) get after delete expects 404
try {
    Invoke-RestMethod -Uri "$BaseUrl/users/$id" -Method Get
    Write-Host "GET /users/$id after delete -> 200 (unexpected)"
    exit 1
}
catch {
    $sc = Get-StatusCodeFromException $_
    Write-Host "GET /users/$id after delete -> $sc (expected 404)"
}

Write-Host "== OK =="
