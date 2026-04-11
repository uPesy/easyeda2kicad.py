# easyeda2kicad v1.0.0

[![PyPI version](https://badge.fury.io/py/easyeda2kicad.svg)](https://badge.fury.io/py/easyeda2kicad)
[![License](https://img.shields.io/github/license/upesy/easyeda2kicad.py.svg)](https://pypi.org/project/isort/)
[![Downloads](https://pepy.tech/badge/easyeda2kicad)](https://pepy.tech/project/easyeda2kicad)
![Python versions](https://img.shields.io/pypi/pyversions/easyeda2kicad.svg)
[![Git hook: pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

A Python script that converts any electronic components from [EasyEDA](https://easyeda.com/) or [LCSC](https://www.lcsc.com/) to a KiCad library including **3D model** in color. This tool will speed up your PCB design workflow especially when using [JLCPCB SMT assembly services](https://jlcpcb.com/caa). **It supports KiCad v6 and newer.**

<p align="center">
  <img src="https://raw.githubusercontent.com/uPesy/easyeda2kicad.py/master/ressources/demo_symbol.png" width="500">
</p>
<div align="center">
  <img src="https://raw.githubusercontent.com/uPesy/easyeda2kicad.py/master/ressources/demo_footprint.png" width="500">
</div>

## 💾 Installation

If you have already Python installed you can run directly in the common terminal.<br>
If not, you can use the Python executable included with Kicad by using the KiCad Command Prompt.
<div align="left">
  <img src="/ressources/kicad_command_prompt_install.png" width="800">
</div>

Then run this command to install easyeda2kicad

```bash
pip install easyeda2kicad
```

### Installation using the KiCad Command Prompt

KiCad ships with its own Python interpreter. If you don't have a separate Python installation, you can use the **KiCad Command Prompt** to install easyeda2kicad into KiCad's Python environment.

**Windows:** Open the KiCad Command Prompt via *Start Menu → KiCad → KiCad Command Prompt*, then run:

```bash
pip install easyeda2kicad
```

**Linux / macOS:** KiCad's Python is typically not on the system PATH. Use the full path to KiCad's pip, for example:

```bash
/usr/lib/kicad/lib/python3/dist-packages/../../../bin/python3 -m pip install easyeda2kicad
```

Or locate it with:

```bash
find /usr -name "pip*" | grep kicad
```

After installation, run `easyeda2kicad` from the same KiCad Command Prompt.

## 💻 Usage

```bash
# For symbol + footprint + 3d model (with --full argument)
easyeda2kicad --full --lcsc_id=C2040
# For components not listed in public libraries (user-created)
easyeda2kicad --full --uuid=18f70c95488944a99ceedb9505986f4e
# For symbol + footprint + 3d model
easyeda2kicad --symbol --footprint --3d --lcsc_id=C2040
# For symbol + footprint
easyeda2kicad --symbol --footprint --lcsc_id=C2040
# For symbol only
easyeda2kicad --symbol --lcsc_id=C2040
# For footprint only
easyeda2kicad --footprint --lcsc_id=C2040
# For 3d model only
easyeda2kicad --3d --lcsc_id=C2040
# Import multiple components at once
easyeda2kicad --full --lcsc_id C2040 C20197 C163691
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

### Import User-created Components

If you created your own symbol, footprint or 3D model which is not listed in public libraries, you can retrieve the component by specifying the uuid argument. Find the uuid through the network inspector of your browser when you select a component in your workspace library(thus filed a request). The requested url should be something like these:
https://easyeda.com/api/components/{uuid}?version=6.5.42&uuid={uuid}&datastrid=blah
https://www.easyeda.com/api/components/{uuid}?version=6.5.54&uuid={uuid}&_=blah

### Custom symbol fields

Use `--custom-field` to add extra properties to generated symbols:

```bash
easyeda2kicad --symbol --lcsc_id=C2040 --custom-field "Manufacturer:Texas Instruments" "Package:LQFN-56"
```

Malformed values (missing `:`) fail fast. Duplicate keys use the last value.

If EasyEDA does not provide a datasheet URL for a symbol, easyeda2kicad falls
back to `https://www.lcsc.com/datasheet/<LCSC-ID>.pdf`.

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

## 🔥 Important Notes

### WARRANTY

The correctness of the symbols and footprints converted by easyeda2kicad can't be guaranteed. Easyeda2kicad speeds up custom library design process, but you should remain careful and always double check the footprints and symbols generated.
