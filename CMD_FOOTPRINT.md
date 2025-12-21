# EasyEDA Footprint Commands Reference

This document provides a compact reference for all EasyEDA footprint shape commands with field definitions and real examples.

**Units**: All coordinates and dimensions use EasyEDA internal units (1 unit = 10 mil = 0.254 mm)

## Command Overview

| Command     | Description                           | Implementation              |
| ----------- | ------------------------------------- | --------------------------- |
| PAD         | Footprint pad (SMD or through-hole)   | ✅ Implemented              |
| TRACK       | Copper track/trace or silkscreen line | ✅ Implemented              |
| RECT        | Rectangle shape                       | ✅ Implemented              |
| CIRCLE      | Circle shape                          | ✅ Implemented              |
| HOLE        | Non-plated hole                       | ✅ Implemented              |
| VIA         | Via connection                        | ✅ Implemented              |
| ARC         | Arc segment                           | ✅ Implemented              |
| TEXT        | Text label                            | ✅ Implemented              |
| SOLIDREGION | Filled copper region                  | ❌ Parsed but not converted |
| SVGNODE     | 3D model metadata (JSON)              | ✅ Implemented              |

---

## PAD - Footprint Pad

**Format:**

```
PAD~shape~center_x~center_y~width~height~layer_id~net~number~hole_radius~points~rotation~id~hole_length~hole_point~is_plated~is_locked~[extra_fields]
```

**Example:**

```
PAD~RECT~3994.299~2995~9.0551~9.0551~11~~1~2.7559~3989.7715 2990.4725 3998.8266 2990.4725 3998.8266 2999.5276 3989.7715 2999.5276~0~gge118~0~~Y~0~0~0.19685~3994.299,2995
```

**Fields:**

| Index | Field       | Type   | Unit     | Description                                  |
| ----- | ----------- | ------ | -------- | -------------------------------------------- |
| 0     | PAD         | -      | -        | Command identifier                           |
| 1     | shape       | string | -        | Shape: RECT, OVAL, ELLIPSE, POLYGON          |
| 2     | center_x    | float  | EE units | X coordinate of pad center                   |
| 3     | center_y    | float  | EE units | Y coordinate of pad center                   |
| 4     | width       | float  | EE units | Pad width                                    |
| 5     | height      | float  | EE units | Pad height                                   |
| 6     | layer_id    | int    | -        | Layer ID (1=F.Cu, 2=B.Cu, 11=\*.Cu)          |
| 7     | net         | string | -        | Net name (empty for no net)                  |
| 8     | number      | string | -        | Pad number (1, 2, 3, etc.)                   |
| 9     | hole_radius | float  | EE units | Drill hole radius (0 for SMD)                |
| 10    | points      | string | EE units | Space-separated coordinates for polygon pads |
| 11    | rotation    | float  | degrees  | Pad rotation angle                           |
| 12    | id          | string | -        | Unique element ID (e.g., "gge118")           |
| 13    | hole_length | float  | EE units | Oval hole length (0 for round)               |
| 14    | hole_point  | string | -        | Hole coordinates                             |
| 15    | is_plated   | string | -        | "Y" for plated, "N" for non-plated           |
| 16    | is_locked   | int    | -        | 1 if locked, 0 if unlocked                   |

**Notes:**

- Through-hole pads have `hole_radius > 0`
- SMD pads have `hole_radius = 0`
- POLYGON shape pads use the `points` field for custom outlines

---

## TRACK - Line/Trace

**Format:**

```
TRACK~stroke_width~layer_id~net~points~id~is_locked
```

**Example:**

```
TRACK~1~3~~3966.65 3007.66 3957.1495 3007.6495 3957.1495 3015.6495 3966.65 3015.65~gge265~0
```

**Fields:**

| Index | Field        | Type   | Unit     | Description                                |
| ----- | ------------ | ------ | -------- | ------------------------------------------ |
| 0     | TRACK        | -      | -        | Command identifier                         |
| 1     | stroke_width | float  | EE units | Line width/thickness                       |
| 2     | layer_id     | int    | -        | Layer ID (1=F.Cu, 3=F.SilkS, etc.)         |
| 3     | net          | string | -        | Net name (empty for silkscreen)            |
| 4     | points       | string | EE units | Space-separated X Y coordinates (polyline) |
| 5     | id           | string | -        | Unique element ID                          |
| 6     | is_locked    | int    | -        | 1 if locked, 0 if unlocked                 |

