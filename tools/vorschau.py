#!/usr/bin/env python3
"""
Vorschaubild eines ESPHome-Designs zeichnen, aus genau dem Display-Code (lambda), der aufs Geraet geht.

Aufruf:  python3 tools/vorschau.py <design.yaml> <ausgabe.png> [--cache <ordner>]

So geht es:
  1. Die Display-lambda (erste Seite) wird mit einer kleinen Nachbildung von ESPHome (it.print, printf,
     filled_rectangle, filled_circle, ...) als normales C++-Programm uebersetzt (g++) und ausgefuehrt.
  2. Das Programm schreibt eine Liste der Zeichenbefehle; Python zeichnet sie mit Pillow (Groesse aus
     model/rotation bzw. dimensions des Displays, z.B. ST7796 320x480, ST7789V quer 320x240).
  3. Schriften wie auf dem Geraet: 1-Bit (ohne Kantenglaettung), gleiche Groesse und Staerke.
     Google-Schriften kommen aus dem Repo google/fonts, MDI-Symbole aus Templarian/MaterialDesign-Webfont,
     eigene Schriften (/config/esphome/fonts/X.ttf) aus fonts/X.ttf im Repo, falls vorhanden.
  4. Farben werden auf die 8-Bit-Palette des Displays (3-3-2) gerundet.
Werte (Temperaturen usw.) sind feste Beispielwerte, die Uhr steht auf Fr 20.11.2026 11:30.
"""
import os, re, sys, subprocess, tempfile, urllib.request, hashlib
import yaml
from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
B, H = 320, 480   # wird in main() aus der Display-Konfiguration gesetzt

# Grundgroesse (Breite x Hoehe bei rotation 0) der ili9xxx-Modelle
MODELLE = {"st7796": (320, 480), "ili9488": (320, 480), "ili9486": (320, 480), "st7789v": (240, 320),
           "ili9341": (240, 320), "ili9342": (320, 240), "ili9481": (320, 480)}

GFONTS = {
    "roboto": "ofl/roboto/Roboto%5Bwdth,wght%5D.ttf",
    "roboto condensed": "ofl/robotocondensed/RobotoCondensed%5Bwght%5D.ttf",
    "anton": "ofl/anton/Anton-Regular.ttf",
    "vt323": "ofl/vt323/VT323-Regular.ttf",
    "rubik": "ofl/rubik/Rubik%5Bwght%5D.ttf",
    "limelight": "ofl/limelight/Limelight-Regular.ttf",
    "federo": "ofl/federo/Federo-Regular.ttf",
    "poiret one": "ofl/poiretone/PoiretOne-Regular.ttf",
    "josefin sans": "ofl/josefinsans/JosefinSans%5Bwght%5D.ttf",
    "playfair display": "ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "roboto slab": "apache/robotoslab/RobotoSlab%5Bwght%5D.ttf",
    "cinzel": "ofl/cinzel/Cinzel%5Bwght%5D.ttf",
}
GF_URL = "https://raw.githubusercontent.com/google/fonts/main/"


# ---------- YAML lesen (ESPHome-Tags wie !secret / !lambda einfach durchlassen) ----------
class Lader(yaml.SafeLoader):
    pass
def _tag(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode): return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode): return loader.construct_sequence(node)
    return loader.construct_mapping(node)
Lader.add_multi_constructor("!", _tag)


def laden(url, cache):
    os.makedirs(cache, exist_ok=True)
    ziel = os.path.join(cache, hashlib.md5(url.encode()).hexdigest() + ".ttf")
    if not os.path.exists(ziel):
        with urllib.request.urlopen(url, timeout=60) as r, open(ziel + ".tmp", "wb") as f:
            f.write(r.read())
        os.replace(ziel + ".tmp", ziel)
    return ziel


