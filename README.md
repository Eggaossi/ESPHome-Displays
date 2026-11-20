# Wetterstation by Ossi

ESPHome-Display (ESP32-S3, ST7796 320x480, 8-Bit-Farben) im lila Gehaeuse.
Zeigt Werte aus Home Assistant: Aussentemperatur gross, Aussenwerte, Innenwerte
(Kueche), Raumklima von 6 Raeumen, Strom Kueche, Server-Watt, Bitcoin.

## Aufbau

- `esphome/anzeige.yaml` - Package mit Zeit, Schriften, Tastern, LEDs,
  Sensoren und der Display-Zeichnung. Hier wird geaendert.
- `esphome/geraet-vorlage.yaml` - Vorlage der Geraete-YAML im ESPHome Builder
  (echte Schluessel stehen nur in Home Assistant).
- `alt/` - fruehere Fassungen (Schluessel entfernt).

## Aktualisieren

ESPHome Builder -> Wetterstation-Display -> Installieren -> Wirelessly.
ESPHome holt `esphome/anzeige.yaml` bei jedem Kompilieren neu (`refresh: 0s`).
