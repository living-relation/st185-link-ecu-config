# Data feed for the ST185 live dashboard (Cowork artifact). Prints one JSON line prefixed with ##JSON##.
$ErrorActionPreference = 'SilentlyContinue'
$r = 'C:\projects\active\st185-link-ecu-config'
$L = @()
function Add($g, $f, $base) {
  $script:L += [pscustomobject]@{ g = $g; p = $f.FullName; n = $(if ($base) { $f.FullName.Substring($base.Length + 1) } else { $f.Name }); t = $f.LastWriteTime.ToString('s') }
}
# Every ST185 file lives inside the project folder (DECISIONS R67); heavy CAD sits untracked beside its design
Get-ChildItem "$r\docs\research" -File -Filter *.html | ForEach-Object { Add 'Research & picks' $_ $null }
foreach ($d in 'cad') {
  Get-ChildItem "$r\$d" -Recurse -File -Include *.html, *.pdf, *.f3d | ForEach-Object { Add 'CAD' $_ $r }
}
Get-ChildItem "$r\docs\harness\routes" -File -Filter ROUTE-*.html | Where-Object { $_.Name -notmatch '-rev\d' } | ForEach-Object { Add 'Routes (approved)' $_ $null }
Get-ChildItem "$r\docs\harness\rebuild" -File -Recurse -Include *.harness, *.harnesslib | ForEach-Object { Add 'Harness drawings' $_ $null }
foreach ($f in 'docs\research-hub.html', 'docs\OPEN-ITEMS.md', 'docs\harness\redesign\DECISIONS.md', 'docs\electrical\ENGINE-ROOM-POWER-REDISTRIBUTION.md') {
  $i = Get-Item "$r\$f"; if ($i) { Add 'Plans & decisions' $i $null }
}
# Open tracker rows owned by Daniel
$rows = @()
Get-Content "$r\docs\OPEN-ITEMS.md" | Where-Object { $_ -match '^\|\s*[A-Z]?[0-9-]+\s*\|' } | ForEach-Object {
  $c = $_.Split('|') | ForEach-Object { $_.Trim() }
  if ($c.Count -gt 6 -and $c[4] -match 'Daniel' -and $c[-3] -notmatch '^(Closed|Done)') {
    $rows += [pscustomobject]@{ id = $c[1]; area = $c[2]; text = $c[3]; status = $c[-3] }
  }
}
$head = (git -C $r log -1 --format='%h %cd' --date=format:'%Y-%m-%d %H:%M' 2>$null)
'##JSON##' + (@{ files = $L; rows = $rows; head = $head; now = (Get-Date).ToString('s') } | ConvertTo-Json -Depth 4 -Compress)
