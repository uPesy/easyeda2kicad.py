# easyeda2kicad

[![PyPI version](https://img.shields.io/pypi/v/easyeda2kicad.svg)](https://pypi.org/project/easyeda2kicad/)
[![License](https://img.shields.io/github/license/upesy/easyeda2kicad.py.svg)](https://github.com/uPesy/easyeda2kicad.py/blob/master/LICENSE)
[![Downloads](https://pepy.tech/badge/easyeda2kicad)](https://pepy.tech/project/easyeda2kicad)
![Python versions](https://img.shields.io/pypi/pyversions/easyeda2kicad.svg)
[![Git hook: pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Python script that converts any electronic components from [EasyEDA](https://easyeda.com/) or [LCSC](https://www.lcsc.com/) to a KiCad library including **3D model** in color. This tool will speed up your PCB design workflow especially when using [JLCPCB SMT assembly services](https://jlcpcb.com/caa). **It supports KiCad v6 and newer.**

<p align="center">
  <img src="https://raw.githubusercontent.com/uPesy/easyeda2kicad.py/master/ressources/demo_symbol.png" width="500">
</p>
<div align="center">
  <img src="https://raw.githubusercontent.com/uPesy/easyeda2kicad.py/master/ressources/demo_footprint.png" width="500">
</div>

## 💾 Installation

If you have Python installed on your system:

```bash
pip install easyeda2kicad
```

### Installation using the KiCad Command Prompt

KiCad ships with its own Python interpreter. If you don't have a separate Python installation, you can use KiCad's bundled Python to install easyeda2kicad.

**Windows:** KiCad bundles its own Python. Search for *KiCad Command Prompt* in the Start Menu, then run `pip install easyeda2kicad`. Note: KiCad's Scripts folder is not on PATH, so use `python -m easyeda2kicad` to run the tool from the KiCad Command Prompt.

**Linux:** On most distributions, KiCad uses the system Python — `pip install easyeda2kicad` works directly.

**macOS:** KiCad bundles its own Python. Install into it with:

```bash
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -m pip install easyeda2kicad
```

> **Tip:** In the PCB Editor, open *Tools → Scripting Console* and run `import sys; print(sys.executable)` to get KiCad's Python path. Then run that path with `-m pip install easyeda2kicad` in a terminal.

After installation, run `easyeda2kicad` from the same terminal or KiCad Command Prompt.

## 💻 Usage

```bash
# Symbol + footprint + 3D model
easyeda2kicad --full --lcsc_id=C2040
# Individual parts
easyeda2kicad --symbol --lcsc_id=C2040
easyeda2kicad --footprint --lcsc_id=C2040
easyeda2kicad --3d --lcsc_id=C2040
# Multiple components at once
easyeda2kicad --full --lcsc_id C2040 C20197 C163691
# Custom output path
easyeda2kicad --full --lcsc_id=C2040 --output ~/libs/my_lib
# SVG preview (no KiCad conversion)
easyeda2kicad --svg --lcsc_id=C2040 --output ~/libs/my_lib
```

By default, all libraries are saved in `~/Documents/Kicad/easyeda2kicad/` (Linux/macOS) or `C:/Users/your_name/Documents/Kicad/easyeda2kicad/` (Windows), with:

- `easyeda2kicad.kicad_sym` file for symbol library (KiCad v6+)
- `easyeda2kicad.pretty/` folder for footprint libraries
- `easyeda2kicad.3dshapes/` folder for 3D models (`.wrl` and `.step` format)

If you want to save components symbol/footprint in your own libs, you can specify the output lib path by using `--output` option.

```bash
easyeda2kicad --full --lcsc_id=C2040 --output ~/libs/my_lib
```

This command will save:

- the symbol in `~/libs/my_lib.kicad_sym` file for symbol library. The file will be created if it doesn't exist.
- the footprint in `~/libs/my_lib.pretty/` folder for footprint libraries. The folder will be created if it doesn't exist.
- the 3d models in `~/libs/my_lib.3dshapes/` folder for 3d models. The folder will be created if it doesn't exist. The 3D models will be saved both in .WRL and .STEP format.

Use `--overwrite` to replace an existing symbol, footprint, or 3D model already in the library:

```bash
easyeda2kicad --full --lcsc_id=C2040 --output ~/libs/my_lib --overwrite
```

### Project-relative 3D model paths

When working in a KiCad project folder, use `--project-relative` together with `--output` to store 3D model paths relative to the project root (`${KIPRJMOD}`):

```bash
easyeda2kicad --full --lcsc_id=C2040 --output ~/myproject/libs/my_lib --project-relative
```

This stores the 3D path as `${KIPRJMOD}/libs/my_lib.3dshapes/...` instead of an absolute filesystem path, making the project portable.

### Multiple IDs at once

You can import several components in a single call:

```bash
easyeda2kicad --full --lcsc_id C2040 C20197 C163691
```

### Custom symbol fields

Use `--custom-field` to add extra properties to generated symbols:

```bash
easyeda2kicad --symbol --lcsc_id=C2040 --custom-field "Manufacturer:Texas Instruments" "Package:LQFN-56"
```

Malformed values (missing `:`) fail fast. Duplicate keys use the last value.

If EasyEDA does not provide a datasheet URL for a symbol, easyeda2kicad falls back to `https://www.lcsc.com/datasheet/<LCSC-ID>.pdf`.

### Using a proxy server

Set the `HTTPS_PROXY` environment variable — no extra argument needed:

```bash
# Linux / macOS
HTTPS_PROXY=http://proxy.example.com:8080 easyeda2kicad --full --lcsc_id=C2040
# Windows
set HTTPS_PROXY=http://proxy.example.com:8080 && easyeda2kicad --full --lcsc_id=C2040
```

### Caching and debug

Use `--use-cache` to cache API responses in `.easyeda_cache/` for faster, offline-capable runs. Use `--debug` for verbose log output. Both flags can be combined:

```bash
easyeda2kicad --full --lcsc_id=C2040 --use-cache --debug
```

Clear the cache with `rm -rf .easyeda_cache`.

## 🔗 Add libraries in Kicad

**These are the instructions to add the default easyeda2kicad libraries in Kicad.**
Before configuring KiCad, run the script at least once to create lib files. For example :

```bash
easyeda2kicad --symbol --footprint --lcsc_id=C2040
```

- In KiCad, Go to Preferences > Configure Paths, and add the environment variables `EASYEDA2KICAD` :
  - Windows : `C:/Users/your_username/Documents/Kicad/easyeda2kicad/`,
  - Linux : `/home/your_username/Documents/Kicad/easyeda2kicad/`
- Go to Preferences > Manage Symbol Libraries, and Add the global library `easyeda2kicad` : `${EASYEDA2KICAD}/easyeda2kicad.kicad_sym`
- Go to Preferences > Manage Footprint Libraries, and Add the global library `easyeda2kicad` : `${EASYEDA2KICAD}/easyeda2kicad.pretty`
- Enjoy :wink:

## 📚 Documentation

For detailed information about the EasyEDA data format and how commands are parsed:

- **[CMD_FOOTPRINT.md](docs/CMD_FOOTPRINT.md)** - Compact reference for all footprint commands (PAD, TRACK, RECT, etc.) with field definitions and real examples
- **[CMD_SYMBOL.md](docs/CMD_SYMBOL.md)** - Compact reference for all symbol commands (P, R, C, E, A, PL, PG, PT) with field definitions and real examples
- **[CMD_3D_MODEL.md](docs/CMD_3D_MODEL.md)** - Reference for 3D model download, OBJ/STEP formats, and WRL conversion

## GUIs & related projects

- [Import-LIB-KiCad-Plugin](https://github.com/Steffen-W/Import-LIB-KiCad-Plugin) — KiCad plugin with GUI to import components directly within KiCad
- [EasyEDA2Kicad-GUI](https://github.com/ProjectProcrastinator/EasyEDA2Kicad-GUI) — cross-platform desktop GUI wrapper (Electron)
- [kicad_jlcimport](https://github.com/jvanderberg/kicad_jlcimport) — independent JLCPCB component importer for KiCad
- [easyEdaDownloader](https://github.com/JoeShade/easyEdaDownloader) — Chrome extension to download EasyEDA components (JavaScript)
- [easyeda2eagle](https://github.com/nschurando/easyeda2eagle) — EasyEDA to Eagle converter, based on this project

## 🔥 Important Notes

### WARRANTY

The correctness of the symbols and footprints converted by easyeda2kicad can't be guaranteed. Easyeda2kicad speeds up custom library design process, but you should remain careful and always double check the footprints and symbols generated.
