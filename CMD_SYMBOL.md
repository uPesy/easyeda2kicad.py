# EasyEDA Symbol Commands Reference

This document provides a compact reference for all EasyEDA symbol shape commands with field definitions and real examples.

**Units**: Symbol coordinates use canvas pixels (virtual units). No direct conversion - symbols are drawn based on relative positioning.

## Command Overview

| Command | Description              | Implementation            |
| ------- | ------------------------ | ------------------------- |
| P       | Pin with number and name | ✅ Implemented            |
| R       | Rectangle                | ✅ Implemented            |
| C       | Circle                   | ✅ Implemented            |
| E       | Ellipse                  | ✅ Implemented            |
| A       | Arc                      | ✅ Implemented            |
| PL      | Polyline (open path)     | ✅ Implemented            |
| PG      | Polygon (closed path)    | ✅ Implemented            |
| PT      | Path (SVG path)          | ✅ Implemented            |
| T       | Text label               | ❌ Not parsed             |
| PI      | Pie/Elliptical arc       | ❌ Not supported in KiCad |

---

## P - Pin

**Format:**

```
P~visibility~locked~type~x~y~rotation~id~flags^^dot_x~dot_y^^path~color^^name_data^^number_data^^dot_data^^clock_data
```

**Example:**

```
P~show~0~1~350~310~180~gge6~0^^350~310^^M 350 310 h 10~#000000^^1~363.7~314~0~VSS~start~~~#000000^^1~359.5~309~0~1~end~~~#000000^^0~357~310^^0~M 360 313 L 363 310 L 360 307
```

**Structure (Split by `^^`):**

| Segment | Data           | Description                                         |
| ------- | -------------- | --------------------------------------------------- |
| 0       | Settings       | visibility~locked~type~x~y~rotation~id~flags        |
| 1       | Dot position   | dot_x~dot_y                                         |
| 2       | Pin path       | path~color                                          |
| 3       | Pin name       | show~x~y~rotation~text~text_anchor~font~color       |
| 4       | **Pin number** | show~x~y~rotation~**number**~text_anchor~font~color |
| 5       | Dot circle     | show~circle_x~circle_y                              |
| 6       | Clock symbol   | show~path                                           |

**Settings Fields:**

| Index | Field      | Type   | Description                                                          |
| ----- | ---------- | ------ | -------------------------------------------------------------------- |
| 0     | P          | -      | Command identifier                                                   |
| 1     | visibility | string | "show" or "hide"                                                     |
| 2     | locked     | int    | 1 if locked, 0 if unlocked                                           |
| 3     | type       | int    | Pin type: 0=unspecified, 1=input, 2=output, 3=bidirectional, 4=power |
| 4     | x          | float  | X coordinate                                                         |
| 5     | y          | float  | Y coordinate                                                         |
| 6     | rotation   | int    | Rotation angle (0, 90, 180, 270)                                     |
| 7     | id         | string | Unique element ID                                                    |
| 8     | flags      | int    | Additional flags                                                     |

**Pin Number Extraction:**

- Segment 4 (split by `^^`), field 4 contains the **correct KiCad pin number**
- Example: `1~359.5~309~0~1~end` → pin number is `1`

**Notes:**

- Pin path defines the visual line from the symbol to the pin connection point
- Name and number have independent visibility flags
- Dot circle is used for inverted pins (active low)
- Clock symbol appears on clock input pins

---

## R - Rectangle

**Format:**

```
R~x~y~rx~ry~width~height~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

**Example:**

```
R~360~298~2~2~80~34~#880000~1~0~none~gge4~0~
```

**Fields:**

| Index | Field        | Type   | Unit   | Description                                |
| ----- | ------------ | ------ | ------ | ------------------------------------------ |
| 0     | R            | -      | -      | Command identifier                         |
| 1     | x            | float  | pixels | X coordinate (top-left corner)             |
| 2     | y            | float  | pixels | Y coordinate (top-left corner)             |
| 3     | rx           | float  | pixels | X-radius for rounded corners (0 for sharp) |
| 4     | ry           | float  | pixels | Y-radius for rounded corners (0 for sharp) |
| 5     | width        | float  | pixels | Rectangle width                            |
| 6     | height       | float  | pixels | Rectangle height                           |
| 7     | stroke_color | string | -      | Border color (hex, e.g., "#880000")        |
| 8     | stroke_width | float  | pixels | Border line width                          |
| 9     | stroke_style | int    | -      | Line style (0=solid, 1=dashed, etc.)       |
| 10    | fill_color   | string | -      | Fill color ("none" for transparent)        |
| 11    | id           | string | -      | Unique element ID                          |
| 12    | locked       | int    | -      | 1 if locked, 0 if unlocked                 |

**Notes:**

- Can have rounded corners using rx/ry
- If rx=0 and ry=0, corners are sharp (90°)
- Fill color "none" means transparent/unfilled

---

## C - Circle

**Format:**

```
C~center_x~center_y~radius~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

**Example:**

