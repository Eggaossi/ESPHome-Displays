# ESPHome-Displays (by Ossi)

Alle ESPHome-Displays von Home Assistant an einem Ort. Ein Ordner je Display
unter `displays/`. GitHub baut bei jeder Aenderung die Firmware, das Display
holt sie sich selbst (Selbst-Update, prueft alle 30 s) - kein "Installieren" noetig.
(22.11.2026 kurz auf "nur pruefen, in HA installieren" umgestellt, am 23.11.2026 auf Wunsch des Nutzers zurueck.)

## Aufbau je Display (`displays/<name>/`)
- `<name>.yaml` - Geraete-Datei (Board, WLAN, Selbst-Update, Schluessel aus Secrets)
- `anzeige.yaml` - AKTIVES Design (wird aus `designs/` erzeugt)
- `designs/` - gespeicherte Designs mit Vorschau
- `alt/` - fruehere Fassungen
- `<Name>-KI_Info.txt` - Projektbeschreibung fuer die KI

## Design wechseln
`python3 tools/design_aktivieren.py displays/<name> designs/anzeige_<design>.yaml`
(raeumt unbenutzte Schriften weg), committen, pushen. Fertig.

## Firmware
Zweig `firmware`: `<name>/firmware.ota.bin`, `manifest.json`, `version.txt`,
bei Fehlern `fehler.txt` und `build.log`.

## GitHub-Secrets (Settings -> Secrets and variables -> Actions)
`WIFI_SSID`, `WIFI_PASSWORD`, `OTA_PASSWORD`, je Display ein API-Schluessel
(`WETTERSTATION_API_KEY`, `RAUMLUFT_STUBE_API_KEY`), `FONTS_KEY` fuer die eigenen Schriften.

## Displays
- `wetterstation` - Wetterstation (ST7796 320x480)
- `raumluft-stube` - CO-Melder, CO2, Temperatur, Feuchte in der Stube (ST7789V quer 320x240), HA-Geraet `co-ossi-stube`