**Notes:**

- Points form a polyline (connected line segments)
- Minimum 2 points (4 values: x1 y1 x2 y2)
- Used for copper traces, silkscreen lines, and fabrication outlines

---

## RECT - Rectangle

**Format:**

```
RECT~x~y~width~height~stroke_width~id~layer_id~is_locked~[fill_color]~[...]
```

**Example:**

```
RECT~3980.15~2979.15~12.5~4.5~3~gge226~0~1~none~~~
```

**Fields:**

| Index | Field        | Type   | Unit     | Description                          |
| ----- | ------------ | ------ | -------- | ------------------------------------ |
| 0     | RECT         | -      | -        | Command identifier                   |
| 1     | x            | float  | EE units | X coordinate (top-left corner)       |
| 2     | y            | float  | EE units | Y coordinate (top-left corner)       |
| 3     | width        | float  | EE units | Rectangle width                      |
| 4     | height       | float  | EE units | Rectangle height                     |
| 5     | stroke_width | float  | EE units | Border line width                    |
| 6     | id           | string | -        | Unique element ID                    |
| 7     | layer_id     | int    | -        | Layer ID (0=F.Fab, 3=F.SilkS, etc.)  |
| 8     | is_locked    | int    | -        | 1 if locked, 0 if unlocked           |
| 9+    | ...          | -      | -        | Additional fields (fill color, etc.) |

**Notes:**

- `stroke_width` applies to **all 4 border lines** of the rectangle
- Converted to 4 separate fp_line entries in KiCad
- After our fix: `stroke_width` is correctly converted (was missing before)

---

## CIRCLE - Circle

**Format:**

```
CIRCLE~cx~cy~radius~stroke_width~layer_id~id~is_locked~[...]
```

**Example:**

```
CIRCLE~4011.819~2995~2.9528~5.9055~12~gge381~0~~
```

**Fields:**

| Index | Field        | Type   | Unit     | Description                   |
| ----- | ------------ | ------ | -------- | ----------------------------- |
| 0     | CIRCLE       | -      | -        | Command identifier            |
| 1     | cx           | float  | EE units | X coordinate of circle center |
| 2     | cy           | float  | EE units | Y coordinate of circle center |
| 3     | radius       | float  | EE units | Circle radius                 |
| 4     | stroke_width | float  | EE units | Border line width             |
| 5     | layer_id     | int    | -        | Layer ID                      |
| 6     | id           | string | -        | Unique element ID             |
| 7     | is_locked    | int    | -        | 1 if locked, 0 if unlocked    |

**Notes:**

- Drawn as outline circle in KiCad (fp_circle)
- `stroke_width` defines the line thickness

---

## HOLE - Non-Plated Hole

**Format:**

```
HOLE~center_x~center_y~radius~id~is_locked
```

**Example:**

```
HOLE~4011.819~2995~6.2598~gge130~0
```

**Fields:**

| Index | Field     | Type   | Unit     | Description                 |
| ----- | --------- | ------ | -------- | --------------------------- |
| 0     | HOLE      | -      | -        | Command identifier          |
| 1     | center_x  | float  | EE units | X coordinate of hole center |
| 2     | center_y  | float  | EE units | Y coordinate of hole center |
| 3     | radius    | float  | EE units | Hole radius                 |
| 4     | id        | string | -        | Unique element ID           |
| 5     | is_locked | int    | -        | 1 if locked, 0 if unlocked  |

**Notes:**

- Non-plated holes (mounting holes, mechanical holes)
- Diameter = radius × 2

---

## VIA - Via Connection

**Format:**

```
VIA~center_x~center_y~diameter~net~radius~id~is_locked
```

**Example:**

```
VIA~3978~3003~3.9370~VCC~4.9213~gge150~0
```

**Fields:**

| Index | Field     | Type   | Unit     | Description                |
| ----- | --------- | ------ | -------- | -------------------------- |
| 0     | VIA       | -      | -        | Command identifier         |
| 1     | center_x  | float  | EE units | X coordinate of via center |
| 2     | center_y  | float  | EE units | Y coordinate of via center |
| 3     | diameter  | float  | EE units | Via hole diameter          |
| 4     | net       | string | -        | Net name                   |
| 5     | radius    | float  | EE units | Via pad radius             |
| 6     | id        | string | -        | Unique element ID          |
| 7     | is_locked | int    | -        | 1 if locked, 0 if unlocked |

