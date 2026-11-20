#!/usr/bin/env python3
"""Erzeugt anzeige_artdeco.yaml und anzeige_holz.yaml aus anzeige_amiga2.yaml (gleiche Sensoren/Taster),
nur Kopf, Schriften und Display-lambda sind neu."""
import re, sys
D = "/home/claude/esphome-displays/displays/wetterstation/designs/"
src = open(D + "anzeige_amiga2.yaml", encoding="utf-8").read()
i_font = src.index("\nfont:\n") + 1
i_knopf = src.index("# Knopf in Home Assistant")
i_lambda = src.index("        lambda: |-\n") + len("        lambda: |-\n")
rumpf_vor = src[src.index("\nglobals:") + 1:i_font]
rumpf_mitte = src[i_knopf:i_lambda]


def gf(fid, fam, w, size, glyphs=None):
    s = f"  - file:\n      type: gfonts\n      family: {fam}\n      weight: {w}\n    id: {fid}\n    size: {size}\n"
    if glyphs: s += f'    glyphs: "{glyphs}"\n'
    return s


MDI = '''  - file:
      type: web
      url: "https://github.com/Templarian/MaterialDesign-Webfont/raw/master/fonts/materialdesignicons-webfont.ttf"
    id: mdi_icons_klein
    size: 18
    glyphs:
      - "\\U000F058E"  # water-percent
      - "\\U000F029A"  # gauge
      - "\\U000F059D"  # weather-windy
      - "\\U000F05A8"  # white-balance-sunny

'''

# gemeinsamer Teil jeder lambda: Tages-Tiefst/Hoechst und Raumliste
GEMEINSAM = r'''
          auto time = id(sntp_time).now();
          char lbuf[48];
          // ----- Tages-Tiefst/Hoechst (eigene Rechnung, Reset bei Datumswechsel) -----
          bool ta_ok = id(sensor_luxmeter_lux_korrigierte_temperatur).has_state();
          float ta = id(sensor_luxmeter_lux_korrigierte_temperatur).state;
          if (time.is_valid() && time.day_of_month != id(hz_tag)) {
            id(hz_tag) = time.day_of_month;
            id(hz_min) = 1000;
            id(hz_max) = -1000;
          }
          if (ta_ok) {
            if (ta < id(hz_min)) id(hz_min) = ta;
            if (ta > id(hz_max)) id(hz_max) = ta;
          }
          struct Raum { const char *name; sensor::Sensor *t; sensor::Sensor *h; };
          Raum raeume[] = {
            {"Kueche (innen)", id(sensor_thermo_hygrometer_3_temperatur), id(sensor_thermo_hygrometer_3_luftfeuchtigkeit)},
            {"Schlafzimmer oben", id(sensor_thermo_hygrometer_1_temperatur), id(sensor_thermo_hygrometer_1_luftfeuchtigkeit)},
            {"Bad", id(sensor_thermo_hygrometer_4_temperatur), id(sensor_thermo_hygrometer_4_luftfeuchtigkeit)},
            {"Schlafzimmer Mutti", id(sensor_thermo_hygrometer_2_temperatur), id(sensor_thermo_hygrometer_2_luftfeuchtigkeit)},
            {"Werkstatt Ossi", id(sensor_thermo_hygrometer_5_temperatur), id(sensor_thermo_hygrometer_5_luftfeuchtigkeit)},
            {"Heizraum Pumpe", id(sensor_thermo_hygrometer_6_temperatur), id(sensor_thermo_hygrometer_6_luftfeuchtigkeit)},
            {"Retroraum", id(sensor_thermo_hygrometer_7_temperatur), id(sensor_thermo_hygrometer_7_luftfeuchtigkeit)},
          };
          const char *wt[] = {"Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"};
          // Text linksbuendig ueber TOP_RIGHT zeichnen (gleiche Hoehe wie rechtsbuendiger Text)
          auto links = [&](int x, int y, esphome::display::BaseFont *f, Color c, const char *t) {
            int bx, by, bw, bh;
            it.get_text_bounds(x, y, t, f, TextAlign::TOP_LEFT, &bx, &by, &bw, &bh);
            it.print(x + bw, y, f, c, TextAlign::TOP_RIGHT, t);
          };
          // fett: zweimal mit 1 px Versatz (sonst ist die "1" duenner)
          auto fett = [&](int x, int y, esphome::display::BaseFont *f, Color c, TextAlign a, const char *t) {
            it.print(x, y, f, c, a, t);
            it.print(x + 1, y, f, c, a, t);
          };
'''

