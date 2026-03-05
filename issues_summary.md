# Issue Status Overview: easyeda2kicad.py

Issues marked ✅ have been tested and confirmed fixed. Issues marked N/A are out of scope.

Source: [github.com/uPesy/easyeda2kicad.py/issues](https://github.com/uPesy/easyeda2kicad.py/issues)

---

## Tested & Fixed ✅

| Issue | Title                                                                         | Category    | Notes                                                                                 |
|-------|-------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------|
| –     | Footprint arc shown as full circle (C652779)                                  | Footprint   | acos clamp fix in compute_arc (max(-1,min(1,p/n)))                                    |
| –     | Add Manufacturer, MPN, LCSC Part, Keywords to symbol and footprint properties | Enhancement | Complete BOM export now possible; fields sourced from EasyEDA API (c_para + tags)     |
| #26   | Feature request: Add GUI                                                      | Feature     | Resolved – GUI available as KiCad plugin (Import-LIB-KiCad-Plugin)                    |
| #65   | C93830 symbol garbled                                                         | Symbol      | Arc direction fixed (bool('0')==True bug in svg_path_parser.__post_init__)            |
| #67   | SOT89 footprint garbled                                                       | Footprint   | C880738/C495224 visually verified, no issues                                          |
| #69   | C398355 – fails to import symbol                                              | Symbol      | 8 pins imported correctly, no longer empty                                            |
| #71   | Fails to import (multiple imports)                                            | Symbol      | Second import shows warning, no data loss                                             |
| #73   | Minor issue with through hole pads                                            | Footprint   | C1525 visually verified, no issues                                                    |
| #74   | All pins type "Unspecified"                                                   | Symbol      | C398355 now has output/power_in/unspecified types                                     |
| #75   | Conflicts with parts in other libraries                                       | Other       | Not reproducible; use --output to specify a dedicated library path                    |
| #77   | Remove Python 3.5/3.6/3.7 support                                             | Other       | `python_requires=">=3.10"` reflects actual minimum; no active fix needed              |
| #78   | Install without Python (KiCad Prompt)                                         | Other       | README updated with KiCad Command Prompt installation instructions                    |
| #80   | 3D models: Problems with `d` interpretation                                   | 3D          | `d` (dissolve) parsed but ignored; transparency hardcoded to 0 — no invisible objects |
| #85   | Refactor path manipulation with Pathlib                                       | Other       | Only 1x `import os` remains in `__main__.py`                                          |
| #87   | Adding symbol fails after manual edit                                         | Symbol      | Manually tested, no failure                                                           |
| #88   | Colon in part name causes invalid symbol                                      | Symbol      | sanitize_fields now replaces ':' with '_' in symbol name; C26393 verified             |
| #89   | Parenthesis in MPN causes regex error                                         | Symbol      | C150122 (TLP152) imports without error                                                |
| #91   | Floating / misaligned 3D parts after full import                              | 3D          | WRL XY centering now applied for THT as well; C503582 verified                        |
| #92   | Unknown footprint designator: VIA                                             | Footprint   | C2913198: 12 VIAs correctly exported as thru_hole pads                                |
| #98   | `is_locked` not always boolean                                                | Footprint   | Handled gracefully, no validation error                                               |
| #101  | Windows: files on other than C: drive                                         | Other       | expanduser("~") + makedirs(exist_ok=True); drive-neutral since v0.7                   |
| #106  | Broken TFBGA footprint                                                        | Footprint   | C1349508 visually verified, correct                                                   |
| #107  | Silkscreen conversion error (C86580)                                          | Footprint   | Fallback F.Fab correct for layer_id=0 (undefined in EasyEDA spec); C86580 verified    |
| #111  | Directory path without filename creates empty file                            | Other       | Falls back to EasyEDA name, no empty filename                                         |
| #115  | Fails to update symbol                                                        | Other       | Manually tested, symbol remains importable after edit                                 |
| #116  | ValueError: could not convert string to float                                 | Symbol      | C18723582 and C16197220 import correctly after `.split()[0]` fix                      |
| #119  | Add proxy server support                                                      | Other       | N/A – no code needed; set `HTTPS_PROXY` env variable; documented in README            |
| #123  | Thermal pad pin has wrong number                                              | Footprint   | C650157 (QFN with thermal pad) visually verified, pin numbers correct                 |
| #124  | Incorrect footprint for LM73100                                               | Footprint   | C3210761 visually verified, no issues                                                 |
| #125  | C2904734 divide by 0 error                                                    | Symbol      | Fixed by degenerate-arc skip (radius==0) and acos clamp in arc computation            |
| #131  | Relative links for 3D models include full path                                | 3D          | os.path.relpath() used before ${KIPRJMOD}; no absolute path prefix; C434858 verified  |
| #137  | Incorrect conversion for SK6805-EC15                                          | Footprint   | C2874885 silkscreen visually verified, correct                                        |
| #139  | Arc shown as near-complete circle (AD8403ARUZ1)                               | Symbol      | C652779 visually verified, no arc error                                               |
| #141  | Adding part causes invalid kicad_sym syntax                                   | Symbol      | Parentheses balanced after 2+ imports                                                 |
| #142  | EasyEDA 3D and schematic model problems                                       | Symbol/3D   | Off-grid fixed by bbox snapping to 5px grid; 3D offset fixed by XY centering          |
| #143  | Wrong library paths in docs (Linux)                                           | Other       | Current README uses correct `${EASYEDA2KICAD}/easyeda2kicad.*` paths                  |
| #147  | Symbol library broken after KiCad 8.05 update                                 | Symbol      | Manually tested, works correctly                                                      |
| #149  | SS34 Diode symbol slightly misaligned                                         | Symbol      | C154551 visually verified, pins on grid and connectable                               |
| #150  | BOM processing for LCSC parts                                                 | Feature     | Bulk import via `--lcsc_id C1 C2 C3` already supported                                |
| #152  | `--full` with no 3D model gets spurious error                                 | 3D          | C1349508: graceful WARNING only, no crash                                             |
| #153  | Incorrect conversion of C3171752                                              | Symbol      | Visually verified, no issues                                                          |
| #154  | Crash when converting C157482 (TypeError)                                     | Symbol      | No longer crashes                                                                     |
| #155  | Crash: KeyError 'packageDetail' (C5187472)                                    | Footprint   | No longer crashes                                                                     |
| #156  | Pin numbering swapped for C5446                                               | Symbol      | C5446 pins 2/3 visually verified, correct                                             |
| #168  | UFQFPN footprint pads do not match source                                     | Footprint   | C432211 visually verified, correct                                                    |
| #169  | Tool stops working after symbol modification                                  | Symbol      | Manually tested, no failure                                                           |
| #175  | No courtyard in imported footprints                                           | Footprint   | C880738/C86580/C1349508/C2685 all have courtyard                                      |
| #179  | Wrong pin numbering (C2874885)                                                | Symbol      | Pin numbers visually verified, correct                                                |
| #182  | Input should be a valid boolean (C5290175)                                    | Footprint   | No longer crashes                                                                     |

---

## Tested & Still Broken ❌

| Issue | Title        | Category | Notes                     |
|-------|--------------|----------|---------------------------|
| –     | No open bugs | –        | All known issues resolved |

---

## Out of Scope (N/A) – Feature Requests

| Issue | Title                                 | Reason                                                                                              |
|-------|---------------------------------------|-----------------------------------------------------------------------------------------------------|
| #164  | Conversion of manufacturer PN         | Would require web scraping LCSC search; fragile and hard to maintain, no official search API exists |
| #171  | Ability to enter EasyEDA Component ID | EasyEDA UUID endpoint undocumented; only LCSC API known; too fragile without official docs          |
| #177  | GUI with AI assistant                 | Not planned                                                                                         |

---

## Out of Scope (N/A) – Repository / Meta

| Issue | Title                                   | Reason              |
|-------|-----------------------------------------|---------------------|
| #151  | Missing git tags                        | Upstream repo issue |
| #176  | More users should be able to review PRs | Upstream repo issue |
| #181  | Project is dead?                        | Meta issue          |
| #184  | Offer to help maintain the project      | Meta issue          |
