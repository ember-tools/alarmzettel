"""
Prints the personnel plan as the server calculates it, for comparison with the browser.

Neither is stored anywhere; both are derived from the chains, once in the browser for the view
and once here for the sheet in hand. If the two drift apart, the printout contradicts the screen,
which is exactly what deriving them is meant to prevent.

    python tools/plan_vergleichen.py <arbeitsmappe.json>

`./toolchain.sh ablauf-vergleichen` runs both sides and compares them. The coordinates come from
`punkte.json` beside the working set, not from the address service: what is compared is the
calculation, not the lookup, and both sides get the same numbers.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from data.ablaufplan import plandaten
from data.alarmplan import einsaetze
from entities.alarm import Arbeitsmappe

if len(sys.argv) < 2:
    sys.exit("Aufruf: python tools/plan_vergleichen.py <arbeitsmappe.json>")

mappe = Arbeitsmappe.model_validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))

punkte = json.loads((Path(sys.argv[1]).parent / "punkte.json").read_text(encoding="utf-8"))

daten = plandaten(mappe, punkte)

for blatt in daten["personen"]:
    for zeile in blatt["zeilen"]:
        print(" | ".join([
            "PLAN", blatt["name"], zeile["datum"], zeile["von"], zeile["bis"], zeile["art"],
            zeile["vonOrt"], zeile["ort"], zeile["lage"],
            "faehrt" if zeile["faehrt"] else "-", zeile["fahrzeug"],
            str(zeile["geschaetzt"] if zeile["geschaetzt"] is not None else "-"),
        ]))

for einsatz in einsaetze(mappe, punkte):
    print(" | ".join([
        "EINSATZ", einsatz["lage"], str(einsatz["nummer"]), einsatz["ortId"],
        einsatz["von"], einsatz["da"], einsatz["bis"],
        ",".join(f"{eintrag['name']}{'' if eintrag['aufgebot'] else '*'}"
                 for eintrag in einsatz["beteiligte"]),
    ]))