**Notes:**

- Plated through-hole connecting copper layers
- Converted to pad in KiCad with drill

---

## ARC - Arc Segment

**Format:**

```
ARC~stroke_width~layer_id~net~path~helper_dots~id~is_locked
```

**Example:**

```
ARC~1~3~~M 3980 3000 A 5 5 0 0 1 3985 3005~~gge200~0
```

**Fields:**

| Index | Field        | Type   | Unit     | Description                                           |
| ----- | ------------ | ------ | -------- | ----------------------------------------------------- |
| 0     | ARC          | -      | -        | Command identifier                                    |
| 1     | stroke_width | float  | EE units | Arc line width                                        |
| 2     | layer_id     | int    | -        | Layer ID                                              |
| 3     | net          | string | -        | Net name (usually empty)                              |
| 4     | path         | string | -        | SVG path (M x y A rx ry rotation large-arc sweep x y) |
| 5     | helper_dots  | string | -        | Helper dots for editing                               |
| 6     | id           | string | -        | Unique element ID                                     |
| 7     | is_locked    | int    | -        | 1 if locked, 0 if unlocked                            |

**Notes:**

- Path uses SVG arc format: `M startX startY A radiusX radiusY rotation large-arc-flag sweep-flag endX endY`
- Converted to KiCad fp_arc using arc computation

---

## TEXT - Text Label

**Format:**

```
TEXT~type~center_x~center_y~stroke_width~rotation~mirror~layer_id~net~font_size~text~text_path~is_displayed~id~is_locked
```

**Example:**

```
TEXT~P~3986~3003~1~0~0~13~~7~REF**~M3986,3003~1~gge300~0
```

**Fields:**

| Index | Field        | Type   | Unit     | Description                               |
| ----- | ------------ | ------ | -------- | ----------------------------------------- |
| 0     | TEXT         | -      | -        | Command identifier                        |
| 1     | type         | string | -        | Text type: "P"=Reference, "N"=Value, etc. |
| 2     | center_x     | float  | EE units | X coordinate of text center               |
| 3     | center_y     | float  | EE units | Y coordinate of text center               |
| 4     | stroke_width | float  | EE units | Text line thickness                       |
| 5     | rotation     | int    | degrees  | Text rotation (0, 90, 180, 270)           |
| 6     | mirror       | string | -        | Mirror flag                               |
| 7     | layer_id     | int    | -        | Layer ID                                  |
| 8     | net          | string | -        | Net name (usually empty)                  |
| 9     | font_size    | float  | EE units | Font size                                 |
| 10    | text         | string | -        | Text content                              |
| 11    | text_path    | string | -        | Text path for rendering                   |
| 12    | is_displayed | int    | -        | 1 if visible, 0 if hidden                 |
| 13    | id           | string | -        | Unique element ID                         |
| 14    | is_locked    | int    | -        | 1 if locked, 0 if unlocked                |

**Notes:**

- Type "N" is typically hidden in KiCad (value text on F.Fab)
- Type "P" is the reference designator

---

## SOLIDREGION - Filled Copper Region

**Format:**

```
SOLIDREGION~layer_id~~path~id~net~[...]
```

**Example:**

```
SOLIDREGION~100~~M 3976.4252 3009.7242 L 3979.5748 3009.7242 L 3979.5748 3012.8738 L 3976.4252 3012.8738 Z~solid~gge344~~~~0
```

**Fields:**

| Index | Field       | Type   | Unit | Description                                 |
| ----- | ----------- | ------ | ---- | ------------------------------------------- |
| 0     | SOLIDREGION | -      | -    | Command identifier                          |
| 1     | layer_id    | int    | -    | Layer ID (99=ComponentShape, 100=LeadShape) |
| 2     | ...         | -      | -    | Empty field                                 |
| 3     | path        | string | -    | SVG path defining the filled region         |
| 4+    | ...         | -      | -    | Additional fields                           |

**Notes:**

- ❌ Currently parsed but **NOT converted** to KiCad
- Used for filled copper areas and zones
- Path uses SVG format (M=move, L=line, Z=close path)

---

## SVGNODE - 3D Model Metadata

**Format:**

```
SVGNODE~{JSON}~...
```

**Example:**

```
SVGNODE~{"gId":"g1_outline","attrs":{"uuid":"ed3be94b43cd45f99a7c943270463433","title":"CONN-TH_TE_1-770174-0","c_origin":"3986.1495,3002.1653","z":"-16.5354","c_rotation":"0,0,0"}}~...
```

