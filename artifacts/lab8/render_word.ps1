$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
 $review = Join-Path $PSScriptRoot "report8-review.docx"
 Copy-Item (Join-Path $PSScriptRoot "СПЗ 8.docx") $review -Force
 $doc = $word.Documents.Open($review, $false, $true)
 $doc.ActiveWindow.View.Type = 3
 $doc.Repaginate()
 $total = $doc.ComputeStatistics(2)
 Write-Output "Pages: $total"
 $folder = Join-Path $PSScriptRoot "preview"
 New-Item -ItemType Directory -Path $folder -Force | Out-Null
 for ($i=1; $i -le $total; $i++) {
  $page = $doc.ActiveWindow.Panes.Item(1).Pages.Item($i)
  [byte[]]$bits = $page.EnhMetaFileBits
  $stream = New-Object System.IO.MemoryStream(,$bits)
  $emf = [System.Drawing.Image]::FromStream($stream)
  $bmp = New-Object System.Drawing.Bitmap 1000,1414
  $graphics = [System.Drawing.Graphics]::FromImage($bmp)
  $graphics.Clear([System.Drawing.Color]::White)
  $graphics.DrawImage($emf,0,0,1000,1414)
  $bmp.Save((Join-Path $folder ("page-{0:D2}.png" -f $i)), [System.Drawing.Imaging.ImageFormat]::Png)
  $graphics.Dispose(); $bmp.Dispose(); $emf.Dispose(); $stream.Dispose()
  Write-Output "Rendered $i"
 }
 $doc.Close(0)
 Remove-Item $review -Force
} finally { $word.Quit() }
