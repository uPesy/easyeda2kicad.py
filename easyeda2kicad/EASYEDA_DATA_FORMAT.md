# EasyEDA Data Format Documentation

This document describes the data format used by EasyEDA/LCSC for electronic components and how they are parsed and converted to KiCad format.

## Table of Contents

1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [JSON Structure](#json-structure)
4. [Symbol Data Format](#symbol-data-format)
5. [Footprint Data Format](#footprint-data-format)
6. [3D Model Data Format](#3d-model-data-format)
7. [Shape Designators Reference](#shape-designators-reference)
8. [Coordinate System and Units](#coordinate-system-and-units)
9. [Parsing Workflow](#parsing-workflow)
10. [Conversion to KiCad](#conversion-to-kicad)

---

## Overview

The EasyEDA to KiCad converter downloads component data from the EasyEDA API in JSON format. This data includes:

- **Symbol**: Schematic representation (pins, shapes, text)
- **Footprint**: PCB footprint (pads, silkscreen, copper regions)
- **3D Model**: 3D representation in OBJ and STEP formats
- **Metadata**: Component information (manufacturer, part number, datasheet, etc.)

The data uses a custom text-based format for shapes, where each shape is represented as a string with tilde-separated (`~`) fields.

### Implementation Status Legend

Throughout this document, you will see these markers indicating implementation status:

- ✅ **Fully Implemented** - Feature is completely parsed and converted to KiCad
- ⚠️ **Partially Implemented** - Feature is parsed but conversion may be incomplete or have limitations
- ❌ **Not Implemented** - Feature is present in EasyEDA data but not currently parsed or converted
- 🔍 **Undocumented** - Feature exists in data but is not well understood

---

## API Endpoints

### 1. Component Data API

**Endpoint**: `https://easyeda.com/api/products/{lcsc_id}/components?version=6.4.19.5`

**Method**: GET

**Parameters**:
- `{lcsc_id}`: LCSC part number (e.g., "C6568", "C167219")

**Response**: JSON object containing symbol, footprint, and metadata

**Features**:
- Supports gzip compression
- Requires custom User-Agent header: `easyeda2kicad v{version}`
- Returns empty dict on error

**Example Request**:
```python
url = "https://easyeda.com/api/products/C167219/components?version=6.4.19.5"
headers = {
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "easyeda2kicad v1.0.0"
}
```

### 2. 3D Model OBJ Format

**Endpoint**: `https://modules.easyeda.com/3dmodel/{uuid}`

**Method**: GET

**Parameters**:
- `{uuid}`: 3D model UUID from component data

**Response**: Text-based OBJ file with material definitions

### 3. 3D Model STEP Format

**Endpoint**: `https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}`

**Method**: GET

**Parameters**:
- `{uuid}`: 3D model UUID from component data

**Response**: Binary STEP file

**Note**: The path segment `qAxj6KHrDKw4blvCG8QJPs7Y` is a bucket identifier found in EasyEDA's JavaScript source.

---

## JSON Structure

### Top-Level Response

```json
{
  "success": true,
  "code": 0,
  "result": {
    "uuid": "component_unique_id",
    "title": "Component Name",
    "description": "Component description",
    "docType": 2,
    "type": 3,
    "thumb": "//image.easyeda.com/components/...",
    "lcsc": {
      "id": 178602,
      "number": "C167219",
      "step": 5,
      "min": 5,
      "price": 0.1078,
      "stock": 1415,
      "url": "https://lcsc.com/product-detail/..."
    },
    "owner": {
      "uuid": "owner_id",
      "username": "LCSC",
      "nickname": "LCSC"
    },
    "tags": ["Power Inductors"],
    "dataStr": { /* Symbol data - see below */ },
    "SMT": true,
    "packageDetail": { /* Footprint data - see below */ }
  }
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `uuid` | string | Unique component identifier |
| `title` | string | Component name/part number |
| `docType` | number | Document type (2 = symbol) |
| `type` | number | Component type (3 = standard component) |
| `SMT` | boolean | Surface mount technology flag |
| `dataStr` | object | Symbol data structure |
| `packageDetail` | object | Footprint data structure |
| `lcsc.number` | string | LCSC part number (e.g., "C167219") |
| `lcsc.price` | number | Component price in USD |
| `lcsc.stock` | number | Available stock quantity |

---

## Symbol Data Format

Symbol data is stored in the `dataStr` field and contains the schematic representation.

### Symbol Structure

```json
"dataStr": {
  "head": {
    "docType": "2",
    "editorVersion": "6.2.44",
    "x": 400,
    "y": 300,
    "c_para": {
      "pre": "L?",
      "name": "FXL0630-3R3-M",
      "package": "IND-SMD_L7.0-W6.6",
      "nameAlias": "Value",
      "Contributor": "LCSC",
      "Manufacturer": "cjiang",
      "Manufacturer Part": "FXL0630-3R3-M",
      "Value": "3.3uH",
      "Supplier Part": "C167219",
      "JLCPCB Part Class": "Extended Part"
    },
    "puuid": "package_uuid",
    "uuid": "component_uuid"
  },
  "canvas": "CA~1000~1000~#FFFFFF~yes~#CCCCCC~5~...",
  "shape": [
    "P~show~0~2~420~300~0~gge3~0^^420~300^^M 420 300 h -3~...",
    "A~M 383.117 299.932 A 4 3.9 0 1 1 391.082 299.936~~#880000~1~0~none~gge17~0"
  ],
  "BBox": {
    "x": 378,
    "y": 295.7,
    "width": 44,
    "height": 6.3
  }
}
```

### Symbol Metadata (`c_para`)

| Field | Description | Example |
|-------|-------------|---------|
| `pre` | Component prefix/designator | "U?", "R?", "L?" |
| `name` | Component name | "FXL0630-3R3-M" |
| `package` | Footprint package name | "IND-SMD_L7.0-W6.6" |
| `Manufacturer` | Manufacturer name | "cjiang" |
| `Manufacturer Part` | Manufacturer part number | "FXL0630-3R3-M" |
| `Value` | Component value | "3.3uH", "100nF" |
| `Supplier Part` | LCSC part number | "C167219" |
| `JLCPCB Part Class` | JLCPCB classification | "Basic Part", "Extended Part" |

### Symbol Bounding Box

The bounding box defines the actual extents of the symbol geometry:

```json
"BBox": {
  "x": 327.6,     // Left edge X coordinate (geometry origin)
  "y": 234.7,     // Top edge Y coordinate (geometry origin)
  "width": 144.7, // Width in pixels
  "height": 142.2 // Height in pixels
}
```

The parser uses `BBox.x/y` as the origin for all symbol coordinates, with fallback to `head.x/y` if BBox is not available.

### Symbol Shapes

The `shape` array contains shape definitions as tilde-separated strings. See [Shape Designators Reference](#shape-designators-reference) for detailed format.

**Symbol Shape Types and Implementation Status**:

| Designator | Shape Type | Status | Notes |
|------------|------------|--------|-------|
| `P` | Pin | ✅ Fully Implemented | Complete pin parsing with all segments |
| `R` | Rectangle | ✅ Fully Implemented | Handles format inconsistencies |
| `C` | Circle | ✅ Fully Implemented | |
| `E` | Ellipse | ⚠️ Partially Implemented | Only converted if rx == ry (becomes circle), true ellipses skipped |
| `A` | Arc | ✅ Fully Implemented | SVG arc parsing |
| `PL` | Polyline | ✅ Fully Implemented | |
| `PG` | Polygon | ✅ Fully Implemented | |
| `PT` | Path | ✅ Fully Implemented | SVG path with M, L, C, Z commands |
| `T` | Text | ❌ **NOT IMPLEMENTED** | Text labels on symbols are ignored |
| `PI` | Pie/Elliptical Arc | ❌ **NOT IMPLEMENTED** | Mentioned in code comment but no handler exists |

---

## Footprint Data Format

Footprint data is stored in the `packageDetail` field and contains the PCB footprint.

### Footprint Structure

```json
"packageDetail": {
  "uuid": "package_uuid",
  "title": "IND-SMD_L7.0-W6.6",
  "docType": 4,
  "dataStr": {
    "head": {
      "docType": "4",
      "editorVersion": "6.5.48",
      "c_para": {
        "package": "IND-SMD_L7.0-W6.6",
        "pre": "L?",
        "3DModel": "IND-SMD_L7.0-W6.6-H3.0"
      },
      "x": 3987.9646,
      "y": 3009,
      "uuid_3d": "43ba165dae7e4f5b88ae140d98d63cbd"
    },
    "canvas": "CA~1000~1000~#000000~yes~#FFFFFF~10~...",
    "shape": [
      "PAD~RECT~3976.154~3009~9.4488~12.5984~1~~1~0~...",
      "TRACK~1~3~~3974.1851 3000.8065 3974.1851 2996.0079~...",
      "SOLIDREGION~100~~M 3995.445 3003.0945 L 4001.7442 3003.0945~...",
      "SVGNODE~{\"gId\":\"g1_outline\",\"attrs\":{...}}~..."
    ],
    "layers": [
      "1~TopLayer~#FF0000~true~true~true~",
      "2~BottomLayer~#0000FF~true~false~true~"
    ]
  }
}
```

### Footprint Metadata (`c_para`)

| Field | Description | Example |
|-------|-------------|---------|
| `package` | Package name | "IND-SMD_L7.0-W6.6" |
| `pre` | Component prefix | "L?" |
| `3DModel` | 3D model name reference | "IND-SMD_L7.0-W6.6-H3.0" |

### Footprint Shapes

**Footprint Shape Types and Implementation Status**:

| Designator | Shape Type | Status | Notes |
|------------|------------|--------|-------|
| `PAD` | Solder pad | ✅ Fully Implemented | Through-hole and SMD, including custom polygon pads |
| `TRACK` | Copper track | ✅ Fully Implemented | |
| `HOLE` | Mounting hole | ✅ Fully Implemented | |
| `VIA` | Via connection | ✅ Fully Implemented | |
| `CIRCLE` | Circle | ✅ Fully Implemented | |
| `ARC` | Arc segment | ✅ Fully Implemented | |
| `RECT` | Rectangle | ✅ Fully Implemented | |
| `TEXT` | Text label | ✅ Fully Implemented | Reference designators, values, etc. |
| `SOLIDREGION` | Filled copper region | ❌ **NOT IMPLEMENTED** | Copper pours/zones are parsed but not converted |
| `SVGNODE` | 3D model metadata | ✅ Fully Implemented | Used to extract 3D model info |

### Layer Mapping

EasyEDA uses numeric layer IDs that map to KiCad layer names:

| EasyEDA ID | EasyEDA Name | KiCad Name | Purpose |
|------------|--------------|------------|---------|
| 1 | TopLayer | F.Cu | Front copper |
| 2 | BottomLayer | B.Cu | Back copper |
| 3 | TopSilkLayer | F.SilkS | Front silkscreen |
| 4 | BottomSilkLayer | B.SilkS | Back silkscreen |
| 5 | TopPasteMaskLayer | F.Paste | Front solder paste |
| 6 | BottomPasteMaskLayer | B.Paste | Back solder paste |
| 7 | TopSolderMaskLayer | F.Mask | Front solder mask |
| 8 | BottomSolderMaskLayer | B.Mask | Back solder mask |
| 10 | BoardOutLine | Edge.Cuts | Board outline |
| 11 | Multi-Layer | *.Cu *.Mask | All copper layers |
| 12 | Document | Dwgs.User | Documentation |
| 13 | TopAssembly | F.Fab | Front fabrication |
| 14 | BottomAssembly | B.Fab | Back fabrication |
| 99 | ComponentShapeLayer | F.Fab | Component outline |
| 100 | LeadShapeLayer | F.Fab | Lead shape |
| 101 | ComponentPolarityLayer | F.Fab | Polarity marking |

---

## 3D Model Data Format

3D model information is embedded in the footprint as an SVGNODE shape.

### SVGNODE Structure

```json
"SVGNODE~{
  \"gId\": \"g1_outline\",
  \"nodeName\": \"g\",
  \"attrs\": {
    \"uuid\": \"d792f813c1054fc4ac994ff75db25e02\",
    \"title\": \"IND-SMD_L7.0-W6.6-H3.0\",
    \"c_origin\": \"3987.9646,3009\",
    \"z\": \"0\",
    \"c_rotation\": \"0,0,0\"
  }
}~..."
```

### 3D Model Metadata

| Field | Type | Description |
|-------|------|-------------|
| `uuid` | string | 3D model UUID for downloading |
| `title` | string | 3D model name |
| `c_origin` | string | Translation offset (x,y) in footprint coordinates |
| `z` | string | Z-height offset |
| `c_rotation` | string | Rotation angles (rx,ry,rz) in degrees |

### 3D Model Files

**OBJ Format**:
- Text-based format with vertices, faces, and materials
- Contains material properties (Ka, Kd, Ks, d)
- Uses millimeter units

**STEP Format**:
- Binary CAD format
- Industry-standard for mechanical interchange
- Passed through without conversion

---

## Shape Designators Reference

All shapes use tilde (`~`) as field separator. Fields are positional, meaning their order matters.

### Pin (P)

**Format**: `P~visibility~locked~type~x~y~rotation~id~flags^^dot_x~dot_y^^path~color^^name_data^^number_data^^...`

**Example**: `P~show~0~2~420~300~0~gge3~0^^420~300^^M 420 300 h -3~#800^^0~413~300~0~2~end~~~#800^^0~421~296~0~2~start~~~#800^^0~420~300^^0~M 417 297 L 414 300 L 417 303`

**Segments** (split by `^^`):
1. Basic settings: `visibility~locked~type~x~y~rotation~id~flags`
2. Dot position: `dot_x~dot_y`
3. Pin path: `path~color`
4. Pin name data: `show~x~y~rotation~orientation~name~text~color`
5. **Pin number data**: `show~x~y~rotation~orientation~number~text~color`
   - `number` field (index 4 of this segment) contains the **correct KiCad pin number**
6. Dot bis: Circle indicator for inverted pins
7. Clock: Clock indicator path

**Pin Types**:
- `0` - Unspecified
- `1` - Input
- `2` - Output
- `3` - Bidirectional
- `4` - Power

**Visibility**:
- `show` - Pin is visible
- `hide` - Pin is hidden

**Path Format**: SVG path, typically `M x y h length` for horizontal pins

**IMPORTANT**: The pin number must be extracted from segment 4, field 4 (segment[4][4]), NOT from `spice_pin_number` in segment 0.

### Rectangle (R)

**Format**: `R~x~y~[empty]~[empty]~width~height~stroke_color~stroke_width~style~fill~id~locked~rx~ry`

**Example**: `R~380~290~~5~20~#FF0000~1~solid~none~gge5~0~0~0`

**Note**: Some rectangles have empty fields at indices 2-3. These must be detected and skipped during parsing.

**Fields**:
- `x`, `y` - Top-left corner position
- `width`, `height` - Dimensions
- `stroke_color` - Border color (hex)
- `stroke_width` - Border width
- `style` - Line style (solid, dashed, dotted)
- `fill` - Fill color or "none"
- `rx`, `ry` - Corner radius

### Circle (C)

**Format**: `C~cx~cy~radius~stroke_color~stroke_width~style~fill~id~locked`

**Example**: `C~400~300~10~#FF0000~1~solid~none~gge10~0`

**Fields**:
- `cx`, `cy` - Center position
- `radius` - Radius
- `stroke_color` - Border color
- `stroke_width` - Border width
- `style` - Line style
- `fill` - Fill color or "none"

### Ellipse (E)

**Format**: `E~cx~cy~rx~ry~stroke_color~stroke_width~style~fill~id~locked`

**Example**: `E~400~300~20~10~#FF0000~1~solid~none~gge12~0`

**Fields**:
- `cx`, `cy` - Center position
- `rx` - Horizontal radius
- `ry` - Vertical radius

**Note**: Only converted to KiCad if `rx == ry` (becomes a circle). True ellipses are not supported in KiCad symbols.

### Arc (A)

**Format**: `A~path~helper_dots~stroke_color~stroke_width~style~fill~id~locked`

**Example**: `A~M 383.117 299.932 A 4 3.9 0 1 1 391.082 299.936~~#880000~1~0~none~gge17~0`

**Path Format**: SVG elliptical arc
```
M start_x start_y A rx ry rotation large_arc_flag sweep_flag end_x end_y
```

**Flags**:
- `large_arc_flag` - 0 for arc <180°, 1 for arc >180°
- `sweep_flag` - 0 for counter-clockwise, 1 for clockwise

### Polyline (PL)

**Format**: `PL~points~stroke_color~stroke_width~style~fill~id~locked`

**Example**: `PL~380 300 390 310 400 300~#FF0000~1~solid~none~gge20~0`

**Points Format**: Space-separated x,y pairs: `x1 y1 x2 y2 x3 y3 ...`

### Polygon (PG)

**Format**: Same as Polyline but automatically closed

**Example**: `PG~380 300 390 310 400 300~#FF0000~1~solid~#FFCCCC~gge22~0`

### Path (PT)

**Format**: `PT~path~stroke_color~stroke_width~style~fill~id~locked`

**Example**: `PT~M 380 300 L 390 310 C 395 315 405 315 410 310 Z~#FF0000~1~solid~none~gge24~0`

**SVG Commands**:
- `M x y` - Move to
- `L x y` - Line to
- `H x` - Horizontal line to x
- `V y` - Vertical line to y
- `C x1 y1 x2 y2 x y` - Cubic Bezier curve
- `Z` - Close path

### Text (T) - ❌ NOT IMPLEMENTED

**Format**: `T~type~x~y~rotation~color~font~font_size~stroke_width~~text_anchor~text_type~text~display~text_anchor_2~id~locked~pinpart`

**Example**: `T~L~400~290~0~#0000FF~Tahoma~11.5pt~0.1~~middle~comment~RP2040~1~middle~gge860~0~pinpart`

**Status**: This shape type is NOT currently parsed by easyeda2kicad. Text labels on symbols are silently ignored.

**Fields** (Inferred from example):
- `type` - Text type (L = Label?)
- `x`, `y` - Position coordinates
- `rotation` - Rotation angle
- `color` - Text color (hex)
- `font` - Font family name
- `font_size` - Font size (e.g., "11.5pt")
- `stroke_width` - Stroke width
- `text_anchor` - Text alignment
- `text_type` - Type of text (e.g., "comment")
- `text` - Actual text content
- `display` - Visibility flag
- `id` - Unique identifier
- `locked` - Lock status

**Impact**: Component names, values, and other text annotations on symbols will not appear in converted KiCad symbols.

### Pie/Elliptical Arc (PI) - ❌ NOT IMPLEMENTED

**Format**: Unknown (not found in sample data)

**Status**: Referenced in code comment `# "PI" : Pie, Elliptical arc seems to be not supported in Kicad` but no parser implementation exists.

**Impact**: If components use pie-shaped or elliptical arc shapes, they will be silently ignored with a warning message.

### Pad (PAD)

**Format**: `PAD~shape~x~y~width~height~layer~net~number~hole_radius~points~rotation~id~hole_length~hole_point~plated~locked`

**Example**: `PAD~RECT~3976.154~3009~9.4488~12.5984~1~~1~0~3971.4296 3002.7008 3980.8784 3002.7008~0~gge5~0~~Y~0`

**Shapes**:
- `RECT` - Rectangle
- `OVAL` - Oval/obround
- `ELLIPSE` - Ellipse
- `POLYGON` - Custom polygon

**Through-hole Detection**:
- `hole_radius > 0` indicates through-hole pad
- `plated = "Y"` for plated through-hole
- `plated = "N"` for non-plated hole

**Layer**:
- `1` - Top layer only
- `2` - Bottom layer only
- `11` - All layers (through-hole)

**Custom Polygon Pads**:
- When shape is `POLYGON`, the `points` field contains polygon vertices
- Points are space-separated: `x1 y1 x2 y2 x3 y3 ...`

### Track (TRACK)

**Format**: `TRACK~width~layer~net~points~id~locked`

**Example**: `TRACK~1~3~~3974.1851 3000.8065 3974.1851 2996.0079~gge256~0`

**Fields**:
- `width` - Track width
- `layer` - Layer ID
- `net` - Net name (empty for silkscreen)
- `points` - Space-separated points: `x1 y1 x2 y2 ...`

### Solid Region (SOLIDREGION) - ❌ NOT IMPLEMENTED

**Format**: `SOLIDREGION~layer~path~...`

**Example**: `SOLIDREGION~100~~M 3995.445 3003.0945 L 4001.7442 3003.0945 L 4001.7442 3014.9055 Z~solid~gge102~...`

**Status**: SOLIDREGION shapes are detected in the parser but explicitly ignored (see `easyeda_importer.py:402`). They are NOT converted to KiCad copper zones or filled regions.

**Usage**: In EasyEDA, these represent filled copper regions, typically for:
- Thermal relief pads
- Ground planes
- Copper pours
- Component body outlines on fabrication layer

**Path Format**: SVG path with M (move), L (line), Z (close) commands

**Impact**: Footprints will be missing copper fill regions. This can affect:
- Thermal performance (missing thermal relief)
- Component appearance on fabrication layer
- Ground plane connections
- EMI shielding regions

**Workaround**: SOLIDREGION data is still present in the parsed data structure, but the exporter does not process it. Manual recreation in KiCad may be necessary for critical thermal or electrical performance.

### Hole (HOLE)

**Format**: `HOLE~x~y~radius~id~locked`

**Example**: `HOLE~4000~3010~1.5~gge50~0`

**Usage**: Non-plated mounting or alignment holes

### Via (VIA)

**Format**: `VIA~x~y~diameter~net~radius~id~locked`

**Example**: `VIA~4000~3010~0.8~~0.3~gge52~0`

**Usage**: Electrical connections between layers

### Text (TEXT)

**Format**: `TEXT~type~x~y~width~rotation~mirror~layer~net~font_size~text~path~display~id~locked`

**Example**: `TEXT~L~4000~3010~0~0~0~3~~12~Reference~M 4000 3010~~gge60~0`

**Types**:
- `L` - Label
- `P` - Property/attribute
- `N` - Name
- `V` - Value

---

## Coordinate System and Units

### EasyEDA Coordinate System

**Symbol Coordinates**:
- Origin: Canvas top-left (0, 0)
- Units: Pixels (virtual canvas units)
- Y-axis: Increases downward
- Bounding box: Defines symbol extents

**Footprint Coordinates**:
- Origin: Canvas center or arbitrary point
- Units: "mils" × 10 (where 1 mil = 0.001 inch)
- Conversion to mm: `value × 10 × 0.0254`
- Y-axis: Increases downward

### Unit Conversions

**Symbol to KiCad v5** (mils):
```
ki_value_mils = ee_value_pixels × 10
```

**Symbol to KiCad v6+** (mm):
```
ki_value_mm = ee_value_pixels × 10 × 0.0254
```

**Footprint to KiCad** (mm):
```
ki_value_mm = ee_value_easyeda × 10 × 0.0254
```

### Coordinate Transformation

**Y-axis Inversion**:
```python
ki_y = -ee_y  # KiCad uses upward Y-axis
```

**Relative to Bounding Box**:
```python
ki_x = ee_x - bbox.x
ki_y = -(ee_y - bbox.y)
```

---

## Parsing Workflow

### 1. Component Data Download

```python
from easyeda2kicad.easyeda.easyeda_api import EasyedaApi

api = EasyedaApi()
component_data = api.get_cad_data_of_component("C167219")
```

### 2. Symbol Parsing

**Implementation**: `easyeda_importer.py::EasyedaSymbolImporter`

**Steps**:
1. Extract metadata from `dataStr.head.c_para`
2. Parse bounding box from `dataStr.head` (x, y)
3. Iterate through `dataStr.shape` array:
   - Split each shape by `~` to get designator
   - Dispatch to appropriate handler based on designator
   - Create dataclass instance with parsed fields
4. Special handling for pins:
   - Split by `^^` to get segments
   - Extract pin number from segment[4][4]
   - Parse pin path, name, and style flags
5. Convert string fields to proper types (float, int, bool)

### 3. Footprint Parsing

**Implementation**: `easyeda_importer.py::EasyedaFootprintImporter`

**Steps**:
1. Extract metadata from `packageDetail.dataStr.head.c_para`
2. Determine footprint type:
   ```python
   is_smd = component["SMT"] and "-TH_" not in package_title
   fp_type = "smd" if is_smd else "tht"
   ```
3. Parse bounding box
4. Iterate through `packageDetail.dataStr.shape` array:
   - Create appropriate dataclass for each shape
   - Special handling for SVGNODE (3D model info)
5. Apply unit conversion: `value_mm = value × 10 × 0.0254`

### 4. 3D Model Parsing

**Implementation**: `easyeda_importer.py::Easyeda3dModelImporter`

**Steps**:
1. Find SVGNODE in footprint shape array
2. Parse JSON from SVGNODE data
3. Extract model UUID and transformation data
4. Download model files:
   ```python
   obj_data = api.get_raw_3d_model_obj(uuid)
   step_data = api.get_step_3d_model(uuid)
   ```
5. Store in `Ee3dModel` dataclass

---

## Conversion to KiCad

### Symbol Conversion

**Implementation**: `export_kicad_symbol.py::ExporterSymbolKicad`

#### Coordinate Transformation

**KiCad v5 (mils)**:
```python
ki_x_mils = (ee_x - bbox.x) × 10
ki_y_mils = -(ee_y - bbox.y) × 10
```

**KiCad v6+ (mm)**:
```python
ki_x_mm = (ee_x - bbox.x) × 10 × 0.0254
ki_y_mm = -(ee_y - bbox.y) × 10 × 0.0254
```

#### Pin Conversion

**Pin Length Extraction**:
```python
# From path like "M 420 300 h -3"
path_parts = path.split("h")
pin_length = abs(int(float(path_parts[-1])))
```

**Pin Type Mapping**:
| EasyEDA | KiCad |
|---------|-------|
| 0 | unspecified |
| 1 | input |
| 2 | output |
| 3 | bidirectional |
| 4 | power_in |

**Pin Style**:
- dot + clock → `inverted_clock`
- dot only → `inverted`
- clock only → `clock`
- neither → `line`

#### Shape Conversion

**Rectangles**:
```python
# Convert to two corner coordinates
x1, y1 = transform(ee_x, ee_y)
x2, y2 = transform(ee_x + width, ee_y + height)
```

**Circles**:
```python
center_x, center_y = transform(ee_cx, ee_cy)
radius = ee_radius × scale_factor
```

**Arcs**:
- Compute center point from SVG arc parameters
- Calculate start and end angles
- Convert to KiCad arc format (center, start point, end point)

**Polylines/Polygons**:
```python
points = ee_points.split()
for i in range(0, len(points), 2):
    x, y = transform(float(points[i]), float(points[i+1]))
```

**Paths**:
- Parse SVG path commands (M, L, H, V, C, Z)
- Convert to KiCad polyline or polygon

### Footprint Conversion

**Implementation**: `export_kicad_footprint.py::ExporterFootprintKicad`

#### Coordinate Transformation

```python
# Convert EasyEDA to mm and make relative to bbox
ki_x_mm = (ee_x - bbox.x) × 10 × 0.0254
ki_y_mm = (ee_y - bbox.y) × 10 × 0.0254
```

#### Pad Conversion

**Shape Mapping**:
| EasyEDA | KiCad |
|---------|-------|
| RECT | rect |
| OVAL | oval |
| ELLIPSE | circle (if rx==ry) |
| POLYGON | custom |

**Through-hole Detection**:
```python
if hole_radius > 0:
    if hole_length > 0:
        # Oval hole
        drill = f"(drill oval {hole_width} {hole_length})"
    else:
        # Round hole
        drill = f"(drill {diameter})"
```

**Custom Polygon Pads**:
```python
# Base pad at minimal size
(pad "1" smd custom (at 0 0) (size 0.005 0.005)
  (layers "F.Cu" "F.Paste" "F.Mask")
  (options (clearance outline) (anchor rect))
  (primitives
    (gr_poly
      (pts
        (xy x1 y1)
        (xy x2 y2)
        ...
      )
      (width 0)
    )
  )
)
```

#### Layer Conversion

```python
LAYER_MAP = {
    1: "F.Cu",      # Top copper
    2: "B.Cu",      # Bottom copper
    3: "F.SilkS",   # Top silkscreen
    4: "B.SilkS",   # Bottom silkscreen
    10: "Edge.Cuts",
    11: "*.Cu *.Mask",  # Through-hole
    12: "Dwgs.User"
}
```

#### Arc Computation

Implements W3C SVG elliptical arc endpoint-to-center conversion:

```python
def svg_arc_to_center_parameterization(
    start_x, start_y, rx, ry, rotation,
    large_arc_flag, sweep_flag, end_x, end_y
):
    # 1. Compute center point
    # 2. Compute start and end angles
    # 3. Calculate angle extent
    # Returns: (cx, cy, start_angle, end_angle)
```

#### 3D Model Integration

**Position Adjustment**:
```python
# Make relative to footprint bbox
x = model_3d.translation.x - bbox.x
y = model_3d.translation.y - bbox.y

# Z-height: inverted for SMD, 0 for through-hole
z = -model_3d.translation.z if fp_type == "smd" else 0
```

**Rotation Conversion**:
```python
# EasyEDA uses 0-360°, KiCad expects 0-360°
rx = 360 - model_3d.rotation.x
ry = 360 - model_3d.rotation.y
rz = 360 - model_3d.rotation.z
```

**KiCad Output**:
```
(model "${EASYEDA2KICAD}/IND-SMD_L7.0-W6.6-H3.0.wrl"
  (at (xyz x y z))
  (scale (xyz 1 1 1))
  (rotate (xyz rx ry rz))
)
```

### 3D Model Conversion

**Implementation**: `export_kicad_3d_model.py::Exporter3dModelKicad`

#### OBJ to WRL (VRML) Conversion

**Parsing OBJ**:
1. Extract material definitions (newmtl blocks):
   ```
   newmtl material_name
   Ka 0.2 0.2 0.2    # Ambient color
   Kd 0.8 0.8 0.8    # Diffuse color
   Ks 0.5 0.5 0.5    # Specular color
   d 1.0              # Dissolve (opacity)
   ```

2. Extract vertices (v lines):
   ```
   v 1.234 5.678 9.012
   ```

3. Extract faces grouped by material (usemtl, f lines):
   ```
   usemtl material_name
   f 1 2 3
   f 2 3 4
   ```

**Coordinate Conversion**:
```python
# OBJ uses mm, KiCad WRL uses inches
inch = mm / 25.4
```

**VRML Generation**:
```vrml
#VRML V2.0 utf8

Shape {
  appearance Appearance {
    material Material {
      diffuseColor R G B
      specularColor R G B
      ambientIntensity intensity
      transparency alpha
    }
  }
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        x1 y1 z1,
        x2 y2 z2,
        ...
      ]
    }
    coordIndex [
      v1, v2, v3, -1,
      v4, v5, v6, -1,
      ...
    ]
  }
}
```

#### STEP Pass-through

STEP files are binary CAD format and passed through without conversion:
```python
with open(output_path, 'wb') as f:
    f.write(step_data)
```

---

## Data Format Quirks and Special Cases

### 1. String Type Conversions

All EasyEDA data comes as strings and requires safe conversion:

```python
def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except:
        return default

def safe_int(value, default=0):
    try:
        # Convert via float first to handle "1.0" → 1
        return int(float(value)) if value else default
    except:
        return default

def safe_bool(value):
    return str(value).lower() in ("true", "1", "yes", "on", "show")
```

### 2. Rectangle Format Inconsistency

Some rectangles have empty fields at indices 2-3:

```python
# Incorrect format: R~x~y~~width~height~...
# Expected format: R~x~y~width~height~...

def parse_rectangle(fields):
    if fields[2] == '' and fields[3] == '':
        # Skip empty fields
        x, y = fields[0], fields[1]
        width, height = fields[4], fields[5]
        remaining = fields[6:]
    else:
        x, y = fields[0], fields[1]
        width, height = fields[2], fields[3]
        remaining = fields[4:]
```

### 3. Pin Number Extraction

**CRITICAL**: Pin number MUST be extracted from segment 4, element 4, NOT from spice_pin_number:

```python
# Split by ^^
segments = pin_string.split("^^")

# Segment 4 contains pin number data
if len(segments) > 4:
    number_data = segments[4].split("~")
    if len(number_data) > 4:
        correct_pin_number = number_data[4]  # THIS is the correct number
```

The `spice_pin_number` in segment 0 may be incorrect for KiCad purposes.

### 4. SMD vs Through-Hole Detection

```python
is_smd = bool(component["SMT"]) and "-TH_" not in package_title
fp_type = "smd" if is_smd else "tht"
```

Through-hole components often have "-TH" or "-TH_" in the package name even if SMT flag is True.

### 5. 3D Model Z-Height

For SMD components, the z-translation is inverted in KiCad:

```python
if fp_type == "smd":
    z = -round(model_3d.translation.z, 2)
else:
    z = 0  # Through-hole components sit at PCB surface
```

### 6. Path Command Handling

Pin paths may use `v` (vertical) which should be replaced with `h` (horizontal):

```python
path = path.replace("v", "h")
```

This appears to be an EasyEDA quirk where vertical and horizontal are sometimes swapped.

### 7. Custom Polygon Pads

Custom polygon pads require a minimal base pad to avoid visual artifacts:

```python
# Base pad size: 0.005mm (minimal)
(size 0.005 0.005)

# Actual shape in primitives
(primitives
  (gr_poly ...)
)
```

If the base pad is too large, it will be visible outside the polygon.

### 8. Pin Path Length

Pin length must be extracted from the SVG path, not from coordinates:

```python
# Path format: "M x y h length" or "M x y v length"
parts = path.replace("v", "h").split("h")
if len(parts) > 1:
    pin_length = abs(int(float(parts[-1])))
else:
    pin_length = 0  # Pin with no length
```

### 9. Arc Angle Calculation

SVG arcs use endpoint parameterization, but KiCad uses center parameterization:

```python
# SVG: M x1 y1 A rx ry rotation large_arc sweep x2 y2
# KiCad: (arc (start x1 y1) (mid xm ym) (end x2 y2))

# Must compute center point and angles, then convert to 3-point arc
```

### 10. Layer Assignment for Shapes

Shapes without explicit layer IDs default based on shape type:

- Symbols: All shapes go to symbol body (no layer concept)
- Footprints:
  - PAD with layer 11 → `*.Cu *.Mask` (all layers)
  - TRACK on layer 3 → `F.SilkS` (front silkscreen)
  - SOLIDREGION on layer 100 → `F.Fab` (front fabrication)

---

## Example: Complete Component

### Example Component: FXL0630-3R3-M (C167219)

**Component Type**: Power Inductor
**Package**: IND-SMD_L7.0-W6.6
**Value**: 3.3uH

**Symbol** (2 pins, 4 arcs representing inductor coils):
```
Pin 1: At (380, 300), type input
Pin 2: At (420, 300), type output
Arc 1: Coil segment 1
Arc 2: Coil segment 2
Arc 3: Coil segment 3
Arc 4: Coil segment 4
```

**Footprint** (2 SMD pads):
```
Pad 1: Rectangular, 9.45mm × 12.60mm, front copper
Pad 2: Rectangular, 9.45mm × 12.60mm, front copper
Solid regions: Copper pour areas (3 regions)
Tracks: Silkscreen outlines (3 tracks)
```

**3D Model**:
```
Name: IND-SMD_L7.0-W6.6-H3.0
UUID: 43ba165dae7e4f5b88ae140d98d63cbd
Translation: (3987.96, 3009, 0)
Rotation: (0, 0, 0)
```

---

## File Locations in Codebase

| Purpose | File Path |
|---------|-----------|
| API Client | `easyeda2kicad/easyeda/easyeda_api.py` |
| Data Structures | `easyeda2kicad/easyeda/parameters_easyeda.py` |
| Import/Parse | `easyeda2kicad/easyeda/easyeda_importer.py` |
| Symbol Export | `easyeda2kicad/kicad/export_kicad_symbol.py` |
| Footprint Export | `easyeda2kicad/kicad/export_kicad_footprint.py` |
| 3D Model Export | `easyeda2kicad/kicad/export_kicad_3d_model.py` |
| Main Entry Point | `easyeda2kicad/__main__.py` |
| SVG Parser | `easyeda2kicad/easyeda/svg_path_parser.py` |

---

## Summary of Known Limitations and Missing Features

This section summarizes all features that are not fully implemented in the current version of easyeda2kicad.

### Symbol Conversion Limitations

| Feature | Status | Impact | Reference |
|---------|--------|--------|-----------|
| Text annotations (T) | ❌ Not Implemented | Component labels, values, and notes on symbols are lost | See "Text (T)" in Shape Designators |
| Pie/Elliptical arcs (PI) | ❌ Not Implemented | Pie-shaped or special arc segments will be missing | See "Pie/Elliptical Arc (PI)" |
| True ellipses (E) | ⚠️ Partial | Only circular ellipses (rx==ry) converted; true ellipses ignored | See "Ellipse (E)" |
| SVG Bezier curves in paths | ⚠️ Approximated | Bezier curves in PT shapes may be simplified to straight segments | See `parameters_easyeda.py:345-347` |

### Footprint Conversion Limitations

| Feature | Status | Impact | Reference |
|---------|--------|--------|-----------|
| SOLIDREGION copper fills | ❌ Not Implemented | Thermal reliefs, ground planes, copper pours are missing | See "Solid Region (SOLIDREGION)" |

### Data Structure Discrepancies

| Issue | Description | Location |
|-------|-------------|----------|
| Rectangle empty fields | Some rectangles have empty fields at indices 2,3 requiring special handling | `easyeda_importer.py:192-197` |
| Pin number location | Correct pin number in segment[4][4], NOT in spice_pin_number | `easyeda_importer.py:91-107` |
| Path v→h conversion | Vertical path commands incorrectly used, must be replaced with horizontal | `parameters_easyeda.py:122` |
| ✅ **Bounding Box parsing (FIXED)** | Now correctly uses BBox.x/y (geometry bounds) instead of head.x/y (canvas position). Width/height fields added. | `easyeda_importer.py:293-321`, `parameters_easyeda.py:55-69` |

### Conversion Quality Notes

1. **Symbol Text Loss**: All text annotations on symbols (component names, values, notes) are completely lost during conversion. This can make symbols harder to identify in schematics.

2. **Thermal Performance**: Missing SOLIDREGION data means footprints lack thermal relief patterns. This can affect heat dissipation for power components.

3. **Visual Accuracy**: Bezier curves and true ellipses may be simplified or omitted, causing visual differences between EasyEDA and KiCad representations.

4. **Copper Fill Regions**: Any copper pours or ground plane sections defined in SOLIDREGION will be absent from KiCad footprints and must be manually recreated.

### Recommended Actions for Users

- **After conversion**, manually inspect symbols for missing text and add labels as needed
- **For power components**, verify or add thermal relief patterns to pads
- **For complex shapes**, check that curves and arcs converted correctly
- **For copper pours**, manually recreate SOLIDREGION areas using KiCad's zone/pour tools

---

## Further Reading

- [EasyEDA API Documentation](https://easyeda.com/Doc/Tutorial/API.htm) (if available)
- [KiCad File Formats](https://dev-docs.kicad.org/en/file-formats/)
- [SVG Path Specification](https://www.w3.org/TR/SVG/paths.html)
- [VRML 2.0 Specification](https://www.web3d.org/standards)

---

## Changelog

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2025-11-03 | Initial comprehensive documentation |

---

## Contributing

When contributing to the parser or converter, please ensure:

1. All new shape types are documented in this file
2. Coordinate transformations are clearly explained
3. Edge cases and quirks are noted in the "Special Cases" section
4. Example data is provided for complex formats
5. Unit tests cover the parsing and conversion logic

---

## License

This documentation is part of the easyeda2kicad project and follows the same license.
