#!/usr/bin/env python3
"""Macht aus einem Design-Package die aktive anzeige.yaml eines Displays.

Aufruf:  python3 tools/design_aktivieren.py displays/wetterstation designs/anzeige_gruen.yaml

- uebernimmt das Design 1:1
- entfernt Schriften, die im Display-Code nicht benutzt werden (spart Flash und
  vermeidet, dass GitHub fehlende eigene Schriftdateien braucht)
"""
import re
import sys
import pathlib

ordner = pathlib.Path(sys.argv[1])
quelle = ordner / sys.argv[2]
text = quelle.read_text(encoding="utf-8")

# Display-Code (alle lambdas) sammeln und benutzte ids finden
benutzt = set(re.findall(r"id\((\w+)\)", text[text.index("\ndisplay:"):]))

zeilen = text.split("\n")
start = next(i for i, z in enumerate(zeilen) if z.startswith("font:"))
ende = next(i for i in range(start + 1, len(zeilen)) if zeilen[i] and not zeilen[i].startswith(" "))

# Font-Liste in Bloecke ("  - file:" ... bis zum naechsten "  - ") zerlegen
bloecke, aktuell = [], []
for z in zeilen[start + 1:ende]:
    if z.startswith("  - "):
        if aktuell:
            bloecke.append(aktuell)
        aktuell = [z]
    elif z.startswith("  #") and not aktuell:
        continue
    else:
        aktuell.append(z)
if aktuell:
    bloecke.append(aktuell)

behalten, weg = [], []
for b in bloecke:
    m = re.search(r"^\s+id:\s*(\w+)", "\n".join(b), re.M)
    (behalten if m and m.group(1) in benutzt else weg).append(b)
    if m and m.group(1) not in benutzt:
        pass

neu = zeilen[:start + 1]
for b in behalten:
    # Kommentarzeilen am Blockende (Ueberschrift des naechsten Blocks) weglassen
    while b and b[-1].strip().startswith("#"):
        b = b[:-1]
    neu += b
neu += [""] + zeilen[ende:]
ziel = ordner / "anzeige.yaml"
kopf = f"# AKTIVES DESIGN - erzeugt aus {sys.argv[2]} (tools/design_aktivieren.py)\n"
ziel.write_text(kopf + "\n".join(neu), encoding="utf-8")
ids_weg = [re.search(r"id:\s*(\w+)", "\n".join(b)).group(1) for b in weg if re.search(r"id:\s*(\w+)", "\n".join(b))]
print(f"{ziel}: {len(behalten)} Schriften behalten, entfernt: {', '.join(ids_weg)}")
