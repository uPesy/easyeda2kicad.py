# Code Audit – easyeda2kicad

**Datum:** 2026-03-03
**Basis:** Vollständige Analyse aller Python-Dateien im Paket `easyeda2kicad/`
**Format:** Abarbeitbare Checkliste nach den 6 Prüfkriterien

---

## Legende

- `[ ]` Offen / muss bearbeitet werden
- `[x]` Erledigt
- **[BUG]** Funktionaler Fehler
- **[DEAD]** Toter / ungenutzter Code
- **[DUP]** Duplizierte Logik
- **[SMELL]** Code Smell / schlechtes Muster
- **[MINOR]** Kleinigkeit / Typo / Lesbarkeit

---

## 1. Integrationsfähigkeit

### Befunde

- [x] **[SMELL]** `helpers.py:189–238` – `add_sub_components_in_symbol_lib_file()` implementiert exakt dieselbe Sub-Symbol-Integrations-Logik wie `__main__.py:283–310`. Die Helper-Funktion wird im aktuellen Code nirgends aufgerufen und ist damit dead code, der aber durch den gleichnamigen Kontext suggeriert, die "offizielle" Implementierung zu sein. Risiko: Divergenz bei künftigen Änderungen. **→ Entfernt.**

- [x] **[SMELL]** `easyeda_importer.py` – `Easyeda3dModelImporter.create_3d_model()` erzeugte **zwei neue** `EasyedaApi()`-Instanzen für OBJ und STEP (Zeilen 523–524), anstatt eine gemeinsame Instanz zu nutzen. Das führt zu zwei unabhängigen SSL-Kontexten, zwei separaten Cache-Initialisierungen und ist inkonsistent mit der API-Nutzung in `__main__.py`, wo eine einzige `EasyedaApi`-Instanz übergeben wird.

  **→ Behoben:** Optionaler `api`-Parameter in `Easyeda3dModelImporter.__init__`. `__main__.py` übergibt die vorhandene Instanz; intern wird nur eine neue Instanz als Fallback erzeugt.

- [x] **[SMELL]** `__main__.py` – `arguments.get("v5")` für einen argparse-Key der immer vorhanden ist. **→ Behoben:** `arguments["v5"]`. Regel: `["key"]` für argparse-Keys (immer gesetzt), `.get("key")` nur für dynamisch ergänzte Keys (`use_default_folder`, `kicad_version`). Außerdem `typing.List` → natives `list` modernisiert.

---

## 2. Komplexität und Struktur

### Befunde

- [ ] **[SMELL]** `easyeda_importer.py:427–501` – `EasyedaFootprintImporter.extract_easyeda_data()` nutzt eine lange `if/elif`-Kette für Footprint-Designatoren (PAD, TRACK, HOLE, VIA, CIRCLE, ARC, RECT, TEXT, SVGNODE). Das Symbol-Importer nutzt hingegen ein sauberes Dispatcher-Dict (`easyeda_handlers`). Die Footprint-Seite sollte analog umgebaut werden.

- [x] **[SMELL]** `__main__.py:227–409` – `_process_component()` ~180 Zeilen. **→ Behoben:** Die drei `if arguments[...]`-Blöcke 1:1 in `_process_symbol()`, `_process_footprint()`, `_process_3d_model()` extrahiert. `_process_component()` ist jetzt ~20 Zeilen.

- [x] **[SMELL]** `export_kicad_symbol.py:169–231` – `convert_ee_arcs()` hatte keine Bounds-Prüfung für `ee_arc.path[1]`. **→ Behoben:** `len(ee_arc.path) < 2`-Check + `or` → `and` korrigiert.

- [x] **[SMELL]** `parameters_kicad_symbol.py` – `export_handler()` nutzte `getattr(..., f"export_v{kicad_version}")()` mit rohem String. **→ Behoben:** Signatur auf `KicadVersion` umgestellt, `f"export_{kicad_version.name}"` wie in `export()`. `getattr(..., None)` mit klarer `ValueError`-Meldung statt stummem `AttributeError`.

- [x] **[SMELL]** `export_kicad_footprint.py:541–542` – `y_low = min(pad.pos_y for pad in ki.pads)` crashte mit `ValueError` bei leerem Pad-List. **→ Behoben:** `default=0` hinzugefügt.

---

## 3. Redundanz und Dead Code

### Befunde

- [x] **[DUP]** `_safe_float`, `_safe_int`, `_safe_bool` waren in zwei Dateien identisch definiert. **→ Behoben:** Nur noch in `parameters_easyeda.py`, `easyeda_importer.py` importiert von dort.

- [x] **[DEAD]** `helpers.py:136–150` – `get_local_config()` – **→ Entfernt.**

