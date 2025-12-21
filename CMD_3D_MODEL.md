# EasyEDA 3D Model Format Reference

This document describes how 3D models are obtained and integrated into KiCad footprints.

**Key Concept**: 3D models are **downloaded** from EasyEDA servers (OBJ + STEP), not generated locally.

---

## Workflow Overview

1. Extract UUID and metadata from SVGNODE in footprint data
2. Download OBJ and STEP files from EasyEDA using UUID
3. Convert OBJ → WRL (VRML) for KiCad visualization
4. Pass-through STEP files unchanged (binary)
5. Reference models in footprint with coordinate transformation

---

## SVGNODE Metadata

See [CMD_FOOTPRINT.md](CMD_FOOTPRINT.md#svgnode---3d-model-metadata) for command format.

**Example:**

```
SVGNODE~{"gId":"g1_outline","attrs":{"uuid":"43ba165dae7e4f5b88ae140d98d63cbd","title":"IND-SMD_L7.0-W6.6-H3.0","c_origin":"3987.9646,3009","z":"0","c_rotation":"0,0,0"}}~...
```

**Attributes:**

| Field        | Type   | Description                    | Example                  |
| ------------ | ------ | ------------------------------ | ------------------------ |
| `uuid`       | string | Model identifier for download  | "43ba165d..."            |
| `title`      | string | Model name (becomes filename)  | "IND-SMD_L7.0-W6.6-H3.0" |
| `c_origin`   | string | Translation (x,y) in EE units  | "3987.9646,3009"         |
| `z`          | string | Z-height in EE units           | "0"                      |
| `c_rotation` | string | Rotation (rx,ry,rz) in degrees | "0,0,0"                  |

## Download Endpoints

### OBJ Format (Text-based)

**Endpoint:**

```
https://modules.easyeda.com/3dmodel/{uuid}
```

**Response:** Text file with vertices and materials

**Units:** Millimeters

### STEP Format (Binary CAD)

**Endpoint:**

```
https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}
```

**Response:** Binary STEP file (ISO 10303-21)

**Notes:**

- `qAxj6KHrDKw4blvCG8QJPs7Y` is EasyEDA's storage bucket ID
- STEP files are passed through unchanged

---

## OBJ File Structure

**Material Block:**

```obj
newmtl material_name
Ka 0.2 0.2 0.2    # Ambient color (R G B)
Kd 0.8 0.8 0.8    # Diffuse color (R G B)
Ks 0.5 0.5 0.5    # Specular color (R G B)
d 1.0              # Dissolve/opacity (0.0-1.0)
endmtl
```

**Vertices:**

```obj
v 1.234 5.678 9.012
v 2.345 6.789 0.123
```

**Faces:**

```obj
usemtl material_name
f 1 2 3           # Triangle using vertices 1,2,3
f 2 3 4
```

---

## OBJ → WRL Conversion

### Coordinate Conversion

**OBJ (mm) → WRL (inches):**

```python
inch = mm / 25.4
```

**Example:**

- OBJ: `v 25.4 50.8 76.2` (mm)
- WRL: `1.0 2.0 3.0` (inches)

### VRML Output Format

```vrml
#VRML V2.0 utf8

Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0.8 0.8 0.8
      specularColor 0.5 0.5 0.5
      ambientIntensity 0.2
      transparency 0
      shininess 0.5
    }
  }
  geometry IndexedFaceSet {
    ccw TRUE
    solid FALSE
    coord Coordinate {
      point [ 1.0 2.0 3.0, 2.0 3.0 4.0, ... ]
    }
    coordIndex [ 0, 1, 2, -1, 1, 2, 3, -1, ... ]
  }
}
```

**Notes:**

- Each OBJ material → separate VRML Shape
- Vertex indices: 1-based (OBJ) → 0-based (VRML)
- Face delimiter: `-1`

---

## Coordinate Transformation

### Translation

```python
# Make relative to footprint bounding box
x_mm = (model_3d.translation.x - bbox.x) * 10 * 0.0254
y_mm = (model_3d.translation.y - bbox.y) * 10 * 0.0254

# Z-height
if fp_type == "smd":
    z_mm = -round(model_3d.translation.z * 10 * 0.0254, 2)  # Inverted
else:
    z_mm = 0  # Through-hole at PCB surface
```

### Rotation

```python
# EasyEDA → KiCad (degrees)
rx = 360 - model_3d.rotation.x
ry = 360 - model_3d.rotation.y
rz = 360 - model_3d.rotation.z
```

### Unit Conversion

**EasyEDA Units → Millimeters:**

```python
mm = easyeda_units * 10 * 0.0254
```

---

## KiCad Footprint Integration

**Model Reference:**

```
(model "${EASYEDA2KICAD}/IND-SMD_L7.0-W6.6-H3.0.wrl"
  (at (xyz -0.635 0.127 -0.508))
  (scale (xyz 1 1 1))
  (rotate (xyz 0 0 0))
)

(model "${EASYEDA2KICAD}/IND-SMD_L7.0-W6.6-H3.0.step"
  (at (xyz -0.635 0.127 -0.508))
  (scale (xyz 1 1 1))
  (rotate (xyz 0 0 0))
)
```

**File Structure:**

```
MyLibrary.pretty/
  └── Footprint.kicad_mod
MyLibrary.3dshapes/
  ├── IND-SMD_L7.0-W6.6-H3.0.wrl   # VRML (converted from OBJ)
  └── IND-SMD_L7.0-W6.6-H3.0.step  # STEP (binary pass-through)
```

## Limitations

| Issue                  | Description                                 |
| ---------------------- | ------------------------------------------- |
| Network Required       | 3D models cannot be obtained offline        |
| Material Approximation | VRML may not perfectly match OBJ appearance |
| Server Dependency      | Requires EasyEDA servers to be available    |

---

## Debug Caching

Enable local caching for faster re-conversion:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Cache Location:** `.easyeda_cache/`
**Files:** `{uuid}.obj`, `{uuid}.step`
