param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

function Invoke-Json {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $false)]$Body
    )

    $headers = @{ "Accept" = "application/json" }

    if ($null -ne $Body) {
        $headers["Content-Type"] = "application/json"
        $json = $Body | ConvertTo-Json -Depth 10
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -Body $json
    }

    return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers
}

$products = @(
    @{ name = "Basic Tee"; description = "Soft cotton t-shirt"; price = 19.9; stock_quantity = 25 },
    @{ name = "Coffee Mug"; description = "Ceramic mug 300ml"; price = 9.5; stock_quantity = 100 },
    @{ name = "Sticker Pack"; description = "Set of 10 stickers"; price = 4.0; stock_quantity = 250 }
)

Write-Host "Seeding products into $BaseUrl/products ..."

foreach ($p in $products) {
    try {
        $created = Invoke-Json -Method "POST" -Url "$BaseUrl/products" -Body $p
        Write-Host "Created product #$($created.id): $($created.name)"
    }
    catch {
        Write-Host "Failed to create '$($p.name)': $($_.Exception.Message)"
    }
}

$all = Invoke-Json -Method "GET" -Url "$BaseUrl/products"
Write-Host "Total products now: $($all.Count)"