- [x] **[DEAD]** `helpers.py:189–238` – `add_sub_components_in_symbol_lib_file()` – **→ Entfernt.**

- [x] **[DEAD]** `helpers.py:170–174` – `get_arc_angle_end()` – beide Zweige identisch, nirgends aufgerufen. **→ Entfernt.**

- [x] **[DEAD]** `parameters_kicad_footprint.py:232–243` – `KiFootprintSolidRegion` / `KiFootprintCopperArea` hatten nur `# TODO`. **→ Keine toten Klassen**, sondern Stubs für geplante Features (EasyEDA SOLIDREGION = Exposed-Pad-Kupferfüllung → KiCad zone; COPPERAREA = Kupfer-Füllzone). `# TODO` durch erklärende Kommentare ersetzt; `...` im Importer durch `pass` mit Hinweis ersetzt.

- [ ] **[DEAD]** `export_kicad_symbol.py:284–327` – `convert_ee_paths()` gibt immer ein leeres `kicad_beziers`-Listenresultat zurück, weil der `C`-Befehlshandler nur `...` (no-op) ist. Die Bezier-Liste wird zwar als zweiter Rückgabewert propagiert und in `KiSymbol.beziers` gespeichert, hat aber nie Inhalt.

- [x] **[DEAD]** `helpers.py` – `sym_lib_regex_pattern["v6_99"]` leerer String + `KicadVersion.v6_99` Enum-Eintrag ohne Implementierung. **→ Entfernt.** `v6` deckt KiCad 6+ ab (Format stabil seit 6.0).

- [x] **[DEAD]** Alle `__fields__ = property(...)` – Pydantic-Legacy-Shim auf allen Dataclasses in `parameters_easyeda.py`. **→ Entfernt (~20 Klassen).**

- [ ] **[DEAD]** `parameters_kicad_symbol.py:562–596` – `KiSymbolBezier` – vollständig implementierte Klasse mit `export_v5()` und `export_v6()`, aber Bezier-Kurven werden niemals erzeugt (siehe Punkt oben zu `convert_ee_paths`). Die Klasse ist derzeit ungenutzter Code.

- [x] **[MINOR]** `export_kicad_symbol.py` – auskommentierte Codeblöcke (Pin-Längen-Justierung, `pin_spacing`). **→ Entfernt.**

- [x] **[MINOR]** `__main__.py` – auskommentierte `print()`-Anweisungen. **→ Entfernt.**

- [x] **[MINOR]** `export_kicad_footprint.py` – auskommentierte `print()`-Anweisungen. **→ Entfernt.**

---

## 4. Modernität und Wartbarkeit

### Befunde

- [x] **[SMELL]** **Gemischte Typing-Stile**: `__main__.py` verwendet `list[str]` (Python 3.9+ native), während andere Dateien noch `from typing import List` / `List[str]` nutzen. Einheitlich auf native Typen umstellen.

- [x] **[SMELL]** `parameters_easyeda.py:708` – `ee_footprint` verletzt PEP 8. **→ Behoben:** In `EeFootprint` umbenannt (`parameters_easyeda.py`, `easyeda_importer.py`, `export_kicad_footprint.py`, `__init__.py`).

- [x] **[BUG]** `parameters_kicad_symbol.py` – `field(default_factory=List[List[float]])` war kein aufrufbares Objekt. **→ Behoben:** `field(default_factory=list)`.

- [ ] **[SMELL]** `parameters_easyeda.py:424–427` und alle anderen Dataclasses – `convert_to_mm()` **mutiert das Objekt in-place**. Das bedeutet, ein zweimaliger Aufruf würde die Werte doppelt konvertieren. In `ExporterFootprintKicad.generate_kicad_footprint()` werden alle Shapes konvertiert. Kein Schutz gegen Doppel-Konvertierung.

- [x] **[SMELL]** `export_kicad_footprint.py` – `fp_to_ki()` gab bei NaN-Input `float("nan")` zurück statt `0.0`. **→ Behoben:** try/except, immer `0.0` für NaN/None/leer.

- [x] **[SMELL]** `easyeda_importer.py` – `str(origin) == "typing.Union"` war fragiler Versionsvergleich. **→ Behoben:** `origin is Union`.

- [x] **[SMELL]** `easyeda_api.py` – `api_response["success"] is False` konnte KeyError geben wenn `"success"`-Key fehlt. **→ Behoben:** `api_response.get("success") is False`.

- [x] **[MINOR]** `easyeda_api.py` – `assert isinstance(...)` für Laufzeitvalidierung. **→ Behoben:** `if not isinstance(...): return None`.

---

## 5. Kommentare und Dokumentation