def schrift(eintrag, cache):
    """Pillow-Schrift fuer einen font:-Eintrag (oder None)."""
    f = eintrag.get("file")
    size = int(eintrag.get("size", 20))
    weight = 400
    pfad = None
    if isinstance(f, dict):
        typ = str(f.get("type", "")).lower()
        if typ == "gfonts":
            fam = str(f.get("family", "")).lower()
            weight = int(f.get("weight", 400) or 400)
            if fam in GFONTS: pfad = laden(GF_URL + GFONTS[fam], cache)
        elif typ == "web":
            url = str(f.get("url", ""))
            url = re.sub(r"https://github\.com/([^/]+)/([^/]+)/raw/", r"https://raw.githubusercontent.com/\1/\2/", url)
            pfad = laden(url, cache)
        elif typ == "local":
            f = f.get("path")
    if isinstance(f, str):
        if f.startswith("gfonts://"):
            teile = f[9:].split("@")
            fam = teile[0].lower()
            if len(teile) > 1:
                w = teile[1].lower()
                weight = {"thin": 100, "light": 300, "regular": 400, "medium": 500, "bold": 700, "black": 900}.get(w, int(w) if w.isdigit() else 400)
            if fam in GFONTS: pfad = laden(GF_URL + GFONTS[fam], cache)
        else:
            lokal = os.path.join(REPO, "fonts", os.path.basename(f))
            if os.path.exists(lokal): pfad = lokal
    if pfad is None:
        return None
    font = ImageFont.truetype(pfad, size)
    try:
        achsen = font.get_variation_axes()
        werte = []
        for a in achsen:
            name = a.get("name", b"")
            name = name.decode() if isinstance(name, bytes) else str(name)
            if name.lower().startswith("weight"):
                werte.append(max(a["minimum"], min(a["maximum"], weight)))
            else:
                werte.append(a.get("default", a["minimum"]))
        if achsen: font.set_variation_by_axes(werte)
    except Exception:
        pass
    return font


def beispiel(name):
    """Beispielwert eines Sensors aus seinem Namen."""
    n = name.lower()
    if "korrigierte_temperatur" in n or (("aussen" in n or "outside" in n) and "temp" in n): return 1.6
    if "co2" in n: return 650
    if "co_raw" in n: return 0.38
    if n.startswith("co_") or n == "co": return 2.4
    if "humidity" in n: return 47
    # Raeume: je Sensor etwas anders, aber immer gleich (aus dem Namen gerechnet)
    h = int(hashlib.md5(n.encode()).hexdigest(), 16)
    if "temperatur" in n or n.endswith("_temp"): return round(14 + (h % 70) / 10, 1)
    if "feucht" in n: return 48 + h % 26
    if "druck" in n: return 910
    if "wind" in n: return 3.2
    if "licht" in n or "lux" in n or "helligkeit" in n: return 310.8
    if "voltage" in n or "spannung" in n: return 229.4
    if "current" in n or "strom" in n: return 0.12
    if "power" in n or "leistung" in n: return 22
    if "bitcoin" in n or "btc" in n: return 56302
    return 12.3