```
C~400~300~5~#880000~1~0~none~gge10~0
```

**Fields:**

| Index | Field        | Type        | Unit   | Description                   |
| ----- | ------------ | ----------- | ------ | ----------------------------- |
| 0     | C            | -           | -      | Command identifier            |
| 1     | center_x     | float       | pixels | X coordinate of circle center |
| 2     | center_y     | float       | pixels | Y coordinate of circle center |
| 3     | radius       | float       | pixels | Circle radius                 |
| 4     | stroke_color | string      | -      | Border color (hex)            |
| 5     | stroke_width | float       | pixels | Border line width             |
| 6     | stroke_style | int         | -      | Line style                    |
| 7     | fill_color   | string/bool | -      | Fill color or "none"          |
| 8     | id           | string      | -      | Unique element ID             |
| 9     | locked       | int         | -      | 1 if locked, 0 if unlocked    |

---

## E - Ellipse

**Format:**

```
E~center_x~center_y~radius_x~radius_y~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

**Example:**

```
E~365~303~1.5~1.5~#880000~1~0~#880000~gge3~0
```

**Fields:**

| Index | Field        | Type        | Unit   | Description                    |
| ----- | ------------ | ----------- | ------ | ------------------------------ |
| 0     | E            | -           | -      | Command identifier             |
| 1     | center_x     | float       | pixels | X coordinate of ellipse center |
| 2     | center_y     | float       | pixels | Y coordinate of ellipse center |
| 3     | radius_x     | float       | pixels | Horizontal radius              |
| 4     | radius_y     | float       | pixels | Vertical radius                |
| 5     | stroke_color | string      | -      | Border color (hex)             |
| 6     | stroke_width | float       | pixels | Border line width              |
| 7     | stroke_style | int         | -      | Line style                     |
| 8     | fill_color   | string/bool | -      | Fill color or "none"           |
| 9     | id           | string      | -      | Unique element ID              |
| 10    | locked       | int         | -      | 1 if locked, 0 if unlocked     |

**Notes:**

- If radius_x == radius_y, it's effectively a circle
- Can be filled or outline only

---

## A - Arc

**Format:**

```
A~path~helper_dots~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

**Example:**

```
A~M 383.117 299.932 A 4 3.9 0 1 1 391.082 299.936~~#880000~1~0~none~gge17~0
```

**Fields:**

| Index | Field        | Type   | Description                                                                |
| ----- | ------------ | ------ | -------------------------------------------------------------------------- |
| 0     | A            | -      | Command identifier                                                         |
| 1     | path         | string | SVG arc path: `M startX startY A rx ry rotation large-arc sweep endX endY` |
| 2     | helper_dots  | string | Helper dots for visual editing (usually empty)                             |
| 3     | stroke_color | string | Line color (hex)                                                           |
| 4     | stroke_width | float  | Line width                                                                 |
| 5     | stroke_style | int    | Line style                                                                 |
| 6     | fill_color   | string | Fill color or "none"                                                       |
| 7     | id           | string | Unique element ID                                                          |
| 8     | locked       | int    | 1 if locked, 0 if unlocked                                                 |

**SVG Arc Path Format:**

- `M x y` - Move to start point
- `A rx ry rotation large-arc-flag sweep-flag x y` - Arc to end point
  - `rx, ry` - Radii
  - `rotation` - X-axis rotation
  - `large-arc-flag` - 0 or 1 (use larger arc)
  - `sweep-flag` - 0 or 1 (sweep direction)
  - `x, y` - End point

---

## PL - Polyline

**Format:**

```
PL~points~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

**Example:**

```
PL~380 290 390 290 390 310 380 310~#880000~1~0~none~gge8~0
```

**Fields:**

| Index | Field        | Type   | Unit   | Description                                          |
| ----- | ------------ | ------ | ------ | ---------------------------------------------------- |
| 0     | PL           | -      | -      | Command identifier                                   |
| 1     | points       | string | pixels | Space-separated coordinates: `x1 y1 x2 y2 x3 y3 ...` |
| 2     | stroke_color | string | -      | Line color (hex)                                     |
| 3     | stroke_width | float  | pixels | Line width                                           |
| 4     | stroke_style | int    | -      | Line style                                           |
| 5     | fill_color   | string | -      | Fill color (usually "none" for polyline)             |
| 6     | id           | string | -      | Unique element ID                                    |
| 7     | locked       | int    | -      | 1 if locked, 0 if unlocked                           |

**Notes:**

- **Open path** - does not automatically close back to start
- Typically not filled
- Used for drawing complex outlines

---

## PG - Polygon

**Format:**

```
PG~points~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

**Example:**

```
PG~380 290 390 290 390 310 380 310~#880000~1~0~#880000~gge9~0
```

**Fields:**