# ======================================================================================
ARTDECO_FONTS = (gf("ad_temp", "Limelight", 400, 130, "-0123456789") + gf("ad_temp_k", "Limelight", 400, 96, "-0123456789")
    + gf("ad_grad", "Limelight", 400, 40, "°") + gf("fe18", "Federo", 400, 18) + gf("fe14", "Federo", 400, 14)
    + gf("js13", "Josefin Sans", 700, 13) + gf("js15", "Josefin Sans", 700, 15) + gf("js17", "Josefin Sans", 700, 17)
    + gf("js20", "Josefin Sans", 700, 20) + gf("js26", "Josefin Sans", 700, 26) + MDI)

ARTDECO = r'''          // =========== Design "Art deco": Schwarz, Gold, Champagner; Limelight, Federo, Josefin Sans ===========
          const Color SCHWARZ  = Color(0, 0, 0);
          const Color GOLD     = Color(219, 182, 0);     // Linien, Ueberschriften
          const Color DGOLD    = Color(146, 109, 0);     // feine Linien, Faecher
          const Color CHAMP    = Color(255, 219, 85);    // grosse Zahl, Werte
          const Color HELL     = Color(219, 219, 85);    // normale Schrift (ohne Blau, sonst weisslich)
          const Color MATT     = Color(146, 146, 0);     // Unterzeilen
          const Color GRUEN    = Color(73, 182, 0);
          const Color OCKER    = Color(219, 146, 0);
          const Color ROT      = Color(219, 36, 0);
          it.fill(SCHWARZ);
''' + GEMEINSAM + r'''
          auto feuchte_farbe = [&](float h) -> Color {
            if (h >= 70) return ROT;
            if (h >= 60) return OCKER;
            return GRUEN;
          };
          // Raute (Art-deco-Schmuck)
          auto raute = [&](int x, int y, int r, Color c) {
            it.filled_triangle(x - r, y, x, y - r, x + r, y, c);
            it.filled_triangle(x - r, y, x, y + r, x + r, y, c);
          };
          // Trennlinie: doppelt, mit Raute in der Mitte und Titel
          auto trenner = [&](int y, const char *titel) {
            int bx, by, bw, bh;
            it.get_text_bounds(160, y, titel, id(fe14), TextAlign::TOP_CENTER, &bx, &by, &bw, &bh);
            int l = bx - 10, r = bx + bw + 10;
            it.horizontal_line(12, y + 7, l - 12, DGOLD);   it.horizontal_line(12, y + 10, l - 12, GOLD);
            it.horizontal_line(r, y + 7, 308 - r, DGOLD);   it.horizontal_line(r, y + 10, 308 - r, GOLD);
            raute(l - 2, y + 9, 3, GOLD);  raute(r + 1, y + 9, 3, GOLD);
            it.print(160, y, id(fe14), GOLD, TextAlign::TOP_CENTER, titel);
          };
          // Faecher (Sonnenstrahlen) als Halbkreis, oben nach unten (dir=1) oder unten nach oben (dir=-1)
          auto faecher = [&](int cx, int cy, int r, int dir) {
            for (int i = 0; i <= 12; i++) {
              float a = 3.14159f * i / 12.0f;
              it.line(cx, cy, cx + (int) (r * cosf(a)), cy + dir * (int) (r * sinf(a)), i % 2 ? DGOLD : GOLD);
            }
            it.filled_circle(cx, cy, 3, GOLD);
          };

          // ----- Rahmen: zwei Goldlinien mit gestuften Ecken -----
          it.rectangle(0, 0, 320, 480, GOLD);
          it.rectangle(4, 4, 312, 472, DGOLD);
          for (int s = 0; s < 3; s++) {
            int d = 8 + s * 5;
            // gestufte Ecken: kleine Winkel nach innen
            it.horizontal_line(4, d, d - 3, GOLD);  it.vertical_line(d, 4, d - 3, GOLD);
            it.horizontal_line(316 - d + 3, d, d - 3, GOLD);  it.vertical_line(315 - d, 4, d - 3, GOLD);
            it.horizontal_line(4, 475 - d, d - 3, GOLD);  it.vertical_line(d, 476 - d + 3, d - 3, GOLD);
            it.horizontal_line(316 - d + 3, 475 - d, d - 3, GOLD);  it.vertical_line(315 - d, 476 - d + 3, d - 3, GOLD);
          }
          faecher(160, 4, 20, 1);
          faecher(160, 475, 14, -1);

          // ----- Kopf: Datum links, Titel, Uhr rechts -----
          if (time.is_valid()) {
            links(24, 12, id(js15), HELL, wt[(time.day_of_week + 5) % 7]);
            snprintf(lbuf, sizeof(lbuf), "%02d.%02d.%04d", time.day_of_month, time.month, time.year);
            links(24, 29, id(js13), MATT, lbuf);
            snprintf(lbuf, sizeof(lbuf), "%02d:%02d", time.hour, time.minute);
            fett(296, 9, id(js26), CHAMP, TextAlign::TOP_RIGHT, lbuf);
          }
          it.print(160, 30, id(fe14), GOLD, TextAlign::TOP_CENTER, "OSSI'S");
          trenner(44, "WETTERSTATION");

          // ----- Aussen -----
          it.print(16, 64, id(fe14), GOLD, TextAlign::TOP_LEFT, "AUSSEN");
          if (ta_ok) {
            int t = (int) roundf(ta);
            char g[8];
            snprintf(g, sizeof(g), "%d", t);
            esphome::display::BaseFont *f = id(ad_temp);
            int x1, y1, w, h;
            it.get_text_bounds(0, 0, g, f, TextAlign::TOP_LEFT, &x1, &y1, &w, &h);
            if (w > 150) { f = id(ad_temp_k); it.get_text_bounds(0, 0, g, f, TextAlign::TOP_LEFT, &x1, &y1, &w, &h); }
            int x0 = 98 - (w + 26) / 2;
            if (x0 < 12) x0 = 12;
            it.print(x0 + w, 70, f, CHAMP, TextAlign::TOP_RIGHT, g);
            it.print(x0 + w + 2, 84, id(ad_grad), GOLD, TextAlign::TOP_LEFT, "°");
          } else {
            it.print(98, 130, id(js17), ROT, TextAlign::TOP_CENTER, "keine Daten");
          }
          if (id(hz_min) < 999) {
            snprintf(lbuf, sizeof(lbuf), "heute %.1f° bis %.1f°", id(hz_min), id(hz_max));
            it.print(98, 202, id(js13), MATT, TextAlign::TOP_CENTER, lbuf);
          }
          // senkrechte Doppellinie mit Raute
          it.vertical_line(192, 70, 140, DGOLD);  it.vertical_line(195, 70, 140, GOLD);
          raute(194, 140, 4, GOLD);
          auto wert = [&](int nr, const char *symbol, bool ok, Color wf, const char *text) {
            int y = 70 + nr * 35;
            it.print(204, y + 6, id(mdi_icons_klein), GOLD, TextAlign::TOP_LEFT, symbol);
            if (ok) { int bx, by, bw, bh; it.get_text_bounds(228, y + 7, text, id(js17), TextAlign::TOP_LEFT, &bx, &by, &bw, &bh);
                      fett(228 + bw, y + 7, id(js17), wf, TextAlign::TOP_RIGHT, text); }
            else it.print(228, y + 7, id(js17), ROT, TextAlign::TOP_LEFT, "--");
          };
          char buf[16];
          snprintf(buf, sizeof(buf), "%.0f %%", id(sensor_luxmeter_aussen_luftfeuchtigkeit).state);
          wert(0, "\U000F058E", id(sensor_luxmeter_aussen_luftfeuchtigkeit).has_state(), HELL, buf);
          float druck = id(sensor_luxmeter_aussen_luftdruck).state;
          snprintf(buf, sizeof(buf), "%d hPa", (int) druck);
          wert(1, "\U000F029A", id(sensor_luxmeter_aussen_luftdruck).has_state(), druck < 1000 ? OCKER : (druck > 1030 ? ROT : HELL), buf);
          snprintf(buf, sizeof(buf), "%.1f km/h", id(wind_speed_kmh).state);
          wert(2, "\U000F059D", id(wind_speed_kmh).has_state(), HELL, buf);
          snprintf(buf, sizeof(buf), "%.1f lx", id(aussenfuhler_umgebungslicht).state);
          wert(3, "\U000F05A8", id(aussenfuhler_umgebungslicht).has_state(), HELL, buf);

          // ----- Raumklima -----
          trenner(214, "RAUMKLIMA");
          it.print(236, 232, id(js13), MATT, TextAlign::TOP_RIGHT, "Temp");
          it.print(304, 232, id(js13), MATT, TextAlign::TOP_RIGHT, "Feuchte");
          for (int i = 0; i < 7; i++) {
            int y = 248 + i * 18;
            Color nf = i == 0 ? GOLD : HELL;
            int bx, by, bw, bh;
            it.get_text_bounds(16, y, raeume[i].name, id(js15), TextAlign::TOP_LEFT, &bx, &by, &bw, &bh);
            it.print(16 + bw, y, id(js15), nf, TextAlign::TOP_RIGHT, raeume[i].name);
            if (raeume[i].t->has_state()) { snprintf(lbuf, sizeof(lbuf), "%.1f°C", raeume[i].t->state); fett(235, y, id(js15), CHAMP, TextAlign::TOP_RIGHT, lbuf); }
            else it.print(236, y, id(js15), ROT, TextAlign::TOP_RIGHT, "--");
            if (raeume[i].h->has_state()) {
              float h = raeume[i].h->state;
              snprintf(lbuf, sizeof(lbuf), "%.0f%%", h);
              fett(289, y, id(js15), feuchte_farbe(h), TextAlign::TOP_RIGHT, lbuf);
              raute(299, y + 7, 4, feuchte_farbe(h));
            } else it.print(290, y, id(js15), ROT, TextAlign::TOP_RIGHT, "--");
          }

          // ----- Strom Kueche -----
          trenner(376, "STROM KUECHE");
          if (id(sensor_kuchl_steckdose_switch_0_voltage).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.1f V", id(sensor_kuchl_steckdose_switch_0_voltage).state);
            int bx, by, bw, bh; it.get_text_bounds(16, 394, lbuf, id(js17), TextAlign::TOP_LEFT, &bx, &by, &bw, &bh);
            fett(16 + bw, 394, id(js17), CHAMP, TextAlign::TOP_RIGHT, lbuf);
          }
          if (id(sensor_kuchl_steckdose_switch_0_current).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.2f A", id(sensor_kuchl_steckdose_switch_0_current).state);
            fett(160, 394, id(js17), HELL, TextAlign::TOP_CENTER, lbuf);
          }
          if (id(sensor_kuchl_steckdose_switch_0_power).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.1f W", id(sensor_kuchl_steckdose_switch_0_power).state);
            fett(303, 394, id(js17), HELL, TextAlign::TOP_RIGHT, lbuf);
          }
          if (id(sensor_shellyplusplugs_e465b8b6b9e0_switch_0_power).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "Server %.0f W", id(sensor_shellyplusplugs_e465b8b6b9e0_switch_0_power).state);
            it.print(160, 412, id(js13), MATT, TextAlign::TOP_CENTER, lbuf);
          }

          // ----- Bitcoin -----
          it.horizontal_line(12, 422, 296, DGOLD);
          it.horizontal_line(12, 425, 296, GOLD);
          it.print(26, 430, id(fe18), GOLD, TextAlign::TOP_LEFT, "BITCOIN");
          it.print(26, 448, id(js13), MATT, TextAlign::TOP_LEFT, "Kurs in Euro");
          if (id(bitcoin_preis).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.0f EUR", id(bitcoin_preis).state);
            fett(296, 429, id(js26), CHAMP, TextAlign::TOP_RIGHT, lbuf);
          }
          // Build-Nummer oben unter der Uhr (unten lag sie auf dem Geraet ueber der Ecke)
          it.printf(296, 33, id(js13), DGOLD, TextAlign::TOP_RIGHT, "Build %s", ESPHOME_PROJECT_VERSION);
'''