**Fields:**

| Index | Field   | Type   | Description               |
| ----- | ------- | ------ | ------------------------- |
| 0     | SVGNODE | -      | Command identifier        |
| 1     | JSON    | object | 3D model metadata as JSON |

**JSON Attributes:**

- `uuid`: 3D model UUID for downloading OBJ/STEP files
- `title`: 3D model name
- `c_origin`: Origin coordinates (x,y) in EE units
- `z`: Z-offset in EE units
- `c_rotation`: Rotation angles (x,y,z) in degrees
- `c_width`, `c_height`: 3D model bounding box dimensions

**Notes:**

- Used to extract 3D model information
- UUID is used to download .obj and .step files from EasyEDA servers
- See [CMD_3D_MODEL.md](CMD_3D_MODEL.md) for detailed 3D model download and conversion documentation

---

## Unit Conversion

**EasyEDA Units → Millimeters:**

```python
mm = easyeda_units * 10 * 0.0254
```

**Examples:**

- 1 EE unit = 10 mil = 0.254 mm
- 100 EE units = 1000 mil = 25.4 mm
- 3937 EE units = 39370 mil = 1000 mm

**Common stroke_width values:**

- 1 EE unit → 0.254 mm (thin lines, silkscreen)
- 3 EE units → 0.762 mm (thick lines, before our fix conversion)
- 3 EE units → 0.194 mm (after our fix with double conversion for rectangles)

---

## Layer IDs

| ID  | EasyEDA Name           | KiCad Layer | Usage               |
| --- | ---------------------- | ----------- | ------------------- |
| 0   | (undefined)            | F.Fab       | Default fallback    |
| 1   | TopLayer               | F.Cu        | Front copper        |
| 2   | BottomLayer            | B.Cu        | Back copper         |
| 3   | TopSilkLayer           | F.SilkS     | Front silkscreen    |
| 4   | BottomSilkLayer        | B.SilkS     | Back silkscreen     |
| 5   | TopPasteMaskLayer      | F.Paste     | Front solder paste  |
| 6   | BottomPasteMaskLayer   | B.Paste     | Back solder paste   |
| 7   | TopSolderMaskLayer     | F.Mask      | Front solder mask   |
| 8   | BottomSolderMaskLayer  | B.Mask      | Back solder mask    |
| 10  | BoardOutLine           | Edge.Cuts   | Board outline       |
| 11  | Multi-Layer            | _.Cu _.Mask | All copper layers   |
| 12  | Document               | Cmts.User   | Documentation       |
| 13  | TopAssembly            | F.Fab       | Front fabrication   |
| 14  | BottomAssembly         | B.Fab       | Back fabrication    |
| 15  | Mechanical             | Dwgs.User   | Mechanical drawings |
| 19  | 3DModel                | -           | 3D model layer      |
| 99  | ComponentShapeLayer    | F.Fab       | Component outline   |
| 100 | LeadShapeLayer         | F.Fab       | Lead shape          |
| 101 | ComponentPolarityLayer | F.Fab       | Polarity marking    |

---

## Recent Fixes

### Fix 1: Rectangle Missing Closing Line (2025)

**Problem:** The 4th line of rectangles had zero length (start == end)

```python
# Before (WRONG):
points_start_y = [start_y, start_y, start_y + height, start_y]  # Last should be start_y + height

# After (FIXED):
points_start_y = [start_y, start_y, start_y + height, start_y + height]
```

### Fix 2: Rectangle stroke_width Not Converted (2025)

**Problem:** `stroke_width` was not converted to mm in `EeFootprintRectangle.convert_to_mm()`

```python
# Before (MISSING):
def convert_to_mm(self):
    self.x = convert_to_mm(self.x)
    self.y = convert_to_mm(self.y)
    self.width = convert_to_mm(self.width)
    self.height = convert_to_mm(self.height)
    # stroke_width was NOT converted!

# After (FIXED):
def convert_to_mm(self):
    self.x = convert_to_mm(self.x)
    self.y = convert_to_mm(self.y)
    self.width = convert_to_mm(self.width)
    self.height = convert_to_mm(self.height)
    self.stroke_width = convert_to_mm(self.stroke_width)  # ADDED
```

**Result:** Rectangle lines now have correct width (~0.19 mm instead of 0.76 mm)
