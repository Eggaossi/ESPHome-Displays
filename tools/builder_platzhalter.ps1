# Alte Geraete-Dateien im ESPHome Builder durch einen Platzhalter ersetzen (23.11.2026).
# Nach der Uebernahme baut GitHub die Firmware (Repo ESPHome-Displays), die Builder-Datei wird nicht mehr gebraucht.
# Sie enthaelt aber noch den ALTEN API-Schluessel und das ALTE OTA-Passwort; "Installieren" im Builder wuerde das
# Geraet darauf zurueckstellen. Der Platzhalter hat nur Name + friendly_name (der Builder zeigt das Geraet weiter
# als online), ohne Board -> Installieren ist nicht moeglich.
# Nur Dateien, die schon umgestellt sind (enthalten "platform: http_request" bzw. das Manifest aus dem Repo).
# Sicherung jeder Datei vorher nach C:\Backups. Aufruf: pwsh -File tools\builder_platzhalter.ps1
$ordner = '\\192.168.178.14\config\esphome'
if (-not (Test-Path $ordner)) { "FEHLER: $ordner nicht erreichbar"; exit 1 }
$geraete = @(
  @{ name = 'werkstatt-zentrale-by-ossi'; anzeige = 'Werkstatt-Zentrale by Ossi'; ordner = 'werkstatt-zentrale' },
  @{ name = 'luxmeter';                   anzeige = 'Luxmeter';                   ordner = 'luxmeter' }
)
$zeit = Get-Date -Format 'yyyy-MM-dd_HH-mm'
foreach ($g in $geraete) {
  $f = @(Get-ChildItem $ordner -Filter *.yaml -File | Where-Object { (Get-Content $_.FullName -Raw) -match "(?m)^\s+name:\s*$([regex]::Escape($g.name))\s*$" })
  if ($f.Count -ne 1) { "{0,-28} UEBERSPRUNGEN: {1} Dateien gefunden {2}" -f $g.name, $f.Count, ($f.Name -join ', '); continue }
  $f = $f[0].FullName
  $t = [IO.File]::ReadAllText($f)
  if ($t -match 'PLATZHALTER') { "{0,-28} schon Platzhalter ({1})" -f $g.name, (Split-Path $f -Leaf); continue }
  if ($t -notmatch "ESPHome-Displays/firmware/$($g.ordner)/manifest.json") { "{0,-28} UEBERSPRUNGEN: noch nicht auf Selbst-Update umgestellt ({1})" -f $g.name, (Split-Path $f -Leaf); continue }
  $s = "C:\Backups\builder_$($g.ordner)_$zeit.yaml"
  Copy-Item $f $s
  $neu = "# PLATZHALTER (23.11.2026) - NICHT hier installieren!`n" +
    "# Dieses Geraet wird von GitHub gebaut (Repo Eggaossi/ESPHome-Displays, Ordner displays/$($g.ordner))`n" +
    "# und holt sich neue Firmware selbst. Aenderungen nur dort. Alte Fassung: $s`n" +
    "esphome:`n  name: $($g.name)`n  friendly_name: $($g.anzeige)`n"
  [IO.File]::WriteAllText($f, $neu, (New-Object Text.UTF8Encoding $false))
  "{0,-28} OK: {1} ersetzt (Sicherung {2})" -f $g.name, (Split-Path $f -Leaf), $s
}
