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

    $headers = @{
        "Accept" = "application/json"
    }

    if ($null -ne $Body) {
        $headers["Content-Type"] = "application/json"

        $json = $Body | ConvertTo-Json -Depth 10

        return Invoke-RestMethod `
            -Method $Method `
            -Uri $Url `
            -Headers $headers `
            -Body $json
    }

    return Invoke-RestMethod `
        -Method $Method `
        -Uri $Url `
        -Headers $headers
}

$products = @(

    # Electronics

    @{
        name = "Wireless Mouse"
        description = "Ergonomic wireless mouse with silent click buttons and USB receiver."
        price = 24.90
        stock_quantity = 120
    },

    @{
        name = "Mechanical Keyboard"
        description = "Compact mechanical keyboard with RGB backlight and tactile switches."
        price = 79.90
        stock_quantity = 60
    },

    @{
        name = "USB-C Charger"
        description = "Fast charging USB-C wall adapter compatible with phones and tablets."
        price = 18.50
        stock_quantity = 200
    },

    @{
        name = "Bluetooth Speaker"
        description = "Portable Bluetooth speaker with deep bass and 12-hour battery life."
        price = 49.90
        stock_quantity = 80
    },

    @{
        name = "Webcam Full HD"
        description = "1080p webcam with built-in microphone for video calls and streaming."
        price = 39.90
        stock_quantity = 45
    },

    @{
        name = "Laptop Stand"
        description = "Adjustable aluminum laptop stand for ergonomic desk setup."
        price = 32.00
        stock_quantity = 90
    },

    @{
        name = "Gaming Headset"
        description = "Over-ear gaming headset with noise isolation and detachable microphone."
        price = 69.90
        stock_quantity = 55
    },

    @{
        name = "Portable SSD 1TB"
        description = "High-speed external SSD with USB-C connectivity and compact design."
        price = 119.90
        stock_quantity = 35
    },

    # Home & Kitchen

    @{
        name = "Ceramic Coffee Mug"
        description = "Minimalist ceramic coffee mug with matte finish and comfortable grip."
        price = 12.90
        stock_quantity = 180
    },

    @{
        name = "Electric Kettle"
        description = "Stainless steel electric kettle with automatic shut-off feature."
        price = 44.90
        stock_quantity = 70
    },

    @{
        name = "Desk Lamp"
        description = "LED desk lamp with adjustable brightness and touch controls."
        price = 27.90
        stock_quantity = 95
    },

    @{
        name = "Memory Foam Pillow"
        description = "Comfortable memory foam pillow designed for neck support."
        price = 36.50
        stock_quantity = 65
    },

    @{
        name = "Air Fryer"
        description = "Compact air fryer with digital controls and non-stick basket."
        price = 129.90
        stock_quantity = 40
    },

    @{
        name = "Water Bottle"
        description = "Insulated stainless steel water bottle for hot and cold drinks."
        price = 21.90
        stock_quantity = 150
    },

    @{
        name = "Storage Basket Set"
        description = "Set of woven storage baskets for shelves and closets."
        price = 29.90
        stock_quantity = 85
    },

    # Fashion

    @{
        name = "Basic Cotton T-Shirt"
        description = "Soft cotton t-shirt with regular fit for everyday wear."
        price = 19.90
        stock_quantity = 140
    },

    @{
        name = "Running Shoes"
        description = "Lightweight running shoes with breathable mesh upper."
        price = 89.90
        stock_quantity = 50
    },

    @{
        name = "Classic Hoodie"
        description = "Fleece hoodie with front pocket and adjustable drawstring hood."
        price = 54.90
        stock_quantity = 75
    },

    @{
        name = "Leather Wallet"
        description = "Slim leather wallet with multiple card slots and cash compartment."
        price = 34.90
        stock_quantity = 110
    },

    @{
        name = "Baseball Cap"
        description = "Adjustable baseball cap with curved brim and embroidered logo."
        price = 16.90
        stock_quantity = 130
    },

    # Office

    @{
        name = "Notebook Set"
        description = "Pack of hardcover notebooks for notes, journaling, and planning."
        price = 14.90
        stock_quantity = 160
    },

    @{
        name = "Gel Pen Pack"
        description = "Smooth writing gel pens with assorted ink colors."
        price = 8.90
        stock_quantity = 220
    },

    @{
        name = "Monitor Arm"
        description = "Adjustable monitor arm for single monitor desk setups."
        price = 64.90
        stock_quantity = 45
    },

    @{
        name = "Office Chair"
        description = "Ergonomic office chair with lumbar support and adjustable height."
        price = 189.90
        stock_quantity = 25
    },

    # Fitness

    @{
        name = "Yoga Mat"
        description = "Non-slip yoga mat with comfortable cushioning for workouts."
        price = 26.90
        stock_quantity = 100
    },

    @{
        name = "Resistance Bands"
        description = "Set of resistance bands for strength training and stretching."
        price = 17.90
        stock_quantity = 150
    },

    @{
        name = "Protein Shaker Bottle"
        description = "Leakproof shaker bottle with mixing ball for protein drinks."
        price = 11.90
        stock_quantity = 170
    },

    # Gaming

    @{
        name = "Gaming Mouse Pad"
        description = "Large gaming mouse pad with smooth surface and anti-slip base."
        price = 15.90
        stock_quantity = 140
    },

    @{
        name = "Controller Charging Dock"
        description = "Dual controller charging dock compatible with wireless controllers."
        price = 28.90
        stock_quantity = 65
    },

    # Misc

    @{
        name = "Scented Candle"
        description = "Soy wax scented candle with clean burn and relaxing fragrance."
        price = 13.90
        stock_quantity = 120
    },

    @{
        name = "Pet Feeding Bowl"
        description = "Stainless steel feeding bowl for cats and small dogs."
        price = 9.90
        stock_quantity = 200
    }
)

Write-Host ""
Write-Host "========================================="
Write-Host "Seeding products into $BaseUrl/products"
Write-Host "========================================="
Write-Host ""

$success = 0
$failed = 0

foreach ($product in $products) {
    try {
        $created = Invoke-Json `
            -Method "POST" `
            -Url "$BaseUrl/products" `
            -Body $product

        $success++

        Write-Host "[CREATED] #$($created.id) - $($created.name)"
    }
    catch {
        $failed++

        Write-Host "[FAILED ] $($product.name)"
        Write-Host "          $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "========================================="
Write-Host "Seed completed"
Write-Host "========================================="
Write-Host "Success: $success"
Write-Host "Failed : $failed"

try {
    $allProducts = Invoke-Json `
        -Method "GET" `
        -Url "$BaseUrl/products"

    Write-Host "Total products available: $($allProducts.Count)"
}
catch {
    Write-Host "Could not fetch product count."
}