MOCK = r'''
#include <cstdio>
#include <ctime>
#include <cstdarg>
#include <cstdint>
#include <cmath>
#include <string>
#include <map>
#include <vector>
#include <algorithm>
#include <cstring>
using namespace std;
#define ESPHOME_PROJECT_VERSION "Vorschau"
struct Color { uint8_t r, g, b, w; Color() : r(0), g(0), b(0), w(0) {}
  Color(int r_, int g_, int b_, int w_ = 0) : r(r_), g(g_), b(b_), w(w_) {}
  static const Color BLACK, WHITE; };
const Color Color::BLACK(0, 0, 0); const Color Color::WHITE(255, 255, 255);
#define COLOR_ON Color(255, 255, 255)
#define COLOR_OFF Color(0, 0, 0)
enum class TextAlign : int { TOP = 0, CENTER_VERTICAL = 1, BASELINE = 2, BOTTOM = 4, LEFT = 0, CENTER_HORIZONTAL = 8, RIGHT = 16,
  TOP_LEFT = 0, TOP_CENTER = 8, TOP_RIGHT = 16, CENTER_LEFT = 1, CENTER = 9, CENTER_RIGHT = 17,
  BASELINE_LEFT = 2, BASELINE_CENTER = 10, BASELINE_RIGHT = 18, BOTTOM_LEFT = 4, BOTTOM_CENTER = 12, BOTTOM_RIGHT = 20 };
namespace esphome { namespace display {
struct BaseFont { int nr; int hoehe; int basis; map<uint32_t, int> breite; int standard; };
} }
using esphome::display::BaseFont;
static vector<uint32_t> utf8(const char *s) { vector<uint32_t> v; const unsigned char *p = (const unsigned char *) s;
  while (*p) { uint32_t c = *p; int n = 0;
    if (c >= 0xF0) { c &= 7; n = 3; } else if (c >= 0xE0) { c &= 15; n = 2; } else if (c >= 0xC0) { c &= 31; n = 1; }
    p++; while (n-- > 0 && *p) { c = (c << 6) | (*p & 63); p++; } v.push_back(c); } return v; }
static void hexaus(const char *s) { for (const unsigned char *p = (const unsigned char *) s; *p; p++) printf("%02x", *p); }
struct Display {
  int get_width() { return BREITE; } int get_height() { return HOEHE; }
  void fill(Color c) { ::printf("F %d %d %d\n", c.r, c.g, c.b); }
  void clear() { fill(Color(0, 0, 0)); }
  void draw_pixel_at(int x, int y, Color c = COLOR_ON) { ::printf("P %d %d %d %d %d\n", x, y, c.r, c.g, c.b); }
  void line(int x1, int y1, int x2, int y2, Color c = COLOR_ON) { ::printf("L %d %d %d %d %d %d %d\n", x1, y1, x2, y2, c.r, c.g, c.b); }
  void horizontal_line(int x, int y, int w, Color c = COLOR_ON) { if (w > 0) line(x, y, x + w - 1, y, c); }
  void vertical_line(int x, int y, int h, Color c = COLOR_ON) { if (h > 0) line(x, y, x, y + h - 1, c); }
  void rectangle(int x, int y, int w, int h, Color c = COLOR_ON) { ::printf("R %d %d %d %d %d %d %d 0\n", x, y, w, h, c.r, c.g, c.b); }
  void filled_rectangle(int x, int y, int w, int h, Color c = COLOR_ON) { ::printf("R %d %d %d %d %d %d %d 1\n", x, y, w, h, c.r, c.g, c.b); }
  void circle(int x, int y, int r, Color c = COLOR_ON) { ::printf("C %d %d %d %d %d %d 0\n", x, y, r, c.r, c.g, c.b); }
  void filled_circle(int x, int y, int r, Color c = COLOR_ON) { ::printf("C %d %d %d %d %d %d 1\n", x, y, r, c.r, c.g, c.b); }
  void triangle(int x1, int y1, int x2, int y2, int x3, int y3, Color c = COLOR_ON) { line(x1, y1, x2, y2, c); line(x2, y2, x3, y3, c); line(x3, y3, x1, y1, c); }
  void filled_triangle(int x1, int y1, int x2, int y2, int x3, int y3, Color c = COLOR_ON) { ::printf("D %d %d %d %d %d %d %d %d %d\n", x1, y1, x2, y2, x3, y3, c.r, c.g, c.b); }
  int breite(const char *t, BaseFont *f) { int w = 0; for (uint32_t c : utf8(t)) { auto i = f->breite.find(c); w += (i != f->breite.end()) ? i->second : f->standard; } return w; }
  void get_text_bounds(int x, int y, const char *t, BaseFont *f, TextAlign a, int *x1, int *y1, int *w, int *h) {
    int al = (int) a; *w = breite(t, f); *h = f->hoehe;
    if (al & 8) *x1 = x - *w / 2; else if (al & 16) *x1 = x - *w; else *x1 = x;
    if (al & 1) *y1 = y - *h / 2; else if (al & 2) *y1 = y - f->basis; else if (al & 4) *y1 = y - *h; else *y1 = y; }
  void print(int x, int y, BaseFont *f, Color c, TextAlign a, const char *t) {
    int x1, y1, w, h; get_text_bounds(x, y, t, f, a, &x1, &y1, &w, &h);
    ::printf("T %d %d %d %d %d %d ", x1, y1, f->nr, c.r, c.g, c.b); hexaus(t); ::printf("\n"); }
  void print(int x, int y, BaseFont *f, Color c, const char *t) { print(x, y, f, c, TextAlign::TOP_LEFT, t); }
  void print(int x, int y, BaseFont *f, TextAlign a, const char *t) { print(x, y, f, COLOR_ON, a, t); }
  void print(int x, int y, BaseFont *f, const char *t) { print(x, y, f, COLOR_ON, TextAlign::TOP_LEFT, t); }
  void print(int x, int y, BaseFont *f, Color c, TextAlign a, const string &t) { print(x, y, f, c, a, t.c_str()); }
  void print(int x, int y, BaseFont *f, Color c, const string &t) { print(x, y, f, c, t.c_str()); }
  void printf(int x, int y, BaseFont *f, Color c, TextAlign a, const char *fmt, ...) __attribute__((format(printf, 7, 8))) {
    char b[256]; va_list v; va_start(v, fmt); vsnprintf(b, sizeof(b), fmt, v); va_end(v); print(x, y, f, c, a, b); }
  void printf(int x, int y, BaseFont *f, Color c, const char *fmt, ...) __attribute__((format(printf, 6, 7))) {
    char b[256]; va_list v; va_start(v, fmt); vsnprintf(b, sizeof(b), fmt, v); va_end(v); print(x, y, f, c, TextAlign::TOP_LEFT, b); }
  void printf(int x, int y, BaseFont *f, TextAlign a, const char *fmt, ...) __attribute__((format(printf, 6, 7))) {
    char b[256]; va_list v; va_start(v, fmt); vsnprintf(b, sizeof(b), fmt, v); va_end(v); print(x, y, f, COLOR_ON, a, b); }
  void printf(int x, int y, BaseFont *f, const char *fmt, ...) __attribute__((format(printf, 5, 6))) {
    char b[256]; va_list v; va_start(v, fmt); vsnprintf(b, sizeof(b), fmt, v); va_end(v); print(x, y, f, COLOR_ON, TextAlign::TOP_LEFT, b); }
};
struct ESPTime { int second = 0, minute = 30, hour = 11, day_of_week = 6, day_of_month = 20, day_of_year = 324, month = 11, year = 2026;
  bool is_valid() const { return true; }
  size_t strftime(char *b, size_t n, const char *fmt) { struct tm t = {}; t.tm_sec = second; t.tm_min = minute; t.tm_hour = hour;
    t.tm_mday = day_of_month; t.tm_mon = month - 1; t.tm_year = year - 1900; t.tm_wday = day_of_week - 1; return ::strftime(b, n, fmt, &t); }
  string strftime(const char *fmt) { char b[64]; strftime(b, sizeof(b), fmt); return b; } };
struct ZeitQuelle { ESPTime now() { return ESPTime(); } ESPTime utcnow() { return ESPTime(); } };
namespace sensor { struct Sensor { float state; bool has_state() const { return true; } float get_state() const { return state; } }; }
using sensor::Sensor;
struct TextSensor { string state; bool has_state() const { return true; } };
struct BinarySensor { bool state; bool has_state() const { return true; } };
struct Etwas { bool state = false; bool has_state() const { return false; } bool is_on() const { return false; } };
'''


