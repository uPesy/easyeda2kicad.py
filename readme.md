# easyeda2kicad.py

A Python script that convert any electronic components from [LCSC](https://www.lcsc.com/) or [EasyEDA](https://easyeda.com/) to a Kicad library

<p align="center">
  <img src="https://raw.githubusercontent.com/uPesy/easyeda2kicad.py/master/ressources/demo_symbol.png" width="500">
</p>
<div align="center">
  <img src="https://raw.githubusercontent.com/uPesy/easyeda2kicad.py/master/ressources/demo_footprint.png" width="500">
</div>


## Installation

```bash
git clone https://github.com/uPesy/easyeda2kicad.py.git
cd easyeda2kicad.py/
pip install requirements.txt
```
The script uses only one external library [pydantic](https://pydantic-docs.helpmanual.io/) for data validation.

## Usage
All librairies are saved in `easyeda2kicad.py/output_lib` :
- `easyeda2kicad.lib` for symbol library
- `easyeda2kicad.pretty/` for footprint library

**Cli usage :**

```bash
# For symbol + footprint
python easyeda2kicad.py --symbol --footprint --lcsc_id=C2040
# For symbol only
python easyeda2kicad.py --symbol --lcsc_id=C2040
# For footprint only
python easyeda2kicad.py --footprint --lcsc_id=C2040
```

## Add libraries in Kicad

Before configuring KiCad, run at least once time the script to create lib files

- In KiCad, Go to Preferences > Configure Paths, and add the environment variables `EASYEDA2KICAD` : `path/to/easyeda2kicad.py/ouput_lib`
- Go to Preferences > Manage Symbol Libraries, and Add the global library `easyeda2kicad` : `${EASYEDA2KICAD}/easyeda2kicad.lib`
- Go to Preferences > Manage Footprint Libraries, and Add the global library `easyeda2kicad` : `${EASYEDA2KICAD}/easyeda2kicad.pretty`
- Enjoy :wink:

## Notes

**It's still in development : all features are not implemented. I'm not a Python expert and don't have a lot of free time for coding.
I need your help to improve the code base architecture, adding unit tests and adding in the pip repo
Feel free to contribute on the `dev` branch :slightly_smiling_face:**

Some stuffs to be done:
- [ ] Improve the readme
- [ ] Refactoring the code
- [ ] Add unit testing and code coverage badge
- [ ] Adding in the Python repo to install it with pip
- [ ] Call the script directly from the terminal without using python easyeda2kicad.py

## Inspirations

- [KiPart](https://github.com/devbisme/KiPart) - A utility that generates single
and multi-unit symbols from a CSV file containing all the pin information for
one or more parts.