# ======================================================================================
HOLZ_FONTS = (gf("hm_temp", "Playfair Display", 900, 48, "-0123456789") + gf("hm_titel", "Cinzel", 700, 15)
    + gf("hm_label", "Cinzel", 700, 13) + gf("rs11", "Roboto Slab", 600, 11) + gf("rs14", "Roboto Slab", 800, 14)
    + gf("rs16", "Roboto Slab", 700, 16) + gf("rs20", "Roboto Slab", 700, 20) + gf("rs24", "Roboto Slab", 800, 24) + MDI)

HOLZ = r'''          // =========== Design "Holz und Messing": alte Wetterstation, Nussholz, Messingschilder, Zeigerinstrument ===========
          const Color HOLZ     = Color(73, 36, 0);       // dunkles Nussholz
          const Color MASER    = Color(109, 36, 0);      // Holzmaserung
          const Color DUNKEL   = Color(36, 0, 0);        // Fugen, Gravur
          const Color MESSING  = Color(182, 146, 0);     // Schilder
          const Color MESS_H   = Color(219, 182, 0);     // Messing-Glanzkante
          const Color MESS_D   = Color(109, 73, 0);      // Messing-Schattenkante
          const Color CREME    = Color(219, 219, 85);    // Zifferblatt, Schrift auf Holz
          const Color GRAVUR   = Color(36, 36, 0);       // Schrift auf Messing (eingraviert)
          const Color ZEIGER   = Color(182, 0, 0);
          const Color GRUEN    = Color(0, 109, 0);
          const Color OCKER    = Color(146, 73, 0);
          const Color ROT      = Color(182, 0, 0);
          it.fill(HOLZ);
''' + GEMEINSAM + r'''
          auto feuchte_farbe = [&](float h) -> Color {
            if (h >= 70) return ROT;
            if (h >= 60) return OCKER;
            return GRUEN;
          };
          // Holzmaserung: ein paar leicht wellige Linien
          for (int i = 0; i < 16; i++) {
            int y0 = 12 + i * 30 + (i % 3) * 4;
            for (int x = 0; x < 320; x += 8) {
              int dy = ((x / 8 + i) % 5 == 0) ? 1 : 0;
              it.horizontal_line(x, y0 + dy, 8, MASER);
            }
          }
          // Niete
          auto niet = [&](int x, int y) {
            it.filled_circle(x, y, 3, MESS_D);
            it.filled_circle(x, y, 2, MESS_H);
            it.draw_pixel_at(x - 1, y - 1, CREME);
          };
          // Messingschild mit Glanz- und Schattenkante und vier Nieten
          auto schild = [&](int x, int y, int w, int h) {
            it.filled_rectangle(x + 2, y + 2, w, h, DUNKEL);            // Schatten aufs Holz
            it.filled_rectangle(x, y, w, h, MESSING);
            it.horizontal_line(x, y, w, MESS_H);  it.vertical_line(x, y, h, MESS_H);
            it.horizontal_line(x, y + h - 1, w, MESS_D);  it.vertical_line(x + w - 1, y, h, MESS_D);
            niet(x + 6, y + 6);  niet(x + w - 7, y + 6);  niet(x + 6, y + h - 7);  niet(x + w - 7, y + h - 7);
          };

          // ----- Kopf: Datum und Uhr auf Holz, Namensschild in der Mitte -----
          if (time.is_valid()) {
            links(10, 6, id(rs14), CREME, wt[(time.day_of_week + 5) % 7]);
            snprintf(lbuf, sizeof(lbuf), "%02d.%02d.", time.day_of_month, time.month);
            links(10, 23, id(rs14), CREME, lbuf);
            snprintf(lbuf, sizeof(lbuf), "%02d:%02d", time.hour, time.minute);
            fett(309, 9, id(rs24), CREME, TextAlign::TOP_RIGHT, lbuf);
          }
          schild(78, 5, 164, 36);
          it.print(160, 9, id(hm_label), GRAVUR, TextAlign::TOP_CENTER, "OSSI'S");
          it.print(160, 21, id(hm_titel), GRAVUR, TextAlign::TOP_CENTER, "WETTERSTATION");

          // ----- Thermometer als Zeigerinstrument (-20 bis +40 Grad) -----
          const int cx = 90, cy = 128, r = 70;
          it.filled_circle(cx + 2, cy + 3, r + 7, DUNKEL);
          it.filled_circle(cx, cy, r + 7, MESS_D);
          it.filled_circle(cx, cy, r + 5, MESSING);
          it.circle(cx, cy, r + 3, MESS_H);
          it.filled_circle(cx, cy, r, CREME);
          // Skala: 270 Grad Bogen, -20 unten links, +40 unten rechts
          for (int v = -20; v <= 40; v += 5) {
            float a = (135.0f + (v + 20) * 270.0f / 60.0f) * 3.14159f / 180.0f;
            int l = (v % 10 == 0) ? 9 : 5;
            float ca = cosf(a), sa = sinf(a);
            it.line(cx + (int) ((r - 2) * ca), cy + (int) ((r - 2) * sa), cx + (int) ((r - 2 - l) * ca), cy + (int) ((r - 2 - l) * sa), GRAVUR);
            if (v % 20 == 0) {
              snprintf(lbuf, sizeof(lbuf), "%d", v);
              it.print(cx + (int) ((r - 20) * ca), cy + (int) ((r - 20) * sa) - 6, id(rs11), GRAVUR, TextAlign::TOP_CENTER, lbuf);
            }
          }
          // Frostbereich unter 0 blau-grau ist am Display zu grell, deshalb nur ein roter Bogen ab 30 Grad
          for (int v = 30; v <= 40; v++) {
            float a = (135.0f + (v + 20) * 270.0f / 60.0f) * 3.14159f / 180.0f;
            it.draw_pixel_at(cx + (int) ((r - 3) * cosf(a)), cy + (int) ((r - 3) * sinf(a)), ROT);
            it.draw_pixel_at(cx + (int) ((r - 4) * cosf(a)), cy + (int) ((r - 4) * sinf(a)), ROT);
          }
          if (ta_ok) {
            float v = ta < -20 ? -20 : (ta > 40 ? 40 : ta);
            float a = (135.0f + (v + 20) * 270.0f / 60.0f) * 3.14159f / 180.0f;
            int zx = cx + (int) ((r - 12) * cosf(a)), zy = cy + (int) ((r - 12) * sinf(a));
            it.line(cx, cy, zx, zy, ZEIGER);  it.line(cx + 1, cy, zx + 1, zy, ZEIGER);  it.line(cx, cy + 1, zx, zy + 1, ZEIGER);
            it.filled_circle(cx, cy, 5, MESS_D);
            it.filled_circle(cx, cy, 3, MESSING);
            // Zahl an der Grundlinie ausrichten (auf dem Geraet sonst tiefer als in der Vorschau), Grad-Kringel selbst zeichnen
            snprintf(lbuf, sizeof(lbuf), "%d", (int) roundf(ta));
            int bx, by, bw, bh;
            it.get_text_bounds(cx, cy + 52, lbuf, id(hm_temp), TextAlign::BASELINE_CENTER, &bx, &by, &bw, &bh);
            it.print(cx, cy + 52, id(hm_temp), GRAVUR, TextAlign::BASELINE_CENTER, lbuf);
            it.circle(bx + bw + 6, cy + 18, 4, GRAVUR);
            it.circle(bx + bw + 6, cy + 18, 3, GRAVUR);
          } else {
            it.print(cx, cy + 20, id(rs16), ROT, TextAlign::TOP_CENTER, "keine Daten");
          }
          if (id(hz_min) < 999) {
            snprintf(lbuf, sizeof(lbuf), "heute %.1f° bis %.1f°", id(hz_min), id(hz_max));
            it.print(cx, 208, id(rs14), CREME, TextAlign::TOP_CENTER, lbuf);
          }

          // ----- Aussenwerte rechts auf kleinen Schildern -----
          auto wert = [&](int nr, const char *symbol, bool ok, Color wf, const char *text) {
            int y = 50 + nr * 41;
            schild(178, y, 134, 34);
            it.print(190, y + 8, id(mdi_icons_klein), GRAVUR, TextAlign::TOP_LEFT, symbol);
            if (ok) { int bx, by, bw, bh; it.get_text_bounds(212, y + 8, text, id(rs16), TextAlign::TOP_LEFT, &bx, &by, &bw, &bh);
                      it.print(212 + bw, y + 8, id(rs16), wf, TextAlign::TOP_RIGHT, text); }
            else it.print(212, y + 8, id(rs16), ROT, TextAlign::TOP_LEFT, "--");
          };
          char buf[16];
          snprintf(buf, sizeof(buf), "%.0f %%", id(sensor_luxmeter_aussen_luftfeuchtigkeit).state);
          wert(0, "\U000F058E", id(sensor_luxmeter_aussen_luftfeuchtigkeit).has_state(), GRAVUR, buf);
          float druck = id(sensor_luxmeter_aussen_luftdruck).state;
          snprintf(buf, sizeof(buf), "%d hPa", (int) druck);
          wert(1, "\U000F029A", id(sensor_luxmeter_aussen_luftdruck).has_state(), druck < 1000 ? OCKER : (druck > 1030 ? ROT : GRAVUR), buf);
          snprintf(buf, sizeof(buf), "%.1f km/h", id(wind_speed_kmh).state);
          wert(2, "\U000F059D", id(wind_speed_kmh).has_state(), GRAVUR, buf);
          snprintf(buf, sizeof(buf), "%.1f lx", id(aussenfuhler_umgebungslicht).state);
          wert(3, "\U000F05A8", id(aussenfuhler_umgebungslicht).has_state(), GRAVUR, buf);

          // ----- Raumklima: grosses Messingschild -----
          schild(8, 228, 304, 152);
          it.print(20, 233, id(hm_label), GRAVUR, TextAlign::TOP_LEFT, "RAUMKLIMA");
          it.print(232, 235, id(rs11), MESS_D, TextAlign::TOP_RIGHT, "Temp");
          it.print(294, 235, id(rs11), MESS_D, TextAlign::TOP_RIGHT, "Feuchte");
          it.horizontal_line(18, 250, 284, MESS_D);
          it.horizontal_line(18, 251, 284, MESS_H);
          for (int i = 0; i < 7; i++) {
            int y = 255 + i * 17;
            Color nf = i == 0 ? ROT : GRAVUR;
            links(20, y, id(rs14), nf, raeume[i].name);
            if (raeume[i].t->has_state()) { snprintf(lbuf, sizeof(lbuf), "%.1f°C", raeume[i].t->state); it.print(232, y, id(rs14), GRAVUR, TextAlign::TOP_RIGHT, lbuf); }
            else it.print(232, y, id(rs14), ROT, TextAlign::TOP_RIGHT, "--");
            if (raeume[i].h->has_state()) {
              float h = raeume[i].h->state;
              snprintf(lbuf, sizeof(lbuf), "%.0f%%", h);
              it.print(286, y, id(rs14), feuchte_farbe(h), TextAlign::TOP_RIGHT, lbuf);
              it.filled_circle(295, y + 8, 4, MESS_D);
              it.filled_circle(295, y + 8, 3, feuchte_farbe(h));
            } else it.print(286, y, id(rs14), ROT, TextAlign::TOP_RIGHT, "--");
          }

          // ----- Strom Kueche und Bitcoin auf Holz, getrennt durch eine Messingleiste -----
          it.filled_rectangle(8, 389, 304, 3, MESSING);
          it.horizontal_line(8, 389, 304, MESS_H);
          it.print(10, 396, id(hm_label), MESS_H, TextAlign::TOP_LEFT, "STROM KUECHE");
          if (id(sensor_shellyplusplugs_e465b8b6b9e0_switch_0_power).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "Server %.0f W", id(sensor_shellyplusplugs_e465b8b6b9e0_switch_0_power).state);
            it.print(310, 397, id(rs14), CREME, TextAlign::TOP_RIGHT, lbuf);
          }
          if (id(sensor_kuchl_steckdose_switch_0_voltage).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.1f V", id(sensor_kuchl_steckdose_switch_0_voltage).state);
            links(10, 414, id(rs16), CREME, lbuf);
          }
          if (id(sensor_kuchl_steckdose_switch_0_current).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.2f A", id(sensor_kuchl_steckdose_switch_0_current).state);
            it.print(160, 414, id(rs16), CREME, TextAlign::TOP_CENTER, lbuf);
          }
          if (id(sensor_kuchl_steckdose_switch_0_power).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.1f W", id(sensor_kuchl_steckdose_switch_0_power).state);
            it.print(310, 414, id(rs16), CREME, TextAlign::TOP_RIGHT, lbuf);
          }
          it.filled_rectangle(8, 436, 304, 3, MESSING);
          it.horizontal_line(8, 436, 304, MESS_H);
          it.print(10, 446, id(hm_label), MESS_H, TextAlign::TOP_LEFT, "BITCOIN");
          it.printf(10, 462, id(rs11), MESS_H, TextAlign::TOP_LEFT, "Build %s", ESPHOME_PROJECT_VERSION);
          if (id(bitcoin_preis).has_state()) {
            snprintf(lbuf, sizeof(lbuf), "%.0f EUR", id(bitcoin_preis).state);
            fett(309, 444, id(rs24), CREME, TextAlign::TOP_RIGHT, lbuf);
          }
'''