### Befunde

- [x] **[SMELL]** `easyeda_importer.py` – `ROOT CAUSE FIX`-Kommentar war ein Entwicklungs-Prozess-Kommentar. **→ Durch erklärendes Docstring ersetzt.**

- [x] **[SMELL]** `parameters_easyeda.py:349–351` – Drei `# TODO`-Kommentare ohne Kontext. **→ Behoben:** In einen einheitlichen „Known limitation"-Kommentar umgewandelt (M/L/Z unterstützt, C/Q/A übersprungen, Link zur SVG-Spec erhalten).

- [x] **[MINOR]** `export_kicad_footprint.py:393–395` – Kommentar „appears intentional" ohne Erklärung. **→ Behoben:** Als `# FIXME` umformuliert mit empirischer Beobachtung und klarem Hinweis, dass die Ursache unbekannt ist.

- [x] **[MINOR]** `export_kicad_footprint.py:298–300` – „seem to" ohne Verifikation. **→ Behoben:** Als `# FIXME` markiert mit Klarstellung, dass das Verhalten empirisch beobachtet, aber nicht formal verifiziert ist.

- [x] **[MINOR]** `parameters_kicad_symbol.py` – `# TODO: 360 - ?` im `export_v6()`-Pin-Rotationsformat. **→ Durch erklärenden Kommentar ersetzt** (180°-Offset EasyEDA → KiCad Konvention).

- [x] **[MINOR]** `easyeda_importer.py` – Typo `"Unknow"` → `"Unknown"` (×2). **→ Behoben.**

- [x] **[MINOR]** `parameters_easyeda.py` – Auskommentierte No-op-Zeile. **→ Entfernt.**

---

## 6. Allgemeine Produktionsreife

### Befunde

- [x] **[BUG]** `helpers.py` – `get_arc_angle_end()` – beide Zweige identisch, nirgends aufgerufen. **→ Entfernt.**

- [x] **[BUG]** `export_kicad_3d_model.py` – `points.insert(-1, points[-1])` erzeugte Duplikat. **→ Entfernt.**

- [x] **[BUG]** `export_kicad_symbol.py` – `convert_ee_arcs()` ohne Bounds-Check + falsche `or`-Bedingung. **→ Behoben.**

- [x] **[BUG]** `export_kicad_footprint.py` – `min()`/`max()` auf leerer Pad-Liste → `ValueError`. **→ Behoben:** `default=0`.

- [x] **[MINOR]** `parameters_easyeda.py` – Typo `miror` → `mirror` in `EeFootprintText`. **→ Behoben.**

- [x] **[SMELL]** `easyeda_api.py` – `debug_cache_enabled` wurde einmalig in `__init__` gesetzt, bevor der Logger konfiguriert war. **→ Behoben:** Als `@property` implementiert, wird bei jedem Zugriff frisch ausgewertet.

- [x] **[SMELL]** `export_kicad_footprint.py:286–287` – Pad-Nummern-Bereinigung ohne Kommentar und ohne Log. **→ Behoben:** Erklärender Kommentar + `logging.debug()` hinzugefügt.

- [x] **[SMELL]** `easyeda_api.py` – Hardcodierte KiCad-9.0/10.0-Zertifikatspfade. **→ Behoben:** `glob.glob()` findet alle KiCad-Versionen unter `/Applications/` automatisch.

- [x] **[SMELL]** `export_kicad_3d_model.py:127–130` – OBJ ohne `usemtl`-Einträge → leere WRL ohne Warnung. **→ Behoben:** Early-return mit `logging.warning()` und `raw_wrl=None` (kein WRL-File wird geschrieben).

- [x] **[SMELL]** `export_kicad_3d_model.py:130` – `materials[name]` ohne KeyError-Schutz. **→ Bereits behoben:** `materials.get(material_name)` mit `None`-Check und `logging.warning()` + `continue`.

---

## Zusammenfassung der Prioritäten

### Hoch (Code-Qualität, strukturelle Probleme)

| # | Datei | Zeile | Problem |
|---|-------|-------|---------|
| 1 | `export_kicad_footprint.py` | 427–501 | Footprint-Importer: lange if/elif-Kette statt Dispatcher-Dict (wie im Symbol-Importer) |
| 2 | `parameters_easyeda.py` | 424–427 | `convert_to_mm()` mutiert Objekt in-place – theoretisches Risiko, in der Praxis kein Problem |
| 3 | `export_kicad_symbol.py` + `parameters_kicad_symbol.py` | 284–327 / 562–596 | Bezier-Kurven (`convert_ee_paths` C-Befehl + `KiSymbolBezier`) sind toten Code – nie befüllt |

