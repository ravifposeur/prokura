$ErrorActionPreference = "Stop"

$api = $env:PROKURA_API_BASE_URL
if (-not $api) {
  $api = "http://127.0.0.1:5000"
}

function Invoke-ProkuraJson {
  param(
    [string]$Method,
    [string]$Path,
    [object]$Body = $null
  )

  $params = @{
    Method = $Method
    Uri = "$api$Path"
    ContentType = "application/json"
  }
  if ($null -ne $Body) {
    $params.Body = ($Body | ConvertTo-Json -Depth 10)
  }
  $response = Invoke-RestMethod @params
  if (-not $response.success) {
    throw "API call failed: $Method $Path"
  }
  return $response.data
}

$stamp = Get-Date -Format "yyyyMMddHHmmss"

Write-Host "== Catalog Service =="
$product = Invoke-ProkuraJson -Method Post -Path "/api/products" -Body @{
  sku = "SKU-SMOKE-$stamp"
  nama_produk = "Smoke Test Product $stamp"
  kategori = "Bahan Pokok"
  satuan = "Kg"
  harga_dasar = 25000
  stok_gudang = 10
}
$product | ConvertTo-Json -Depth 5

$search = Invoke-ProkuraJson -Method Get -Path "/api/products?q=Smoke%20Test%20Product%20$stamp&include_empty=true"
Write-Host "Search result count: $(@($search).Count)"

Write-Host "== Inventory Service =="
$stock = Invoke-ProkuraJson -Method Patch -Path "/api/products/$($product.product_id)/stock" -Body @{
  quantity = 5
  note = "Smoke test restock"
}
$stock | ConvertTo-Json -Depth 5

$movements = Invoke-ProkuraJson -Method Get -Path "/api/inventory/movements?product_id=$($product.product_id)"
Write-Host "Movement count: $(@($movements).Count)"

Write-Host "== Customer Service =="
$company = Invoke-ProkuraJson -Method Post -Path "/api/companies" -Body @{
  nama_perusahaan = "PT Smoke Customer $stamp"
  npwp = "SMOKE-$stamp"
  kategori_industri = "Hotel"
  limit_kredit = 10000000
}
$company | ConvertTo-Json -Depth 5

$user = Invoke-ProkuraJson -Method Post -Path "/api/users" -Body @{
  company_id = $company.company_id
  nama_lengkap = "Smoke User $stamp"
  email = "smoke.$stamp@prokura.test"
  peran = "Procurement"
}
$user | ConvertTo-Json -Depth 5

Write-Host "== Order Service =="
$order = Invoke-ProkuraJson -Method Post -Path "/api/orders" -Body @{
  company_id = $company.company_id
  dibuat_oleh = $user.user_id
  metode_pembayaran = "Tempo_30_Hari"
  total_tagihan = 50000
  items = @(
    @{
      product_id = $product.product_id
      kuantitas = 2
      harga_final = 25000
    }
  )
}
$order | ConvertTo-Json -Depth 5

$history = Invoke-ProkuraJson -Method Get -Path "/api/companies/$($company.company_id)/orders"
Write-Host "Customer order history count: $(@($history).Count)"

Write-Host "== Reporting Service =="
$report = Invoke-ProkuraJson -Method Get -Path "/api/reports/sales?start=2026-01-01&end=2999-12-31"
$report.summary | ConvertTo-Json -Depth 5
Write-Host "Top products count: $($report.top_products.Count)"
Write-Host "Top clients count: $($report.top_clients.Count)"

Write-Host "== Final Database State =="
$finalProduct = Invoke-ProkuraJson -Method Get -Path "/api/products?q=SKU-SMOKE-$stamp&include_empty=true"
$finalMovements = Invoke-ProkuraJson -Method Get -Path "/api/inventory/movements?product_id=$($product.product_id)"
$finalProduct | ConvertTo-Json -Depth 5
$finalMovements | ConvertTo-Json -Depth 5

Write-Host "Smoke test complete."