| Index | Field        | Type   | Unit   | Description                                          |
| ----- | ------------ | ------ | ------ | ---------------------------------------------------- |
| 0     | PG           | -      | -      | Command identifier                                   |
| 1     | points       | string | pixels | Space-separated coordinates: `x1 y1 x2 y2 x3 y3 ...` |
| 2     | stroke_color | string | -      | Border color (hex)                                   |
| 3     | stroke_width | float  | pixels | Border line width                                    |
| 4     | stroke_style | int    | -      | Line style                                           |
| 5     | fill_color   | string | -      | Fill color (can be filled or "none")                 |
| 6     | id           | string | -      | Unique element ID                                    |
| 7     | locked       | int    | -      | 1 if locked, 0 if unlocked                           |

**Notes:**

- **Closed path** - automatically closes back to first point
- Can be filled with solid color
- Used for solid shapes in symbols

---

## PT - Path

**Format:**

```
PT~path~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

**Example:**

```
PT~M 380 300 L 390 300 L 390 310~#880000~1~0~none~gge11~0
```

**Fields:**

| Index | Field        | Type   | Description                                      |
| ----- | ------------ | ------ | ------------------------------------------------ |
| 0     | PT           | -      | Command identifier                               |
| 1     | path         | string | SVG path data (M=move, L=line, C=curve, Z=close) |
| 2     | stroke_color | string | Line color (hex)                                 |
| 3     | stroke_width | float  | Line width                                       |
| 4     | stroke_style | int    | Line style                                       |
| 5     | fill_color   | string | Fill color or "none"                             |
| 6     | id           | string | Unique element ID                                |
| 7     | locked       | int    | 1 if locked, 0 if unlocked                       |

**SVG Path Commands:**

- `M x y` - Move to
- `L x y` - Line to
- `C x1 y1 x2 y2 x y` - Cubic Bezier curve
- `Q x1 y1 x y` - Quadratic Bezier curve
- `A rx ry rotation large-arc sweep x y` - Arc
- `Z` - Close path

**Notes:**

- Most flexible shape type
- Supports complex curves and Bezier paths
- Can combine multiple drawing operations

---

## T - Text Label (NOT IMPLEMENTED)

**Format:**

```
T~type~x~y~rotation~color~font~font_size~stroke_width~text_anchor~text_type~text~display~id~locked
```

**Example:**

```
T~L~400~290~0~#0000FF~Tahoma~11.5pt~0.1~~middle~comment~RP2040~1~middle~gge860~0~pinpart
```

**Status**: ❌ This shape type is **NOT** currently parsed by easyeda2kicad. Text labels on symbols are silently ignored.

**Impact**: Component names, values, and other text annotations on symbols will not appear in converted KiCad symbols.

---

## PI - Pie/Elliptical Arc (NOT SUPPORTED)

**Format**: Unknown

**Status**: ❌ Referenced in code but not implemented. Not supported in KiCad.

**Impact**: If components use pie-shaped or elliptical arc shapes, they will be silently ignored with a warning message.

---

## Coordinate System

**Symbol Coordinates:**

- Origin: Canvas top-left (0, 0)
- Units: Pixels (virtual canvas units)
- Y-axis: Increases **downward** (opposite of KiCad)
- No absolute unit conversion - symbols scale relative to pin spacing

**Bounding Box:**

- Defined by `dataStr.BBox` or fallback to `dataStr.head.x/y`
- Used to center the symbol in KiCad
- All coordinates are relative to this origin

**Conversion to KiCad:**

```python
# Symbol units to KiCad v6+ (mm)
ki_x_mm = (ee_x - bbox_x) * 10 * 0.0254
ki_y_mm = -(ee_y - bbox_y) * 10 * 0.0254  # Note: Y inverted
```

**Conversion to KiCad v5:**

```python
# Symbol units to KiCad v5 (mils)
ki_x_mils = (ee_x - bbox_x) * 10
ki_y_mils = -(ee_y - bbox_y) * 10  # Note: Y inverted
```

---

## Pin Types

| Value | Type          | Description                  |
| ----- | ------------- | ---------------------------- |
| 0     | Unspecified   | No electrical type specified |
| 1     | Input         | Input signal                 |
| 2     | Output        | Output signal                |
| 3     | Bidirectional | Input/output                 |
| 4     | Power         | Power or ground pin          |

---

## Stroke Styles

| Value | Style  | Description     |
| ----- | ------ | --------------- |
| 0     | Solid  | Continuous line |
| 1     | Dashed | Dashed line     |
| 2     | Dotted | Dotted line     |

---

## Common Colors

| Color | Hex Code | Usage             |
| ----- | -------- | ----------------- |
| Red   | #880000  | Symbol outlines   |
| Blue  | #0000FF  | Pin numbers, text |
| Black | #000000  | Pin paths         |
| Green | #008000  | Alternative       |

---

## Rectangle Format Variants

EasyEDA has **two formats** for rectangles:

**Format 1**: Without rounded corners

```
R~x~y~~width~height~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

- Empty fields at positions 3,4 (rx, ry)

**Format 2**: With rounded corners

```
R~x~y~rx~ry~width~height~stroke_color~stroke_width~stroke_style~fill_color~id~locked
```

- rx, ry values at positions 3,4

The parser handles both formats automatically.
