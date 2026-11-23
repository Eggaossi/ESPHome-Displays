# Werkstatt-Zentrale einmalig auf das Selbst-Update umstellen (23.11.2026), wie tools\luxmeter_uebernahme.ps1.
# Sucht im ESPHome Builder (\\192.168.178.14\config\esphome) die YAML mit "name: werkstatt-zentrale-by-ossi" und
# ergaenzt sie NUR um das Selbst-Update (ota http_request, http_request, update mit Manifest aus dem Zweig firmware).
# Altes OTA-Passwort und API-Schluessel bleiben, damit "Installieren" im ESPHome Builder noch klappt. Danach holt sich
# das Geraet die GitHub-Fassung (gemeinsames OTA-Passwort, neuer API-Schluessel) selbst.
# Sicherung vorher nach C:\Backups. Aufruf: pwsh -File tools\werkstatt_zentrale_uebernahme.ps1
$ordner = '\\192.168.178.14\config\esphome'
if (-not (Test-Path $ordner)) { "FEHLER: $ordner nicht erreichbar"; exit 1 }
$f = Get-ChildItem $ordner -Filter *.yaml -File | Where-Object { (Get-Content $_.FullName -Raw) -match '(?m)^\s+name:\s*werkstatt-zentrale-by-ossi\s*$' }
if (@($f).Count -ne 1) { "FEHLER: $(@($f).Count) Dateien mit name: werkstatt-zentrale-by-ossi gefunden: $($f.Name -join ', ')"; exit 1 }
$f = $f[0].FullName
"Datei: $f"
$t = [IO.File]::ReadAllText($f) -replace "`r`n", "`n"
if ($t -match 'platform: http_request') { "Schon umgestellt - nichts geaendert"; exit 0 }
$s = "C:\Backups\werkstatt-zentrale_$(Get-Date -Format 'yyyy-MM-dd_HH-mm').yaml"
Copy-Item $f $s
$neu = [regex]::new('(?m)^(ota:\n(?:[ \t]+.*\n)*?[ \t]+password:[^\n]*\n)').Replace($t, "`$1  - platform: http_request`n", 1)
if ($neu -eq $t) { "FEHLER: ota-Block nicht gefunden - nichts geaendert (Sicherung $s)"; exit 1 }
$neu = $neu.TrimEnd("`n") + "`n`n# Selbst-Update von GitHub (Repo ESPHome-Displays), Uebernahme 23.11.2026`n" +
  "http_request:`n  verify_ssl: false`n  timeout: 30s`n`n" +
  "update:`n  - platform: http_request`n    id: fw_update`n    name: Firmware GitHub`n" +
  "    source: https://raw.githubusercontent.com/Eggaossi/ESPHome-Displays/firmware/werkstatt-zentrale/manifest.json`n" +
  "    update_interval: 30s`n    on_update_available:`n      then:`n        - update.perform: fw_update`n"
[IO.File]::WriteAllText($f, $neu, (New-Object Text.UTF8Encoding $false))
"OK: $(Split-Path $f -Leaf) ergaenzt (Sicherung $s). Jetzt im ESPHome Builder bei der Werkstatt-Zentrale: Installieren > Drahtlos."
