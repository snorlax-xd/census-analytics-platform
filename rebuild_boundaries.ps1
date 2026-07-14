# rebuild_boundaries.ps1
#
# Regenerates the India state/UT boundary files from scratch: dissolves
# districts -> state polygons (Python/Shapely), simplifies + converts
# format (mapshaper), then re-corrects ring winding that mapshaper
# normalizes away (Python/Shapely again). Four manual steps, one command.
#
# Run from the repo root:
#   .\rebuild_boundaries.ps1
#
# Stops immediately on any step's failure instead of silently continuing
# with a stale or partial file — each step is checked explicitly rather
# than relying on $ErrorActionPreference alone, since external tools
# (mapshaper, python.exe) don't always set PowerShell's $LASTEXITCODE
# reliably on failure.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($name, $scriptblock) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    & $scriptblock
    if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
        Write-Host "FAILED: $name (exit code $LASTEXITCODE). Stopping." -ForegroundColor Red
        exit 1
    }
}

Step "1/4 Dissolve districts into state boundaries" {
    .\Backend\.venv\Scripts\python.exe Backend\scripts\prepare_boundaries.py --write
}

Step "2/4 Simplify + convert (national view)" {
    mapshaper "Backend\scripts\_boundary_work\india_states_2011.geojson" -simplify 10% -o "Frontend\src\assets\india-simplified.json" format=geojson
}

Step "3/4 Convert full detail (focused state view)" {
    mapshaper "Backend\scripts\_boundary_work\india_states_2011.geojson" -o "Frontend\src\assets\india-full-detail.json" format=geojson
}

Step "4/4 Re-fix ring winding (mapshaper normalizes it away)" {
    .\Backend\.venv\Scripts\python.exe Backend\scripts\fix_winding_post_mapshaper.py
}

Write-Host "`nDone. Reload /tab1 (hard refresh) and confirm the map renders correctly before committing." -ForegroundColor Green