def schreibe(name, titel, beschreibung, fonts, lam):
    kopf = f'''# =====================================================================
#  Wetterstation by Ossi - Anzeige-Teil (Package fuer ESPHome)
#  DESIGN "{titel}" (Entwurf, 20.11.2026): {beschreibung}
#  Wird von der Geraete-YAML per "packages:" geholt (Auswahl ueber design.txt / App HA-Displays).
#  Hier stehen: Zeit, Schriften, Taster, LEDs, Sensoren aus Home Assistant
#  und die Display-Zeichnung. KEINE Passwoerter/Schluessel (Repo oeffentlich).
# =====================================================================

'''
    text = kopf + rumpf_vor + "font:\n" + fonts + rumpf_mitte + lam
    open(D + f"anzeige_{name}.yaml", "w", encoding="utf-8").write(text)


schreibe("artdeco", "Art deco", "Schwarz, Gold, Champagner; Limelight, Federo, Josefin Sans; Faecher, gestufte Ecken",
         ARTDECO_FONTS, ARTDECO)
schreibe("holz", "Holz und Messing", "alte Wetterstation: Nussholz, Messingschilder mit Nieten, Zeiger-Thermometer; Playfair, Cinzel, Roboto Slab",
         HOLZ_FONTS, HOLZ)
print("ok")