def groesse(cfg):
    """Breite x Hoehe des Displays aus der Konfiguration (Vorgabe 320x480)."""
    disp = cfg.get("display")
    if isinstance(disp, dict): disp = [disp]
    for d in disp or []:
        if not isinstance(d, dict): continue
        dim = d.get("dimensions")
        if isinstance(dim, dict) and dim.get("width"):
            b, h = int(dim["width"]), int(dim["height"])
        elif isinstance(dim, str) and "x" in dim:
            b, h = map(int, dim.lower().split("x"))
        else:
            b, h = MODELLE.get(str(d.get("model", "")).lower(), (320, 480))
        if int(d.get("rotation", 0) or 0) in (90, 270): b, h = h, b
        return b, h
    return 320, 480


def lambda_suchen(cfg):
    disp = cfg.get("display")
    if isinstance(disp, dict): disp = [disp]
    for d in disp or []:
        if not isinstance(d, dict): continue
        if d.get("pages"): return d["pages"][0].get("lambda")
        if d.get("lambda"): return d["lambda"]
    return None


def main():
    args = sys.argv[1:]
    cache = os.path.join(tempfile.gettempdir(), "vorschau_schriften")
    if "--cache" in args:
        i = args.index("--cache"); cache = args[i + 1]; del args[i:i + 2]
    quelle, ziel = args[0], args[1]
    cfg = yaml.load(open(quelle, encoding="utf-8"), Lader)
    global B, H
    B, H = groesse(cfg)
    code = lambda_suchen(cfg)
    if not code: sys.exit("keine Display-lambda gefunden")

    benutzt = set(re.findall(r"\bid\((\w+)\)", code))
    decl = []

    # Schriften
    fonts = []
    for e in cfg.get("font") or []:
        if not isinstance(e, dict) or e.get("id") not in benutzt: continue
        f = schrift(e, cache)
        nr = len(fonts)
        fonts.append(f)
        zeichen = set(chr(c) for c in range(32, 256))
        for esc in re.findall(r"\\U([0-9A-Fa-f]{8})|\\u([0-9A-Fa-f]{4})", code):
            zeichen.add(chr(int(esc[0] or esc[1], 16)))
        for ch in re.findall(r'"((?:[^"\\]|\\.)*)"', code):
            zeichen.update(ch)
        if f is None:
            decl.append(f"BaseFont _font{nr}{{{nr}, 10, 8, {{}}, 6}}; BaseFont *{e['id']} = &_font{nr};")
            continue
        asc, desc = f.getmetrics()
        breiten = []
        for z in sorted(zeichen):
            try:
                if f.getmask(z).getbbox() is None and z != " ": continue
                breiten.append(f"{{{ord(z)}u,{int(round(f.getlength(z)))}}}")
            except Exception:
                pass
        decl.append(f"BaseFont _font{nr}{{{nr}, {asc + desc}, {asc}, {{{','.join(breiten)}}}, {int(round(f.getlength('0')))}}}; "
                    f"BaseFont *{e['id']} = &_font{nr};")
    erledigt = {e["id"] for e in cfg.get("font") or [] if isinstance(e, dict) and e.get("id") in benutzt}

    # Sensoren, Globals, Zeit
    # auch Teil-Sensoren mit eigener id (z.B. scd4x: co2/temperature/humidity)
    sensoren = []
    for e in cfg.get("sensor") or []:
        if not isinstance(e, dict): continue
        sensoren.append(e)
        sensoren += [v for v in e.values() if isinstance(v, dict) and v.get("id")]
    for e in sensoren:
        if e.get("id") in benutzt and e["id"] not in erledigt:
            decl.append(f"Sensor {e['id']}{{{float(beispiel(e['id']))}f}};"); erledigt.add(e["id"])
    for e in cfg.get("text_sensor") or []:
        if isinstance(e, dict) and e.get("id") in benutzt and e["id"] not in erledigt:
            decl.append(f'TextSensor {e["id"]}{{"Beispiel"}};'); erledigt.add(e["id"])
    for e in cfg.get("binary_sensor") or []:
        if isinstance(e, dict) and e.get("id") in benutzt and e["id"] not in erledigt:
            decl.append(f"BinarySensor {e['id']}{{false}};"); erledigt.add(e["id"])
    for e in cfg.get("globals") or []:
        if isinstance(e, dict) and e.get("id") in benutzt and e["id"] not in erledigt:
            wert = {"hz_min": "0.7", "hz_max": "1.9", "hz_tag": "20"}.get(e["id"], str(e.get("initial_value", "0")).strip("'\""))
            decl.append(f"{e.get('type', 'int')} {e['id']} = {wert};"); erledigt.add(e["id"])
    for e in cfg.get("time") or []:
        if isinstance(e, dict) and e.get("id") in benutzt and e["id"] not in erledigt:
            decl.append(f"ZeitQuelle {e['id']};"); erledigt.add(e["id"])
    for n in sorted(benutzt - erledigt):
        decl.append(f"Etwas {n};")

    # id() wie ESPHome umsetzen: id(x).foo -> x->foo (bei uns Objekt: x.foo), id(x) allein -> Zeiger auf x;
    # Globals immer als Wert, Schriften sind bei uns schon Zeiger
    globs = {e["id"] for e in cfg.get("globals") or [] if isinstance(e, dict)}
    fids = {e["id"] for e in cfg.get("font") or [] if isinstance(e, dict)}
    def ersetze(m):
        n, punkt = m.group(1), m.group(2)
        if n in globs or n in fids: return n + punkt
        return (n + punkt) if punkt else f"(&{n})"
    code = re.sub(r"\bid\((\w+)\)(\.?)", ersetze, code)
    prog = f"#define BREITE {B}\n#define HOEHE {H}\n" + MOCK + "\n".join(decl) + "\nvoid zeichne(Display &it) {\n" + code + "\n}\nint main() { Display d; zeichne(d); return 0; }\n"
    with tempfile.TemporaryDirectory() as tmp:
        cpp = os.path.join(tmp, "v.cpp"); exe = os.path.join(tmp, "v")
        open(cpp, "w", encoding="utf-8").write(prog)
        r = subprocess.run(["g++", "-std=c++17", "-O0", "-w", "-o", exe, cpp], capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stderr[-4000:]); sys.exit("Uebersetzen fehlgeschlagen")
        befehle = subprocess.run([exe], capture_output=True, text=True, check=True).stdout

    def farbe(r, g, b):
        # 8-Bit-Palette des Displays (3-3-2): R/G 8 Stufen, B 4 Stufen
        return (round(int(r) / 255 * 7) * 255 // 7, round(int(g) / 255 * 7) * 255 // 7, round(int(b) / 255 * 3) * 255 // 3)

    img = Image.new("RGB", (B, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    for z in befehle.splitlines():
        t = z.split(" ")
        k = t[0]
        if k == "F":
            d.rectangle([0, 0, B, H], fill=farbe(*t[1:4]))
        elif k == "P":
            d.point((int(t[1]), int(t[2])), fill=farbe(*t[3:6]))
        elif k == "L":
            d.line([int(t[1]), int(t[2]), int(t[3]), int(t[4])], fill=farbe(*t[5:8]))
        elif k == "R":
            x, y, w, h = map(int, t[1:5])
            if w <= 0 or h <= 0: continue
            if t[8] == "1": d.rectangle([x, y, x + w - 1, y + h - 1], fill=farbe(*t[5:8]))
            else: d.rectangle([x, y, x + w - 1, y + h - 1], outline=farbe(*t[5:8]))
        elif k == "C":
            x, y, r = map(int, t[1:4])
            if t[7] == "1": d.ellipse([x - r, y - r, x + r, y + r], fill=farbe(*t[4:7]))
            else: d.ellipse([x - r, y - r, x + r, y + r], outline=farbe(*t[4:7]))
        elif k == "D":
            p = list(map(int, t[1:7]))
            d.polygon([(p[0], p[1]), (p[2], p[3]), (p[4], p[5])], fill=farbe(*t[7:10]))
        elif k == "T":
            x, y, nr = int(t[1]), int(t[2]), int(t[3])
            text = bytes.fromhex(t[7]).decode("utf-8", "replace") if len(t) > 7 else ""
            f = fonts[nr] or ImageFont.load_default()
            # Zeichen fuer Zeichen mit ganzzahligem Vorschub, wie ESPHome
            cx = x
            for ch in text:
                d.text((cx, y), ch, font=f, fill=farbe(*t[4:7]), anchor="la")
                cx += int(round(f.getlength(ch))) if fonts[nr] else 6
    img.save(ziel)


if __name__ == "__main__":
    main()
